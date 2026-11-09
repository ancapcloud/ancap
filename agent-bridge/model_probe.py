"""Acceptance probes for the actual local model APIs used by both workers."""
import json
from pathlib import Path
import sys
import time
import urllib.request


def call(endpoint, body):
    request=urllib.request.Request('http://127.0.0.1:11434'+endpoint,
        data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=600) as response:
        return json.loads(response.read())


def main():
    model=sys.argv[1]
    results=dict(model=model)
    show=call('/api/show',dict(model=model))
    results['capabilities']=show.get('capabilities',[])
    base=dict(model=model,stream=False,think=False,keep_alive='30m',
              options=dict(num_ctx=65536,num_predict=256,temperature=0))
    started=time.monotonic()
    answer=call('/api/chat',dict(**base,format='json',messages=[dict(role='user',content='Return exactly {"answer":12} as JSON, no explanation.')]))
    results['json_passed']=json.loads(answer['message']['content'])=={'answer':12}
    tool=dict(type='function',function=dict(name='record_check',description='Record the requested check.',
         parameters=dict(type='object',properties=dict(result=dict(type='string',enum=['pass'])),required=['result'])))
    messages=[dict(role='user',content='Call record_check with result equal to pass. Use the tool now; no prose.')]
    native=call('/api/chat',dict(**base,messages=messages,tools=[tool]))
    calls=native['message'].get('tool_calls',[])
    results['native_tools_passed']=any(c.get('function',{}).get('name')=='record_check' and c['function'].get('arguments')=={'result':'pass'} for c in calls)
    compatible=call('/v1/chat/completions',dict(model=model,messages=messages,tools=[tool],
                      stream=False,max_tokens=256,temperature=0,reasoning_effort='none'))
    calls=compatible['choices'][0]['message'].get('tool_calls',[])
    results['openai_tools_passed']=any(c.get('function',{}).get('name')=='record_check' and json.loads(c['function'].get('arguments','{}'))=={'result':'pass'} for c in calls)
    results['seconds']=round(time.monotonic()-started,1)
    target=Path(__file__).resolve().parent/'runtime/model-probe.json'
    target.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print(json.dumps(results))
    if not all(results[k] for k in ('json_passed','native_tools_passed','openai_tools_passed')):
        raise SystemExit(1)


if __name__=='__main__':main()
