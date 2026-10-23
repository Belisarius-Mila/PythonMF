"""Bounded serial SDR rendering from an immutable real-day edit; no archive writes."""
from __future__ import annotations

import math
import os
import shutil
import subprocess
import time
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from app.camino_film_editor import validate_draft, timeline_shots, TEXT_CARD_FIT_ERROR
from app.camino_film_photo import PHOTO_VIEW_SIZE, decode_photo, read_photo
from camino.film.media import FONT, binary, duration_ms, probe, title_image
from camino.film.project import FilmError, digest, fingerprint, write_json
from camino.film.render import DiskMeter, PROFILES


def ffmpeg(args, *, timeout=600):
    try:
        result = subprocess.run(["/usr/bin/nice", "-n", "10", binary("ffmpeg"), "-nostdin", "-hide_banner",
             "-v", "error", "-xerror", "-n", "-threads", "2", "-filter_complex_threads", "1",
             *args], stdin=subprocess.DEVNULL, capture_output=True, timeout=timeout,
             check=False, umask=0o077)
        if result.returncode:
            raise FilmError("Mediální proces nedokončil export.")
    except (FilmError, OSError, subprocess.TimeoutExpired) as error:
        raise FilmError("Místní mediální proces selhal; neúplný export se nevydává.") from error


def window(draft, total, interval):
    start, end = (interval["start_ms"], interval["end_ms"]) if interval else (0, total)
    shots, voices, cursor = [], [], 0
    for shot in timeline_shots(draft):
        if not shot["included"]:
            continue
        length = shot["out_ms"] - shot["in_ms"]
        lo, hi = max(start, cursor), min(end, cursor + length)
        if hi > lo:
            offset = lo - cursor
            shots.append({**shot, "in_ms": shot["in_ms"] + offset,
                "out_ms": shot["in_ms"] + offset + hi - lo, "at_ms": lo - start})
        cursor += length
    for voice in draft["voices"]:
        if not voice["included"]:
            continue
        lo = max(start, voice["at_ms"])
        hi = min(end, voice["at_ms"] + voice["out_ms"] - voice["in_ms"])
        if hi > lo:
            offset = lo - voice["at_ms"]
            voices.append({**voice, "at_ms": lo - start, "in_ms": voice["in_ms"] + offset,
                           "out_ms": voice["in_ms"] + offset + hi - lo})
    return shots, voices, end - start


def prepare_photo(source: Path, target: Path, size=None):
    """Decode the main SDR photo, not auxiliary MPO images; keep its complete frame."""
    with decode_photo(read_photo(source), size or PHOTO_VIEW_SIZE) as photo:
        with target.open("xb") as handle:
            photo.save(handle, "PNG")
    target.chmod(0o600)


def text_card_image(target, text, size):
    """Fit the complete author-selected text, never silently clip or shorten it."""
    width, height = size
    image = Image.new("RGB", size, (20, 27, 38))
    draw = ImageDraw.Draw(image)
    for pixels in range(round(height * .055), round(height * .029) - 1, -1):
        font = ImageFont.truetype(str(FONT), pixels)
        lines = []
        for paragraph in text.split("\n"):
            line = ""
            for word in paragraph.split():
                if draw.textlength(word, font=font) > width * .84:
                    lines = None
                    break
                candidate = (line + " " + word).strip()
                if draw.textlength(candidate, font=font) > width * .84:
                    lines.append(line); line = word
                else:
                    line = candidate
            if lines is None:
                break
            lines.append(line)
        spacing = round(pixels * 1.4)
        if lines is not None and len(lines) * spacing <= height * .8:
            top = (height - len(lines) * spacing) / 2
            for i, line in enumerate(lines):
                draw.text((width / 2, top + i * spacing), line, anchor="mt", fill="white", font=font)
            with target.open("xb") as handle:
                image.save(handle, "PNG")
            target.chmod(0o600)
            return
    raise FilmError(TEXT_CARD_FIT_ERROR)


