"""Round 3: Semantic Scholar per-reference records + expanded Europe PMC / PubMed
field maps. Live, failure-tolerant, cached to results/external_verification3.json."""
import json, pathlib, time, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "external_verification3.json"

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

REF_DOIS = ["10.1119/1.10903", "10.1088/0034-4885/72/9/096601", "10.1063/1.3148293",
            "10.1146/annurev-bioeng-010510-103409", "10.1073/pnas.1910837117",
            "10.1038/nature04090", "10.1103/PhysRevLett.99.048102", "10.1038/35002125",
            "10.1073/pnas.2112672118", "10.1126/science.abb3405",
            "10.1002/jcc.21334", "10.1021/acs.jcim.1c00203", "10.1038/nprot.2016.051"]
def s2_refs():
    out = {}
    for doi in REF_DOIS:
        try:
            d = get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,year,citationCount")
            out[doi] = {"title": (d.get("title") or "")[:55], "year": d.get("year"),
                        "citations": d.get("citationCount")}
            time.sleep(0.35)
        except Exception as ex:
            out[doi] = {"error": str(ex)[:100]}
    return out
try_q("semanticscholar_references_13", s2_refs)

EPMC_TOPICS = ["magnetophoresis microswimmer", "ciliary propulsion low Reynolds",
               "artificial bacterial flagella fabrication", "two-photon polymerization microrobot",
               "E.coli swimming hydrodynamics", "sperm cell propulsion model",
               "targeted drug delivery magnetism", "microfluidic drug screening",
               "living robot self-organization", "morphogenetic engineering swarm"]
def epmc_more():
    out = {}
    for t in EPMC_TOPICS:
        try:
            d = get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={urllib.parse.quote(t)}&format=json&pageSize=1")
            out[t] = {"hit_count": d.get("hitCount")}
            time.sleep(0.25)
        except Exception as ex:
            out[t] = {"error": str(ex)[:100]}
    return out
try_q("europepmc_topics_10", epmc_more)

PUBMED_TERMS = ["magnetic helical microrobot", "soft microrobot locomotion",
                "xenobot replication", "microswimmer collective behavior",
                "resistive force theory flagellum", "Brownian motor",
                "magnetic drug targeting in vivo", "biohybrid robot cardiac cells",
                "microbot navigation control", "helical nanomotor"]
def pubmed_more():
    out = {}
    for t in PUBMED_TERMS:
        try:
            d = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term="
                    + urllib.parse.quote(t) + "&retmode=json")
            out[t] = {"pubmed_count": int(d["esearchresult"]["count"])}
            time.sleep(0.3)
        except Exception as ex:
            out[t] = {"error": str(ex)[:100]}
    return out
try_q("pubmed_terms_10", pubmed_more)

OUT.write_text(json.dumps(rec, indent=1))
print("written:", OUT); print("ok:", list(rec["queries"].keys())); print("errors:", list(rec["errors"].keys()))
