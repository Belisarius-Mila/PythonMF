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
    import console
except Exception:
    console = None
try:
    from objc_util import ObjCClass
except Exception:
    ObjCClass = None

# --- PATH SETTINGS ---
BASE_DIR = Path(__file__).parent
CSV_FILE = BASE_DIR / 'VocabularyFR.csv'
JSON_FILE = BASE_DIR / 'mapping.json'
PICT_FOLDER = BASE_DIR / 'Pict'
TTS_LOG_FILE = BASE_DIR / 'tts_fr_debug.log'


class VocabTrainer(ui.View):
    def __init__(self):
        self.background_color = '#f2f2f7'
        self.update_interval = 0.1
        self.words = []
        self.image_map = {}
        self.current_word = None
        self.current_index = None
        self.filter_ht = False

        # Selection cycle state: random order without repeats in current set.
        self.selection_signature = None
        self.shown_in_selection = set()
        self.auto_running = False
        self.auto_phase = 'idle'
        self.auto_next_time = 0.0
        self._av_synth = None
        self._last_utterance = None
        self.sync_files = [CSV_FILE.name, 'VerbeFR.csv']
        self.sync_dir_hints = ('PythonMF/VocabularyFR', 'PythonMF', 'VocabularyFR')
        self._tts_log('init.start')
        self._tts_recover('init')

        # Load JSON mapping
        if JSON_FILE.exists():
            try:
                with open(JSON_FILE, mode='r', encoding='utf-8') as f:
                    self.image_map = json.load(f)
            except Exception:
                pass

        # Load CSV words
        if CSV_FILE.exists():
            try:
                with open(CSV_FILE, mode='r', encoding='utf-8') as f:
                    self.words = list(csv.DictReader(f))
            except Exception:
                pass

        self.setup_ui()

    def setup_ui(self):
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
        self.img_view = ui.ImageView(frame=(10, 80, 355, 170), background_color='#d1d1d6', corner_radius=12)
        self.img_view.content_mode = ui.CONTENT_SCALE_ASPECT_FIT
        self.add_subview(self.img_view)

        # Word card
        self.card = ui.View(frame=(10, 260, 355, 80), background_color='white', corner_radius=12)
        self.add_subview(self.card)
        self.label_fr = ui.Label(frame=(10, 10, 270, 60), font=('<system-bold>', 28), alignment=ui.ALIGN_CENTER)
        self.card.add_subview(self.label_fr)
        self.btn_spk = ui.Button(
            frame=(290, 15, 50, 50),
            image=ui.Image.named('iob:ios7_volume_high_32'),
            action=self.speak_current,
        )
        self.card.add_subview(self.btn_spk)

        # Show translation button
        self.btn_rev = ui.Button(frame=(10, 350, 355, 60), background_color='#007aff', tint_color='white', corner_radius=12)
        self.btn_rev.title = 'UKAZAT PREKLAD'
        self.btn_rev.font = ('<system-bold>', 18)
        self.btn_rev.action = self.reveal_translation
        self.add_subview(self.btn_rev)

        # Sentence block: FR and CZ with different font sizes.
        self.sent_box = ui.View(frame=(10, 420, 355, 140), background_color='#ffffff', corner_radius=10)
        self.add_subview(self.sent_box)
        self.txt_sent_fr = ui.TextView(
            frame=(8, 8, 339, 64),
            editable=False,
            font=('<system-bold>', 18),
            background_color='#ffffff',
        )
        self.sent_box.add_subview(self.txt_sent_fr)
        self.txt_sent_cz = ui.TextView(
            frame=(8, 76, 339, 56),
            editable=False,
            font=('<system>', 16),
            background_color='#ffffff',
        )
        self.sent_box.add_subview(self.txt_sent_cz)

        # Switches
        self.lbl_l = ui.Label(frame=(12, 575, 100, 30), text='Nauceno', alignment=ui.ALIGN_RIGHT)
        self.add_subview(self.lbl_l)
        self.sw_l = ui.Switch(frame=(120, 575, 50, 30), action=self.update_l)
        self.add_subview(self.sw_l)

        self.lbl_ht = ui.Label(frame=(12, 615, 100, 30), text='Tezky (HT)', alignment=ui.ALIGN_RIGHT)
        self.add_subview(self.lbl_ht)
        self.sw_ht = ui.Switch(frame=(120, 615, 50, 30), action=self.update_ht)
        self.add_subview(self.sw_ht)

        # Auto controls (turbo-like cycle)
        self.btn_auto = ui.Button(frame=(230, 575, 62, 32), background_color='#ff9500', tint_color='white', corner_radius=8)
        self.btn_auto.title = 'Auto'
        self.btn_auto.font = ('<system-bold>', 14)
        self.btn_auto.action = self.start_auto
        self.add_subview(self.btn_auto)

        self.btn_fin = ui.Button(frame=(302, 575, 62, 32), background_color='#8e8e93', tint_color='white', corner_radius=8)
        self.btn_fin.title = 'Fin'
        self.btn_fin.font = ('<system-bold>', 14)
        self.btn_fin.action = self.stop_auto
        self.add_subview(self.btn_fin)
        self.btn_datafresh = ui.Button(frame=(230, 615, 134, 32), background_color='#0a84ff', tint_color='white', corner_radius=8)
        self.btn_datafresh.title = 'DataFresh'
        self.btn_datafresh.font = ('<system-bold>', 14)
        self.btn_datafresh.action = self.refresh_data
        self.add_subview(self.btn_datafresh)

        # Next button
        self.btn_nxt = ui.Button(frame=(10, 675, 355, 75), background_color='#34c759', tint_color='white', corner_radius=15)
        self.btn_nxt.title = 'DALSI SLOVICKO'
        self.btn_nxt.font = ('<system-bold>', 20)
        self.btn_nxt.action = self.next_word
        self.add_subview(self.btn_nxt)

        if self.words:
            self.update_stats()
            self.next_word(None)

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
        """Indices after HT filter."""
        return [
            i for i, w in enumerate(self.words)
            if (not self.filter_ht or self.is_true(w.get('HT')))
        ]

    def _active_indices(self):
        """Active set for selection and counter (all or HT-filtered)."""
        pool = self._pool_indices()
        return pool

    def _current_selection_signature(self, active_indices):
        """Selection signature to detect set changes and reset cycle."""
        return (tuple(active_indices), self.filter_ht)

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
        try:
            return bool(speech.is_speaking())
        except Exception:
            return None

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

    def _reload_words(self):
        if not CSV_FILE.exists():
            self.words = []
            return
        with open(CSV_FILE, mode='r', encoding='utf-8') as f:
            self.words = list(csv.DictReader(f))

    def refresh_data(self, sender):
        self.stop_auto(None)
        def _run_refresh_once():
            try:
                return refresh_files_from_icloud(
                    local_dir=str(BASE_DIR),
                    filenames=self.sync_files,
                    app_dir_hints=self.sync_dir_hints,
                    strict=True,
                )
            except TypeError:
                # Backward compatibility when older datafresh_sync.py is deployed on iOS.
                return refresh_files_from_icloud(
                    local_dir=str(BASE_DIR),
                    filenames=self.sync_files,
                    app_dir_hints=self.sync_dir_hints,
                )

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

        lines = []
        if result["updated"]:
            lines.append('Aktualizovano: ' + ', '.join(result["updated"]))
        if result.get("unchanged"):
            lines.append('Už aktuální: ' + ', '.join(result["unchanged"]))
        if result["missing"]:
            lines.append('Nenalezeno: ' + ', '.join(result["missing"]))
            diagnostics = result.get("diagnostics") or {}
            diag_parts = []
            for name in result["missing"]:
                roots = diagnostics.get(name) or []
                if roots:
                    sample = ', '.join(roots[:2])
                    diag_parts.append(f'{name} roots={len(roots)} sample={sample}')
            if diag_parts:
                lines.append('Debug: ' + ' | '.join(diag_parts))
        if result["failed"]:
            lines.append('Chyby: ' + ' | '.join(result["failed"]))
        sources = result.get("sources") or {}
        if sources:
            source_lines = [f'{k} <= {v}' for k, v in sources.items()]
            lines.append('Zdroj: ' + ' | '.join(source_lines))
        if not lines:
            lines.append('Bez zmen.')
        # Zobraz mezivýsledek v lbl_stats (bez alertu = neblokuje).
        short = lines[0] if lines else 'Probíhá...'
        self.lbl_stats.text = f'DataFresh: {short}'
        self.lbl_stats.text_color = '#ff9500'

        # Automaticky spustíme druhý refresh po 2s — iCloud mezitím stáhne nový soubor.
        def _second_refresh():
            result2 = _run_refresh_once()
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
            status = 'Aktualizovano' if result2.get('updated') else 'Hotovo'
            self.lbl_stats.text = f'✓ {status}: {total} slovicek'
            self.lbl_stats.text_color = '#2e7d32'
            def _restore():
                self.update_stats()
                self.lbl_stats.text_color = '#8e8e93'
            ui.delay(_restore, 4.0)

        ui.delay(_second_refresh, 2.0)

    def next_word(self, sender):
        self.stop_auto(None)
        self._advance_word(speak_fr=True)

    def _advance_word(self, speak_fr=True):
        active_indices = self._active_indices()

        if not active_indices:
            self.label_fr.text = 'Hotovo!'
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
        self.btn_rev.title = 'UKAZAT PREKLAD'
        self.txt_sent_fr.text = ''
        self.txt_sent_cz.text = ''
        self.sw_l.value = self.is_true(self.current_word.get('L'))
        self.sw_ht.value = self.is_true(self.current_word.get('HT'))

        # Reset and load image
        self.img_view.image = None
        cz_word = self.current_word.get('CZ', '').strip()
        img_base_name = self.image_map.get(cz_word)
        if img_base_name:
            image_path = PICT_FOLDER / f'{img_base_name}.png'
            if image_path.exists():
                self.img_view.image = ui.Image.named(str(image_path))

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
        self.auto_running = True
        self.auto_phase = 'next_word'
        self.auto_next_time = 0.0
        # Kickstart immediately; further steps are driven by update().
        self.update()

    def stop_auto(self, sender):
        self.auto_running = False
        self.auto_phase = 'idle'
        self.auto_next_time = 0.0

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
                self.auto_phase = 'speak_cz'
                self.auto_next_time = now + 0.85
            elif self.auto_phase == 'speak_cz':
                cz_word = (self.current_word or {}).get('CZ', '')
                self.btn_rev.title = cz_word
                if cz_word:
                    self._safe_say(cz_word)
                self.auto_phase = 'next_word'
                self.auto_next_time = now + 2.0
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

    def update_l(self, sender):
        if self.current_word:
            self.current_word['L'] = 'True' if sender.value else 'False'
            self.save_current_state()

    def update_ht(self, sender):
        if self.current_word:
            self.current_word['HT'] = 'True' if sender.value else 'False'
            self.update_stats()
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
        self.stop_auto(None)
        self._tts_log('will_close', speaking=self._is_speaking())
        self._tts_recover('will_close')
        # Keep close side-effect free (no auto-launch of another script).


if __name__ == '__main__':
    v = VocabTrainer()
    v.present('sheet')
