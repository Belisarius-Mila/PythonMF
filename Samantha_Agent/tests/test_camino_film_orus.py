"""Orus contract: no private network calls, exact consent, bounded cost and real local audio."""
import base64
import copy
import io
import http.client
import json
import math
import os
from pathlib import Path
import struct
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
import wave

from app import camino_film_orus as orus
from app.camino_film_narration import prepare_narration, narration_bytes
from camino.film.project import FilmError
from tests import test_camino_film_photo_layers as photo_layers


def consent(text):
    return {"text": text, "voice": orus.VOICE, "tempo": 0.9,
            "max_cost_microusd": len(text) * 30}


def wav_bytes(seconds=0.5):
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(24000)
        audio.writeframes(b"".join(struct.pack("<h", int(5000 * math.sin(2 * math.pi * 440 * i / 24000)))
                                  for i in range(round(seconds * 24000))))
    return output.getvalue()


class OrusContractTests(unittest.TestCase):
    def test_utf8_chunks_keep_every_character_newline_and_emoji(self):
        for text in ["A" * 6000, "🙂" * 6000, ("Příliš žluťoučký kůň.\n" * 400)[:6000], " x " * 2000]:
            with self.subTest(length=len(text)):
                chunks = orus.split_text(text)
                self.assertEqual("".join(chunks), text)
                self.assertTrue(all(0 < len(part.encode("utf-8")) <= 5000 for part in chunks))
                self.assertLessEqual(len(chunks), 10)

    def test_consent_binds_text_voice_tempo_and_exact_price(self):
        text = "🙂 Český text.\n"
        self.assertEqual(orus.consent_cost(text, consent(text)), len(text) * 30)
        for key, value in [("text", text + " "), ("voice", "Zuzana"), ("tempo", 1.0),
                           ("max_cost_microusd", True), ("max_cost_microusd", 1),
                           ("max_cost_microusd", 999999)]:
            with self.subTest(key=key, value=value):
                with self.assertRaises(FilmError):
                    orus.consent_cost(text, {**consent(text), key: value})
        with self.assertRaises(FilmError):
            orus.consent_cost("x" * 6001, consent("x" * 6001))

    def test_credentials_stay_local_and_unsafe_permissions_or_symlink_block_auth(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            key = root / "key.json"
            key.write_text('{"private_key":"SYNTHETIC-SECRET"}'); key.chmod(0o600)
            with patch.object(orus, "CREDENTIAL_FILE", key):
                with patch.object(orus, "_credential_bytes", side_effect=AssertionError("readiness must not read secrets")):
                    self.assertTrue(orus.voice_profile()["ready"])
                key.chmod(0o644)
                self.assertFalse(orus.voice_profile()["ready"])
                with self.assertRaises(FilmError) as error: orus.access_token()
                self.assertNotIn("SYNTHETIC-SECRET", str(error.exception))
            linked = root / "linked.json"; linked.symlink_to(key)
            with patch.object(orus, "CREDENTIAL_FILE", linked):
                self.assertFalse(orus.voice_profile()["ready"])

    def test_official_auth_validates_destination_and_redacts_errors(self):
        info = {"type": "service_account", "project_id": "camino-orus", "token_uri": orus.TOKEN_URL}
        credentials = Mock(token="SYNTHETIC-ACCESS-TOKEN")
        with patch.object(orus, "_credential_bytes", return_value=json.dumps(info).encode()), \
             patch("google.oauth2.service_account.Credentials.from_service_account_info", return_value=credentials):
            self.assertEqual(orus.access_token(), "SYNTHETIC-ACCESS-TOKEN")
            credentials.refresh.assert_called_once()
        info["token_uri"] = "https://foreign.invalid/token"
        with patch.object(orus, "_credential_bytes", return_value=json.dumps(info).encode()), \
             patch("google.oauth2.service_account.Credentials.from_service_account_info") as factory:
            with self.assertRaises(FilmError): orus.access_token()
            factory.assert_not_called()

    def test_synthesis_http_failure_and_timeout_are_never_retried_or_exposed(self):
        for error in [HTTPError(orus.SYNTHESIS_URL, 403, "SYNTHETIC-SECRET", {}, io.BytesIO(b"secret")),
                      URLError("SYNTHETIC-SECRET"), TimeoutError("SYNTHETIC-SECRET")]:
            opener = Mock(); opener.open.side_effect = error
            with patch.object(orus, "build_opener", return_value=opener):
                with self.assertRaises(FilmError) as caught:
                    orus.request_audio("Syntetický text.", "SYNTHETIC-TOKEN")
            self.assertEqual(opener.open.call_count, 1)
            self.assertNotIn("SYNTHETIC", str(caught.exception))

    def test_audio_post_uses_exact_text_and_fixed_google_endpoint(self):
        text = "Celý text.\nDruhý řádek 🙂"
        response = Mock()
        response.__enter__ = Mock(return_value=response); response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps({"audioContent": base64.b64encode(wav_bytes()).decode()}).encode()
        opener = Mock(); opener.open.return_value = response
        with patch.object(orus, "build_opener", return_value=opener):
            result = orus.request_audio(text, "SYNTHETIC-TOKEN")
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, orus.SYNTHESIS_URL)
        self.assertEqual(json.loads(request.data)["input"]["text"], text)
        self.assertEqual(json.loads(request.data)["voice"]["name"], orus.VOICE)
        self.assertEqual(result, wav_bytes())
        self.assertIsNone(orus._NoRedirect().redirect_request(None, None, None, None, None, None))

    def test_real_joined_audio_keeps_full_6000_characters_and_slower_tempo(self):
        from camino.film.media import probe, duration_ms
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            text = "🙂" * 6000
            parts = orus.split_text(text)
            with patch.object(orus, "access_token", return_value="synthetic"), \
                 patch.object(orus, "request_audio", return_value=wav_bytes()) as request:
                revalidate = Mock()
                length = orus.synthesize_orus(text, directory, consent(text), revalidate)
            self.assertEqual("".join(c.args[0] for c in request.call_args_list), text)
            self.assertEqual(request.call_count, len(parts))
            self.assertEqual(revalidate.call_count, len(parts) + 1)
            self.assertAlmostEqual(length, 500 * len(parts) / .9, delta=150)
            self.assertEqual(duration_ms(probe(directory / "speech.m4a"), "audio"), length)
            self.assertEqual(len(list(directory.glob("cloud-part-*-request.json"))), len(parts))

    def test_privacy_change_stops_before_next_part_and_never_falls_back(self):
        with tempfile.TemporaryDirectory() as tmp:
            text = "🙂" * 6000
            with patch.object(orus, "access_token", return_value="synthetic"), \
                 patch.object(orus, "request_audio", return_value=wav_bytes()) as request, \
                 patch("app.camino_film_narration.synthesize") as local:
                validate = Mock(side_effect=[None, FilmError("Soukromí se změnilo.")])
                with self.assertRaises(FilmError):
                    orus.synthesize_orus(text, Path(tmp), consent(text), validate)
            self.assertEqual(request.call_count, 1)
            local.assert_not_called()
            self.assertFalse((Path(tmp) / "speech.m4a").exists())


