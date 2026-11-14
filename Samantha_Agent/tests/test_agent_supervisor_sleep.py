from __future__ import annotations
import copy
from datetime import timedelta
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import Mock

from app.agent_supervisor import AgentSupervisor, LABELS
from app.agent_supervisor_probes import collect, power_probe
from tests.test_agent_supervisor import evidence, NOW, FAILURE, RECOVERY


class PowerProbeTests(unittest.TestCase):
    def runner(self, capabilities, wake=None):
        def run(args, **kwargs):
            self.assertEqual(kwargs['timeout'], 3)
            if args[0].endswith('pmset'):
                self.assertEqual(args, ['/usr/bin/pmset', '-g', 'systemstate'])
                return subprocess.CompletedProcess(args, 0, capabilities, '')
            self.assertEqual(args, ['/usr/sbin/sysctl', '-n', 'kern.waketime'])
            return subprocess.CompletedProcess(args, 0, wake or '{ sec = 1794555000, usec = 123 }', '')
        return run

    def test_full_wake_and_maintenance_wake_are_distinct_without_lid_assumptions(self):
        for text, expected in [('CPU Graphics Audio Network', 'awake'), ('CPU Network', 'sleeping'), ('None', 'sleeping')]:
            result = power_probe(runner=self.runner('Current System Capabilities are: '+text+' \nCurrent Power State: 4\n'))
            self.assertEqual(result['state'], expected)
            self.assertTrue(result['wake_at'].endswith('+00:00'))

    def test_unknown_capabilities_never_claim_sleep_or_health(self):
        for text in ['', 'PRIVATE malformed text', 'Current System Capabilities are: Surprise']:
            self.assertEqual(power_probe(runner=self.runner(text)), {'state': 'unknown'})

    def test_failed_wake_timestamp_still_uses_safe_transition_fallback(self):
        result = power_probe(runner=self.runner('Current System Capabilities are: CPU Graphics', 'invalid'))
        self.assertEqual(result, {'state': 'awake', 'wake_at': ''})

    def test_sleep_and_unknown_skip_all_watched_probes(self):
        for state in ['sleeping', 'unknown']:
            probes = {key: Mock(side_effect=AssertionError('must not contact services')) for key in LABELS}
            probes['power'] = lambda: {'state': state}
            self.assertEqual(collect(probes=probes), {'power': {'state': state}})
            for key in LABELS: probes[key].assert_not_called()

    def test_power_failure_is_redacted_and_does_not_wake_services(self):
        probes = {'power': Mock(side_effect=OSError('PRIVATE TOKEN'))}
        self.assertEqual(collect(probes=probes), {'power': {'state': 'unknown'}})


class SleepLifecycleTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(); self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)/'supervisor'; self.now = NOW; self.sent = []
        self.value = self.healthy()
        self.service = self.instance()
        self.service.configure(enabled=True, notifications_enabled=True,
            failure_url=FAILURE, recovery_url=RECOVERY, confirmed=True)

    def healthy(self):
        value = evidence(self.now)
        value['power'] = {'state': 'awake', 'wake_at': (NOW-timedelta(hours=1)).isoformat()}
        return value

    def instance(self):
        return AgentSupervisor(self.root, collector=lambda: copy.deepcopy(self.value), clock=lambda:self.now,
            sender=lambda url:self.sent.append(url) or {'status':'accepted'})

    def step(self, seconds=120, bad=False, power=None):
        self.now += timedelta(seconds=seconds); self.value = self.healthy()
        if bad: self.value['cockpit']['reachable'] = False
        if power is not None: self.value['power'] = power
        return self.service.check(scheduled=True)

    def ready(self):
        self.service.check(scheduled=True)
        self.step(300)

    def test_darkwake_and_long_sleep_never_open_or_close_incidents_or_send(self):
        self.value = {'power': {'state': 'sleeping'}}
        for _ in range(8):
            result = self.service.check(scheduled=True)
            self.assertTrue(result['notifications_paused'])
            self.assertEqual({r['state'] for r in result['rows']}, {'paused'})
            self.now += timedelta(minutes=17)
        self.assertEqual(self.sent, [])
        self.assertEqual(self.service.repository.read()['incidents'], {})
        raw = self.service.repository.read()['rows']
        self.assertEqual({r['state'] for r in raw}, {'unknown'})
        self.assertEqual({r['code'] for r in raw}, {'unavailable'}, 'previous Cockpit must still be able to read the snapshot')

    def test_wake_grace_survives_restart_and_repeated_polling_without_extension(self):
        self.step(0, power={'state':'sleeping'})
        first = self.step(120, bad=True)
        self.assertEqual(first['notification_pause_reason'], 'wake_grace')
        due = self.service.repository.read()['resume_after']
        self.service = self.instance()
        self.step(120, bad=True)
        self.assertEqual(self.service.repository.read()['resume_after'], due)
        self.assertEqual(self.sent, [])
        self.step(180, bad=True)
        self.assertEqual(self.sent, [], 'first post-grace failure needs confirmation')
        self.step(120, bad=True)
        self.assertEqual(self.sent, [FAILURE])

    def test_transient_failure_never_alerts_or_sends_false_recovery(self):
        self.ready(); self.step(bad=True); self.step()
        self.assertEqual(self.sent, [])
        self.assertEqual(self.service.repository.read()['events'], {})

    def test_only_continuous_bad_samples_confirm_then_recover_once(self):
        self.ready(); self.step(bad=True)
        self.service.check(scheduled=True)
        self.assertEqual(self.sent, [], 'repeated same-time check is not another interval')
        self.step(120, bad=True); self.step(120, bad=True)
        self.assertEqual(self.sent, [FAILURE])
        self.step(); self.step()
        self.assertEqual(self.sent, [FAILURE, RECOVERY])

    def test_incident_is_frozen_during_sleep_and_grace_without_false_recovery(self):
        self.ready(); self.step(bad=True); self.step(bad=True)
        incident = self.service.repository.read()['incidents']['cockpit']['id']
        self.step(power={'state':'sleeping'})
        self.assertFalse(self.service.repository.read()['incidents']['cockpit']['closed_at'])
        self.step(); self.step(120)
        self.assertEqual(self.sent, [FAILURE])
        self.step(180)
        self.assertEqual(self.sent, [FAILURE, RECOVERY])
        self.assertEqual(self.service.repository.read()['incidents']['cockpit']['id'], incident)

    def test_gap_without_darkwake_record_still_starts_grace(self):
        self.ready()
        result = self.step(3600, bad=True)
        self.assertEqual(result['notification_pause_reason'], 'wake_grace')
        self.assertEqual(self.sent, [])

    def test_os_wake_timestamp_catches_short_sleep_between_regular_samples(self):
        self.ready()
        self.now += timedelta(seconds=120); self.value = self.healthy()
        self.value['power']['wake_at'] = (self.now-timedelta(seconds=10)).isoformat()
        self.assertEqual(self.service.check(scheduled=True)['notification_pause_reason'], 'wake_grace')

    def test_unknown_and_future_power_evidence_never_claim_health_or_dispatch(self):
        self.ready()
        for power in [{'state':'unknown'}, {'state':'awake','wake_at':(self.now+timedelta(days=1)).isoformat()}]:
            result = self.step(bad=True, power=power)
            self.assertEqual(result['notification_pause_reason'], 'power_unknown')
            self.assertEqual({r['state'] for r in result['rows']}, {'paused'})
        self.assertEqual(self.sent, [])

    def test_night_email_staleness_does_not_restart_incidents_each_darkwake(self):
        self.now = NOW.replace(hour=2); self.value = self.healthy()
        self.value['email']['health']['finished_at'] = (self.now-timedelta(hours=2)).isoformat()
        self.service.check(scheduled=True)
        self.now += timedelta(minutes=5)
        self.service.check(scheduled=True)
        self.now += timedelta(minutes=2)
        self.service.check(scheduled=True)
        self.assertEqual(self.sent, [])
        self.assertNotIn('email', self.service.repository.read()['incidents'])

    def test_pending_notification_before_sleep_requires_fresh_confirmation(self):
        self.ready(); self.step(bad=True)
        original = self.service._dispatch
        self.service._dispatch = lambda _config: None
        self.step(bad=True)
        self.service._dispatch = original
        self.step(power={'state':'sleeping'})
        self.step(bad=True); self.step(300, bad=True)
        self.assertEqual(self.sent, [])
        self.step(120, bad=True)
        self.assertEqual(self.sent, [FAILURE])

    def test_autosave_has_time_for_its_ten_minute_cycle_after_wake(self):
        self.service.check(scheduled=True)
        for _ in range(3):
            self.now += timedelta(minutes=2)
            self.value = self.healthy()
            self.value['autosave']['latest_modified_at'] = (NOW-timedelta(hours=1)).isoformat()
            result = self.service.check(scheduled=True)
        self.assertEqual(next(r for r in result['rows'] if r['id']=='autosave')['code'], 'autosave_wake_grace')
        self.assertEqual(self.sent, [])
        self.now += timedelta(minutes=4)
        self.value = self.healthy()
        self.assertEqual(next(r for r in self.service.check(scheduled=True)['rows'] if r['id']=='autosave')['state'], 'ok')
        self.assertEqual(self.sent, [])

    def test_autosave_still_fails_after_its_wake_allowance_and_confirmation(self):
        self.service.check(scheduled=True)
        # Keep the scheduler's own last sample recent, as in regular two-minute ticks.
        for seconds in [300, 420, 540, 660, 780, 900, 960]:
            self.now = NOW+timedelta(seconds=seconds)
            self.value = self.healthy(); self.value['autosave']['latest_modified_at'] = (NOW-timedelta(hours=1)).isoformat()
            self.service.check(scheduled=True)
        self.now += timedelta(seconds=120)
        self.value['email'] = evidence(self.now)['email']
        self.service.check(scheduled=True)
        self.assertEqual(self.sent, [FAILURE])
