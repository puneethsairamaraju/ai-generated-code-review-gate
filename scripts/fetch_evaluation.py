"""Download immutable source PR diffs. Never execute code from the dataset."""
import hashlib, json, urllib.request
from pathlib import Path
CASES = [('psf/requests',6865),('langchain-ai/langchain',11302),('langchain-ai/langchain',5291),('langchain-ai/langchain',22904)]
root=Path('evaluation');(root/'diffs').mkdir(exist_ok=True)
records=[]
for repo,number in CASES:
    url=f'https://api.github.com/repos/{repo}/pulls/{number}'
    req=urllib.request.Request(url,headers={'User-Agent':'ai-review-gate-evaluation'})
    with urllib.request.urlopen(req,timeout=30) as response: pr=json.load(response)
    req=urllib.request.Request(pr['diff_url'],headers={'User-Agent':'ai-review-gate-evaluation'})
    with urllib.request.urlopen(req,timeout=30) as response: data=response.read()
    name=f'{repo.split("/")[0]}-{number}.diff';(root/'diffs'/name).write_bytes(data)
    records.append({'id':name[:-5],'url':pr['html_url'],'title':pr['title'],'base_sha':pr['base']['sha'],'head_sha':pr['head']['sha'],'diff':f'diffs/{name}','sha256':hashlib.sha256(data).hexdigest(),'label_status':'agent-reviewed','expected_block':False,'rationale':'PENDING REVIEW'})
(root/'cases.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
for repo in ('psf/requests','langchain-ai/langchain'):
    req=urllib.request.Request(f'https://api.github.com/repos/{repo}/license',headers={'User-Agent':'ai-review-gate-evaluation'})
    with urllib.request.urlopen(req,timeout=30) as response: info=json.load(response)
    import base64
    (root/(repo.split('/')[0]+'-LICENSE')).write_bytes(base64.b64decode(info['content']))
print('Downloaded',len(records),'PR diffs with provenance and licenses')
