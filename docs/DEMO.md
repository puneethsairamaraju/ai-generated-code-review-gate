# A one-minute demo

Install with `python -m pip install -e ".[dev]"`, then run:

```console
python scripts/demo.py
```

The script actually invokes the CLI twice and verifies exit codes. It treats all
sample source as text; it never executes the unsafe expression.

1. `examples/unsafe.diff` adds `eval(user_input)`. The report must say FAIL with
   SEC003 and exit code 1.
2. `examples/clean.diff` adds `value = 42`. The report must say PASS and exit code 0.
3. The captured reports are saved to `verification/demo.json`.

To demonstrate live Gemini review, set GEMINI_API_KEY and run:

```console
python -m review_gate.cli review --diff examples/unsafe.diff --llm --provider gemini --input-usd-per-million 0.75 --output-usd-per-million 3.75
```

The JSON report includes latency, provider token counts and an estimated cost.
Prices are explicit inputs, not assumed account billing rates.

This demo checks the gate, not the functional equivalence of the two sample programs.
