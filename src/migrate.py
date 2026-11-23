from pathlib import Path
from storage import get_connection

MIGRATIONS_DIR = Path(__file__).parent.parent / "migrations"

def migrate() -> None:
    with get_connection() as co:
        co.execute("""CREATE TABLE IF NOT EXISTS schema_migrations (
                            name TEXT PRIMARY KEY,
                            applied_at TIMESTAMPTZ NOT NULL DEFAULT now())""")
        applied = {row[0] for row in co.execute("SELECT name FROM schema_migrations")}
        for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
            if path.name in applied:
                continue
            print("applying:", path.name)
            with co.transaction():
                co.execute(path.read_text(encoding="utf-8"))
                co.execute("INSERT INTO schema_migrations (name) VALUES (%s)", (path.name,))

if __name__ == "__main__":
    migrate()