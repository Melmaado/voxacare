import os
import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb
from schemas import PatientFile

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

def get_connection():
    return psycopg.connect(DATABASE_URL)

def init_db() -> None:
    with get_connection() as co:
        co.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                data JSONB NOT NULL
                )
            """)

def save_patient(patient: PatientFile) -> None:
    with get_connection() as co:
        co.execute(
            """INSERT INTO patients (patient_id, data) VALUES (%s, %s)
                ON CONFLICT (patient_id) DO UPDATE SET data = EXCLUDED.data""",
            (patient.patient_id, Jsonb(patient.model_dump(mode="json"))),
            )

def load_patient(patient_id: str) -> PatientFile:
    with get_connection() as co:
        row = co.execute("SELECT data FROM patients WHERE patient_id = %s", (patient_id,)).fetchone()
    if row is None:
        raise KeyError(f"Unknown patient: {patient_id}")
    return PatientFile.model_validate(row[0])

def list_patient_ids() -> list[str]:
    with get_connection() as co:
        rows = co.execute("SELECT patient_id FROM patients ORDER BY patient_id").fetchall()
    return [row[0] for row in rows]
