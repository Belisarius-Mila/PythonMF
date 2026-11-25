#!/usr/bin/env python3
"""Explicit one-shot maintenance; prepare never calls the model or changes service."""
from pathlib import Path
import argparse,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from app import recovery_guide_revalidation as recovery

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','run','accept'))
    parser.add_argument('--request-id',required=True)
    parser.add_argument('--approved-digest')
    parser.add_argument('--confirmed',action='store_true')
    parser.add_argument('--refresh-budget',action='store_true')
    parser.add_argument('--proposed-macos')
    parser.add_argument('--proposed-max-calls',type=int)
    args=parser.parse_args()
    options={'request_id':args.request_id}
    if args.action=='prepare':options.update(refresh_budget=args.refresh_budget,proposed_macos=args.proposed_macos,proposed_max_calls=args.proposed_max_calls)
    if args.action!='prepare':options.update(approved_digest=args.approved_digest,confirmed=args.confirmed)
    result=getattr(recovery,args.action)(**options)
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
