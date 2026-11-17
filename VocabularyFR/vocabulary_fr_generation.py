"""Bounded Azure production for an approved private FR plan; no publication.

One invocation processes at most 10,000 SSML characters. A shared durable
ledger also caps the complete plan and money across invocations. Any reserved
or uncertain request blocks further transport until explicitly reconciled.
"""
from __future__ import annotations

import argparse
from decimal import Decimal
import fcntl
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'Samantha_Agent'))

from app.file_persistence import atomic_write_json
from app.speech.azure_tts_mp3 import CharacterBudget, ssml_parts, synthesize_azure_tts_mp3_sync
from vocabulary_fr_catalog import digest, encoded, load, private_output, safe_file, sha
import vocabulary_fr_export as export

VOICES = {'fr': 'fr-FR-HenriNeural', 'cz': 'cs-CZ-VlastaNeural'}
UNCERTAIN = {'reserved', 'uncertain'}


def code_sources(code_commit):
    if not isinstance(code_commit, str) or not re.fullmatch(r'[0-9a-f]{40}', code_commit):
        raise ValueError('Exact production code commit required.')
    files = {}
    for relative in ('VocabularyFR/vocabulary_fr_catalog.py', 'VocabularyFR/vocabulary_fr_audio.py',
                     'VocabularyFR/vocabulary_fr_export.py', 'VocabularyFR/vocabulary_fr_generation.py',
                     'Samantha_Agent/app/speech/azure_tts_mp3.py'):
        frozen = subprocess.run(['git', '-C', str(ROOT), 'show', code_commit + ':' + relative],
                                capture_output=True, check=True).stdout
        if (ROOT / relative).read_bytes() != frozen:
            raise ValueError('Running production code differs from checkpoint.')
        files[relative] = sha(frozen)
    return files


def checked_plan(plan, approval):
    unsigned = {k: v for k, v in plan.items() if k != 'planSha256'}
    identity = sha(encoded(unsigned))
    if (plan.get('schemaVersion') != 1 or plan.get('project') != 'VocabularyFR'
            or plan.get('planSha256') != identity or approval.get('planSha256') != identity
            or approval.get('approved') is not True
            or approval.get('provider') != 'registered-azure-neural'
            or approval.get('voices') != VOICES or approval.get('rate') != '-10%'
            or approval.get('maxCharactersPerInvocation') != 10000
            or approval.get('publicPromotionApproved') is not False
            or approval.get('noAutomaticRetry') is not True
            or approval.get('sourceBundleManifestSha256') != plan.get('sourceBundleManifestSha256')):
        raise ValueError('Plan, source or explicit approval does not match.')
    jobs = plan.get('jobs', {})
    if not jobs:
        raise ValueError('No production jobs.')
    count = 0
    for key, job in jobs.items():
        fields = {k: job.get(k) for k in ('kind', 'channel', 'voice', 'rate', 'text')}
        if (job.get('id') != key or sha(encoded(fields)) != key
                or fields['kind'] not in {'words', 'sentences'}
                or fields['channel'] not in VOICES or fields['voice'] != VOICES[fields['channel']]
                or fields['rate'] != '-10%' or not job.get('sourceUids')):
            raise ValueError('Invalid exact speech job.')
        _ssml, billable = ssml_parts(fields['text'], fields['voice'], fields['rate'])
        if billable != job.get('billableCharacters'):
            raise ValueError('Billable text changed.')
        count += billable
    price = Decimal(str(approval['quotedPriceUsdPerMillionCharacters']))
    cap = Decimal(str(approval['maxCostUsdExcludingTax']))
    if (price <= 0 or cap <= 0 or cap > 2 or count != plan.get('totalBillableCharacters')
            or count != approval.get('planBillableCharacters') or Decimal(count) * price / 1000000 > cap):
        raise ValueError('Complete plan exceeds the approved character or cost scope.')
    batched = []
    for batch in plan.get('batches', []):
        ids = batch.get('jobIds', [])
        if (not ids or any(key not in jobs for key in ids)
                or sum(jobs[k]['billableCharacters'] for k in ids) != batch.get('reservedCharacters')
                or not 0 < batch['reservedCharacters'] <= 10000):
            raise ValueError('Invalid bounded invocation.')
        batched.extend(ids)
    if len(batched) != len(jobs) or set(batched) != set(jobs):
        raise ValueError('Batches do not cover each approved job once.')
    return identity


