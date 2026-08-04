import ui
import csv
import random
import speech
import json
import time
import os
import webbrowser
from urllib.parse import quote
from pathlib import Path
from datafresh_sync import refresh_files_from_icloud

try:
    from datafresh_sync import (
        DATAFRESH_API_VERSION,
        datafresh_status_text,
        refresh_result_succeeded,
    )
except ImportError:
    DATAFRESH_API_VERSION = 1

    def refresh_result_succeeded(result, filename):
        return False

    def datafresh_status_text(result, filename, loaded_rows):
        return '✗ Nahraj spolu s AppFR.py také nový datafresh_sync.py.'

try:
    import console
except Exception:
    console = None
try:
    import dialogs
except Exception:
    dialogs = None
try:
    from objc_util import ObjCClass
except Exception:
    ObjCClass = None

# --- PATH SETTINGS ---
BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / 'VocabularyFR.csv'
VERBE_FILE = BASE_DIR / 'VerbeFR.csv'
JSON_FILE = BASE_DIR / 'mapping.json'
PICT_FOLDER = BASE_DIR / 'Pict'
TTS_LOG_FILE = BASE_DIR / 'tts_fr_debug.log'
SOURCES_FILE = BASE_DIR / 'datafresh_sources.json'
FORCE_MANUAL_DATAFRESH_MAPPING = False
FAST_DATAFRESH_ONLY = True
VOCAB_REQUIRED_COLUMNS = ('FR', 'CZ')
IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.webp', '.gif')


