#Author Deniz Rahnefeld (409637)
#
# SCHRITT 3 - Sicherheitstests des bewertungen-Bereichs.
#
# Geprueft werden ausschliesslich die fuer das Uniprojekt geforderten Aspekte:
#   - Schutz vor Cross-Site-Scripting (XSS)
#   - Schutz vor SQL-Injection
#
# XSS: Der wichtigste angreifbare Wert ist der frei eingebbare Kommentar, der
# gespeichert und spaeter wieder angezeigt wird (stored XSS). Zusaetzlich werden
# Titel/Namen aus der DB in Dropdowns und in der Statistik-Ansicht ausgegeben.
# Dank Jinja2-Autoescaping muessen alle diese Werte escaped erscheinen.
#
# SQL-Injection: Alle Queries sind parametrisiert (psycopg %s + Parameter-Tupel).
# Die Fake-DB (conftest.py) zeichnet jeden execute()-Aufruf auf, sodass geprueft
# werden kann, dass boesartige Eingaben NUR als Parameter uebergeben werden.

from bewertungen import queries


XSS_PAYLOAD = "<script>alert('xss')</script>"
SQLI_PAYLOAD = "' OR '1'='1"
SQLI_DROP = "1); DROP TABLE bew_vortrag;--"


def login_as(client, user_id=1):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


# ===========================================================================
# XSS-Tests
# ===========================================================================

# ---------------------------------------------------------------------------
# Test 1 (XSS): Der frei eingebbare Ausarbeitungs-Kommentar wird in der
# Statistik-Ansicht escaped ausgegeben (stored XSS). Ansicht nur fuer Dozenten.
# ---------------------------------------------------------------------------
def test_xss_kommentar_in_ansicht_escaped(client, monkeypatch):
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "doz")
    monkeypatch.setattr(
        "bewertungen.routes.get_user_info",
        lambda sid: {"vorname": "Max", "nachname": "Mustermann", "matr_nr": "123456", "titel": "Star Wars"},
    )
    monkeypatch.setattr("bewertungen.routes.get_vortragsstatistiken", lambda sid: {"anzahl_bewertungen": 1})
    monkeypatch.setattr(
        "bewertungen.routes.get_ausarbeitung_statistiken",
        lambda sid: {"titel": "Star Wars", "umfang": "+", "referenzen": "o",
                     "sprachliche_gestaltung": "+", "inhalt": "o",
                     "schwierigkeitsgrad": "+", "kommentar": XSS_PAYLOAD},
    )
    monkeypatch.setattr("bewertungen.routes.get_seminarleistung", lambda sid: None)
    login_as(client, 1)

    resp = client.post("/bewertungen/ansicht", data={"s_id": "5"})
    body = resp.data.decode()
    assert "<script>alert('xss')</script>" not in body
    assert "&lt;script&gt;" in body


# ---------------------------------------------------------------------------
# Test 2 (XSS): Auch der (aus der DB geladene) Name in der Ansicht wird escaped.
# ---------------------------------------------------------------------------
def test_xss_name_in_ansicht_escaped(client, monkeypatch):
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "doz")
    monkeypatch.setattr(
        "bewertungen.routes.get_user_info",
        lambda sid: {"vorname": XSS_PAYLOAD, "nachname": "Mustermann", "matr_nr": "123456", "titel": None},
    )
    monkeypatch.setattr("bewertungen.routes.get_vortragsstatistiken", lambda sid: {"anzahl_bewertungen": None})
    monkeypatch.setattr("bewertungen.routes.get_ausarbeitung_statistiken", lambda sid: {"titel": None})
    monkeypatch.setattr("bewertungen.routes.get_seminarleistung", lambda sid: None)
    login_as(client, 1)

    resp = client.post("/bewertungen/ansicht", data={"s_id": "5"})
    body = resp.data.decode()
    assert "<script>alert('xss')</script>" not in body
    assert "&lt;script&gt;" in body


# ---------------------------------------------------------------------------
# Test 3 (XSS): Das Vortrags-Dropdown escaped den Titel (aus der DB).
# ---------------------------------------------------------------------------
def test_xss_vortrag_dropdown_escaped(client, monkeypatch):
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "stud")
    monkeypatch.setattr(
        "bewertungen.routes.get_bewertbare_vortraege",
        lambda exclude_account_id=None: [
            {"t_id": 1, "titel": XSS_PAYLOAD, "vorname": "Max", "nachname": "Mustermann"}
        ],
    )
    login_as(client, 5)

    resp = client.get("/bewertungen/vortrag")
    body = resp.data.decode()
    assert "<script>alert('xss')</script>" not in body
    assert "&lt;script&gt;" in body


# ---------------------------------------------------------------------------
# Test 4 (XSS): Das Ausarbeitungs-Dropdown escaped den Namen (aus der DB).
# ---------------------------------------------------------------------------
def test_xss_ausarbeitung_dropdown_escaped(client, monkeypatch):
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "doz")
    monkeypatch.setattr(
        "bewertungen.routes.get_bewertbare_ausarbeitungen",
        lambda d_id: [{"t_id": 1, "titel": "Star Wars", "vorname": XSS_PAYLOAD, "nachname": "Test"}],
    )
    login_as(client, 1)

    resp = client.get("/bewertungen/ausarbeitung")
    body = resp.data.decode()
    assert "<script>alert('xss')</script>" not in body
    assert "&lt;script&gt;" in body


