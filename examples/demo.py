"""Six synthetic contrasts; these are mechanism tests, not benchmark scores."""

import json
from pathlib import Path
from chronotrace_memory import query_bundle

bundle = json.loads(Path(__file__).with_name("alice.json").read_text(encoding="utf-8"))
checks = [
    ("Current home", dict(intent="current", as_of="2026-08-01", entity="Alice", attribute="home_city"), ["Berlin"]),
    ("February, using later correction", dict(intent="past", as_of="2026-02-01", entity="Alice", attribute="home_city"), ["Lyon"]),
    ("February, known by March", dict(intent="past", as_of="2026-02-01", known_at="2026-03-01", entity="Alice", attribute="home_city"), ["Paris"]),
    ("Complete home history", dict(intent="history", entity="Alice", attribute="home_city"), ["Paris", "Berlin", "Lyon"]),
    ("Work city stays separate", dict(intent="current", as_of="2026-08-01", entity="Alice", attribute="work_city"), ["Rome"]),
    ("Bob stays separate", dict(intent="current", as_of="2026-08-01", entity="Bob", attribute="home_city"), ["Madrid"]),
]
for label, query, expected in checks:
    result = query_bundle(bundle, **query)
    assert result["answer_values"] == expected, (label, result)
    assert result["raw_sources_unchanged"]
    print(f"{label}: {', '.join(result['answer_values'])}")
print("6 synthetic contrasts passed; raw sources unchanged.")
