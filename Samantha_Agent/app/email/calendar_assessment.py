"""Optional calendar evidence from the existing email assessment; no IO or model calls."""
from __future__ import annotations

from email import policy
from email.parser import BytesParser
import re

from .calendar_proposal import Candidate, Claim, materialize
from .icloud_provider import _html_to_text


def source_context(observed):
    source = observed.source
    if not source.original_eml or len(source.original_eml) > 8*1024*1024:
        raise ValueError('Zdrojový e-mail chybí nebo překročil limit návrhového pilotu.')
    context = {'subject':source.subject, 'date':source.date, 'body':source.body_text, 'html':source.body_html}
    if sum(len(value.encode()) for value in context.values()) > 256000:
        raise ValueError('Text zprávy chybí nebo překročil limit; model nebyl spuštěn.')
    mime = BytesParser(policy=policy.default).parsebytes(source.original_eml)
    formal = any(part.get_content_type()=='text/calendar' or (part.get_filename() or '').lower().endswith('.ics') for part in mime.walk())
    recurring = bool(re.search(r'\b(každ[ýéou]\s+(pondělí|úterý|střed[au]|čtvrtek|pátek|sobot[au]|neděli|týden|měsíc)|every\s+(monday|tuesday|wednesday|thursday|friday|week|month)|RRULE\s*:)',source.body_text+' '+_html_to_text(source.body_html),re.I))
    context['manual_reason'] = 'Formální kalendářová pozvánka vyžaduje ruční zpracování.' if formal else 'Opakování vyžaduje ruční zpracování.' if recurring else ''
    if not context['manual_reason'] and not (source.body_text or source.body_html):
        raise ValueError('Text zprávy chybí; model nebyl spuštěn.')
    return context


def calendar_suggestion(observed, raw_candidate, *, model):
    """A bad optional candidate must never discard the existing email proposal."""
    base = {'version': 1, 'source_digest': observed.content_digest, 'model': model}
    try:
        context = source_context(observed)
        if context['manual_reason']:
            candidate = Candidate(kind='manual_required',
                title=Claim(value=context['subject'], source='subject' if context['subject'] else 'none', quote=context['subject']),
                uncertainties=[context['manual_reason']])
        elif raw_candidate is None:
            return {**base, 'status': 'not_applicable'}
        else:
            candidate = Candidate.model_validate(raw_candidate)
        materialize(candidate, context)  # Use exactly the existing citation resolver.
        if candidate.kind == 'not_applicable':
            return {**base, 'status': 'not_applicable'}
        if any(len(warning) > 1000 for warning in candidate.uncertainties):
            raise ValueError('Upozornění překročilo limit.')
        return {**base, 'status': 'ready', 'candidate': candidate.model_dump(), 'input': context}
    except ValueError:
        return {**base, 'status': 'invalid'}
