<p align="center"><img src="assets/Voxacare_Full_Logo.png" width="380" alt="Voxacare"></p>

# Voxacare

Voice-to-record assistant for hospital care teams. Caregivers dictate after a care act, an LLM turns the dictation into structured entries in the patient file, the caregiver validates them, and an agent answers the team's questions with sources.

> WIP: student project (ECAM Brussels, AI course, 2026-2027). All patients and data are fictional. Not a medical device: the tool never diagnoses or decides, caregivers always validate.

## What works today
- **Web app**: patient list, dictation with caregiver review before saving, patient file grouped by observation domain or by date, questions with clickable sources
- **Dictation → patient file**: Mistral extracts structured entries (type, observation domain, done or planned). Nothing is saved until the caregiver validates
- **Team questions**: an agent bound to one patient reads the file through a tool and answers with citations. Every cited id is checked in code
- **Whole care team**: nurses, doctors, occupational therapists, physiotherapists, dietitians, social workers. Psychiatry is the main use case, general hospital is the control case
- **Storage**: PostgreSQL (JSONB), parameterized queries
- **API**: FastAPI, with request validation by Pydantic and interactive docs at `/docs`
- **Docker**: database and API start with one command
- **Footprint tracking**: every LLM call is logged with tokens, latency, cost and estimated gCO2e (EcoLogits). Baseline: ~0.007 gCO2e for one dictation and three questions

## Stack
Python · Pydantic · LangChain · Mistral · FastAPI · PostgreSQL (pgvector image) · Docker Compose · vanilla HTML/CSS/JS

## Planned
- **Drafts and a "to validate" queue**: caregivers dictate between patients and validate at the end of a round
- **Authentication and access rights** per role and ward (the author comes from the login, not a free field), Row-Level Security, audit log
- **Better extraction**: domain definitions designed with field caregivers, guardrail for empty or off-topic dictations
- **Evaluation**: annotated test dictations and a scoring script, real dictations from caregivers held out as the test set, rate of corrections made by caregivers
- **History**: append-only entries table (no overwrite, full history), schema versioning and migrations (Alembic)
- **Retrieval**: RAG on entries with pgvector, filtered by patient
- **Drug information tool**: a local MCP server (openFDA, by active substance)
- Per-patient summary sheet by observation domain, for multidisciplinary staff meetings
- Rule-based checks (dose given twice, drug not prescribed, open instruction not followed)
- Speech-to-text, streaming answers, measured CO2 reduction (fewer calls, smaller models)

## Run it

1. Create a `.env` file at the root (never commit it):
   ```
   MISTRAL_API_KEY=your-key
   POSTGRES_PASSWORD=choose-a-password
   DATABASE_URL=postgresql://voxacare:choose-a-password@localhost:5432/voxacare
   ```
2. Start the database and the API:
   ```bash
   docker compose up --build
   ```
3. In a second terminal, load the fictional patients:
   ```bash
   docker compose exec api python src/seed.py
   ```
4. Open the web app at http://localhost:8000/app/ and the API docs at http://localhost:8000/docs

### Local development (without the API container)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d db                                   # database only
python src/seed.py                                        # fictional patients
python -m uvicorn api:app --reload --app-dir src          # API with auto-reload
```