"""Portable snapshot-query adapter; the frozen research kernel is unchanged."""

from datetime import datetime, timezone
from pathlib import Path

from . import lifecycle as core


def _time(value, field):
    if value is None or value == "":
        return None
    result = core.timestamp(value)
    if isinstance(value, bool) or result is None:
        raise ValueError(f"{field} must be an ISO-8601 timestamp or Unix milliseconds")
    return result


def _sources(bundle):
    if not isinstance(bundle, dict) or not isinstance(bundle.get("sources"), list):
        raise ValueError("input must be an object containing a sources array")
    pool, identities = [], set()
    for i, source in enumerate(bundle["sources"]):
        if not isinstance(source, dict):
            raise ValueError(f"sources[{i}] must be an object")
        for field in ("source_id", "body", "role"):
            if not isinstance(source.get(field), str) or not source[field]:
                raise ValueError(f"sources[{i}].{field} must be a nonempty string")
        if source["source_id"] in identities:
            raise ValueError("source_id must be unique within the snapshot")
        identities.add(source["source_id"])
        if not isinstance(source.get("speaker", ""), str):
            raise ValueError(f"sources[{i}].speaker must be a string")
        for field, default in (("start", 0), ("position", i)):
            if type(source.get(field, default)) is not int or source.get(field, default) < 0:
                raise ValueError(f"sources[{i}].{field} must be a nonnegative integer")
        pool.append({
            "source_id": source["source_id"], "body": source["body"],
            "role": source["role"], "speaker": source.get("speaker", ""),
            "timestamp": _time(source.get("recorded_at"), f"sources[{i}].recorded_at"),
            "start": source.get("start", 0), "position": source.get("position", i),
            "request_id": source.get("request_id"), "session_id": source.get("session_id"),
        })
    return pool


def _events(bundle, pool):
    raw_events = bundle.get("events")
    if not isinstance(raw_events, list):
        raise ValueError("input must contain an events array")
    fields = {"entity", "attribute", "qualifier", "value", "quote", "valid_from", "valid_to", "target_quote"}
    events, rejected, identities = [], [], set()
    for i, raw in enumerate(raw_events):
        if not isinstance(raw, dict) or any(not isinstance(raw.get(k), str) for k in fields):
            rejected.append({"index": i, "reason": "required event string fields are missing or invalid"})
            continue
        if raw.get("kind") not in ("ASSERT", "CORRECT", "RETRACT") or raw.get("cardinality") not in ("single", "multi") or type(raw.get("past_only")) is not bool:
            rejected.append({"index": i, "reason": "invalid kind, cardinality, or past_only"})
            continue
        valid, errors = core.validate_events({"events": [raw]}, pool)
        rejected.extend({"index": i, "reason": reason} for reason in errors)
        for event in valid:
            if event["id"] not in identities:
                events.append(event)
                identities.add(event["id"])
    return events, rejected


def query_bundle(bundle, *, intent="current", as_of=None, known_at=None,
                 entity=None, attribute=None, qualifier=None, ledger_path=None, scope="local"):
    """Query an immutable source snapshot plus explicit, provenance-checked events.

    This API does not infer attributes from prose or load previous DB assertions.
    Every call receives its complete relevant snapshot. SQLite is an optional,
    separate append-only audit store, never the source of truth for raw memories.
    """
    if intent not in {"current", "past", "history"}:
        raise ValueError("intent must be current, past, or history")
    if intent == "history" and as_of not in (None, ""):
        raise ValueError("history ignores valid-time selection; omit as_of")
    if not isinstance(scope, str) or not scope.strip():
        raise ValueError("scope must be a nonempty string")
    for field, value in (("entity", entity), ("attribute", attribute), ("qualifier", qualifier)):
        if value is not None and not isinstance(value, str):
            raise ValueError(f"{field} filter must be a string")
    before = core.digest(bundle)
    pool = _sources(bundle)
    all_events, rejected = _events(bundle, pool)
    events = [e for e in all_events if all(value is None or e[key] == value.strip().casefold()
              for key, value in (("entity", entity), ("attribute", attribute), ("qualifier", qualifier)))]
    if intent == "current" and as_of in (None, ""):
        as_of = datetime.now(timezone.utc).isoformat()
    valid_at = _time(as_of, "as_of")
    recorded_by = _time(known_at, "known_at")
    evidence, relations, statuses = core.project(events, intent, valid_at, recorded_by)
    ambiguous = any(statuses[e["id"]].startswith("unresolved_") for e in evidence)
    answers = evidence if intent == "history" else [e for e in evidence if statuses[e["id"]].startswith("selected_")]
    query = {"intent": intent, "as_of_ms": valid_at, "known_at_ms": recorded_by,
             "entity": entity, "attribute": attribute, "qualifier": qualifier}
    resolution = "history" if intent == "history" else "ambiguous" if ambiguous else "resolved" if answers else "no_matching_state"
    result = {
        "system": "ChronoTrace Memory", "query": query, "resolution": resolution,
        "answer_values": [e["value"] for e in answers] if not ambiguous else [],
        "evidence": evidence, "statuses": statuses, "relations": relations,
        "validated_assertions": len(all_events), "rejected": rejected,
        "raw_sources_unchanged": before == core.digest(bundle), "source_digest": before,
    }
    if ledger_path is not None:
        path = Path(ledger_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        ledger = core.Ledger(path)
        try:
            for event in all_events:
                ledger.append("assertions", scope, event)
            for relation in relations:
                ledger.append("relations", scope, relation)
            ledger.append("projections", scope, result)
        finally:
            ledger.db.close()
    return result