def render_audio_preview(edit, manifest, objects, output, *, revalidate):
    """Metadata-free AAC listening copy, never an original-media HTTP route."""
    sid = edit["audio_preview"]
    source = next(s for s in manifest["sources"] if s["asset_id"] == sid and s["media_kind"] == "audio")
    path = objects / (sid + ".bin")
    if path.is_symlink() or not path.is_file() or digest(path) != source["sha256"]:
        raise FilmError("Komentář neodpovídá uzavřeným podkladům.")
    info = probe(path)
    if (len([s for s in info["streams"] if s["codec_type"] == "audio"]) != 1
            or type(source["duration_ms"]) is not int or not 1 <= source["duration_ms"] <= 3_600_000
            or abs(duration_ms(info, "audio") - source["duration_ms"]) > 60):
        raise FilmError("Komentář nemá ověřenou délku a zvukovou stopu.")
    if shutil.disk_usage(output).free < source["duration_ms"] * 100 + 128 * 1024**2:
        raise FilmError("Chybí místo pro poslechovou kopii komentáře.")
    revalidate()
    partial = output / "render.partial.mp4"
    ffmpeg(["-protocol_whitelist", "file,pipe", "-i", str(path), "-map", "0:a:0", "-vn",
            "-map_metadata", "-1", "-map_chapters", "-1", "-c:a", "aac", "-b:a", "192k",
            "-ar", "48000", "-movflags", "+faststart", str(partial)])
    decoded = probe(partial)
    if (any(s["codec_type"] == "video" for s in decoded["streams"])
            or abs(duration_ms(decoded, "audio") - source["duration_ms"]) > 100):
        raise FilmError("Poslechová kopie nemá správnou délku.")
    ffmpeg(["-protocol_whitelist", "file,pipe", "-i", str(partial), "-f", "null", "-"])
    revalidate()
    final = output / "film.mp4"
    os.link(partial, final)
    with final.open("rb") as handle:
        os.fsync(handle.fileno())
    receipt = {"schema": 1, "scope": "camino-film-audio-preview", "state": "verified",
        "project_id": edit["project_id"], "source_asset_id": sid, "edit_sha256": fingerprint(edit),
        "manifest_sha256": fingerprint(manifest), "bytes": final.stat().st_size, "sha256": digest(final),
        "audio_ms": duration_ms(decoded, "audio"), "decoded_entire_file": True}
    write_json(output / "receipt.json", receipt)
    return receipt


