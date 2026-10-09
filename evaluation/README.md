# Real-PR evaluation pilot

Four independently sourced PR diffs are frozen with their base/head commit IDs,
SHA-256 hashes, links and agent-reviewed rationale in cases.json. The user chose
agent-reviewed labels; these are NOT manually human-labeled ground truth.
Original licenses are retained alongside the diffs. No downloaded code is executed.

Selection: small merged changes in Requests and LangChain covering documentation,
dependency metadata, prompt text and removal/migration of an execution feature.
Labels were written before running this evaluation; rules were not tuned to them.
All four labels are non-blocking under the repository rubric. This measures a
small false-positive pilot only: missed-issue rate and recall are null because
there are no positive labels. Do not call this a representative accuracy result.
Use the separate synthetic benchmark for positive-rule coverage, not as a substitute
for real positive cases. Independent human labels and real regressions remain needed.

Run `python scripts/evaluate.py` for static checks, or set GEMINI_API_KEY and run
`python scripts/evaluate.py --llm --output evaluation/results-gemini.json`.
The latter makes four API calls. Reported errors are separate from clean passes.

Latency is wall-clock time per case, with API latency and provider usage recorded.
Cost is a list-price estimate (not an invoice or verified charge) using Gemini
3.8 Flash rates of $0.75/M input and $3.75/M output, including thinking tokens,
checked October 9, 2026: https://ai.google.dev/gemini-api/docs/latest-model .
Free-tier credits, caching, taxes and unsuccessful request costs are not inferred.
