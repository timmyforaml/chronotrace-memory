# ChronoTrace Memory v0.23 — online Textual service source candidate

This source candidate is separate from the repository's earlier v0.1.1 offline
manual-binding state kernel. It is not a proven accuracy improvement. Full has
not been submitted. The source revision is source-local-extents-01.contract03.

The complete source archive contains the exact bytes deployed for the candidate,
including all 38 original Context Weave / SourceTrail 0.32.0 archive files, their
MIT attribution, four added modules and manifest.json. It contains no credentials,
database, model, benchmark question, answer or raw research result. Some upstream
files use CRLF. The compressed archive intentionally preserves those raw bytes;
normalizing an expanded Git tree would invalidate their provenance hashes.

Use Python 3.12. Create a dedicated source directory and extract source.tar.gz
there. From that extracted directory install requirements.txt in a private venv.
Set private MEMORY_API_KEY and DASHSCOPE_API_KEY outside source control, and set
AE_EMBEDDING_BACKEND=dashscope, AE_EMBEDDING_DIMENSIONS=1024,
AE_EMBEDDING_BATCH_SIZE=10, AE_MODE=query_document_evidence,
AE_CONTEXT_CHARS=24000 and a new absolute instance-specific AE_DATABASE.
Run python -m uvicorn adaptive_evidence.chronotrace_api:app --host 127.0.0.1
--port 18104 --workers 1 --no-access-log behind your authenticated HTTPS service.

To run the 13 synthetic acceptance tests, extract into the adjacent folder named
source and run python -m unittest discover -s . -p test_five_requirements.py -v.
They exercise isolation/cross-session retrieval, durable Add before HTTP 200,
concurrent retry idempotency, legacy request migration, ordered text parts,
immutable envelopes, returned evidence, schema/auth and response bounds. They use
a deterministic synthetic encoder and block external network connections.
From source run python -m unittest discover -s tests -v for 64 upstream checks.

Actual deployment uses text-embedding-v4, no generative memory-service LLM and
the original 24000-character packer. Final Answer remains the evaluator's job.
Text parts are retained in an immutable envelope sidecar and joined by LF for
text retrieval. Image parts are unsupported; this candidate is Textual only.

The state parser is narrow and source-local. A source-relative current/prior
projection is not proof of globally current or unbounded historical truth.
The earlier evaluated revision had zero measured state activation and Smoke
60.6337 and 61.0243. Those scores do not belong to this transport revision, which
has no own Smoke result at material preparation. Full selection is still under
review; no permanent local gain or promotion gate has been claimed passed.

See ATTRIBUTION.zh-CN.md for original author, archive identity and Mem0 reference
boundaries. Attribution, substantive-submission and integrity declarations remain
subject to the participant's confirmation. This directory contains source materials; it does not establish that a Full
evaluation has occurred. The archive is the exact byte-preserving source release.
