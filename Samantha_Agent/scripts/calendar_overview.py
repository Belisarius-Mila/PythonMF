"""Registered redacted calendar overview diagnostics; private details stay in Cockpit."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.calendar_overview import CalendarOverview


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('status','refresh','authorize'))
    parser.add_argument('--confirmed',action='store_true')
    args=parser.parse_args()
    store=CalendarOverview()
    try:
        result=store.snapshot() if args.action=='status' else store.execute({'action':args.action,'confirmed':args.confirmed})
        print(json.dumps({**{key:result.get(key) for key in ('ok','ready','status','authorization','last_loaded_at','calendar_writes','authorization_status')},
                          'calendar_count':len(result.get('calendars',[])), 'selected_count':len(result.get('read_calendar_ids',[])),
                          'event_count':len(result.get('events',[]))},ensure_ascii=False))
        return 0 if result.get('ok') else 1
    except Exception as exc:
        print(json.dumps({'ok':False,'error_type':type(exc).__name__,'automatic_retry':False}))
        return 1


if __name__=='__main__':
    raise SystemExit(main())
