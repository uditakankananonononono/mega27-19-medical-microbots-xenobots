"""Item 19 external verification: verify the literature anchors, physical constants
context and design-law lineage against public scholarly databases. Live queries,
failure-tolerant, cached to results/external_verification.json."""
import json, pathlib, time, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "results" / "external_verification.json"

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

# CrossRef DOI verification of the paper's reference anchors
REFS = {
 "purcell1977": "10.1119/1.10903",
 "lauga2009": "10.1088/0034-4885/72/9/096601",
 "zhang2009abf": "10.1063/1.3148293",
 "nelson2010": "10.1146/annurev-bioeng-010510-103409",
 "kriegman2020": "10.1073/pnas.1910837117",
 "dreyfus2005": "10.1038/nature04090",
 "berg1993": None,
 "howse2007": "10.1103/PhysRevLett.99.048102",
 "elowitz2000": "10.1038/35002125",
 "kriegman2021": "10.1073/pnas.2112672118",
}
def crossref_all():
    out = {}
    for k, doi in REFS.items():
        if not doi:
            out[k] = {"status": "book - no DOI queried"}; continue
        try:
            d = get(f"https://api.crossref.org/works/{doi}")
            m = d.get("message", {})
            out[k] = {"title": (m.get("title") or [""])[0][:80],
                      "year": (m.get("issued", {}).get("date-parts") or [[None]])[0][0],
                      "journal": (m.get("container-title") or [""])[0][:50]}
            time.sleep(0.2)
        except Exception as e:
            out[k] = {"error": str(e)[:120]}
    return out
try_q("crossref_references_10", crossref_all)

# Europe PMC topic counts: field sizes for the paper's core topics
TOPICS = ["helical microswimmer", "magnetic microrobot drug delivery",
          "xenobot", "resistive force theory bacteria",
          "microswimmer Brownian motion", "soft robot evolutionary design",
          "magnetic helical robot step-out", "low Reynolds number swimming"]
def epmc_topics():
    out = {}
    for t in TOPICS:
        try:
            q = urllib.parse.quote(t)
            d = get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/search?query={q}&format=json&pageSize=1")
            out[t] = {"hit_count": d.get("hitCount")}
            time.sleep(0.25)
        except Exception as e:
            out[t] = {"error": str(e)[:120]}
    return out
try_q("europepmc_topic_counts_8", epmc_topics)

# OpenAlex: concept-level work counts for cross-checking field sizes
CONCEPTS = ["microrobotics", "microswimmer", "xenobot", "evolutionary robotics", "Stokes flow"]
def openalex():
    out = {}
    for c in CONCEPTS:
        try:
            d = get(f"https://api.openalex.org/works?search={urllib.parse.quote(c)}&per_page=1")
            out[c] = {"work_count": d.get("meta", {}).get("count")}
            time.sleep(0.25)
        except Exception as e:
            out[c] = {"error": str(e)[:120]}
    return out
try_q("openalex_concept_counts_5", openalex)

# arXiv API: recent preprints on microswimmer control (RSS->Atom XML, count entries)
def arxiv():
    import re as _re
    out = {}
    for q in ["helical microswimmer", "xenobot", "magnetic microrobot control"]:
        try:
            url = ("http://export.arxiv.org/api/query?search_query=all:" +
                   urllib.parse.quote(q) + "&start=0&max_results=5")
            req = urllib.request.Request(url, headers={"User-Agent": "mega27/1.0"})
            with urllib.request.urlopen(req, timeout=25) as r:
                xml = r.read().decode()
            out[q] = {"entries_sampled": xml.count("<entry>")}
            time.sleep(1.0)
        except Exception as e:
            out[q] = {"error": str(e)[:120]}
    return out
try_q("arxiv_preprints_3", arxiv)

# Semantic Scholar: verify the xenobot anchor paper exists with citation count
def s2():
    d = get("https://api.semanticscholar.org/graph/v1/paper/DOI:10.1073/pnas.1910837117?fields=title,year,citationCount")
    return {"title": d.get("title", "")[:80], "year": d.get("year"), "citations": d.get("citationCount")}
try_q("semanticscholar_xenobot", s2)

# NCBI PubMed: xenobot + microrobot medical counts
def ncbi():
    out = {}
    for term in ["xenobot", "medical microrobot", "helical microswimmer magnetic"]:
        d = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term="
                + urllib.parse.quote(term) + "&retmode=json")
        out[term] = {"pubmed_count": int(d["esearchresult"]["count"])}
        time.sleep(0.3)
    return out
try_q("ncbi_pubmed_counts_3", ncbi)

OUT.write_text(json.dumps(rec, indent=1))
print("written:", OUT)
print("ok:", list(rec["queries"].keys()))
print("errors:", list(rec["errors"].keys()))
