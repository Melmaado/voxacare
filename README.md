<p align="center"><img src="assets/Voxacare_Full_Logo.png" width="380" alt="Voxacare"></p>

# Voxacare

Voice-to-record assistant for hospital care teams. Caregivers dictate after a care act, an LLM turns the dictation into structured entries in the patient file, the caregiver validates them, and an agent answers the team's questions with sources from the patient file and from public care guidelines.

> WIP: student project (ECAM Brussels, AI course, 2026-2027). All patients and data are fictional. Not a medical device: the tool never diagnoses or decides, caregivers always validate.

## What works today
- **Web app**: patient list, dictation with caregiver review before saving, patient file grouped by observation domain or by date, questions with clickable sources (patient file ids, and guideline pages that open the PDF at the right page)
- **Dictation → patient file**: Mistral extracts structured entries (type, observation domain, done or planned). Nothing is saved until the caregiver validates
- **Team questions**: an agent bound to one patient with two tools: it reads the patient file, and searches public care guidelines when the question is about good practice (agentic RAG). Every citation is checked in code: file ids must exist, guideline refs must have been retrieved for this question
- **RAG on care guidelines**: 10 public documents (HAS, INRS) on choking, falls, structured communication (Saed), undernutrition, standard precautions, prescription transcription, neuroleptics, violence prevention, seclusion and restraint. Ingestion removes repeated headers and footers and skips unreadable pages; chunks keep source and page; mistral-embed index cached on disk; hybrid search (BM25 + dense, fused with RRF)
- **Whole care team**: nurses, doctors, occupational therapists, physiotherapists, dietitians, social workers. Psychiatry is the main use case, general hospital is the control case
- **Storage**: PostgreSQL (JSONB), parameterized queries
- **API**: FastAPI, with request validation by Pydantic, interactive docs at `/docs`, and clear errors when the LLM fails (502/503/504, logged)
- **Docker**: database and API start with one command
- **Footprint tracking**: every LLM call is logged with tokens, latency, cost and estimated gCO2e (EcoLogits). Baseline: ~0.007 gCO2e for one dictation and three questions

## Stack
Python · Pydantic · LangChain · Mistral · FastAPI · PostgreSQL (pgvector image) · rank-bm25 · Docker Compose · vanilla HTML/CSS/JS

## Planned
- **Evaluation**: retrieval benchmark (hit@k, MRR for dense, BM25, hybrid), annotated test dictations and a scoring script, ablation table, real dictations from caregivers held out as the test set
- **Normalized database**: patients, diagnoses, treatments, instructions, append-only entries (full history), staff, medicines; schema migrations (Alembic)
- **Question history**: a separate table of questions and answers with their sources (traceability, evaluation data, feedback), never mixed with the patient file
- **Conversation memory**: a thread per caregiver and patient, with a measured context strategy
- **Drafts and a "to validate" queue**: caregivers dictate between patients and validate at the end of a round
- **Authentication and access rights** per role and ward, Row-Level Security, audit log
- **Better extraction**: a verification step after extraction, domain definitions designed with field caregivers, guardrail for empty or off-topic dictations
- **Retrieval**: index moved to pgvector, RAG on patient entries filtered by patient
- **Drug information tool**: a local MCP server (openFDA, by active substance)
- Per-patient summary sheet by observation domain, for multidisciplinary staff meetings
- Rule-based checks (drug given but not prescribed, dose given twice, open instruction not followed)
- Speech-to-text, streaming answers, measured CO2 reduction (fewer calls, smaller models)

## Run it

1. Create a `.env` file at the root (never commit it):
   ```
   MISTRAL_API_KEY=your-key
   POSTGRES_PASSWORD=choose-a-password
   DATABASE_URL=postgresql://voxacare:choose-a-password@localhost:5432/voxacare
   ```
2. Download the public care guidelines used by the RAG (once):
   ```bash
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python src/download_protocols.py
   ```
   The PDFs are not stored in the repository. The embedding index is built on the first guideline question and cached in `data/protocols/`.
3. Start the database and the API:
   ```bash
   docker compose up --build
   ```
4. In a second terminal, load the fictional patients:
   ```bash
   docker compose exec api python src/seed.py
   ```
5. Open the web app at http://localhost:8000/app/ and the API docs at http://localhost:8000/docs

### Local development (without the API container)
```bash
docker compose up -d db                                   # database only
python src/seed.py                                        # fictional patients
python -m uvicorn api:app --reload --app-dir src          # API with auto-reload
```