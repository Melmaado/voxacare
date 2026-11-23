import json
from pathlib import Path
from rag import Retriever, load_pages
import sys

EVAL_PATH = Path(__file__).parent.parent / "data" / "eval" / "rag_qa.jsonl"

def ref(doc) -> str:
    return f"{doc.metadata['file'].removesuffix('.pdf')}:p{doc.metadata['page']}"

def load_items() -> list[dict]:
    if not EVAL_PATH.exists():
        raise SystemExit(f"{EVAL_PATH} not found: write the benchmark questions first (one JSON object per line).")
    return [json.loads(line) for line in EVAL_PATH.open(encoding="utf-8") if line.strip()]

def check_anchors(items: list[dict]) -> None:
    pages = {ref(p): p.page_content for p in load_pages()}
    for item in items:
        for page in item["pages"]:
            if page not in pages:
                print(f"ERROR {item['id']}: page {page} not in the corpus")
            elif item["anchor"].lower() not in pages[page].lower():
                print(f"ERROR {item['id']}: anchor {item['anchor']!r} not found on {page}")

def metrics(search, items: list[dict], k: int = 4) -> dict:
    if not items:
        return {"n":0}
    hits, rr = [], []
    for item in items:
        found = [ref(d) for d in search(item["question"], k)]
        ranks = [r for r, page in enumerate(found, start=1) if page in item["pages"]]
        hits.append(bool(ranks))
        rr.append(1 / ranks[0] if ranks else 0)
    return {f"hit@{k}": round(sum(hits) / len(hits), 2), "MRR": round(sum(rr) / len(rr), 2), "n": len(items)}

def show_ranks(search, items: list[dict], k: int = 4) -> None:
    for item in items:
        found = [ref(d) for d in search(item["question"], k)]
        rank = next((r for r, page in enumerate(found, start=1) if page in item["pages"]), None)
        print(f"  {item['id']}: rank={rank} got={found}")

def check_unanswerable(items: list[dict], patient_id: str = "P4") -> None:
    from agent import answer
    for item in items:
        result = answer(patient_id, item["question"])
        ok = result["searched_guidelines"] and not result["sources"] and not result["invalid_citations"]
        print(f"  {item['id']}: {'OK' if ok else 'FAIL'}  found={result['found']}  "
              f"searched={result['searched_guidelines']}  sources={list(result['sources'])}")
        print(f"    {result['answer']}")


if __name__ == "__main__":
    items = load_items()
    check_anchors(items)
    configs = {"baseline": Retriever(), "stopwords": Retriever(stopwords=True)}
    for split in ("dev", "test"):
        answerable = [i for i in items if i["split"] == split and i["pages"]]
        print(f"\n--- {split} ({len(answerable)} answerable questions) ---")
        for name, retriever in configs.items():
            print(f"{name:9} dense :", metrics(retriever.dense, answerable))
            print(f"{name:9} bm25  :", metrics(retriever.lexical, answerable))
            print(f"{name:9} hybrid:", metrics(lambda q, k, r=retriever: r.hybrid(q, k=k), answerable))
        if split == "dev":
            print(f"\n--- bm25 ranks with stopwords removed ({split}) ---")
            show_ranks(configs["stopwords"].lexical, answerable)
    if "--agent" in sys.argv:
        print("\n--- agent on unanswerable questions ---")
        check_unanswerable([i for i in items if not i["pages"]])