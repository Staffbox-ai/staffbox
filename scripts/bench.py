"""Concurrency benchmark for a local Ollama model. Usage: python3 bench.py [model]"""
import json,sys,time,urllib.request,concurrent.futures as cf
M=sys.argv[1] if len(sys.argv)>1 else "qwen3:8b"
PROMPT="Write a 150-word procedure for receiving a pallet of raw steel at a machine shop, as a numbered list. /no_think"
def one(_):
    t=time.time(); body=json.dumps({"model":M,"prompt":PROMPT,"stream":False,"options":{"num_predict":220}}).encode()
    r=json.load(urllib.request.urlopen(urllib.request.Request("http://localhost:11434/api/generate",body,{"Content-Type":"application/json"}),timeout=900))
    return r["eval_count"], r["eval_duration"]/1e9, time.time()-t
for n in (1,2,4):
    with cf.ThreadPoolExecutor(n) as ex: rs=list(ex.map(one,range(n)))
    toks=sum(r[0] for r in rs); wall=max(r[2] for r in rs)
    print(json.dumps({"model":M,"streams":n,"tokens":toks,"wall_s":round(wall,1),"aggregate_tok_s":round(toks/wall,1),"per_stream_tok_s":round(sum(r[0]/r[1] for r in rs)/n,1)}),flush=True)