def check_sources(plan, bundle):
    if digest(safe_file(bundle, 'manifest.json')) != plan['sourceBundleManifestSha256']:
        raise ValueError('Source bundle is not the approved closed version.')
    manifest = load(Path(bundle) / 'manifest.json')
    if manifest['catalogSha256'] != plan['sourceCatalogSha256']:
        raise ValueError('Source catalog changed.')
    return manifest


def decoded(path):
    result = subprocess.run(['ffmpeg', '-v', 'error', '-xerror', '-i', str(path), '-f', 'null', '-'],
                            capture_output=True, timeout=30, check=False)
    if result.returncode or result.stderr:
        raise ValueError('MP3 failed full decoding.')
    result = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration:stream=codec_name',
                             '-of', 'json', str(path)], capture_output=True, text=True, timeout=15, check=True)
    probe = json.loads(result.stdout)
    duration = float(probe['format']['duration'])
    if duration <= .05 or not any(s.get('codec_name') == 'mp3' for s in probe['streams']):
        raise ValueError('Empty or non-MP3 audio.')
    return duration


def produce(plan, approval, output, job_ids, *, synthesize, verify_media=decoded,
            source_guard=lambda: True, interval=.65):
    """Process one bounded invocation. Injection is for synthetic tests only."""
    checked_plan(plan, approval)
    output = private_output(output)
    output.mkdir(parents=True, mode=0o700, exist_ok=True)
    if len(job_ids) != len(set(job_ids)) or set(job_ids) - set(plan['jobs']):
        raise ValueError('Unknown or duplicate selected job.')
    required = sum(plan['jobs'][key]['billableCharacters'] for key in job_ids)
    if not 0 < required <= 10000:
        raise ValueError('One invocation may not exceed 10,000 characters.')
    path = output / 'ledger.json'
    with (output / 'production.lock').open('a+b') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        ledger = (load(path) if path.exists() else {
            'schemaVersion': 1, 'project': 'VocabularyFR-Azure', 'planSha256': plan['planSha256'],
            'approvalSha256': sha(encoded(approval)), 'reservedCharacters': 0, 'jobs': {}, 'runs': [],
            'engineSha256': digest(Path(__file__)),
            'adapterSha256': digest(ROOT / 'Samantha_Agent/app/speech/azure_tts_mp3.py')})
        if (ledger.get('planSha256') != plan['planSha256']
                or ledger.get('approvalSha256') != sha(encoded(approval))
                or ledger.get('engineSha256') != digest(Path(__file__))
                or ledger.get('adapterSha256') != digest(ROOT / 'Samantha_Agent/app/speech/azure_tts_mp3.py')):
            raise ValueError('Receipt belongs to another approval or plan.')
        if any(j.get('state') in UNCERTAIN for j in ledger['jobs'].values()):
            raise ValueError('Uncertain prior request: no automatic transport or retry.')
        for key, previous in ledger['jobs'].items():
            if key not in plan['jobs'] or previous.get('state') != 'complete':
                raise ValueError('Unknown prior request state.')
            if digest(safe_file(output, previous['asset'])) != previous['sha256']:
                raise ValueError('A completed MP3 changed or disappeared; restore, do not regenerate.')
        if sum(plan['jobs'][k]['billableCharacters'] for k in ledger['jobs']) != ledger['reservedCharacters']:
            raise ValueError('Reservation ledger is inconsistent.')
        pending = [k for k in job_ids if k not in ledger['jobs']]
        budget = CharacterBudget(limit=max(1, required))
        run = {'plannedJobs': len(job_ids), 'pendingJobs': len(pending), 'characterLimit': required,
               'state': 'running'}
        ledger['runs'].append(run)
        save = lambda: atomic_write_json(path, ledger, ensure_ascii=False, indent=2)
        save(); last_start = 0.
        for key in pending:
            job = plan['jobs'][key]
            wait = interval - (time.monotonic() - last_start)
            if wait > 0:
                time.sleep(wait)
            if not source_guard():
                raise ValueError('Frozen source/config/code changed; no further transport.')
            total = ledger['reservedCharacters'] + job['billableCharacters']
            cost = Decimal(total) * Decimal(str(approval['quotedPriceUsdPerMillionCharacters'])) / 1000000
            if total > plan['totalBillableCharacters'] or cost > Decimal(str(approval['maxCostUsdExcludingTax'])):
                raise ValueError('Cumulative authorization limit reached before transport.')
            ledger['reservedCharacters'] = total
            previous = {'state': 'reserved', 'characters': job['billableCharacters'],
                        'voice': job['voice'], 'textSha256': sha(job['text'].encode())}
            ledger['jobs'][key] = previous
            save(); last_start = time.monotonic()
            try:
                raw = synthesize(job['text'], voice=job['voice'], rate=job['rate'], budget=budget)
                if not isinstance(raw, bytes) or len(raw) < 1000:
                    raise ValueError('No usable MP3 returned.')
                checksum = sha(raw)
                namespace = 'audio' if job['kind'] == 'words' else 'sentences'
                slug = re.sub(r'([a-z])([A-Z])', r'\1-\2', job['voice']).lower()
                relative = f'assets/vocabulary-fr-{namespace}/{slug}/{checksum}.mp3'
                target = output / relative
                if target.exists():
                    if digest(safe_file(output, relative)) != checksum:
                        raise ValueError('Existing content-addressed MP3 differs.')
                else:
                    export.write_new(target, raw)
                duration = verify_media(target)
            except Exception as exc:
                previous.update(state='uncertain', errorType=type(exc).__name__)
                run['state'] = 'stopped-no-retry'; save()
                raise RuntimeError('Production stopped; reservation retained, no automatic retry.') from None
            previous.update(state='complete', sha256=checksum, asset=relative, bytes=len(raw), durationSeconds=duration)
            save()
            if len(ledger['jobs']) % 25 == 0 or len(pending) <= 2:
                print(json.dumps({'complete': len(ledger['jobs']), 'total': len(plan['jobs']),
                                  'reservedCharacters': ledger['reservedCharacters']}), flush=True)
        run.update(state='complete', reservedCharacters=budget.reserved)
        ledger['state'] = 'complete' if len(ledger['jobs']) == len(plan['jobs']) else 'partial'
        save()
        return {'state': ledger['state'], 'complete': len(ledger['jobs']),
                'reservedCharacters': ledger['reservedCharacters'], 'newRequests': len(pending)}


