"""Round 4: close the accession-level dataset count honestly - more dataset
accessions (Zenodo, DataCite), remaining bibliography DOIs (CrossRef), and AFLOW
magnetic-material records for the drive-design context. Live, failure-tolerant."""
import json, pathlib, time, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "external_verification4.json"

def get(url, timeout=25):
    req = urllib.request.Request(url, headers={"User-Agent": "mega27-item19-verification/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

rec = {"queries": {}, "errors": {}}
def try_q(name, fn):
    try:
        rec["queries"][name] = fn()
    except Exception as e:
        rec["errors"][name] = str(e)[:200]

def zenodo5():
    out = {}
    for q in ["bacterial flagellum hydrodynamics", "magnetic actuation robot",
              "Brownian dynamics simulation", "soft body locomotion", "microswimmer control"]:
        try:
            d = get(f"https://zenodo.org/api/records?q={urllib.parse.quote(q)}&size=5&type=dataset")
            hits = d.get("hits", {}).get("hits", [])
            out[q] = {"dataset_ids": [h.get("id") for h in hits], "total": d.get("hits", {}).get("total")}
            time.sleep(0.3)
        except Exception as ex:
            out[q] = {"error": str(ex)[:100]}
    return out
try_q("zenodo_datasets_5x5", zenodo5)

def datacite3():
    out = {}
    for q in ["xenobot", "magnetic microswimmer trajectory", "soft robot gait"]:
        try:
            d = get(f"https://api.datacite.org/dois?query={urllib.parse.quote(q)}&page[size]=5&resource-type-id=dataset")
            out[q] = {"dataset_dois": [x.get("id") for x in d.get("data", [])],
                      "total": d.get("meta", {}).get("total")}
            time.sleep(0.3)
        except Exception as ex:
            out[q] = {"error": str(ex)[:100]}
    return out
try_q("datacite_datasets_3x5_b", datacite3)

MORE_DOIS = {"berg1993": None,
 "lauga2006": "10.1017/S0022112006003878",
 "purcell2014": "10.1017/jfm.2014.235",
 "abbott2009": "10.1146/annurev.fluid.010908.165205",
 "kim2016xenobot": None,
 "paxton2004": "10.1021/ja047697z",
 "wang2006": "10.1021/nl060695d",
 "ghosh2009": "10.1021/nl900186w",
 "palagi2016": "10.1038/nnano.2016.87",
 "sitti2015": "10.1073/pnas.1412465112"}
def crossref_more():
    out = {}
    for k, doi in MORE_DOIS.items():
        if not doi:
            out[k] = {"status": "no DOI"}; continue
        try:
            d = get(f"https://api.crossref.org/works/{doi}")
            m = d.get("message", {})
            out[k] = {"title": (m.get("title") or [""])[0][:60], "year": (m.get("issued", {}).get("date-parts") or [[None]])[0][0]}
            time.sleep(0.2)
        except Exception as ex:
            out[k] = {"error": str(ex)[:100]}
    return out
try_q("crossref_bibliography_10", crossref_more)

def aflow():
    out = {}
    # AFLOW REST: magnetic materials for drive context (NdFeB, magnetite, permalloy)
    for label, q in [("Nd2Fe14B", "Nd2Fe14B"), ("Fe3O4", "Fe3O4"), ("NiFe_permalloy", "Ni3Fe")]:
        try:
            d = get(f"http://aflow.org/API/aflux/?summary({urllib.parse.quote(q)}),format(json)")
            out[label] = {"query": q, "sample": str(d)[:150]}
            time.sleep(0.3)
        except Exception as ex:
            out[label] = {"error": str(ex)[:100]}
    return out
try_q("aflow_magnetic_materials_3", aflow)

OUT.write_text(json.dumps(rec, indent=1))
print("written:", OUT); print("ok:", list(rec["queries"].keys())); print("errors:", list(rec["errors"].keys()))
