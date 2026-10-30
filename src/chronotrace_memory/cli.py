"""Offline command-line interface. No network requests or model calls."""

import argparse
import json
from pathlib import Path
import sqlite3
import sys

from .api import query_bundle


def main(argv=None):
    parser = argparse.ArgumentParser(description="ChronoTrace Memory: query source-grounded state history offline")
    parser.add_argument("--input", required=True, type=Path, help="JSON source snapshot and explicit events")
    parser.add_argument("--intent", choices=("current", "past", "history"), default="current")
    parser.add_argument("--as-of", help="ISO-8601 valid-time cutoff; current defaults to UTC now")
    parser.add_argument("--known-at", help="ISO-8601 recorded-time cutoff")
    parser.add_argument("--entity", help="exact normalized entity, e.g. Alice")
    parser.add_argument("--attribute", help="exact normalized attribute, e.g. home_city")
    parser.add_argument("--qualifier", help="exact normalized qualifier; omitted matches all")
    parser.add_argument("--ledger", type=Path, help="optional separate derived SQLite audit store")
    parser.add_argument("--scope", default="local", help="derived-ledger namespace")
    parser.add_argument("--compact", action="store_true", help="single-line JSON output")
    args = parser.parse_args(argv)
    try:
        if args.ledger and (args.input.resolve() == args.ledger.resolve() or
                            (args.ledger.exists() and args.input.samefile(args.ledger))):
            raise ValueError("input and derived ledger must be different files")
        bundle = json.loads(args.input.read_text(encoding="utf-8-sig"))
        result = query_bundle(bundle, intent=args.intent, as_of=args.as_of, known_at=args.known_at,
                              entity=args.entity, attribute=args.attribute, qualifier=args.qualifier,
                              ledger_path=args.ledger, scope=args.scope)
        print(json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2))
    except (OSError, ValueError, TypeError, OverflowError, sqlite3.Error) as error:
        print(f"chronotrace: {error}", file=sys.stderr)
        return 2
    return 0
