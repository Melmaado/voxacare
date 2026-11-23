from migrate import migrate
from storage import get_connection, medicine_id, staff_id

STAFF = {"Dr. X": "doctor"}

PATIENTS = [
    {"patient_id": "P1", "pseudonym": "Mr. D.", "age": 67, "ward": "cardiology", "room": "12",
     "reason_for_stay": "Day 2 after cardiac surgery",
     "diagnoses": [], "history": [], "allergies": [],
     "treatments": [("morphine", "5 mg", "SC", "every 4h if needed")],
     "instructions": []},
    {"patient_id": "P4", "pseudonym": "Ms. S.", "age": 34, "ward": "psychiatry", "room": "3",
     "reason_for_stay": "Behavioural disorders, medication adjustment",
     "diagnoses": ["Moderate intellectual disability", "Epilepsy"],
     "history": ["Several previous psychiatric hospitalisations"],
     "allergies": ["Penicillin"],
     "treatments": [("valproate", "500 mg", "oral", "twice a day"),
                    ("risperidone", "1 mg", "oral", "in the evening")],
     "instructions": [("Dr. X", "2026-11-03", "Replace risperidone with aripiprazole 5 mg in the morning. "
                                              "Observe the effect on behaviour, hygiene and meals."),
                      ("Dr. X", "2026-11-03", "Watch for choking risk during meals.")]},
]

def seed() -> None:
    migrate()
    with get_connection() as co:
        for p in PATIENTS:
            pid = p["patient_id"]
            if co.execute("SELECT 1 FROM patients WHERE patient_id = %s", (pid,)).fetchone():
                print("already here:", pid)
                continue
            co.execute("""INSERT INTO patients (patient_id, pseudonym, age, ward, room, reason_for_stay)
                          VALUES (%(patient_id)s, %(pseudonym)s, %(age)s, %(ward)s, %(room)s, %(reason_for_stay)s)""", p)
            for kind, key in (("diagnosis", "diagnoses"), ("history", "history")):
                for label in p[key]:
                    co.execute("INSERT INTO conditions (patient_id, kind, label) VALUES (%s, %s, %s)",
                               (pid, kind, label))
            for substance in p["allergies"]:
                co.execute("INSERT INTO allergies (patient_id, substance) VALUES (%s, %s)", (pid, substance))
            for drug, dose, route, frequency in p["treatments"]:
                co.execute("""INSERT INTO treatments (patient_id, medicine_id, dose, route, frequency)
                              VALUES (%s, %s, %s, %s, %s)""", (pid, medicine_id(co, drug), dose, route, frequency))
            for author, given_on, text in p["instructions"]:
                co.execute("""INSERT INTO instructions (patient_id, author_id, given_on, text)
                              VALUES (%s, %s, %s, %s)""", (pid, staff_id(co, author, STAFF[author]), given_on, text))
            print("saved:", pid, p["pseudonym"])

if __name__ == "__main__":
    seed()