def render_edit(edit, manifest, objects: Path, output: Path, profile, interval, *, progress, revalidate):
    total = validate_draft(edit["draft"], manifest)
    shots, voices, length = window(edit["draft"], total, interval)
    width, height, quality = PROFILES[profile]
    estimate = math.ceil(length / 1000 * 8_000_000) + 64 * 1024**2
    free_before = shutil.disk_usage(output).free
    if free_before < estimate + 1024**3:
        raise FilmError("Chybí místo pro bezpečný export včetně pracovních souborů.")
    sources = {s["asset_id"]: s for s in manifest["sources"]}
    info = {}
    for sid in {r["asset_id"] for r in [*shots, *voices] if "asset_id" in r}:
        source = sources[sid]
        path = objects / (sid + ".bin")
        if path.is_symlink() or not path.is_file() or digest(path) != source["sha256"]:
            raise FilmError("Originál už neodpovídá uzavřenému manifestu.")
        data = probe(path)
        kind = "audio" if source["media_kind"] == "audio" else "video"
        streams = [s for s in data["streams"] if s["codec_type"] == kind]
        if len(streams) != 1:
            raise FilmError("Zdroj nemá jednoznačnou obrazovou nebo zvukovou stopu.")
        track = streams[0]
        if kind == "video" and ((source["media_kind"] != "photo" and max(track.get("width", 0), track.get("height", 0)) > 4096)
                or track.get("color_transfer") in ("smpte2084", "arib-std-b67")
                or track.get("color_primaries") == "bt2020"):
            raise FilmError("Tato verze renderu vyžaduje SDR zdroje a video do 4096 pixelů; HDR se nepřevádí bez ověření.")
        if source["media_kind"] != "photo" and abs(duration_ms(data, kind) - source["duration_ms"]) > 60:
            raise FilmError("Skutečná délka média nesouhlasí s manifestem.")
        info[sid] = data
    revalidate()
    started = time.monotonic()
    with DiskMeter(output) as meter:
        segments = []
        for index, shot in enumerate(shots):
            revalidate()
            card = "card_id" in shot
            source = sources[shot["asset_id"]] if not card else {"media_kind": "text"}
            path = objects / (shot["asset_id"] + ".bin") if not card else output / f"card-{index:04d}.png"
            ms = shot["out_ms"] - shot["in_ms"]
            # Quantize cumulative boundaries, avoiding drift from rounding every clip independently.
            frames = round((shot["at_ms"] + ms) * 30 / 1000) - round(shot["at_ms"] * 30 / 1000)
            if frames < 1:
                raise FilmError("Náhled obsahuje úsek kratší než jeden snímek.")
            seconds = frames / 30
            photo = source["media_kind"] in ("photo", "text")
            if card:
                text_card_image(path, shot["title"], (width, height))
            elif photo:
                working = output / f"photo-{index:04d}.png"
                prepare_photo(path, working, (width, height))
                path = working
            args = ["-loop", "1", "-framerate", "30"] if photo else []
            args += ["-protocol_whitelist", "file,pipe", "-i", str(path)]
            title = output / f"title-{index:04d}.png"
            title_image(title, "" if card else shot["title"], (width, height))
            title.chmod(0o600)
            args += ["-protocol_whitelist", "file,pipe", "-i", str(title)]
            start, end = (0, ms / 1000) if photo else (shot["in_ms"] / 1000, shot["out_ms"] / 1000)
            graph = [f"[0:v]trim=start={start}:end={end},setpts=PTS-STARTPTS,fps=30,"
                f"scale={width}:{height}:force_original_aspect_ratio=decrease:force_divisible_by=2:in_range=auto:out_range=tv:out_color_matrix=bt709,"
                f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p,"
                f"tpad=stop_mode=clone:stop_duration=0.1,trim=duration={seconds}[base]",
                f"[base][1:v]overlay=eof_action=repeat:shortest=0,trim=duration={seconds},"
                "setparams=range=limited:color_primaries=bt709:color_trc=bt709:colorspace=bt709[video]"]
            has_audio = not card and any(s["codec_type"] == "audio" for s in info[shot["asset_id"]]["streams"])
            audio = f"[0:a]atrim=start={start}:end={end},asetpts=PTS-STARTPTS," if has_audio else "anullsrc=r=48000:cl=stereo,"
            graph.append(audio + "aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                f"volume={shot['gain']},apad,atrim=duration={seconds}[audio]")
            segment = output / f"segment-{index:04d}.mkv"
            ffmpeg([*args, "-filter_complex", ";".join(graph), "-map", "[video]", "-map", "[audio]",
                "-map_metadata", "-1", "-map_chapters", "-1", "-c:v", "libx264", "-threads", "2",
                "-preset", "veryfast", "-crf", str(quality), "-pix_fmt", "yuv420p",
                "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
                "-c:a", "pcm_s16le", "-ar", "48000", "-t", str(seconds), str(segment)])
            segments.append(segment)
            progress(round(80 * (index + 1) / len(shots)))
        # The concat file contains generated basenames only, never user text or source paths.
        concat = output / "segments.txt"
        with concat.open("x") as handle:
            handle.write("".join(f"file '{p.name}'\n" for p in segments))
        concat.chmod(0o600)
        args = ["-protocol_whitelist", "file,pipe", "-f", "concat", "-safe", "1", "-i", str(concat)]
        # Matroska's millisecond packet timestamps can overlap by a few PCM samples
        # at joins. Derive one monotonic clock from the actual concatenated samples.
        graph, bed, labels = ["[0:a]asettb=1/48000,asetpts=N/SR/TB[bed0]"], "bed0", []
        for index, voice in enumerate(voices):
            at = voice["at_ms"] / 1000
            end = at + (voice["out_ms"] - voice["in_ms"]) / 1000
            graph.append(f"[{bed}]volume={edit['draft']['duck_gain']}:enable='between(t,{at},{end})'[duck{index}]")
            bed = f"duck{index}"
            args += ["-protocol_whitelist", "file,pipe", "-i", str(objects / (voice["asset_id"] + ".bin"))]
            graph.append(f"[{index+1}:a]atrim=start={voice['in_ms']/1000}:end={voice['out_ms']/1000},"
                "asetpts=PTS-STARTPTS,aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo,"
                f"volume={voice['gain']},adelay={voice['at_ms']}:all=1,apad,atrim=duration={length/1000}[voice{index}]")
            labels.append(f"[voice{index}]")
        graph.append(f"[{bed}]{''.join(labels)}amix=inputs={1+len(voices)}:normalize=0:duration=longest,"
                     f"volume=0.8,atrim=duration={length/1000}[audio]")
        partial = output / "render.partial.mp4"
        ffmpeg([*args, "-filter_complex", ";".join(graph), "-map", "0:v", "-map", "[audio]",
            "-map_metadata", "-1", "-map_chapters", "-1", "-c:v", "copy", "-c:a", "aac",
            "-b:a", "192k", "-ar", "48000", "-t", str(length/1000), "-movflags", "+faststart", str(partial)])
        progress(90)
        data = probe(partial)
        video = next(s for s in data["streams"] if s["codec_type"] == "video")
        audio = next(s for s in data["streams"] if s["codec_type"] == "audio")
        if ((video["width"], video["height"]) != (width, height) or video["codec_name"] != "h264"
                or audio["codec_name"] != "aac"
                or int(video.get("nb_frames", -1)) != round(length * 30 / 1000)
                or any(abs(duration_ms(data, kind) - length) > 100 for kind in ("video", "audio"))):
            raise FilmError("Výstup má chybný formát nebo nesouhlasí délka obrazu a zvuku.")
        ffmpeg(["-protocol_whitelist", "file,pipe", "-i", str(partial), "-f", "null", "-"])
        revalidate()
        final = output / "film.mp4"
        os.link(partial, final)
        with final.open("rb") as handle:
            os.fsync(handle.fileno())
    receipt = {"schema": 1, "scope": "camino-film-edit", "state": "verified", "profile": profile,
        "project_id": edit["project_id"], "revision": edit["revision"], "edit_sha256": fingerprint(edit),
        "manifest_sha256": fingerprint(manifest), "range": interval, "timeline_ms": length,
        "video_ms": duration_ms(data, "video"), "audio_ms": duration_ms(data, "audio"),
        "width": width, "height": height, "sha256": digest(final), "bytes": final.stat().st_size,
        "elapsed_seconds": round(time.monotonic() - started, 3), "decoded_entire_file": True,
        "peak_work_logical_bytes": meter.peak[0], "peak_work_allocated_bytes": meter.peak[1],
        "free_before_bytes": free_before, "free_after_bytes": shutil.disk_usage(output).free,
        "human_playback": "NOT_VERIFIED", "voices_selected": len(voices)}
    write_json(output / "receipt.json", receipt)
    return receipt
