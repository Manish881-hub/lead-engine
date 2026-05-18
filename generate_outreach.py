"""generate_outreach.py — top N from lead_scores.csv -> outreach.jsonl via OpenAI-compatible API."""
import csv, json, os, sys, pathlib
TMPL = pathlib.Path(__file__).parent.joinpath("outreach_prompt.md").read_text()

def render(row):
    out = TMPL
    for k,v in row.items():
        out = out.replace("{{"+k+"}}", v or "")
    return out

def call_llm(prompt):
    from openai import OpenAI
    client = OpenAI()
    r = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),
        messages=[{"role":"user","content":prompt}],
        response_format={"type":"json_object"},
        temperature=0.4,
    )
    return r.choices[0].message.content

def main(infile="lead_scores.csv", outfile="outreach.jsonl", top_n="25"):
    top_n=int(top_n)
    with open(infile) as f: rows=list(csv.DictReader(f))[:top_n]
    with open(outfile,"w") as o:
        for row in rows:
            try:
                data=json.loads(call_llm(render(row)))
                o.write(json.dumps({"lead":row,"outreach":data})+"\n")
                print("OK ", row["author_name"], row["fit_score"])
            except Exception as e:
                print("ERR", row["author_name"], e)

if __name__=="__main__":
    main(*sys.argv[1:])