def seal(plan, approval, source, generated, output, *, code_commit, bundle_id):
    checked_plan(plan, approval); check_sources(plan, source)
    export.verify(source, expected_manifest_sha256=plan['sourceBundleManifestSha256'])
    ledger = load(safe_file(generated, 'ledger.json'))
    if (ledger.get('state') != 'complete' or set(ledger['jobs']) != set(plan['jobs'])
            or ledger.get('planSha256') != plan['planSha256']
            or ledger.get('approvalSha256') != sha(encoded(approval))
            or ledger.get('reservedCharacters') != plan['totalBillableCharacters']
            or any(v.get('state') != 'complete' for v in ledger['jobs'].values())):
        raise ValueError('Production is not completely verified.')
    output = private_output(output)
    if output.exists() or not re.fullmatch(r'[a-z0-9-]{4,100}', bundle_id):
        raise ValueError('Use a new private bundle version.')
    code_files = code_sources(code_commit)
    base = load(Path(source) / 'manifest.json')
    output.mkdir(parents=True, mode=0o700)
    for relative in base['files']:
        export.write_new(output / relative, safe_file(source, relative).read_bytes())
    payload = output / 'payload'; provenance = load(output / 'audio-provenance.json')
    for kind, filename in export.AUDIO_NAMES.items():
        manifest = load(payload / filename)
        manifest['voices'] = VOICES; manifest['provider'] = 'verified-existing-czech-mp3+registered-azure-neural'
        for uid, record in manifest['items'].items():
            for channel in ('fr', 'cz'):
                ref = plan['references'][f'{kind}:{uid}:{channel}']
                if 'existingAsset' in ref:
                    if record[channel] != ref['existingAsset']:
                        raise ValueError('Existing sound identity changed.')
                    continue
                key = ref['jobId']; job = plan['jobs'][key]; completed = ledger['jobs'][key]
                if (job['kind'] != kind or job['channel'] != channel or job['voice'] != VOICES[channel]
                        or uid not in job['sourceUids'] or job['text'] != record['spoken' + channel.title()]):
                    raise ValueError('New MP3 has a different source identity.')
                raw = safe_file(generated, completed['asset']).read_bytes()
                if sha(raw) != completed['sha256']:
                    raise ValueError('Generated MP3 changed.')
                target = payload / completed['asset']
                if not target.exists():
                    export.write_new(target, raw)
                record[channel] = completed['asset']; manifest['assetSha256'][completed['asset']] = completed['sha256']
                origin = provenance.setdefault(completed['asset'], {'provider': 'registered-azure-neural',
                    'voice': job['voice'], 'rate': job['rate'], 'kind': kind})
                reference = {'textSha256': completed['textSha256'], 'jobId': key}
                if reference not in origin.setdefault('productionJobs', []):
                    origin['productionJobs'].append(reference)
        manifest['status'] = 'complete'; manifest['sourceDigest'] = sha(encoded(manifest['items']))
        (payload / filename).write_bytes(encoded(manifest))
    data = load(payload / export.DATA_NAME); data['audioStatus'] = 'complete'
    (payload / export.DATA_NAME).write_bytes(encoded(data))
    (output / 'audio-provenance.json').write_bytes(encoded(provenance))
    for name, value in [('production-plan.json', plan), ('production-approval.json', approval),
                        ('production-receipt.json', ledger)]:
        export.write_new(output / name, encoded(value))
    proof = export.validate_payload(payload, load(output / 'catalog.json'))
    files = {p.relative_to(output).as_posix(): {'bytes': p.stat().st_size, 'sha256': digest(p)}
             for p in sorted(output.rglob('*')) if p.is_file()}
    manifest = {'schemaVersion': 1, 'project': 'VocabularyFR', 'bundleId': bundle_id, 'state': 'closed-private',
        'private': True, 'publicPromotionApproved': False, 'itemCount': data['itemCount'],
        'sourceRowCount': data['sourceRowCount'], 'catalogSha256': digest(output / 'catalog.json'),
        'codeCommit': code_commit, 'codeSourceSha256': {k: v for k, v in code_files.items() if k in base['codeSourceSha256']},
        'productionCodeSha256': code_files, 'sourceBundleManifestSha256': plan['sourceBundleManifestSha256'],
        'productionPlanSha256': plan['planSha256'], 'contentDigest': sha(encoded(files)), 'files': files,
        'verification': proof}
    export.write_new(output / 'manifest.json', encoded(manifest))
    return export.verify(output)


