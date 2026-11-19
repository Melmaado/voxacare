from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agent import answer
from extraction import ExtractedEvent, extract, save_entries
from schemas import Entry, PatientFile, Profession
from storage import init_db, list_patient_ids, load_patient
from pathlib import Path
from fastapi.staticfiles import StaticFiles

init_db()
app = FastAPI(title="Voxacare API")

class DictationIn(BaseModel):
    dictation:str

class EntriesIn(BaseModel):
    events: list[ExtractedEvent]
    author: str
    profession: Profession
    dictation_date: Optional[str] = None

class QuestionIn(BaseModel):
    question: str

def get_patient_or_404(patient_id) ->  PatientFile:
    try:
        return load_patient(patient_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Unknown patient: {patient_id}")


@app.get("/")
def health() -> dict:
    return {"status": "ok", "docs": "/docs"}

@app.get("/patients")
def list_patients() -> list[dict]:
    patients = [load_patient(pid) for pid in list_patient_ids()]
    return [{"patient_id": p.patient_id, "pseudonym": p.pseudonym, "ward": p.ward, "room": p.room}
            for p in patients]

@app.get("/patients/{patient_id}")
def get_patient(patient_id: str) -> PatientFile:
    return get_patient_or_404(patient_id)

@app.post("/patients/{patient_id}/extract")
def extract_dictation(patient_id: str, body: DictationIn) -> list[ExtractedEvent]:
    get_patient_or_404(patient_id)
    return extract(body.dictation)

@app.post("/patients/{patient_id}/entries")
def add_entries(patient_id: str, body: EntriesIn) -> list[Entry]:
    get_patient_or_404(patient_id)
    return save_entries(patient_id, body.events, body.author, body.profession, body.dictation_date)

@app.post("/patients/{patient_id}/ask")
def ask_question(patient_id: str, body: QuestionIn) -> dict:
    get_patient_or_404(patient_id)
    return answer(patient_id, body.question)

ROOT = Path(__file__).parent.parent
app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")
app.mount("/app", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")