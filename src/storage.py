from pathlib import Path
from schemas import PatientFile

DATA_DIR = Path(__file__).parent.parent / "data"

def save_patient(patient: PatientFile) -> None:
    path = DATA_DIR / f"{patient.patient_id}.json"
    path.write_text(patient.model_dump_json(indent=2))

def load_patient(patient_id: str) -> PatientFile:
    path = DATA_DIR / f"{patient_id}.json"
    return PatientFile.model_validate_json(path.read_text())

if __name__ == "__main__":
    from schemas import Treatment

    p1 = PatientFile(
        patient_id="P1", pseudonym="Mr. D.", age=67, ward="cardiology", room="12",
        reason_for_stay="Day 2 after cardiac surgery",
        treatments=[Treatment(drug="morphine", dose="5 mg", route="SC", frequency="every 4h if needed")],
    )
    save_patient(p1)
    print("Saved.")

    reloaded = load_patient("P1")
    print("Reloaded:", reloaded.pseudonym, "-", reloaded.reason_for_stay)