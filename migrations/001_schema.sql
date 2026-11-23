CREATE TYPE profession AS ENUM ('nurse', 'doctor', 'occupational_therapist', 
    'physiotherapist', 'dietitian', 'social_worker', 'other');

CREATE TYPE entry_type as ENUM ('observation', 'intervention', 'medication', 'refusal', 'instruction');

CREATE TYPE domain AS ENUM ('collaboration', 'behaviour', 'slowness', 'continence',
    'eating_swallowing', 'hygiene', 'organisation', 'initiating_interactions',
    'activity_participation', 'sociability', 'physical_health', 'other');

CREATE TABLE staff (
    staff_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    profession profession NOT NULL
);

CREATE TABLE patients (
    patient_id TEXT PRIMARY KEY,
    pseudonym TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 0),
    ward TEXT NOT NULL,
    room TEXT NOT NULL,
    reason_for_stay TEXT NOT NULL
);

CREATE TABLE conditions (
    condition_id SERIAL PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients,
    kind TEXT NOT NULL CHECK (kind IN ('diagnosis', 'history')),
    label TEXT NOT NULL
);

CREATE TABLE allergies (
    allergy_id SERIAL PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients,
    substance TEXT NOT NULL,
    UNIQUE (patient_id, substance)
);

CREATE TABLE medicines (
    medicine_id SERIAL PRIMARY KEY,
    active_substance TEXT NOT NULL UNIQUE
);

CREATE TABLE treatments (
    treatment_id SERIAL PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients,
    medicine_id INTEGER NOT NULL REFERENCES medicines,
    dose TEXT NOT NULL,
    route TEXT,
    frequency TEXT,
    prescribed_by INTEGER REFERENCES staff,
    start_date DATE,
    stop_date DATE
);

CREATE TABLE instructions (
    instruction_id SERIAL PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients,
    author_id INTEGER NOT NULL REFERENCES staff,
    given_on DATE NOT NULL,
    text TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open', 'done'))
);

CREATE TABLE dictations (
    dictation_id SERIAL PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients,
    author_id INTEGER NOT NULL REFERENCES staff,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    text TEXT NOT NULL
);

CREATE TABLE entries (
    entry_id SERIAL PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients,
    dictation_id INTEGER NOT NULL REFERENCES dictations,
    author_id INTEGER NOT NULL REFERENCES staff,
    profession profession NOT NULL,
    type entry_type NOT NULL,
    domain domain,
    status TEXT NOT NULL DEFAULT 'done' CHECK (status IN ('done', 'planned')),
    event_date DATE,
    event_time TEXT,
    content TEXT NOT NULL,
    medicine_id INTEGER REFERENCES medicines,
    dose TEXT,
    route TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    supersedes INTEGER REFERENCES entries
);
CREATE INDEX entries_patient_date ON entries (patient_id, event_date);

CREATE FUNCTION forbid_change() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION 'entries are append-only: add a new entry with supersedes instead';
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER entries_append_only BEFORE UPDATE OR DELETE ON entries
    FOR EACH ROW EXECUTE FUNCTION forbid_change();

CREATE TABLE questions(
    question_id SERIAL PRIMARY KEY,
    patient_id TEXT NOT NULL REFERENCES patients,
    asked_by INTEGER REFERENCES staff,
    asked_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    found BOOLEAN NOT NULL,
    citations TEXT[] NOT NULL DEFAULT '{}',
    prompt_version TEXT NOT NULL
);