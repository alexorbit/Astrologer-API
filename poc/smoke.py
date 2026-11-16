"""Repeatable POC smoke test with synthetic birth details only.

Can be invoked once at startup or externally. No secret in output or URL.
"""
from __future__ import annotations
import json,os,sys,time,urllib.request,urllib.error
BASE=sys.argv[1].rstrip("/") if len(sys.argv)>1 else "http://127.0.0.1:8000"
KEY=os.environ.get("ASTROLOGER_TEST_API_KEY","")
SUBJECT={"name":"Caso sintético GIROO","city":"São Paulo","nation":"BR","year":1990,"month":11,"day":10,"hour":11,"minute":54,"latitude":-23.5505,"longitude":-46.6333,"timezone":"America/Sao_Paulo","houses_system_identifier":"P"}

def req(path,payload=None,auth=True):
    headers={"Content-Type":"application/json"}
    if auth and KEY:headers["X-API-Key"]=KEY
    body=None if payload is None else json.dumps(payload).encode()
    r=urllib.request.Request(BASE+path,data=body,method="GET" if body is None else "POST",headers=headers)
    before=time.perf_counter()
    try:
        with urllib.request.urlopen(r,timeout=90) as response:
            return response.status,json.loads(response.read()),int((time.perf_counter()-before)*1000)
    except urllib.error.HTTPError as exc:
        raw=exc.read()
        try:content=json.loads(raw)
        except ValueError:content={}
        return exc.code,content,int((time.perf_counter()-before)*1000)

def log(name,result,expected=200,check=None):
    code,data,ms=result
    ok=code==expected and (check(data) if check else True)
    print("POC_SMOKE",name,"PASS" if ok else "FAIL","http="+str(code),"ms="+str(ms),flush=True)
    if not ok:
        print("  error_type=",data.get("error_type",""),"message=",str(data.get("message",""))[:120],flush=True)
    return ok

def asset(path, marker):
    r=urllib.request.Request(BASE+path,method="GET")
    started=time.perf_counter()
    with urllib.request.urlopen(r,timeout=20) as response:
        content=response.read(350000).decode("utf-8")
        csp=response.headers.get("Content-Security-Policy","")
        csp_ok=(path!="/poc") or ("img-src 'self' data: blob:" in csp)
        result=(response.status, marker in content and csp_ok, int((time.perf_counter()-started)*1000))
    return result

def main():
    failed=0
    # GET /ready must report the actual library status, not merely HTTP liveness.
    ready=False
    for attempt in range(25):
        try:
            code,data,_=req("/ready")
            if code==200:
                ready=True;break
        except Exception:pass
        time.sleep(3)
    try:
        failed+=not log("health",req("/health"))
    except Exception as exc:
        print("POC_SMOKE health FAIL",type(exc).__name__,flush=True);return 1
    for label,path,marker in [
        ("ui_html","/poc","LABORATÓRIO DE CÁLCULOS"),
        ("ui_css","/poc/app.css",".test-grid"),
        ("ui_js","/poc/app.js","naturalWidth")]:
        try:
            code,valid,ms=asset(path,marker)
            ok=code==200 and valid
            print("POC_SMOKE",label,"PASS" if ok else "FAIL","http="+str(code),"ms="+str(ms),flush=True)
            failed+=not ok
        except Exception as exc:
            print("POC_SMOKE",label,"FAIL",type(exc).__name__,flush=True)
            failed+=1
    if not ready:
        print("POC_SMOKE readiness FAIL: engine not ready, calculations not attempted",flush=True)
        return 1
    if not KEY:
        print("POC_SMOKE auth FAIL: missing secret, calculations not attempted",flush=True);return 1
    tests=[
      ("auth_reject", "/api/v6/chart-data/birth-chart", {"subject":SUBJECT}, 403, False, None),
      ("natal", "/api/v6/chart-data/birth-chart", {"subject":SUBJECT}, 200, True, lambda d:bool(d.get("chart_data"))),
      ("invalid_coordinates", "/api/v6/chart-data/birth-chart", {"subject":{**SUBJECT,"latitude":125}}, 422, True, lambda d:bool(d.get("detail") or d.get("message") or d.get("status")=="ERROR")),
      ("svg", "/api/v6/chart/birth-chart", {"subject":SUBJECT}, 200, True, lambda d:isinstance(d.get("chart"),str) and "<svg" in d["chart"]),
      ("moon", "/api/v6/moon-phase", {"year":2026,"month":11,"day":16,"hour":12,"minute":0,"latitude":-23.5505,"longitude":-46.6333,"timezone":"America/Sao_Paulo"}, 200, True, lambda d:bool(d.get("moon_phase_overview"))),
      ("week", "/api/v6/calendar", {"start_date":"2026-11-16","end_date":"2026-11-22","include_sun_times":False,"include_planetary_hours":False,"include_eclipses":False,"include_voc":False,"include_aspectarian":False,"include_sign_periods":False,"include_retrograde_periods":False}, 200, True, lambda d:isinstance(d.get("ingresses"),list)),
      ("transits", "/api/v6/transits/aspect-timeline", {"subject":SUBJECT,"start_date":"2026-11-16","end_date":"2026-11-22","step_days":1,"refine_exact_moments":False}, 200, True, lambda d:isinstance(d.get("events"),list))
    ]
    for name,path,body,expected,auth,check in tests:
        try:failed+=not log(name,req(path,body,auth),expected,check)
        except Exception as exc:
            print("POC_SMOKE",name,"FAIL",type(exc).__name__,flush=True)
            failed+=1
    # Verify real server-to-server integration to GIROO preview using ONLY
    # a fixed synthetic natal dataset, never reader data or a user token.
    bridge_ok=False
    bridge_url=(
        "https://astros-api-cache-preview-temp-production.up.railway.app"
        "/v1/public/apps/astros/natal-lab-smoke"
    )
    started=time.perf_counter()
    try:
        with urllib.request.urlopen(
            urllib.request.Request(bridge_url,headers={"Accept":"application/json"}),
            timeout=35,
        ) as response:
            output=json.loads(response.read(6000))
            code=response.status
        bridge_ok=(
            code==200 and output.get("status")=="ok"
            and output.get("houses_count")==12
            and output.get("ascendant_present") is True
            and output.get("planet_count",0)>=7
            and "Astrologer-API" in output.get("source","")
            and output.get("cache")=="disabled"
        )
        print("POC_SMOKE giroo_preview_bridge",
            "PASS" if bridge_ok else "FAIL",
            "http="+str(code),
            "ms="+str(int((time.perf_counter()-started)*1000)),
            "houses="+str(output.get("houses_count")),
            "planets="+str(output.get("planet_count")),flush=True)
    except Exception as exc:
        print("POC_SMOKE giroo_preview_bridge FAIL",
            type(exc).__name__,flush=True)
    failed+=not bridge_ok
    print("POC_SMOKE SUMMARY",len(tests)+5-failed,"passed",failed,"failed",flush=True)
    return int(failed>0)
if __name__=="__main__":raise SystemExit(main())
