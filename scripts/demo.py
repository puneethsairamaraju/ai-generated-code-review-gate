"""Run a safe, local blocked/fixed demo. The dangerous source is never executed."""
import json, subprocess, sys, tempfile
from pathlib import Path
rows=[]
with tempfile.TemporaryDirectory() as directory:
    for name,expected in [('unsafe',1),('clean',0)]:
        report=Path(directory)/f'{name}.json'
        run=subprocess.run([sys.executable,'-m','review_gate.cli','review','--diff',f'examples/{name}.diff','--output',str(report)],capture_output=True,text=True)
        if run.returncode!=expected: raise SystemExit(f'{name}: expected {expected}, got {run.returncode}: {run.stderr}')
        print(f'{name.upper()}: exit {run.returncode}\n{run.stdout}')
        rows.append({'scenario':name,'exit_code':run.returncode,'report':json.loads(report.read_text())})
Path('verification/demo.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print('Demo verified: unsafe blocked; clean passed.')
