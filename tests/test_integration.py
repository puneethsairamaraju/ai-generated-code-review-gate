import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from review_gate.llm import review_with_openai, validate_results

DIFF = 'diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -0,0 +1 @@\n+eval(user_input)\n'
RUBRIC = json.loads(Path('rubric.json').read_text())


def results():
    return {'rubric_results': [dict(id=r['id'], passed=True,
        severity=r['default_severity'], file='', line=0, reasoning='No evidence', evidence='')
        for r in RUBRIC['items']]}


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'location', 'severity', 'evidence'])
def test_reject_untrusted_model_output(mutation):
    output = results()
    first = output['rubric_results'][0]
    if mutation == 'missing':
        output['rubric_results'].pop()
    elif mutation == 'duplicate':
        output['rubric_results'].append(first.copy())
    elif mutation == 'severity':
        first['severity'] = 'advisory'
    else:
        first.update(passed=False, file='app.py', line=1, evidence='eval(user_input)')
        first['line' if mutation == 'location' else 'evidence'] = 90 if mutation == 'location' else 'invented'
    with pytest.raises(RuntimeError):
        validate_results(output, RUBRIC, DIFF)


def test_mocked_provider_round_trip(monkeypatch):
    monkeypatch.setenv('OPENAI_API_KEY', 'test-placeholder')
    output = results()
    output['rubric_results'][0].update(passed=False, file='app.py', line=1, evidence='eval(user_input)')
    with patch('urllib.request.urlopen') as request:
        request.return_value.__enter__.return_value.read.return_value = json.dumps({
            'status': 'completed', 'output': [{'content': [{'type': 'output_text', 'text': json.dumps(output)}]}]
        }).encode()
        findings, _ = review_with_openai(DIFF, Path('rubric.json'), 'test-model')
        assert len(findings) == 1
        assert findings[0].severity == 'blocking'


@pytest.mark.parametrize('text,code', [(DIFF, 1), (DIFF.replace('eval(user_input)', 'value = 42'), 0)])
def test_cli_end_to_end(tmp_path, text, code):
    diff = tmp_path / 'sample.diff'
    report = tmp_path / 'report.json'
    diff.write_text(text)
    run = subprocess.run([sys.executable, '-m', 'review_gate.cli', 'review',
        '--diff', str(diff), '--output', str(report)], capture_output=True, text=True)
    assert run.returncode == code, run.stderr
    assert json.loads(report.read_text())['passed'] == (code == 0)


def test_cli_missing_key_fails_closed(tmp_path, monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    diff = tmp_path / 'sample.diff'
    diff.write_text(DIFF)
    report = tmp_path / 'report.json'
    run = subprocess.run([sys.executable, '-m', 'review_gate.cli', 'review', '--llm',
        '--diff', str(diff), '--output', str(report)], capture_output=True, text=True)
    assert run.returncode == 2
    assert not report.exists()

@pytest.mark.parametrize('finish', ['STOP', 'MAX_TOKENS', 'SAFETY'])
def test_gemini_response(monkeypatch, finish):
    from review_gate.llm import review_with_provider
    monkeypatch.setenv('GEMINI_API_KEY', 'test-placeholder')
    output = results()
    output['rubric_results'][0].update(passed=False, file='app.py', line=1, evidence='eval(user_input)')
    with patch('urllib.request.urlopen') as request:
        request.return_value.__enter__.return_value.read.return_value = json.dumps({
            'candidates': [{'finishReason': finish, 'content': {'parts': [{'text': json.dumps(output)}]}}]
        }).encode()
        if finish == 'STOP':
            findings, checks = review_with_provider(DIFF, Path('rubric.json'), 'gemini-2.5-flash', 'gemini')
            assert len(findings) == 1 and len(checks) == 5
            sent = request.call_args.args[0]
            assert 'test-placeholder' not in sent.full_url
            assert json.loads(sent.data)['generationConfig']['responseMimeType'] == 'application/json'
        else:
            with pytest.raises(RuntimeError, match='did not complete'):
                review_with_provider(DIFF, Path('rubric.json'), 'gemini-2.5-flash', 'gemini')
