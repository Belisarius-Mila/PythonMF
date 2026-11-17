#!/usr/bin/env python3
"""Redacted SMS preview/status; tick requires already authorized private policy."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.family_calendar_sms import CalendarSMS


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('status', 'preview', 'tick'))
    args = parser.parse_args(argv)
    try:
        service = CalendarSMS()
        result = getattr(service, args.action)()
    except Exception:
        result = {'status': 'unverified', 'transport_called': False, 'redacted': True}
    print(json.dumps(result, ensure_ascii=False))
    return 1 if result.get('status') == 'unverified' else 0


if __name__ == '__main__':
    raise SystemExit(main())
