# Verified upgrades — October 9, 2026

- 34 local tests pass, including malformed/truncated diffs, HTTP 429/500,
  timeouts, connection errors, malformed model responses, refusal/truncation,
  token accounting, and a mocked all-clear response to a prompt-injection sample.
- A live Gemini prompt-injection sample still blocked the unsafe expression.
  This single trial is not a general prompt-injection resistance guarantee.
- Four frozen real PRs: 0 false positives / 4 non-blocking labels for both static
  and Gemini-assisted modes. No positive real labels; missed-issue rate is unknown.
  Labels are agent-reviewed by user choice, not human-reviewed gold labels.
- Gemini median latency: 11.9438345 seconds; total list-price cost estimate:
  $0.043866 for the four successful requests. Not a verified charge.
- Separate five-case static adversarial probe: 1 true positive, 1 true negative,
  1 false positive and 2 false negatives. False-positive rate 50%, missed-issue
  rate 66.7% on this intentionally challenging tiny synthetic set. These expose
  heuristic weaknesses and must not be pooled with the original 24-case benchmark.
- CI runs the trusted base checker against proposed diff data without AI secrets.
- PR #1 unsafe commit 674d5fdf9c8bd857ddb1517a9863c9185f3b655e failed the review
  check on SEC003; test checks succeeded. Verified failure run:
  https://github.com/puneethsairamaraju/ai-generated-code-review-gate/actions/runs/37988734414

Required branch protection is pending explicit approval after automatic approval
review rejected admin enforcement and force-push/deletion restrictions. A failing
check alone is not proof of enforced merge blocking.

The reproducible local demo is `python scripts/demo.py`. The public PR demonstrates
an actual code fix from unsafe expression execution to JSON deserialization.

Next evaluation work: independent human labels, real positive regressions, larger
samples across repositories, repeated model runs and broader threat coverage.

The fixed demo commit 29316bec53ac308fc5a877464beb60a3a9a23010 passed the same review
workflow: https://github.com/puneethsairamaraju/ai-generated-code-review-gate/actions/runs/37988970143 .
The push-triggered test workflow also passed at that commit.
Live injection sample latency was 89.387 seconds with a $0.0471225 list-price
estimate, including 12,206 thinking tokens. It is reported separately from the
four-PR pilot to avoid concealing the higher-latency adversarial run.