def verify_production(bundle, *, expected_manifest_sha256, decode_audio=False):
    proof = export.verify(bundle, expected_manifest_sha256=expected_manifest_sha256, decode_audio=decode_audio)
    root = Path(bundle); manifest = load(root / 'manifest.json')
    plan = load(safe_file(root, 'production-plan.json'))
    approval = load(safe_file(root, 'production-approval.json'))
    checked_plan(plan, approval)
    ledger = load(safe_file(root, 'production-receipt.json'))
    if (manifest.get('productionCodeSha256') != code_sources(manifest['codeCommit'])
            or manifest.get('productionPlanSha256') != plan['planSha256']
            or ledger.get('planSha256') != plan['planSha256']
            or ledger.get('approvalSha256') != sha(encoded(approval))
            or ledger.get('state') != 'complete' or set(ledger['jobs']) != set(plan['jobs'])
            or ledger.get('reservedCharacters') != plan['totalBillableCharacters']
            or any(v.get('state') != 'complete' for v in ledger['jobs'].values())):
        raise ValueError('Production code/approval/receipt differs from the closed plan.')
    for job_id, completed in ledger['jobs'].items():
        job = plan['jobs'][job_id]
        if (digest(safe_file(root / 'payload', completed['asset'])) != completed['sha256']
                or completed.get('textSha256') != sha(job['text'].encode())
                or completed.get('characters') != job['billableCharacters'] or completed.get('voice') != job['voice']):
            raise ValueError('Closed generated audio lost its exact source provenance.')
    proof.update(newAzureRequests=len(ledger['jobs']), reservedCharacters=ledger['reservedCharacters'],
                 estimatedCostUsdExcludingTax=float(Decimal(ledger['reservedCharacters']) *
                    Decimal(str(approval['quotedPriceUsdPerMillionCharacters'])) / 1000000))
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check-plan', 'generate', 'seal', 'verify'])
    parser.add_argument('--plan', type=Path); parser.add_argument('--approval', type=Path)
    parser.add_argument('--source', type=Path); parser.add_argument('--output', type=Path)
    parser.add_argument('--env-file', type=Path); parser.add_argument('--batch', type=int); parser.add_argument('--pilot', action='store_true')
    parser.add_argument('--generated', type=Path); parser.add_argument('--code-commit'); parser.add_argument('--bundle-id')
    parser.add_argument('--bundle', type=Path); parser.add_argument('--expected-manifest-sha256'); parser.add_argument('--decode-audio', action='store_true')
    args = parser.parse_args()
    if args.command == 'verify':
        if not args.bundle or not args.expected_manifest_sha256:
            parser.error('verify requires bundle and expected-manifest-sha256')
        print(json.dumps(verify_production(args.bundle, expected_manifest_sha256=args.expected_manifest_sha256,
                                          decode_audio=args.decode_audio))); return
    if not all((args.plan, args.approval, args.source)):
        parser.error('plan, approval and source required')
    plan = load(args.plan); approval = load(args.approval)
    checked_plan(plan, approval); check_sources(plan, args.source)
    if args.command == 'check-plan':
        export.verify(args.source, expected_manifest_sha256=plan['sourceBundleManifestSha256'])
        print(json.dumps({'jobs': len(plan['jobs']), 'characters': plan['totalBillableCharacters'], 'approved': True})); return
    if args.command == 'seal':
        if not all((args.generated, args.output, args.code_commit, args.bundle_id)):
            parser.error('seal requires generated, output, code-commit and bundle-id')
        print(json.dumps(seal(plan, approval, args.source, args.generated, args.output,
                              code_commit=args.code_commit, bundle_id=args.bundle_id))); return
    if not args.output or not args.env_file or not args.code_commit or (args.pilot == (args.batch is not None)):
        parser.error('generate requires output, env-file, code-commit and exactly one pilot/batch selection')
    code_sources(args.code_commit)
    from app.capabilities import get_capability, RiskLevel
    from app.communication.trusted_external_generation import TrustedExternalGenerationConsentStore
    consent = TrustedExternalGenerationConsentStore(args.env_file.parent / 'data/private/communication/trusted_external_generation_consent.json')
    cap = get_capability('generate_project_azure_audio_asset')
    if (cap.risk != RiskLevel.EXTERNAL_GENERATION or cap.tool != 'app.speech.azure_tts_mp3.synthesize_azure_tts_mp3_sync'
            or not consent.status()['enabled']):
        raise ValueError('Registered Azure capability or durable consent is unavailable.')
    import os
    from dotenv import dotenv_values
    settings = {**dotenv_values(args.env_file), **os.environ}
    if (not settings.get('AZURE_SPEECH_KEY') or not approval.get('region')
            or settings.get('AZURE_SPEECH_REGION') != approval['region']):
        raise ValueError('Azure credentials are missing or region differs from approved quote.')
    paths = [args.plan, args.approval, Path(args.source) / 'manifest.json', args.env_file,
             Path(__file__), ROOT / 'Samantha_Agent/app/speech/azure_tts_mp3.py']
    signatures = {p: (p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_ctime_ns) for p in paths}
    guard = lambda: consent.status()['enabled'] and all(
        (p.stat().st_ino, p.stat().st_size, p.stat().st_mtime_ns, p.stat().st_ctime_ns) == sig for p, sig in signatures.items())
    if args.pilot:
        ids = [next(k for k, j in plan['jobs'].items() if j['channel'] == channel) for channel in ('fr', 'cz')]
    else:
        if not 0 <= args.batch < len(plan['batches']):
            raise ValueError('Unknown batch.')
        ids = plan['batches'][args.batch]['jobIds']
    synthesize = lambda text, **kwargs: synthesize_azure_tts_mp3_sync(text, env_path=args.env_file, **kwargs)
    print(json.dumps(produce(plan, approval, args.output, ids, synthesize=synthesize, source_guard=guard)), flush=True)


if __name__ == '__main__':
    main()
