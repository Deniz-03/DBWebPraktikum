#Author Deniz Rahnefeld (409637)
#
# Gemeinsame Test-Infrastruktur (pytest-Fixtures).
#
# WICHTIG: Diese Tests laufen komplett OHNE echte Datenbank.
# Alle Datenbankzugriffe werden gemockt. Dadurch sind die Tests:
#   - deterministisch (kein Zustand aus einer echten DB),
#   - überall lauffähig (kein Postgres/keine Umgebungsvariablen nötig),
#   - schnell und ohne Seiteneffekte (keine Testdaten in der echten DB).
#
# Ausführen (aus dem Projektordner SeminarPlanerProjekt):
#   python -m pytest -v

import os
import sys

# Dummy-DB-Zugangsdaten setzen, BEVOR die App importiert wird.
# config.py liest DB_USER/DB_PASSWORD beim Import. Ohne diese Werte
# würde der Import scheitern. Da die DB in den Tests gemockt wird,
# werden diese Werte nie für eine echte Verbindung benutzt.
os.environ.setdefault("DB_USER", "test")
os.environ.setdefault("DB_PASSWORD", "test")
os.environ.setdefault("SECRET_KEY", "test_secret_key")

# Projektwurzel in den Pfad legen, damit `import app` funktioniert,
# egal aus welchem Verzeichnis pytest gestartet wird.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import pytest
from app import app as flask_app


@pytest.fixture
def app():
    """Die Flask-App im Testmodus."""
    flask_app.config.update(TESTING=True)
    flask_app.secret_key = "test_secret_key"
    return flask_app


@pytest.fixture
def client(app):
    """Flask-Testclient, um Routen ohne echten Server anzusprechen."""
    return app.test_client()


# ---------------------------------------------------------------------------
# Fake-Datenbank: zeichnet alle SQL-Aufrufe auf, damit Tests prüfen können,
# dass ausschliesslich parametrisierte Queries verwendet werden (SQL-Injection).
# ---------------------------------------------------------------------------
class FakeCursor:
    """Ersatz für einen psycopg-Cursor.

    Speichert jeden execute()-Aufruf als (query, params)-Tupel in `calls`.
    fetchone()/fetchall() liefern vorgegebene Rückgabewerte aus `results`.

    Wichtig: `calls` und `results` werden GETEILT verwendet. Da jede
    Query-Funktion ihre eigene Verbindung öffnet, müssen die vorbereiteten
    Ergebnisse über alle Verbindungen hinweg der Reihe nach verbraucht werden.
    """

    def __init__(self, calls, results):
        self._calls = calls
        self._results = results  # geteilte Liste (kein copy!)
        self._last = None
        # Manche Query-Funktionen prüfen cur.rowcount (z.B. student_hinzufuegen).
        # Standardmäßig 1, damit "genau eine Zeile geändert" simuliert wird.
        self.rowcount = 1

    def execute(self, query, params=None):
        # Jeder SQL-Aufruf wird mitgeschnitten, inklusive der Parameter.
        self._calls.append((query, params))
        # Nächstes vorbereitetes Ergebnis für fetchone/fetchall bereitstellen.
        self._last = self._results.pop(0) if self._results else None

    def fetchone(self):
        return self._last

    def fetchall(self):
        return self._last if self._last is not None else []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class FakeConn:
    def __init__(self, calls, results):
        self._cur = FakeCursor(calls, results)

    def cursor(self):
        return self._cur

    def commit(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture
def fake_db(monkeypatch):
    """Ersetzt db.connect_to_db durch eine Fake-Verbindung.

    Rückgabe ist eine Funktion `setup(results)`, mit der man die
    fetchone/fetchall-Ergebnisse vorbelegt. `calls` sammelt alle SQL-Aufrufe.
    """
    import db

    calls = []

    def setup(results=None):
        results = results or []

        def _connect():
            return FakeConn(calls, results)

        # Sowohl im db-Modul als auch in den bereits importierten Query-Modulen
        # ersetzen (dort wurde `import db` verwendet -> db.connect_to_db).
        monkeypatch.setattr(db, "connect_to_db", _connect)
        return calls

    return setup