class OrusEditorTests(unittest.TestCase):
    setUp = photo_layers.PhotoLayerTests.setUp
    payload = photo_layers.PhotoLayerTests.payload
    save_text = photo_layers.PhotoLayerTests.save_text
    narration_payload = photo_layers.PhotoLayerTests.narration_payload

    def request(self):
        self.save_text("Syntetický komentář pro Orus.")
        request = self.narration_payload()
        request["cloud_consent"] = consent("Syntetický komentář pro Orus.")
        return request

    def test_editor_orus_receipt_history_and_replay_do_not_duplicate_requests(self):
        request = self.request()
        def speak(text, directory, approved, validate):
            validate(); (directory / "speech.m4a").write_bytes(b"synthetic Orus audio")
            return 11000
        with patch.object(orus, "synthesize_orus", side_effect=speak) as cloud, \
             patch("app.camino_film_narration.synthesize") as local:
            result = prepare_narration(self.editor, request)
            self.assertEqual(prepare_narration(self.editor, request), result)
        self.assertEqual(cloud.call_count, 1); local.assert_not_called()
        take = self.editor.view()["narrations"][0]
        self.assertEqual(take["label"], "Orus · tempo −10 %")
        self.assertEqual(narration_bytes(self.editor, self.pid, request["request_id"]), b"synthetic Orus audio")
        receipt = json.loads((self.store.root / self.pid / "narrations" / request["request_id"] / "receipt.json").read_text())
        self.assertEqual(receipt["voice"], orus.VOICE); self.assertEqual(receipt["tempo"], .9)
        self.assertEqual(receipt["max_cost_microusd"], len(request["cloud_consent"]["text"]) * 30)

    def test_bad_or_stale_consent_never_calls_cloud_or_creates_attempt(self):
        request = self.request()
        request["cloud_consent"]["text"] += " jiný"
        with patch.object(orus, "synthesize_orus") as cloud:
            with self.assertRaises(FilmError): prepare_narration(self.editor, request)
        cloud.assert_not_called()
        self.assertFalse((self.store.root / self.pid / "narrations").exists())

    def test_uncertain_attempt_replay_does_not_retransmit_or_call_local_voice(self):
        request = self.request()
        with patch.object(orus, "synthesize_orus", side_effect=FilmError("Výsledek není potvrzený.")) as cloud, \
             patch("app.camino_film_narration.synthesize") as local:
            with self.assertRaises(FilmError): prepare_narration(self.editor, request)
            with self.assertRaisesRegex(FilmError, "nepotvrzený|není potvrzený"):
                prepare_narration(self.editor, request)
        self.assertEqual(cloud.call_count, 1); local.assert_not_called()
        self.assertEqual(self.editor.view()["narrations"], [])

    def test_privacy_or_text_changed_during_cloud_audio_is_not_attached(self):
        request = self.request()
        def changed(text, directory, approved, validate):
            (directory / "speech.m4a").write_bytes(b"synthetic audio")
            self.save_text("Jiná verze textu.")
            return 1000
        with patch.object(orus, "synthesize_orus", side_effect=changed):
            with self.assertRaisesRegex(FilmError, "změnilo"):
                prepare_narration(self.editor, request)
        self.assertEqual(self.editor.view()["narrations"], [])

    def test_http_consent_route_checks_origin_and_accepts_only_exact_text(self):
        from app import cockpit
        request = self.request()
        server = ThreadingHTTPServer(("127.0.0.1", 0), cockpit.CockpitServer().make_handler())
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.addCleanup(thread.join, 3); self.addCleanup(server.server_close); self.addCleanup(server.shutdown)
        def post(payload, origin=None):
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)
            headers = {"Content-Type": "application/json"}
            if origin: headers["Origin"] = origin
            connection.request("POST", "/api/camino/film/narration", json.dumps(payload), headers)
            response = connection.getresponse(); body = json.loads(response.read()); connection.close()
            return response.status, body
        def speak(text, directory, approved, validate):
            validate(); (directory / "speech.m4a").write_bytes(b"synthetic Orus audio")
            return 11000
        with patch("app.camino_film_editor.production_editor", return_value=self.editor), \
             patch.object(orus, "synthesize_orus", side_effect=speak) as cloud:
            self.assertEqual(post(request, "https://foreign.invalid")[0], 403)
            changed = copy.deepcopy(request); changed["cloud_consent"]["text"] += " cizí"
            self.assertEqual(post(changed)[0], 409)
            cloud.assert_not_called()
            code, result = post(request)
            self.assertEqual(code, 200); self.assertTrue(result["ok"])
            self.assertEqual(post(request)[0], 200)
            self.assertEqual(cloud.call_count, 1)
