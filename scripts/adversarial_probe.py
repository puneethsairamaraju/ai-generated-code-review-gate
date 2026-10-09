"""A deliberately small adversarial probe, separate from the real PR pilot."""
import json,time
from pathlib import Path
from review_gate.diff import added_lines
from review_gate.rules import run_static_rules
cases=[
 ('direct-execution','eval(user_input)',True),
 ('indirect-execution',"getattr(__builtins__, 'eval')(user_input)",True),
 ('unsafe-deserialization','pickle.loads(untrusted_bytes)',True),
 ('safe-json','json.loads(user_input)',False),
 ('comment-only','# eval(user_input) is unsafe; do not use it',False),
]
rows=[];counts=dict(true_positive=0,false_positive=0,true_negative=0,false_negative=0)
for name,code,expected in cases:
 diff=f'diff --git a/sample.py b/sample.py\n--- a/sample.py\n+++ b/sample.py\n@@ -0,0 +1 @@\n+{code}\n'
 started=time.perf_counter();findings=run_static_rules(added_lines(diff));actual=any(f.severity=='blocking' for f in findings)
 category=('true_' if actual==expected else 'false_')+('positive' if actual else 'negative');counts[category]+=1
 rows.append(dict(id=name,source=code,expected_block=expected,actual_block=actual,outcome=category,latency_seconds=time.perf_counter()-started))
result=dict(dataset='synthetic adversarial probe, agent labels, not real PRs',confusion_matrix=counts,
 false_positive_rate=counts['false_positive']/2,missed_issue_rate=counts['false_negative']/3,details=rows)
Path('evaluation/results-adversarial.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(counts))
