import os
import sys
import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from src.kb_indexer import KnowledgeRetriever
from src.tools_handler import ToolsHandler
from src.conversation_agent import ConversationalAgent

def run():
    retriever = KnowledgeRetriever()
    tools = ToolsHandler()
    agent = ConversationalAgent(retriever=retriever, tools=tools)

    df = pd.read_csv("practice/questions.csv", dtype=str).fillna("")
    results = []

    for idx, row in df.iterrows():
        qid = row["id"]
        q = row["question"]
        gold_raw = row["gold_evidence"]
        must = [m.strip().lower() for m in row["must_include"].split(";") if m.strip()]
        ref = row["reference_answer"]

        agent.reset_session()
        # turn 2 so it answers directly
        agent.turn_count = 1
        rep, cited = agent.respond(q)

        ok = True
        for m in must:
            alts = [alt.strip() for alt in m.split("/") if alt.strip()]
            if not any(alt in rep.lower() for alt in alts):
                ok = False
                break

        results.append({
            "id": qid,
            "question": q,
            "must": must,
            "passed": ok,
            "reply": rep,
            "cited": cited,
            "gold": gold_raw,
            "ref": ref
        })

    passed_count = sum(1 for r in results if r["passed"])
    print(f"Passed: {passed_count}/{len(results)} ({passed_count/len(results)*100:.1f}%)")

    with open("diagnostic_output.txt", "w", encoding="utf-8") as f:
        f.write(f"Passed: {passed_count}/{len(results)}\n\n")
        for r in results:
            if not r["passed"]:
                f.write(f"[{r['id']}] Q: {r['question']}\n")
                f.write(f"  MUST: {r['must']}\n")
                f.write(f"  REPLY: {r['reply']}\n")
                f.write(f"  GOLD: {r['gold']}\n")
                f.write(f"  REF: {r['ref']}\n\n")

if __name__ == "__main__":
    run()