class VocabTrainer(ui.View):
    def __init__(self):
        self.background_color = '#f2f2f7'
        self.update_interval = 0.1
        self.words = []
        self.image_map = {}
        self.image_folded_map = {}
        self.image_alias_map = {}
        self.current_word = None
        self.current_index = None
        self.filter_ht = False
        self.last_count = None
        self.verbe_rows = []
        self.verbe_selected_index = None
        self.verbe_speech_token = 0

        # Selection cycle state: random order without repeats in current set.
        self.selection_signature = None
        self.shown_in_selection = set()
        self.auto_running = False
        self.auto_mode = 'basic'
        self.auto_phase = 'idle'
        self.auto_next_time = 0.0
        self.auto_wait_deadline = 0.0
        self.auto_wait_seen_speaking = False
        self.auto_wait_next_phase = 'idle'
        self.auto_wait_after_gap = 0.0
        self._av_synth = None
        self._last_utterance = None
        self.sync_files = [CSV_FILE.name]
        # Canonical source: iCloud Drive / PythonMF / VocabularyFR / VocabularyFR.csv.
        # Do not fall back to older PythonMF/VocabularyFR.csv copies.
        self.sync_dir_hints = ('PythonMF/VocabularyFR',)
        self.source_overrides = self._load_source_overrides()
        self._tts_log('init.start')
        self._tts_recover('init')

        self.image_map = self._load_image_map()

        # Load CSV words
        if CSV_FILE.exists():
            try:
                self.words = self._read_csv_rows(CSV_FILE)
            except Exception:
                pass

        self.setup_ui()

    def _load_source_overrides(self):
        if not SOURCES_FILE.exists():
            return {}
        try:
            with open(SOURCES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, dict):
                return {str(k): str(v) for k, v in data.items() if v}
        except Exception:
            pass
        return {}

    def _save_source_overrides(self):
        try:
            with open(SOURCES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.source_overrides or {}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self._tts_log('source_overrides.save.error', error=repr(e))

    def _picture_folders(self):
        project_dir = BASE_DIR.parent
        candidates = [
            BASE_DIR / 'Pict',
            project_dir / 'Pict',
            Path.cwd() / 'Pict',
            Path.home() / 'Documents' / 'Pict',
        ]
        folders = []
        seen = set()
        for folder in candidates:
            try:
                resolved = folder.expanduser().resolve()
            except Exception:
                resolved = folder
            key = str(resolved)
            if key in seen:
                continue
            seen.add(key)
            folders.append(folder)
        return folders

    def _load_image_map(self):
        mapping_paths = [
            folder / 'mapping.json'
            for folder in self._picture_folders()
            if (folder / 'mapping.json').exists()
        ][:1]
        image_stems = set(self._picture_file_index())
        exact_candidates = {}
        folded_candidates = {}
        alias_candidates = {}
        for mapping_path in mapping_paths:
            if not mapping_path.exists():
                continue
            try:
                with open(mapping_path, mode='r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    for key, value in data.items():
                        key_norm = self._normalize_mapping_key(str(key))
                        folded_key = self._normalize_key(str(key))
                        value_norm = self._normalize_key(str(value))
                        if key_norm and value_norm:
                            exact_candidates.setdefault(key_norm, []).append(value_norm)
                            folded_candidates.setdefault(folded_key, []).append(value_norm)
                            for alias in self._mapping_key_parts(key):
                                alias_candidates.setdefault(alias, []).append(value_norm)
            except Exception as e:
                self._tts_log('image_map.load.error', path=str(mapping_path), error=repr(e))

        def _best_existing_value(values):
            ordered = []
            for value in values:
                if value and value not in ordered:
                    ordered.append(value)
            for value in ordered:
                if value in image_stems:
                    return value
            return ordered[0] if ordered else None

        image_map = {}
        for key, values in exact_candidates.items():
            selected = _best_existing_value(values)
            if selected:
                image_map[key] = selected

        image_folded_map = {}
        for key, values in folded_candidates.items():
            existing = []
            for value in values:
                if value in image_stems and value not in existing:
                    existing.append(value)
            if len(existing) == 1:
                image_folded_map[key] = existing[0]
        self.image_folded_map = image_folded_map

        image_alias_map = {}
        for alias, values in alias_candidates.items():
            existing = []
            for value in values:
                if value in image_stems and value not in existing:
                    existing.append(value)
            if len(existing) == 1:
                image_alias_map[alias] = existing[0]
        self.image_alias_map = image_alias_map
        return image_map

    def _mapping_key_parts(self, text):
        import re

        parts = re.split(r'[,;/|()]', str(text or ''))
        normalized = []
        for part in parts:
            key = self._normalize_mapping_key(part)
            if len(key) >= 4 and key not in normalized:
                normalized.append(key)
        return normalized

    def _find_image_path(self, img_base_name):
        if not img_base_name:
            return None
        raw = str(img_base_name).strip()
        direct = Path(raw)
        if direct.suffix:
            candidates = [direct]
            if not direct.is_absolute():
                candidates.extend(folder / raw for folder in self._picture_folders())
            for candidate in candidates:
                if candidate.exists():
                    return candidate

        lookup_stem = direct.stem if direct.suffix else raw
        return self._picture_file_index().get(self._normalize_key(lookup_stem))

    def _picture_file_index(self):
        """Map normalized stems to real paths without losing filename casing."""
        cached = getattr(self, '_picture_files_cache', None)
        if cached is not None:
            return cached

        images = {}
        extension_rank = {ext: index for index, ext in enumerate(IMAGE_EXTENSIONS)}
        for folder in self._picture_folders():
            if not folder.exists():
                continue
            try:
                names = os.listdir(str(folder))
            except Exception:
                continue
            names.sort(
                key=lambda name: (
                    extension_rank.get(Path(name).suffix.casefold(), len(extension_rank)),
                    name.casefold(),
                    name,
                )
            )
            for name in names:
                path = folder / name
                if not path.is_file() or path.suffix.casefold() not in extension_rank:
                    continue
                stem = self._normalize_key(path.stem)
                if stem and stem not in images:
                    images[stem] = path
        self._picture_files_cache = images
        return images

    def _picture_stems(self):
        return set(self._picture_file_index())

    def _image_base_name_for_word(self, row):
        fr_word = (row.get('FR') or '').strip()
        cz_word = (row.get('CZ') or '').strip()
        mapping_keys = [
            self._normalize_mapping_key(fr_word),
            self._normalize_mapping_key(cz_word),
        ]
        folded_keys = [self._normalize_key(fr_word), self._normalize_key(cz_word)]
        stems = self._picture_stems()
        for key in mapping_keys:
            mapped = self.image_map.get(key)
            if mapped and mapped in stems:
                return mapped

        for key in folded_keys:
            mapped = self.image_folded_map.get(key)
            if mapped and mapped in stems:
                return mapped

        for text in (fr_word, cz_word):
            for alias in self._mapping_key_parts(text):
                mapped = self.image_alias_map.get(alias)
                if mapped and mapped in stems:
                    return mapped
        for key in folded_keys:
            if key and key in stems:
                return key
        return None

    def _load_ui_image(self, image_path):
        """Load common image formats with fallbacks suitable for Pythonista."""
        if not image_path:
            return None
        try:
            image = ui.Image.named(str(image_path))
            if image is not None:
                return image
        except Exception as e:
            self._tts_log('image.named.error', path=image_path.name, error=repr(e))

        try:
            image = ui.Image.from_data(image_path.read_bytes())
            if image is not None:
                return image
        except Exception as e:
            self._tts_log('image.data.error', path=image_path.name, error=repr(e))

        try:
            import io
            from PIL import Image as PILImage

            with PILImage.open(str(image_path)) as source:
                converted = source.convert('RGBA')
                output = io.BytesIO()
                converted.save(output, format='PNG')
            image = ui.Image.from_data(output.getvalue())
            if image is not None:
                return image
        except Exception as e:
            self._tts_log('image.pil.error', path=image_path.name, error=repr(e))

        self._tts_log('image.load.failed', path=image_path.name)
        return None

    def _pick_source_override(self, filename):
        if dialogs is None:
            return None
        try:
            picked = dialogs.pick_document()
        except Exception as e:
            self._tts_log('source_override.pick.error', filename=filename, error=repr(e))
            return None
        if not picked:
            return None
        picked_path = str(picked)
        self.source_overrides[filename] = picked_path
        self._save_source_overrides()
        self._tts_log('source_override.picked', filename=filename, path=picked_path)
        return picked_path

    def _ensure_missing_sources_pinned(self, missing_files):
        if not missing_files:
            return False
        if dialogs is None:
            return False
        changed = False
        for filename in missing_files:
            self.lbl_stats.text = f'DataFresh: vyber {filename}...'
            self.lbl_stats.text_color = '#ff9500'
            if self._pick_source_override(filename):
                changed = True
        return changed

    def _source_mapping_missing(self):
        missing = []
        for filename in self.sync_files:
            pinned = self.source_overrides.get(filename)
            if not pinned or not os.path.exists(pinned):
                missing.append(filename)
        return missing

    def setup_ui(self):
        content_x = 6
        content_w = 383

        # Top bar
        self.top_bar = ui.View(frame=(0, 0, 400, 70), background_color='white')
        self.add_subview(self.top_bar)

        # HT mode toggle
        self.lbl_f = ui.Label(frame=(20, 5, 200, 30), text='Rezim Tezkych (HT): OFF')
        self.top_bar.add_subview(self.lbl_f)
        self.sw_ht_filter = ui.Switch(frame=(230, 5, 50, 30), action=self.toggle_filter)
        self.top_bar.add_subview(self.sw_ht_filter)

        # Word counter
        self.lbl_stats = ui.Label(frame=(20, 35, 300, 30), text='Nacitam...', font=('<system>', 14), text_color='#8e8e93')
        self.top_bar.add_subview(self.lbl_stats)
        self.lbl_remaining = ui.Label(
            frame=(310, 6, 80, 56),
            text='Zbyva:\n0',
            alignment=ui.ALIGN_CENTER,
            font=('<system-bold>', 14),
            text_color='black',
            background_color='#ffe680',
            corner_radius=8,
            number_of_lines=2,
        )
        self.top_bar.add_subview(self.lbl_remaining)

        # Image
        self.img_view = ui.ImageView(frame=(content_x, 80, content_w, 170), background_color='#d1d1d6', corner_radius=12)
        self.img_view.content_mode = ui.CONTENT_SCALE_ASPECT_FIT
        self.add_subview(self.img_view)

        # Word card
        self.card = ui.View(frame=(content_x, 260, content_w, 80), background_color='white', corner_radius=12)
        self.add_subview(self.card)
        self.label_gender = ui.Label(
            frame=(12, 10, 28, 60),
            font=('<system-bold>', 24),
            alignment=ui.ALIGN_CENTER,
            text='',
            text_color='#000000',
        )
        self.card.add_subview(self.label_gender)
        self.label_fr = ui.Label(frame=(44, 10, 270, 60), font=('<system-bold>', 28), alignment=ui.ALIGN_CENTER)
        self.card.add_subview(self.label_fr)
        self.btn_spk = ui.Button(
            frame=(322, 15, 50, 50),
            image=ui.Image.named('iob:ios7_volume_high_32'),
            action=self.speak_current,
        )
        self.card.add_subview(self.btn_spk)

        # Show translation button
        self.btn_rev = ui.Button(frame=(content_x, 350, content_w, 60), background_color='#007aff', tint_color='white', corner_radius=12)
        self.btn_rev.title = 'UKAZAT PREKLAD'
        self.btn_rev.font = ('<system-bold>', 18)
        self.btn_rev.action = self.reveal_translation
        self.add_subview(self.btn_rev)

        # Sentence block: FR and CZ with different font sizes.
        self.sent_box = ui.View(frame=(content_x, 420, content_w, 140), background_color='#ffffff', corner_radius=10)
        self.add_subview(self.sent_box)
        self.txt_sent_fr = ui.TextView(
            frame=(8, 8, 367, 64),
            editable=False,
            font=('<system-bold>', 18),
            background_color='#ffffff',
        )
        self.sent_box.add_subview(self.txt_sent_fr)
        self.txt_sent_cz = ui.TextView(
            frame=(8, 76, 367, 56),
            editable=False,
            font=('<system>', 16),
            background_color='#ffffff',
        )
        self.sent_box.add_subview(self.txt_sent_cz)

        # Switches
        self.btn_verbes = ui.Button(frame=(12, 575, 158, 32), background_color='#5856d6', tint_color='white', corner_radius=8)
        self.btn_verbes.title = 'Slovesa'
        self.btn_verbes.font = ('<system-bold>', 14)
        self.btn_verbes.action = self.open_verbes_screen
        self.add_subview(self.btn_verbes)

        self.lbl_last = ui.Label(frame=(12, 615, 52, 32), text='Last', alignment=ui.ALIGN_RIGHT)
        self.add_subview(self.lbl_last)
        self.btn_last_20 = ui.Button(frame=(72, 615, 44, 32), tint_color='white', corner_radius=8)
        self.btn_last_20.title = '20'
        self.btn_last_20.font = ('<system-bold>', 14)
        self.btn_last_20.action = self.select_last_20
        self.add_subview(self.btn_last_20)
        self.btn_last_50 = ui.Button(frame=(124, 615, 44, 32), tint_color='white', corner_radius=8)
        self.btn_last_50.title = '50'
        self.btn_last_50.font = ('<system-bold>', 14)
        self.btn_last_50.action = self.select_last_50
        self.add_subview(self.btn_last_50)
        self._update_last_buttons()

        # Auto controls (turbo-like cycle)
        self.btn_auto = ui.Button(frame=(230, 575, 42, 32), background_color='#ff9500', tint_color='white', corner_radius=8)
        self.btn_auto.title = 'Auto'
        self.btn_auto.font = ('<system-bold>', 13)
        self.btn_auto.action = self.start_auto
        self.add_subview(self.btn_auto)

        self.btn_all = ui.Button(frame=(276, 575, 42, 32), background_color='#af52de', tint_color='white', corner_radius=8)
        self.btn_all.title = 'All'
        self.btn_all.font = ('<system-bold>', 13)
        self.btn_all.action = self.start_all
        self.add_subview(self.btn_all)

        self.btn_fin = ui.Button(frame=(322, 575, 42, 32), background_color='#8e8e93', tint_color='white', corner_radius=8)
        self.btn_fin.title = 'Fin'
        self.btn_fin.font = ('<system-bold>', 13)
        self.btn_fin.action = self.stop_auto
        self.add_subview(self.btn_fin)
        self.btn_datafresh = ui.Button(frame=(230, 615, 134, 32), background_color='#0a84ff', tint_color='white', corner_radius=8)
        self.btn_datafresh.title = 'DataFresh'
        self.btn_datafresh.font = ('<system-bold>', 14)
        self.btn_datafresh.action = self.refresh_data
        self.add_subview(self.btn_datafresh)

        # Next button
        self.btn_nxt = ui.Button(frame=(content_x, 675, content_w, 75), background_color='#34c759', tint_color='white', corner_radius=15)
        self.btn_nxt.title = 'DALSI SLOVICKO'
        self.btn_nxt.font = ('<system-bold>', 20)
        self.btn_nxt.action = self.next_word
        self.add_subview(self.btn_nxt)

        self.setup_verbes_screen()

        if self.words:
            self.update_stats()
            self.next_word(None)

    def setup_verbes_screen(self):
        self.verbes_view = ui.View(frame=(0, 0, 400, 760), background_color='#f2f2f7')
        self.verbes_view.hidden = True
        self.add_subview(self.verbes_view)

        header = ui.View(frame=(0, 0, 400, 64), background_color='white')
        self.verbes_view.add_subview(header)

        self.btn_verbes_back = ui.Button(frame=(10, 16, 82, 36), background_color='#8e8e93', tint_color='white', corner_radius=8)
        self.btn_verbes_back.title = 'Zpet'
        self.btn_verbes_back.font = ('<system-bold>', 14)
        self.btn_verbes_back.action = self.close_verbes_screen
        header.add_subview(self.btn_verbes_back)

        title = ui.Label(frame=(100, 16, 210, 36), text='Slovesa', alignment=ui.ALIGN_CENTER, font=('<system-bold>', 22))
        header.add_subview(title)

        self.btn_verbes_speak = ui.Button(frame=(318, 16, 72, 36), background_color='#0a84ff', tint_color='white', corner_radius=8)
        self.btn_verbes_speak.title = 'Cist'
        self.btn_verbes_speak.font = ('<system-bold>', 14)
        self.btn_verbes_speak.action = self.speak_selected_verbe
        header.add_subview(self.btn_verbes_speak)

        self.verbes_table = ui.TableView(frame=(6, 74, 164, 668), background_color='white')
        self.verbes_ds = ui.ListDataSource([])
        self.verbes_ds.action = self.select_verbe
        self.verbes_table.data_source = self.verbes_ds
        self.verbes_table.delegate = self.verbes_ds
        self.verbes_view.add_subview(self.verbes_table)

        self.verbe_title = ui.Label(frame=(176, 74, 218, 58), text='Vyber sloveso', alignment=ui.ALIGN_CENTER, font=('<system-bold>', 24), number_of_lines=2)
        self.verbes_view.add_subview(self.verbe_title)

        self.verbe_cz = ui.Label(frame=(176, 132, 218, 34), text='', alignment=ui.ALIGN_CENTER, font=('<system>', 17), text_color='#6b6b70')
        self.verbes_view.add_subview(self.verbe_cz)

        self.verbe_forms = []
        y = 184
        for _ in range(6):
            form = ui.Label(frame=(184, y, 208, 34), text='', alignment=ui.ALIGN_LEFT, font=('<system-bold>', 18), number_of_lines=1)
            self.verbes_view.add_subview(form)
            self.verbe_forms.append(form)
            y += 46

    def _verbe_file_candidates(self):
        candidates = [
            VERBE_FILE,
            BASE_DIR.parent / 'VerbeFR.csv',
            BASE_DIR.parent / 'VocabularyFR' / 'VerbeFR.csv',
            Path.cwd() / 'VerbeFR.csv',
            Path.home() / 'Documents' / 'VerbeFR.csv',
            Path.home() / 'Documents' / 'VocabularyFR' / 'VerbeFR.csv',
        ]
        ordered = []
        seen = set()
        for path in candidates:
            try:
                key = str(path.expanduser().resolve())
            except Exception:
                key = str(path)
            if key in seen:
                continue
            seen.add(key)
            ordered.append(path)
        return ordered

    def _load_verbe_rows(self):
        for path in self._verbe_file_candidates():
            if not path.exists():
                continue
            with open(path, mode='r', encoding='utf-8-sig', newline='') as f:
                rows = list(csv.DictReader(f))
            return [row for row in rows if (row.get('InfFR') or '').strip()]
        raise FileNotFoundError('VerbeFR.csv')

    def open_verbes_screen(self, sender):
        self.stop_auto(None)
        try:
            self.verbe_rows = self._load_verbe_rows()
        except Exception as e:
            self._notify('Slovesa', f'Nelze nacist VerbeFR.csv: {e}')
            return
        self.verbe_selected_index = None
        self.verbes_ds.items = [
            f"{row.get('InfFR', '').strip()} - {row.get('InfCZ', '').strip()}"
            for row in self.verbe_rows
        ]
        self.verbes_table.reload()
        self.verbe_title.text = 'Vyber sloveso'
        self.verbe_cz.text = ''
        for form in self.verbe_forms:
            form.text = ''
        self.verbes_view.hidden = False
        self.verbes_view.bring_to_front()

    def close_verbes_screen(self, sender):
        self.verbes_view.hidden = True

    def select_verbe(self, sender):
        try:
            idx = self._selected_verbe_index(sender)
            if idx is None or idx < 0 or idx >= len(self.verbe_rows):
                self._tts_log('verbe.select.invalid_index', index=repr(idx))
                return
            self.verbe_selected_index = idx
            row = self.verbe_rows[idx]
            self._show_verbe(row)
            # Let the UI update finish before starting TTS.
            ui.delay(lambda r=row: self._speak_verbe_present(r), 0.15)
        except Exception as e:
            self._tts_log('verbe.select.error', error=repr(e))
            self._notify('Slovesa', f'Chyba pri vyberu slovesa: {e}')

    def _selected_verbe_index(self, sender):
        selected = getattr(sender, 'selected_row', None)
        if selected is None:
            selected = getattr(self.verbes_table, 'selected_row', None)
        if isinstance(selected, tuple):
            selected = selected[-1] if selected else None
        if selected is None:
            return None
        try:
            return int(selected)
        except Exception:
            return None

    def _show_verbe(self, row):
        self.verbe_title.text = row.get('InfFR', '').strip()
        self.verbe_cz.text = row.get('InfCZ', '').strip()
        for label, key in zip(self.verbe_forms, ('Ind1', 'Ind2', 'Ind3', 'IndP1', 'IndP2', 'IndP3')):
            label.text = row.get(key, '').strip()

    def speak_selected_verbe(self, sender):
        if self.verbe_selected_index is None:
            return
        if 0 <= self.verbe_selected_index < len(self.verbe_rows):
            self._speak_verbe_present(self.verbe_rows[self.verbe_selected_index])

    def _speak_verbe_present(self, row):
        try:
            forms = [
                row.get(key, '').strip()
                for key in ('Ind1', 'Ind2', 'Ind3', 'IndP1', 'IndP2', 'IndP3')
                if row.get(key, '').strip()
            ]
            if not forms:
                return
            self.verbe_speech_token += 1
            token = self.verbe_speech_token
            self._tts_recover('verbe_present')
            self._speak_verbe_form_sequence(forms, token, 0)
        except Exception as e:
            self._tts_log('verbe.speak.error', error=repr(e))

    def _speak_verbe_form_sequence(self, forms, token, index):
        if token != self.verbe_speech_token:
            return
        if index >= len(forms):
            return
        self._safe_say(forms[index], 'fr-FR')
        ui.delay(lambda: self._speak_verbe_form_sequence(forms, token, index + 1), 2.0)

    def _normalize_key(self, text):
        import unicodedata
        import re
        text = (text or '').strip().casefold()
        text = unicodedata.normalize('NFD', text)
        text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
        return re.sub(r'[^a-z0-9]+', '', text)

    def _normalize_mapping_key(self, text):
        import unicodedata
        text = unicodedata.normalize('NFC', (text or '').strip().casefold())
        return ''.join(char for char in text if char.isalnum())

    def is_true(self, value):
        """Robust bool check for CSV values."""
        if not value:
            return False
        return str(value).strip().lower() in ['true', '1', 'yes', 'ano']

    def update_stats(self):
        """Update counters shown in UI."""
        total = len(self.words)
        ht_count = len([w for w in self.words if self.is_true(w.get('HT'))])
        self.lbl_stats.text = f'Celkem: {total} | Tezkych (HT): {ht_count}'

    def _pool_indices(self):
        """Indices after the Last limit and optional HT filter."""
        indices = list(range(len(self.words)))
        if self.last_count:
            indices = indices[-self.last_count:]
        return [
            i for i in indices
            if (not self.filter_ht or self.is_true(self.words[i].get('HT')))
        ]

    def _active_indices(self):
        """Active set for selection and counter."""
        pool = self._pool_indices()
        return pool

    def _current_selection_signature(self, active_indices):
        """Selection signature to detect set changes and reset cycle."""
        return (tuple(active_indices), self.filter_ht, self.last_count)

    def _update_remaining_counter(self, active_indices):
        total = len(active_indices)
        seen = len([i for i in self.shown_in_selection if i in active_indices])
        if total <= 0:
            remaining = 0
        else:
            # Keep same behavior as desktop trainer: first shown word keeps full count.
            remaining = 0 if seen >= total else (total - seen + 1)
            if remaining < 0:
                remaining = 0
        self.lbl_remaining.text = f'Zbyva:\n{remaining}'

    def _update_gender_badge(self, row):
        if not row:
            self.label_gender.text = ''
            return
        gender = (row.get('gender_fr') or '').strip().lower()
        if gender == 'm':
            self.label_gender.text = 'm'
            self.label_gender.text_color = '#007aff'
        elif gender == 'f':
            self.label_gender.text = 'f'
            self.label_gender.text_color = '#ff3b30'
        else:
            self.label_gender.text = ''

    def _safe_say(self, text, lang=None):
        value = (text or '').strip()
        if not value:
            self._tts_log('say.skip_empty', lang=lang)
            return
        self._tts_log('say.request', lang=lang, text=value[:80], speaking=self._is_speaking())
        self._activate_audio_session()
        if self._objc_say(value, lang):
            return
        try:
            if lang:
                speech.say(value, lang)
            else:
                speech.say(value)
            self._tts_log('py.say.ok', lang=lang, speaking=self._is_speaking())
            return
        except Exception as e:
            # Fallback when a locale voice is unavailable in Pythonista/iOS.
            self._tts_log('py.say.lang_error', lang=lang, error=repr(e))
            try:
                speech.say(value)
                self._tts_log('py.say.fallback_ok', speaking=self._is_speaking())
            except Exception as fallback_e:
                self._tts_log('py.say.fallback_error', error=repr(fallback_e))

    def _objc_say(self, text, lang=None):
        if ObjCClass is None:
            self._tts_log('objc.say.skip', reason='objc_unavailable')
            return False
        try:
            AVSpeechSynthesizer = ObjCClass('AVSpeechSynthesizer')
            AVSpeechUtterance = ObjCClass('AVSpeechUtterance')
            AVSpeechSynthesisVoice = ObjCClass('AVSpeechSynthesisVoice')
            if self._av_synth is None:
                self._av_synth = AVSpeechSynthesizer.new()
            utterance = AVSpeechUtterance.speechUtteranceWithString_(text)
            if lang:
                voice = AVSpeechSynthesisVoice.voiceWithLanguage_(lang)
                if voice is not None:
                    utterance.setVoice_(voice)
            utterance.setRate_(0.45)
            self._last_utterance = utterance
            self._av_synth.speakUtterance_(utterance)
            self._tts_log('objc.say.ok', lang=lang)
            return True
        except Exception as e:
            self._tts_log('objc.say.error', lang=lang, error=repr(e))
            return False

    def _activate_audio_session(self):
        if ObjCClass is None:
            self._tts_log('audio.session.skip', reason='objc_unavailable')
            return
        try:
            session = ObjCClass('AVAudioSession').sharedInstance()
            # Explicitly reactivate playback route before each TTS request.
            session.setCategory_error_('AVAudioSessionCategoryPlayback', None)
            session.setActive_error_(True, None)
            self._tts_log('audio.session.ok')
        except Exception as e:
            self._tts_log('audio.session.error', error=repr(e))

    def _is_speaking(self):
        objc_speaking = None
        if self._av_synth is not None:
            try:
                objc_speaking = bool(self._av_synth.isSpeaking())
            except Exception:
                objc_speaking = None
        try:
            py_speaking = bool(speech.is_speaking())
        except Exception:
            py_speaking = None
        if objc_speaking is True or py_speaking is True:
            return True
        if objc_speaking is False and py_speaking is False:
            return False
        if objc_speaking is not None:
            return objc_speaking
        return py_speaking

    def _tts_recover(self, source):
        try:
            speech.stop()
            self._tts_log('tts.stop.ok', source=source, speaking=self._is_speaking())
        except Exception as e:
            self._tts_log('tts.stop.error', source=source, error=repr(e))
        if self._av_synth is not None:
            try:
                # 0 == AVSpeechBoundaryImmediate
                self._av_synth.stopSpeakingAtBoundary_(0)
                self._tts_log('objc.stop.ok', source=source)
            except Exception as e:
                self._tts_log('objc.stop.error', source=source, error=repr(e))

    def _tts_log(self, event, **meta):
        ts = time.strftime('%Y-%m-%d %H:%M:%S')
        payload = ' | '.join(f'{k}={repr(v)}' for k, v in meta.items())
        line = f'{ts} | {event}'
        if payload:
            line += f' | {payload}'
        try:
            with open(TTS_LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(line + '\n')
        except Exception:
            pass

    def _notify(self, title, message):
        if console is None:
            print(f'{title}: {message}')
            return
        try:
            console.alert(title, message, 'OK', hide_cancel_button=True)
        except Exception:
            print(f'{title}: {message}')

    def _read_csv_rows(self, path):
        with open(path, mode='r', encoding='utf-8-sig', newline='') as f:
            reader = csv.DictReader(f)
            cleaned_rows = []
            for row in reader:
                cleaned = {}
                for key, value in (row or {}).items():
                    clean_key = (key or '').replace('\ufeff', '').strip()
                    cleaned[clean_key] = value
                cleaned_rows.append(cleaned)
            return cleaned_rows

    def _restore_csv_backup(self, backup_bytes):
        if backup_bytes is None:
            return
        try:
            with open(CSV_FILE, 'wb') as f:
                f.write(backup_bytes)
        except Exception as e:
            self._tts_log('datafresh.restore_backup.error', error=repr(e))

    def _restore_invalid_vocab_csv_if_needed(self, result, backup_bytes):
        try:
            rows = self._read_csv_rows(CSV_FILE)
            headers = set(rows[0]) if rows else set()
        except Exception:
            rows = []
            headers = set()
        if rows and set(VOCAB_REQUIRED_COLUMNS).issubset(headers):
            return False
        self._restore_csv_backup(backup_bytes)
        failed = result.setdefault('failed', [])
        failed.append(
            f'{CSV_FILE.name}: odmitnut neplatny CSV zdroj'
        )
        self._tts_log('datafresh.reject_invalid_csv')
        return True

    def _drop_ignored_source_overrides(self, result):
        changed = False
        for filename in result.get('ignored_overrides') or []:
            if filename in self.source_overrides:
                self.source_overrides.pop(filename, None)
                changed = True
                self._tts_log('datafresh.ignore_stale_override', filename=filename)
        if changed:
            self._save_source_overrides()

    def _reload_words(self):
        if not CSV_FILE.exists():
            self.words = []
            return
        self.words = self._read_csv_rows(CSV_FILE)

    def refresh_data(self, sender):
        self.stop_auto(None)
        csv_backup = None
        try:
            if CSV_FILE.exists():
                with open(CSV_FILE, 'rb') as f:
                    csv_backup = f.read()
        except Exception as e:
            self._tts_log('datafresh.backup_csv.error', error=repr(e))

        if FORCE_MANUAL_DATAFRESH_MAPPING:
            missing_pins = self._source_mapping_missing()
            if missing_pins:
                self._ensure_missing_sources_pinned(missing_pins)

        def _run_refresh_once():
            if DATAFRESH_API_VERSION < 2:
                raise RuntimeError('Nahraj spolu s AppFR.py také nový datafresh_sync.py.')
            refreshed = refresh_files_from_icloud(
                local_dir=str(BASE_DIR),
                filenames=self.sync_files,
                app_dir_hints=self.sync_dir_hints,
                source_overrides=self.source_overrides,
                strict=True,
                manual_only=FORCE_MANUAL_DATAFRESH_MAPPING,
                allow_recursive=not FAST_DATAFRESH_ONLY,
                fast=FAST_DATAFRESH_ONLY,
                max_attempts=1,
                required_csv_columns={
                    CSV_FILE.name: VOCAB_REQUIRED_COLUMNS,
                },
            )
            self._drop_ignored_source_overrides(refreshed)
            return refreshed

        try:
            result = _run_refresh_once()
        except Exception as e:
            result = {
                'updated': [],
                'unchanged': [],
                'missing': [],
                'failed': [str(e)],
                'sources': {},
                'diagnostics': {},
                'source_rows': {},
                'local_rows': {},
                'ignored_overrides': [],
            }

        if result.get("missing"):
            if self._ensure_missing_sources_pinned(result.get("missing") or []):
                result = _run_refresh_once()

        # iCloud/File Provider may expose files with delay; retry once automatically.
        if CSV_FILE.name in result.get("missing", []):
            time.sleep(0.8)
            second = _run_refresh_once()
            for key in ("updated", "unchanged", "missing", "failed"):
                result[key] = list(dict.fromkeys((result.get(key) or []) + (second.get(key) or [])))
            merged_sources = dict(result.get("sources") or {})
            merged_sources.update(second.get("sources") or {})
            result["sources"] = merged_sources
            merged_diag = dict(result.get("diagnostics") or {})
            for k, roots in (second.get("diagnostics") or {}).items():
                existing = merged_diag.get(k) or []
                for r in roots or []:
                    if r not in existing:
                        existing.append(r)
                merged_diag[k] = existing
            result["diagnostics"] = merged_diag

        self._restore_invalid_vocab_csv_if_needed(result, csv_backup)

        try:
            # Always reload after DataFresh; file may have changed even when source
            # lookup reports unchanged/missing due delayed iCloud metadata refresh.
            self._reload_words()
            self.selection_signature = None
            self.shown_in_selection.clear()
            self.current_word = None
            self.current_index = None
            self.update_stats()
            if self.words:
                self.next_word(None)
            else:
                self.label_fr.text = 'Hotovo!'
                self.btn_rev.title = 'UKAZAT PREKLAD'
                self.txt_sent_fr.text = ''
                self.txt_sent_cz.text = ''
                self.lbl_remaining.text = 'Zbyva:\n0'
        except Exception as e:
            result["failed"].append(f'{CSV_FILE.name}: load error: {e}')

        first_status = datafresh_status_text(result, CSV_FILE.name, len(self.words))
        self.lbl_stats.text = first_status
        self.lbl_stats.text_color = (
            '#2e7d32'
            if refresh_result_succeeded(result, CSV_FILE.name)
            else '#d32f2f'
        )

        # Automaticky spustíme druhý refresh po 2s — iCloud mezitím stáhne nový soubor.
        def _second_refresh():
            try:
                result2 = _run_refresh_once()
            except Exception as e:
                result2 = {
                    'updated': [],
                    'unchanged': [],
                    'missing': [],
                    'failed': [str(e)],
                    'sources': {},
                    'diagnostics': {},
                    'source_rows': {},
                    'local_rows': {},
                    'ignored_overrides': [],
                }
            self._restore_invalid_vocab_csv_if_needed(result2, csv_backup)
            try:
                self._reload_words()
                self.selection_signature = None
                self.shown_in_selection.clear()
                self.current_word = None
                self.current_index = None
                self.update_stats()
                if self.words:
                    self.next_word(None)
                else:
                    self.label_fr.text = 'Hotovo!'
                    self.lbl_remaining.text = 'Zbyva:\n0'
            except Exception:
                pass
            total = len(self.words)
            final_result = result2
            if (
                not refresh_result_succeeded(result2, CSV_FILE.name)
                and refresh_result_succeeded(result, CSV_FILE.name)
            ):
                final_result = result
            success = refresh_result_succeeded(final_result, CSV_FILE.name)
            self.lbl_stats.text = datafresh_status_text(
                final_result,
                CSV_FILE.name,
                total,
            )
            self.lbl_stats.text_color = '#2e7d32' if success else '#d32f2f'
            if success:
                def _restore():
                    self.update_stats()
                    self.lbl_stats.text_color = '#8e8e93'
                ui.delay(_restore, 4.0)
            else:
                self._notify('DataFresh', self.lbl_stats.text)

        ui.delay(_second_refresh, 2.0)

    def next_word(self, sender):
        self.stop_auto(None)
        self._advance_word(speak_fr=True)

    def _advance_word(self, speak_fr=True):
        active_indices = self._active_indices()

        if not active_indices:
            self.label_fr.text = 'Hotovo!'
            self._update_gender_badge(None)
            self.current_word = None
            self.current_index = None
            self.lbl_remaining.text = 'Zbyva:\n0'
            return

        signature = self._current_selection_signature(active_indices)
        if signature != self.selection_signature:
            self.selection_signature = signature
            self.shown_in_selection.clear()

        available = [i for i in active_indices if i not in self.shown_in_selection]
        if not available:
            # New cycle after all words in the active set were shown once.
            self.shown_in_selection.clear()
            available = list(active_indices)

        self.current_index = random.choice(available)
        self.shown_in_selection.add(self.current_index)
        self._update_remaining_counter(active_indices)
        self.current_word = self.words[self.current_index]

        self.label_fr.text = self.current_word.get('FR', '')
        self._update_gender_badge(self.current_word)
        self.btn_rev.title = 'UKAZAT PREKLAD'
        self.txt_sent_fr.text = ''
        self.txt_sent_cz.text = ''
        if hasattr(self, 'sw_l'):
            self.sw_l.value = self.is_true(self.current_word.get('L'))
        # Reset and load image
        self.img_view.image = None
        img_base_name = self._image_base_name_for_word(self.current_word)
        image_path = self._find_image_path(img_base_name)
        if image_path:
            self.img_view.image = self._load_ui_image(image_path)

        if speak_fr and self.label_fr.text:
            self._safe_say(self.label_fr.text, 'fr-FR')

    def reveal_translation(self, sender):
        if self.current_word:
            self.btn_rev.title = self.current_word.get('CZ', '')
            sentence = self.current_word.get('Sentence', '')
            self.txt_sent_fr.text = sentence
            self.txt_sent_cz.text = self.current_word.get('SentenceT', '')
            if sentence:
                self._safe_say(sentence, 'fr-FR')

    def start_auto(self, sender):
        if self.auto_running:
            return
        self.auto_mode = 'basic'
        self.auto_running = True
        self.auto_phase = 'next_word'
        self.auto_next_time = 0.0
        # Kickstart immediately; further steps are driven by update().
        self.update()

    def start_all(self, sender):
        if self.auto_running:
            return
        self.auto_mode = 'all'
        self.auto_running = True
        self.auto_phase = 'next_word'
        self.auto_next_time = 0.0
        self.update()

    def stop_auto(self, sender):
        self.auto_running = False
        self.auto_mode = 'basic'
        self.auto_phase = 'idle'
        self.auto_next_time = 0.0
        self.auto_wait_deadline = 0.0
        self.auto_wait_seen_speaking = False
        self.auto_wait_next_phase = 'idle'
        self.auto_wait_after_gap = 0.0

    def _begin_wait_for_speech(self, now, next_phase, after_gap=0.0, deadline_window=0.8):
        self.auto_phase = 'wait_speech_done'
        self.auto_wait_deadline = now + deadline_window
        self.auto_wait_seen_speaking = False
        self.auto_wait_next_phase = next_phase
        self.auto_wait_after_gap = after_gap
        self.auto_next_time = now + 0.2

    def update(self):
        if not self.auto_running:
            return
        now = time.time()
        if now < self.auto_next_time:
            return
        try:
            if self.auto_phase == 'next_word':
                # In Auto mode, use default iOS voice (no locale) for stability.
                self._advance_word(speak_fr=False)
                if not self.current_word:
                    self.stop_auto(None)
                    return
                self._safe_say(self.label_fr.text, 'fr-FR')
                self._begin_wait_for_speech(now, 'speak_cz')
            elif self.auto_phase == 'speak_cz':
                cz_word = (self.current_word or {}).get('CZ', '')
                self.btn_rev.title = cz_word
                if cz_word:
                    self._safe_say(cz_word)
                if self.auto_mode == 'all':
                    sentence = (self.current_word or {}).get('Sentence', '').strip()
                    sentence_t = (self.current_word or {}).get('SentenceT', '').strip()
                    if sentence:
                        self.txt_sent_fr.text = sentence
                        self.txt_sent_cz.text = sentence_t
                    if sentence_t:
                        self._begin_wait_for_speech(now, 'speak_sentence_t')
                    elif sentence:
                        self._begin_wait_for_speech(now, 'speak_sentence')
                    else:
                        self._begin_wait_for_speech(now, 'next_word', after_gap=1.5)
                else:
                    if self.filter_ht and self.label_fr.text:
                        self._begin_wait_for_speech(now, 'repeat_fr')
                    else:
                        self._begin_wait_for_speech(now, 'next_word', after_gap=1.5)
            elif self.auto_phase == 'repeat_fr':
                fr_word = (self.current_word or {}).get('FR', '').strip() or (self.label_fr.text or '').strip()
                if fr_word:
                    self._safe_say(fr_word, 'fr-FR')
                self._begin_wait_for_speech(now, 'next_word', after_gap=1.5)
            elif self.auto_phase == 'speak_sentence_t':
                sentence_t = (self.current_word or {}).get('SentenceT', '').strip()
                sentence = (self.current_word or {}).get('Sentence', '').strip()
                if sentence_t:
                    self._safe_say(sentence_t)
                    next_phase = 'speak_sentence' if sentence else 'next_word'
                    next_gap = 0.0 if sentence else 1.5
                    self._begin_wait_for_speech(now, next_phase, after_gap=next_gap)
                elif sentence:
                    self.auto_phase = 'speak_sentence'
                    self.auto_next_time = now
                else:
                    self.auto_phase = 'next_word'
                    self.auto_next_time = now + 1.5
            elif self.auto_phase == 'speak_sentence':
                sentence = (self.current_word or {}).get('Sentence', '').strip()
                if sentence:
                    self._safe_say(sentence, 'fr-FR')
                    self._begin_wait_for_speech(now, 'next_word', after_gap=1.5)
                else:
                    self.auto_phase = 'next_word'
                    self.auto_next_time = now + 1.5
            elif self.auto_phase == 'wait_speech_done':
                speaking = self._is_speaking()
                if speaking is True:
                    self.auto_wait_seen_speaking = True
                    self.auto_next_time = now + 0.2
                elif not self.auto_wait_seen_speaking and now < self.auto_wait_deadline:
                    self.auto_next_time = now + 0.2
                else:
                    self.auto_phase = self.auto_wait_next_phase or 'next_word'
                    self.auto_wait_deadline = 0.0
                    self.auto_wait_seen_speaking = False
                    self.auto_wait_next_phase = 'idle'
                    self.auto_next_time = now + max(0.0, self.auto_wait_after_gap)
                    self.auto_wait_after_gap = 0.0
            else:
                self.auto_phase = 'next_word'
                self.auto_next_time = now
        except Exception:
            self.stop_auto(None)

    def speak_current(self, sender):
        if self.label_fr.text:
            self._safe_say(self.label_fr.text, 'fr-FR')

    def toggle_filter(self, sender):
        self.filter_ht = sender.value
        self.lbl_f.text = f"Rezim Tezkych (HT): {'ON' if sender.value else 'OFF'}"
        self.next_word(None)

    def _update_last_buttons(self):
        inactive_color = '#8e8e93'
        active_color = '#007aff'
        self.btn_last_20.background_color = active_color if self.last_count == 20 else inactive_color
        self.btn_last_50.background_color = active_color if self.last_count == 50 else inactive_color

    def _toggle_last_count(self, count):
        self.last_count = None if self.last_count == count else count
        self._update_last_buttons()
        self.next_word(None)

    def select_last_20(self, sender):
        self._toggle_last_count(20)

    def select_last_50(self, sender):
        self._toggle_last_count(50)

    def update_l(self, sender):
        if self.current_word:
            self.current_word['L'] = 'True' if sender.value else 'False'
            self.save_current_state()

    def save_current_state(self):
        if not self.words:
            return
        try:
            with open(CSV_FILE, mode='w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.words[0].keys())
                writer.writeheader()
                writer.writerows(self.words)
        except Exception as e:
            print(f'Chyba pri ukladani: {e}')

    def _open_launcher_editor(self):
        try:
            rel = f'{BASE_DIR.name}/launcher.py'
            url = f'pythonista3://{quote(rel, safe="/")}?action=edit'
            webbrowser.open(url)
        except Exception:
            pass

    def will_close(self):
        self.verbe_speech_token += 1
        self.stop_auto(None)
        self._tts_log('will_close', speaking=self._is_speaking())
        self._tts_recover('will_close')
        # Keep close side-effect free (no auto-launch of another script).


if __name__ == '__main__':
    v = VocabTrainer()
    v.present('sheet')
