## RAG retrieval — baseline (23/11/2026)

Setup: 10 French guidelines (HAS, INRS), 55 pages, 264 chunks
(1000 chars, overlap 150). Embeddings: mistral-embed. Lexical: BM25Okapi
(no stopword removal). Hybrid: Reciprocal Rank Fusion (c=60, 20 candidates each).
Benchmark: data/eval/rag_qa.jsonl, 13 questions (dev 5, test 8), of which
2 unanswerable. Ground truth = expected pages, each checked by an exact
anchor sentence in the cleaned page text (check_anchors).
Metrics: hit@4 and MRR over answerable questions. Commit: d747a77

| Method | dev hit@4 | dev MRR | test hit@4 | test MRR |
|--------|-----------|---------|------------|----------|
| Dense  | 1.00      | 0.75    | 1.00       | 0.90     |
| BM25   | 0.75      | 0.40    | 0.86       | 0.62     |
| Hybrid | 1.00      | 0.75    | 1.00       | 0.90     |

Notes: n is small (4 dev / 7 test answerable), so one question = 0.25 / 0.14.
Hybrid does not degrade dense but no difference can be claimed.
Dense hit@4 is at ceiling: questions likely reuse the guidelines' wording;
add field-style paraphrases later.

### Error analysis — BM25 on dev (23/11/2026)

| Question | Rank | Retrieved instead |
|----------|------|-------------------|
| rag-01 (warning signs of choking) | 4 | fausses_routes p1, p2 first |
| rag-04 (drugs that raise choking risk) | miss | neuroleptiques p2, fausses_routes p1/p2 |
| rag-05 (exercises against falls) | 3 | chutes p4, p6 first |
| rag-06 (preparing for aggressive moments) | 1 | — |

Findings:
- Main failure is vocabulary mismatch, not stopwords: rag-04 asks for
  "médicaments", the answer page says "benzodiazépines". BM25 only matches
  identical tokens; dense retrieval bridges the gap through embeddings.
- Within-document confusion: "fausse route" appears on every page of the
  guideline (p1: 3, p2: 4, p3: 2 occurrences). BM25 rewards term frequency,
  so the answer page (p3) is the one it ranks lowest (rag-01).
- Duplicate pages in the top k: several chunks of the same page can fill
  two of the 4 slots (fausses_routes p2 in rag-04, violence p2 in rag-06).
  hit@4 therefore counts chunks, not pages, and the agent receives the
  same source twice (wasted context).

Hypotheses before ablation:
- H1: removing French stopwords improves BM25 ranks (rag-01, rag-05)
  but does not fix rag-04.
- H2: deduplicating results by page frees slots and may raise hit@4/MRR.

### Ablation — French stopword removal in BM25 (23/11/2026)

| Config | dev BM25 MRR | dev hybrid MRR | test BM25 hit@4 | test BM25 MRR | test hybrid MRR |
|--------|--------------|----------------|-----------------|---------------|-----------------|
| Baseline | 0.40 | 0.75 | 0.86 | 0.62 | 0.90 |
| Stopwords removed | 0.56 | 0.75 | 1.00 | 0.57 | 0.79 |

Dense unchanged in both configs (sanity check passed). Commit: 282d255

- H1 on dev: confirmed for BM25 (rag-01 4→2, rag-05 3→1); rag-04 recovered
  only at rank 4 (vocabulary mismatch remains); rag-06 regressed 1→2.
- Dev showed no gain for hybrid retrieval, the system the agent uses.
- Test: BM25 finds more pages (hit@4 0.86→1.00) but ranks them lower
  (MRR 0.62→0.57); hybrid MRR drops 0.90→0.79 (≈ one question, n=7).
- Decision: not deployed. Stopword removal stays an option
  (Retriever(stopwords=True)), default off.
- The test split has now been used for a decision: further ablations
  (H2, page deduplication) need new questions.

### Agent on unanswerable questions (23/11/2026) — agent-v8

Criterion: the agent searched the guidelines (search_protocols called),
cites no guideline and no invalid id. Answer read by a human.

| Question | found | searched | sources | Result |
|----------|-------|----------|---------|--------|
| rag-n1 (max daily paracetamol dose) | False | True | none | OK |
| rag-n2 (urinary catheter insertion) | False | True | none | OK |

Bug found by reading the answers: agent-v7 replaced every "not found"
answer by a fixed English string in code (and in the web front), so the
first version of this check could not fail and the answer ignored the
question's language. Fixed in agent-v8: the model writes the not-found
answer, citations are always checked, searched_guidelines is returned.

### Agent v9–v10 fixes (23/11/2026), checked on the 6 agent questions + 2 unanswerable — Commit: c9ec31a

- Repeated tool calls: the injection question called read_patient_file 8 times.
  Fix in code: the tool returns the file once per question, then a short
  "already given" message. Now 1 call.
- Citations written in the answer text but missing from the list ([T1]).
  Fix in code: ids in square brackets are extracted from the text and merged.
  Only strings shaped like an id (E/I/T + number, file:pN) count as citations:
  a first version also caught template placeholders ([valeur], [EVA]) and
  flagged them invalid. Well-formed but unknown ids are still flagged.
- Guidelines mentioned without being searched. Cause: the Answer field
  description told the model to say "neither the file nor the guidelines
  cover it", contradicting the system prompt. Fixed in v10.
- Known issue: citation behaviour shifts between prompt versions. In v10 the
  Saed answer uses the guideline but cites nothing (v9 cited has_saed_2019:p1).
  Judged by eye on 6 questions, v9 vs v10 cannot be compared: next step is an
  agent benchmark with a citation score, rather than more prompt edits.

## Normalized database (23/11/2026) — teacher feedback on the JSONB store

Before: one JSONB document per patient, rewritten in full at every save;
ids computed by position (T1 = first treatment in the list).
After: 10 tables (migrations/001_schema.sql), applied by src/migrate.py
(each migration once, in a transaction, tracked in schema_migrations).

- Stable ids from SERIAL keys (T7, E12): a citation always points to the same row.
- Entries are append-only: a trigger rejects UPDATE and DELETE on entries
  (checked: "ERROR: entries are append-only"); corrections are new entries
  with supersedes. load_patient() shows only the latest version.
- Each entry links to its dictation (raw text kept) and its author (staff).
- profession is copied into each entry on purpose: the profession at the
  time of writing is a fact of the entry (denormalization, justified).
- A dictation and its entries are saved in one transaction.
- load_patient() rebuilds the same PatientFile from joins: agent, API and
  front did not change. Non-regression: agent questions give the same
  answers, with database ids.