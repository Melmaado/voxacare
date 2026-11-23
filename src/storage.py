import os
import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from schemas import Entry, Instruction, PatientFile, Treatment

load_dotenv()
DATABASE_URL = os.environ["DATABASE_URL"]

def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def staff_id(co, name: str, profession: str) -> int:
    return co.execute("""INSERT INTO staff (name, profession) VALUES (%s, %s)
                            ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                            RETURNING staff_id""", (name, profession)).fetchone()["staff_id"]

def medicine_id(co, substance: str) -> int:
    return co.execute("""INSERT INTO medicines (active_substance) VALUES (%s)
                            ON CONFLICT (active_substance) DO UPDATE SET active_substance = EXCLUDED.active_substance
                            RETURNING medicine_id""", (substance.strip().lower(),)).fetchone()["medicine_id"]

def load_patient(patient_id: str) -> PatientFile:
    with get_connection() as co:
        p = co.execute("SELECT * FROM patients WHERE patient_id = %s", (patient_id,)).fetchone()
        if p is None:
            raise KeyError(f"Unknown patient: {patient_id}")
        conditions = co.execute("SELECT kind, label FROM conditions WHERE patient_id = %s ORDER BY condition_id",
                                (patient_id,)).fetchall()
        allergies = co.execute("SELECT substance FROM allergies WHERE patient_id = %s ORDER BY allergy_id",
                                (patient_id,)).fetchall()
        treatments = co.execute("""
            SELECT t.treatment_id, m.active_substance AS drug, t.dose, t.route, t.frequency
            FROM treatments t JOIN medicines m USING (medicine_id)
            WHERE t.patient_id = %s AND t.stop_date IS NULL
            ORDER BY t.treatment_id""", (patient_id,)).fetchall()
        instructions = co.execute("""
            SELECT i.instruction_id, s.name AS author, i.given_on, i.text, i.status
            FROM instructions i JOIN staff s ON s.staff_id = i.author_id
            WHERE i.patient_id = %s
            ORDER BY i.instruction_id""", (patient_id,)).fetchall()
        entries = co.execute("""
            SELECT e.entry_id, e.event_time, s.name AS author, e.profession, e.domain, e.status,
                   e.event_date, e.type, e.content, m.active_substance AS drug, e.dose, e.route, e.dictation_id
            FROM entries e
            JOIN staff s ON s.staff_id = e.author_id
            LEFT JOIN medicines m ON m.medicine_id = e.medicine_id
            WHERE e.patient_id = %s AND NOT EXISTS (SELECT 1 FROM entries newer WHERE newer.supersedes = e.entry_id)
            ORDER BY e.entry_id""", (patient_id,)).fetchall()
    
    return PatientFile(
        patient_id = p["patient_id"], pseudonym=p["pseudonym"], age=p["age"], ward=p["ward"],
        room = p["room"], reason_for_stay=p["reason_for_stay"],
        diagnoses = [c["label"] for c in conditions if c["kind"] == "diagnosis"],
        medical_history = [c["label"] for c in conditions if c["kind"] == "history"],
        allergies = [a["substance"] for a in allergies],
        treatments = [Treatment(id=f"T{t['treatment_id']}", drug=t["drug"], dose=t["dose"],
                              route=t["route"], frequency=t["frequency"]) for t in treatments],
        instructions = [Instruction(id=f"I{i['instruction_id']}", author=i["author"], date=i["given_on"].isoformat(),
                                    text=i["text"], status=i["status"]) for i in instructions],
        entries = [Entry(id=f"E{e['entry_id']}", time=e["event_time"], author=e["author"],
                       profession=e["profession"], domain=e["domain"], status=e["status"],
                       date=e["event_date"].isoformat() if e["event_date"] else None, type=e["type"],
                       content=e["content"], drug=e["drug"], dose=e["dose"], route=e["route"],
                       source_dictation=f"D{e['dictation_id']}") for e in entries],
    )

def list_patient_ids() -> list[str]:
    with get_connection() as co:
        rows = co.execute("SELECT patient_id FROM patients ORDER BY patient_id").fetchall()
    return [row["patient_id"] for row in rows]