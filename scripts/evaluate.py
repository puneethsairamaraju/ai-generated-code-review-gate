"""Evaluate frozen agent-reviewed PRs without training/tuning on their labels."""
import argparse, hashlib, json, statistics, time
from pathlib import Path
from review_gate.diff import added_lines
from review_gate.rules import run_static_rules
from review_gate.llm import review_with_provider


def evaluate(cases_path, llm=False):
    cases=json.loads(cases_path.read_text(encoding='utf-8'))
    counts=dict(true_positive=0,false_positive=0,true_negative=0,false_negative=0)
    rows=[]
    for case in cases:
        data=(cases_path.parent/case['diff']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=case['sha256']:
            raise RuntimeError('Dataset integrity failure: '+case['id'])
        started=time.perf_counter();telemetry={}
        try:
            diff=data.decode('utf-8')
            findings=run_static_rules(added_lines(diff))
            if llm:
                model_findings,_=review_with_provider(diff,Path('rubric.json'),'gemini-3.8-flash','gemini',telemetry)
                findings+=model_findings
            blocked=any(f.severity=='blocking' for f in findings)
            label=('true_' if blocked==case['expected_block'] else 'false_')+('positive' if blocked else 'negative')
            counts[label]+=1
            row=dict(id=case['id'],expected_block=case['expected_block'],blocked=blocked,outcome=label,
                     findings=[{'rule':f.rule_id,'file':f.file,'line':f.line,'severity':f.severity,'reasoning':f.reasoning} for f in findings])
        except (RuntimeError,OSError,ValueError) as exc:
            row=dict(id=case['id'],outcome='error',error=str(exc))
        row['latency_seconds']=round(time.perf_counter()-started,6)
        row['usage']=telemetry
        row['estimated_cost_usd']=None
        if telemetry.get('input_tokens') is not None and telemetry.get('output_tokens') is not None:
            row['estimated_cost_usd']=(telemetry['input_tokens']*.75+(telemetry['output_tokens']+telemetry.get('thinking_tokens',0))*3.75)/1e6
        rows.append(row)
    tp,fp,tn,fn=(counts[k] for k in ('true_positive','false_positive','true_negative','false_negative'))
    return dict(dataset='agent-reviewed PR pilot; not human gold labels',cases=len(cases),mode='hybrid-gemini' if llm else 'static',
        confusion_matrix=counts,false_positive_rate=fp/(fp+tn) if fp+tn else None,
        missed_issue_rate=fn/(tp+fn) if tp+fn else None,
        errors=sum(r['outcome']=='error' for r in rows),median_latency_seconds=statistics.median(r['latency_seconds'] for r in rows),
        estimated_cost_usd=sum(r['estimated_cost_usd'] or 0 for r in rows) if llm else 0,
        pricing={'input_per_million':.75,'output_per_million':3.75,'currency':'USD','as_of':'2026-10-09','source':'https://ai.google.dev/gemini-api/docs/latest-model','note':'List-price estimate including thinking tokens; not an invoice. Failed requests may incur unobserved cost.'},details=rows)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--llm',action='store_true');parser.add_argument('--output',default='evaluation/results-static.json');args=parser.parse_args()
    result=evaluate(Path('evaluation/cases.json'),args.llm)
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ('details','pricing')},indent=2))
