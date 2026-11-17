from typing import Literal, Optional
from pydantic import BaseModel, Field

class Treatment(BaseModel):
    drug: str = Field(description="Active substance, e.g. 'morphine'")
    dose: str = Field(description="Dose with unit, e.g. '5 mg'")
    route: Optional[str] = Field(None, description="SC, IV, oral...")
    frequency: Optional[str] = Field(None, description="e.g. 'every 4 hours if needed'")

class Instruction(BaseModel):
    id: str = Field("", description="Unique id, e.g. 'I1'")
    author: str = Field(description="Who gave the instruction, e.g. 'Dr.X'")
    date: str = Field(description="When it was given")
    text: str = Field(description="The instruction itself")
    status: Literal["open", "done"] = "open"

Domain = Literal[
    "collaboration", "behaviour", "slowness", "continence",
    "eating_swallowing", "hygiene", "organisation",
    "initiating_interactions", "activity_participation", "sociability",
    "physical_health", "other",
]

class Entry(BaseModel):
    id: str = Field(description="Unique id, e.g. 'E1'")
    time: Optional[str] = Field(None, description="Time of the event if said, e.g. '14:00'")
    author: str = Field(description="Caregiver who dictated")
    profession: Literal["nurse", "doctor", "occupational_therapist", "physiotherapist",
                        "dietitian", "social_worker", "other"] = "nurse"
    domain: Optional[Domain] = Field(None, description="Which observation criterion this entry is about")
    type: Literal["observation", "intervention", "medication", "refusal", "instruction"]
    content: str = Field(description="What was said, faithfully, without interpretation")
    drug: Optional[str] = Field(None, description="Only for medication or refusal")
    dose: Optional[str] = Field(None, description="Only if said explicitly")
    route: Optional[str] = Field(None, description="Only if said explicitly")
    source_dictation: str = Field(description="Id of the original dictation, e.g. 'D1'")

class PatientFile(BaseModel):
    patient_id: str
    pseudonym: str
    age: int
    ward: str
    room: str
    reason_for_stay: str
    diagnoses: list[str] = []
    medical_history: list[str] = []
    allergies: list[str] = []
    treatments: list[Treatment] = []
    instructions: list[Instruction] = []
    entries: list[Entry] = []


if __name__ == "__main__":

    p1 = PatientFile(
        patient_id="P1", pseudonym="Mr. D.", age=67,
        ward="cardiology", room="12", reason_for_stay="Day 2 after cardiac surgery",
        treatments=[Treatment(drug="morphine", dose="5 mg", route="SC", frequency="every 4h if needed")],
    )
    
    print(p1.model_dump_json(indent=2))