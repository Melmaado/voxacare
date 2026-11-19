from schemas import PatientFile, Instruction, Treatment
from storage import save_patient, init_db

def seed() -> None:
    init_db()
    p1 = PatientFile(
        patient_id="P1", pseudonym="Mr. D.", age=67, ward="cardiology", room="12",
        reason_for_stay="Day 2 after cardiac surgery",
        treatments=[Treatment(drug="morphine", dose="5 mg", route="SC", frequency="every 4h if needed")],
    )

    p4 = PatientFile(
        patient_id="P4", pseudonym="Ms. S.", age=34, ward="psychiatry", room="3",
        reason_for_stay="Behavioural disorders, medication adjustment",
        diagnoses=["Moderate intellectual disability", "Epilepsy"],
        medical_history=["Several previous psychiatric hospitalisations"],
        allergies=["Penicillin"],
        treatments=[
            Treatment(drug="valproate", dose="500 mg", route="oral", frequency="twice a day"),
            Treatment(drug="risperidone", dose="1 mg", route="oral", frequency="in the evening"),
        ],
        instructions=[
            Instruction(id="I1", author="Dr. X", date="2026-11-03",
                        text="Replace risperidone with aripiprazole 5 mg in the morning. "
                             "Observe the effect on behaviour, hygiene and meals."),
            Instruction(id="I2",author="Dr. X", date="2026-11-03", text="Watch for choking risk during meals."),
        ],
    )

    for patient in (p1, p4):
        save_patient(patient)
        print("Saved", patient.patient_id, patient.pseudonym)


if __name__ == "__main__":
    seed()