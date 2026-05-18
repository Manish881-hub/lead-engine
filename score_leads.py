"""score_leads.py — Reads raw_posts.jsonl -> lead_scores.csv. Zero external deps."""
import json, csv, sys

CFG = {
 "signals": {
  "activation":     {"kw":["activation","stuck at","not using","low dau","retention drop","users churn"], "w":30, "pain":"Users sign up but don't reach aha moment"},
  "adoption":       {"kw":["user adoption","rolling out","internal adoption","no one uses","shelfware"], "w":28, "pain":"Built AI but team won't adopt"},
  "hallucination":  {"kw":["hallucinat","made up","wrong answers","not grounded","rag accuracy"], "w":25, "pain":"Accuracy / trust in LLM output"},
  "integration":    {"kw":["integrate","api limits","rate limit","vendor lock","switch model"], "w":20, "pain":"Plumbing / infra fragility"},
  "cost":           {"kw":["token cost","inference cost","gpu bill","burning cash","unit economics","eating our margin"], "w":22, "pain":"Margins collapsing under model spend"},
  "eval":           {"kw":["eval","benchmark","regression","prompt drift","a/b model","eval harness"], "w":18, "pain":"Can't measure quality reliably"},
  "copilot_usage":  {"kw":["copilot adoption","devs not using","accept rate","suggestion accept"], "w":27, "pain":"Coding assistant low accept rate"},
 },
 "roles": {"founder":15,"co-founder":15,"ceo":15,"chief executive":15,"cto":20,"vp engineering":20,
           "head of engineering":18,"head of product":15,"vp product":15,"chief product officer":15},
 "company_kw": ["ai chatbot","ai assistant","ai writing","ai coding","coding assistant","ai search",
                "copilot","ai chat","generative ai","genai","llm app"],
 "stage": {"seed":10,"series_a":12,"series_b":8,"series_c":4,"bootstrapped":6},
}

def detect(text):
    t=text.lower(); hits=[]
    for name,cfg in CFG["signals"].items():
        for kw in cfg["kw"]:
            if kw in t: hits.append((name,cfg["w"],cfg["pain"],kw)); break
    return hits

def role_pts(title):
    t=(title or "").lower()
    return max((p for r,p in CFG["roles"].items() if r in t), default=0)

def company_pts(desc):
    d=(desc or "").lower()
    return 15 if any(k in d for k in CFG["company_kw"]) else 0

def score(r):
    sigs=detect(r.get("post_text",""))
    sig_pts=max((s[1] for s in sigs), default=0)
    primary=sigs[0] if sigs else (None,0,None,None)
    fit=role_pts(r.get("author_title"))+company_pts(r.get("company_description"))+CFG["stage"].get((r.get("company_stage") or "").lower(),0)
    return {
      "fit_score": sig_pts+fit,
      "author_name": r.get("author_name"),
      "author_title": r.get("author_title"),
      "company_name": r.get("company_name"),
      "company_description": r.get("company_description"),
      "company_stage": r.get("company_stage"),
      "signal": primary[0], "signal_keyword": primary[3], "pain": primary[2],
      "post_url": r.get("post_url"),
      "post_text": r.get("post_text","").replace("\n"," ")[:400],
    }

def main(infile="raw_posts.jsonl", outfile="lead_scores.csv"):
    rows=[score(json.loads(l)) for l in open(infile) if l.strip()]
    rows.sort(key=lambda x:x["fit_score"], reverse=True)
    with open(outfile,"w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"Wrote {len(rows)} leads -> {outfile}")
    for r in rows[:5]:
        print(f"  {r['fit_score']:>3}  {r['author_title']:<22} @ {r['company_name']:<18} [{r['signal']}]  '{r['signal_keyword']}'")

if __name__=="__main__":
    main(*sys.argv[1:])