# ---------------------------------------------------------------------------
# Test 5 (XSS): Das Seminarleistungs-Dropdown escaped den Titel (aus der DB).
# ---------------------------------------------------------------------------
def test_xss_seminarleistung_dropdown_escaped(client, monkeypatch):
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "doz")
    monkeypatch.setattr(
        "bewertungen.routes.get_bewertbare_seminarleistungen",
        lambda d_id: [{"t_id": 1, "titel": XSS_PAYLOAD, "vorname": "Max", "nachname": "Test"}],
    )
    login_as(client, 1)

    resp = client.get("/bewertungen/seminarleistung")
    body = resp.data.decode()
    assert "<script>alert('xss')</script>" not in body
    assert "&lt;script&gt;" in body


# ===========================================================================
# SQL-Injection-Tests
# ===========================================================================

# ---------------------------------------------------------------------------
# Test 6 (SQLi): create_bew_vortrag speichert den Kommentar parametrisiert.
# Ein Injection-Payload landet nur im Parameter-Tupel, nie im Query-String.
# ---------------------------------------------------------------------------
def test_sqli_create_bew_vortrag_parametrisiert(fake_db):
    # is_seminar_vorgetragen() -> True (erste Abfrage), danach INSERT.
    calls = fake_db(results=[{"vorgetragen": True}])
    data = {
        "t_id": 1, "bewertender_id": 5,
        "foliengestaltung": 4, "sprachliche_praesentation": 5, "stil": 3,
        "zeitliche_gestaltung": 2, "verstaendnis": 4, "inhalt": 3,
        "verknuepfung": 4, "diskussion": 5, "beteiligung": 3,
        "kommentar": SQLI_DROP,
    }
    result = queries.create_bew_vortrag(data)
    assert result is True

    insert_calls = [c for c in calls if "INSERT INTO bew_vortrag" in c[0]]
    assert len(insert_calls) == 1
    query, params = insert_calls[0]
    assert "%s" in query
    assert SQLI_DROP not in query          # nicht in die Query eingebaut ...
    assert SQLI_DROP in params             # ... sondern als Parameter uebergeben


# ---------------------------------------------------------------------------
# Test 7 (SQLi): create_bew_ausarbeitung ist ebenfalls parametrisiert.
# ---------------------------------------------------------------------------
def test_sqli_create_bew_ausarbeitung_parametrisiert(fake_db):
    calls = fake_db()
    data = {
        "t_id": 1, "umfang": 3, "referenzen": 3, "sprachliche_gestaltung": 3,
        "inhalt": 3, "schwierigkeitsgrad": 3, "kommentar": SQLI_DROP,
    }
    queries.create_bew_ausarbeitung(data)

    insert_calls = [c for c in calls if "INSERT INTO bew_ausarbeitung" in c[0]]
    assert len(insert_calls) == 1
    query, params = insert_calls[0]
    assert "%s" in query
    assert SQLI_DROP not in query
    assert SQLI_DROP in params


# ---------------------------------------------------------------------------
# Test 8 (SQLi): create_seminarleistung nutzt fuer INSERT UND UPDATE Parameter.
# Selbst eine boesartige t_id gelangt nur als Parameter in die DB.
# ---------------------------------------------------------------------------
def test_sqli_create_seminarleistung_parametrisiert(fake_db):
    calls = fake_db()
    payload_tid = "1); DROP TABLE seminarleistung;--"
    queries.create_seminarleistung({"t_id": payload_tid, "note": 1.0})

    assert any("INSERT INTO seminarleistung" in q for q, _ in calls)
    assert any("UPDATE seminarthema" in q for q, _ in calls)
    for query, params in calls:
        assert "%s" in query
        assert payload_tid not in query
    # Der Payload steckt in mindestens einem Parameter-Tupel.
    assert any(payload_tid in (params or ()) for _, params in calls)


# ---------------------------------------------------------------------------
# Test 9 (SQLi): Lese-Queries (Statistik/Auswahl) sind parametrisiert.
# ---------------------------------------------------------------------------
def test_sqli_lesequeries_parametrisiert(fake_db):
    calls = fake_db(results=[None, []])  # fetchone None, danach fetchall []
    queries.get_vortragsstatistiken(SQLI_PAYLOAD)
    queries.get_bewertbare_seminarleistungen(SQLI_PAYLOAD)

    assert len(calls) >= 2
    for query, params in calls:
        assert "%s" in query
        assert SQLI_PAYLOAD not in query
        assert SQLI_PAYLOAD in (params or ())


# ---------------------------------------------------------------------------
# Test 10 (SQLi): End-to-End ueber die Vortrags-Route. Ein Injection-Kommentar
# wird bis in die DB-Schicht ausschliesslich als Parameter durchgereicht.
# ---------------------------------------------------------------------------
def test_sqli_vortrag_route_end_to_end(client, monkeypatch, fake_db):
    # Guards mocken, aber create_bew_vortrag echt gegen die Fake-DB laufen lassen.
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "stud")
    monkeypatch.setattr("bewertungen.routes.ist_vortrag_bewertbar", lambda t, u: True)
    monkeypatch.setattr("bewertungen.routes.ist_eigener_vortrag", lambda t, u: False)
    calls = fake_db(results=[{"vorgetragen": True}])  # fuer is_seminar_vorgetragen
    login_as(client, 5)

    form = {
        "t_id": "1",
        "foliengestaltung": "4", "sprachliche_praesentation": "5", "stil": "3",
        "zeitliche_gestaltung": "2", "verstaendnis": "4", "inhalt": "3",
        "verknuepfung": "4", "diskussion": "5", "beteiligung": "3",
        "kommentar": SQLI_DROP,
    }
    resp = client.post("/bewertungen/vortrag", data=form)
    assert resp.status_code in (200, 302)  # keine Server-Exception

    insert_calls = [c for c in calls if "INSERT INTO bew_vortrag" in c[0]]
    assert len(insert_calls) == 1
    query, params = insert_calls[0]
    assert "%s" in query
    assert SQLI_DROP not in query
    assert SQLI_DROP in params
