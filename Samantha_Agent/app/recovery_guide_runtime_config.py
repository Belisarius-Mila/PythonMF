"""Explicit, private activation authority. Loading never creates configuration."""
from dataclasses import dataclass
from datetime import datetime
import json
import math
import os
from pathlib import Path, PurePosixPath

from app.recovery_guide_sources import canonical_json, digest, target_preview

ROOT = Path(__file__).resolve().parents[1]


def private(path):
    if any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError('runtime_configuration_alias')
    if path.exists() and (path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077):
        raise ValueError('runtime_configuration_not_private')


@dataclass(frozen=True)
class RuntimeConfig:
    path: Path
    envelope: str
    project: Path
    home: Path

    @property
    def payload(self):return json.loads(self.envelope)
    @property
    def sha256(self):return digest(self.envelope)
    @property
    def root(self):return self.path.parent
    @property
    def destinations(self):
        targets=target_preview(self.home,self.home/'Desktop/PythonMF')
        return tuple(Path(targets[k]) for k in ('local','icloud'))

    def guard(self):
        private(self.path);private(self.root)
        if canonical_json(json.loads(self.path.read_text())) != self.envelope:
            raise ValueError('runtime_activation_changed')
        if self.payload['enabled'] is not True:raise ValueError('runtime_not_activated')

    def permits(self,root,destinations=None):
        self.guard()
        if not root.is_absolute() or '..' in root.parts or not root.resolve().is_relative_to(self.root.resolve()):
            raise ValueError('runtime_state_outside_activation')
        if destinations is not None and tuple(destinations)!=self.destinations:
            raise ValueError('runtime_targets_outside_activation')


def load(project=ROOT,home=None):
    project=project.resolve(strict=True);home=home or Path.home()
    path=project/'data/private/recovery_guide_runtime/activation.json'
    if not path.exists() and not path.is_symlink():return None
    private(path);private(path.parent)
    raw=path.read_text()
    if len(raw.encode())>32000:raise ValueError('runtime_configuration_oversized')
    p=json.loads(raw)
    validate_payload(p)
    return RuntimeConfig(path,canonical_json(p),project,home)


def validate_payload(p):
    required={'schema','enabled','approved_at','schedule','limits','scopes','bootstrap','tokenizer','runtime_evidence','source_ref','publication_policy'}
    if not isinstance(p,dict) or set(p)!=required or type(p['schema']) is not int or p['schema']!=1 or type(p['enabled']) is not bool:
        raise ValueError('runtime_configuration_shape')
    from app.recovery_guide_scheduler import SchedulerPolicy
    from app.recovery_guide_maintainer import Limits
    policy=SchedulerPolicy(**p['schedule']);policy.check();Limits(**p['limits']).check()
    if (p['limits']['max_calls']>policy.max_calls or p['limits']['run_credits']>policy.run_credits
        or p['limits']['month_credits']>policy.month_credits or p['limits']['seconds']>policy.max_seconds):
        raise ValueError('runtime_budget_policy_mismatch')
    if policy.enabled!=p['enabled']:raise ValueError('runtime_schedule_activation_mismatch')
    if not isinstance(p['scopes'],list) or not p['scopes'] or any(not isinstance(s,str) or not s.endswith('/')
        or PurePosixPath(s).is_absolute() or '..' in PurePosixPath(s).parts for s in p['scopes']):
        raise ValueError('runtime_corpus_scope_required')
    if set(p['bootstrap'])!={'path','sha256'}:raise ValueError('runtime_bootstrap_shape')
    import re
    if not Path(p['bootstrap']['path']).is_absolute() or not re.fullmatch('[a-f0-9]{64}',p['bootstrap']['sha256']):
        raise ValueError('runtime_bootstrap_binding_required')
    token=p['tokenizer']
    if (set(token)!={'package_version','encoding','margin','reference_uncertainty_accepted'}
        or token['encoding']!='o200k_base' or not isinstance(token['package_version'],str)
        or type(token['margin']) not in {float,int} or not math.isfinite(token['margin']) or not 1.2<=token['margin']<=2
        or token['reference_uncertainty_accepted'] is not True):raise ValueError('runtime_counter_not_approved')
    evidence=p['runtime_evidence']
    if (set(evidence)!={'server_version','protocol_sha256','input_tokens','reference'}
        or not isinstance(evidence['server_version'],str) or not isinstance(evidence['reference'],str)
        or not evidence['reference'].strip() or not re.fullmatch('[a-f0-9]{64}',evidence['protocol_sha256'])
        or type(evidence['input_tokens']) is not int or not 0<evidence['input_tokens']<=450000
        or p['limits']['input_tokens']>evidence['input_tokens']):raise ValueError('runtime_context_evidence_required')
    if p['source_ref'] not in {'HEAD','refs/heads/main'}:raise ValueError('runtime_source_ref_not_approved')
    publication=p['publication_policy']
    if publication=={'mode':'manual'}:pass
    elif (not isinstance(publication,dict) or set(publication)!={'mode','applications','macos_baseline'}
        or publication['mode']!='validated_auto_v1' or not isinstance(publication['applications'],list)
        or not publication['applications'] or any(not isinstance(a,str) or not a.strip() for a in publication['applications'])
        or len(set(publication['applications']))!=len(publication['applications'])
        or not isinstance(publication['macos_baseline'],str) or not publication['macos_baseline'].strip()):
        raise ValueError('runtime_publication_policy_not_approved')
    from app.recovery_guide_quality import safe_text
    safe_text(canonical_json(publication))
    instant=datetime.fromisoformat(p['approved_at'])
    if instant.tzinfo is None:raise ValueError('runtime_approval_timezone_required')
    return p
