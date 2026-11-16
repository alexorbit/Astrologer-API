"""Repeatable external smoke test. Synthetic data only; never prints API keys.

Usage: ASTROLOGER_TEST_API_KEY=... python poc/smoke.py https://service.example
"""
from __future__ import annotations
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE=sys.argv[1].rstrip("/") if len(sys.argv)>1 else "http://127.0.0.1:8000"
KEY=os.environ.get("ASTROLOGER_TEST_API_KEY","")
SUBJECT={"name":"Caso sintético GIROO","city":"São Paulo","nation":"BR","year":1990,"month":11,"day":10,"hour":11,"minute":54,"latitude":-23.5505,"longitude":-46.6333,"timezone":"America/Sao_Paulo","houses_system_identifier":"P"}

def req(path,payload=None,auth=True):
    headers={"Content-Type":"application/json"}
    if auth and KEY:headers["X-API-Key"]=KEY
    body=None if payload is None else json.dumps(payload).encode()
    request=urllib.request.Request(BASE+path,data=body,method="GET" if body is None else "POST",headers=headers)
    before=time.perf_counter()
    try:
        with urllib.request.urlopen(request,timeout=90) as response:
            return response.status,json.loads(response.read()),int((time.perf_counter()-before)*1000)
    except urllib.error.HTTPError as error:
        return error.code,json.loads(error.read()),int((time.perf_counter()-before)*1000)

def main():
    failed=0
    tests=[("saude","/health",None,None),
        ("autenticacao","/api/v6/chart-data/birth-chart",{"subject":SUBJECT},403),
        ("natal","/api/v6/chart-data/birth-chart",{"subject":SUBJECT},200),
        ("lua","/api/v6/moon-phase",{"year":2026,"month":11,"day":16,"hour":12,"minute":0,"latitude":-23.5505,"longitude":-46.6333,"timezone":"America/Sao_Paulo"},200),
        ("semana","/api/v6/calendar",{"start_date":"2026-11-16","end_date":"2026-11-22","include_sun_times":False,"include_planetary_hours":False,"include_eclipses":False,"include_voc":False,"include_aspectarian":False,"include_sign_periods":False,"include_retrograde_periods":False},200)]
    for name,path,payload,expected in tests:
        if name not in ("saude","autenticacao") and not KEY:
            print(name,"SKIP: missing ASTROLOGER_TEST_API_KEY");continue
        try:
            code,result,latency=req(path,payload,name!="autenticacao")
            ok=code==(expected or 200)
            if ok and name=="natal":ok=bool(result.get("chart_data"))
            if ok and name=="semana":ok=isinstance(result.get("ingresses"),list)
            if ok and name=="lua":ok=bool(result.get("moon_phase_overview"))
            print(name,"PASS" if ok else "FAIL","http="+str(code),"ms="+str(latency))
            if not ok:print("  error_type=",result.get("error_type",""),"message=",str(result.get("message",""))[:120]);failed+=1
        except Exception as exc:
            print(name,"FAIL",type(exc).__name__);failed+=1
    return int(failed>0)
if __name__=="__main__":raise SystemExit(main())
