#Author Deniz Rahnefeld (409637)
#
# SCHRITT 3 - Sicherheitstests des themen-Bereichs.
#
# Geprueft werden ausschliesslich die fuer das Uniprojekt geforderten Aspekte:
#   - Schutz vor Cross-Site-Scripting (XSS)
#   - Schutz vor SQL-Injection
#
# XSS: Titel, Oberbegriff, Beschreibung und Namen werden an vielen Stellen
# ausgegeben (Uebersicht, Detailansicht, Bearbeiten-Formular). Dank Jinja2-
# Autoescaping muessen alle diese Werte escaped erscheinen.
#
# SQL-Injection: Alle Queries sind parametrisiert - auch die dynamisch
# zusammengesetzte Filter-Query (ILIKE %s mit den Wildcards im Parameter).
# Die Fake-DB (conftest.py) zeichnet jeden execute()-Aufruf auf.

from themen import queries


XSS_PAYLOAD = "<script>alert('xss')</script>"
SQLI_PAYLOAD = "' OR '1'='1"
SQLI_DROP = "1); DROP TABLE seminarthema;--"

DOZIERENDE = [{"d_id": 1, "vorname": "Klaus-Dieter", "nachname": "Althoff"}]


def login_as(client, user_id=1):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def thema_dict(**overrides):
    data = {
        "themen_id": 1, "titel": "Star Wars", "oberbegriff": "Galaxis",
        "beschreibung": "Beschreibung", "d_id": 1, "s_id": None,
        "status": "Frei", "semester": 6, "pdf_pfad": None, "vorgetragen": False,
    }
    data.update(overrides)
    return data


# ===========================================================================
# XSS-Tests
# ===========================================================================

# ---------------------------------------------------------------------------
# Test 1 (XSS): Die Themenuebersicht escaped den Titel eines Themas.
# ---------------------------------------------------------------------------
def test_xss_uebersicht_titel_escaped(client, monkeypatch):
    monkeypatch.setattr("themen.routes.hole_user_und_rolle", lambda: (5, "stud"))
    monkeypatch.setattr("themen.routes.get_seminarthemen_by_filter",
        lambda *a, **k: [{"themen_id": 1, "titel": XSS_PAYLOAD, "semester": 6,
                          "status": "Frei", "doz_vorname": "P", "doz_nachname": "R"}])
    monkeypatch.setattr("themen.routes.get_semester", lambda: [])
    monkeypatch.setattr("themen.routes.get_dozierenden", lambda: [])
    monkeypatch.setattr("themen.routes.get_status_optionen", lambda: [])
    login_as(client, 5)

    body = client.get("/themen/uebersicht").data.decode()
    assert "<script>alert('xss')</script>" not in body
    assert "&lt;script&gt;" in body


# ---------------------------------------------------------------------------
# Test 2 (XSS): Die Detailansicht escaped Titel und Beschreibung.
# ---------------------------------------------------------------------------
def test_xss_detail_titel_beschreibung_escaped(client, monkeypatch):
    monkeypatch.setattr("themen.routes.hole_user_und_rolle", lambda: (5, "stud"))
    monkeypatch.setattr("themen.routes.get_seminarthema",
        lambda tid: thema_dict(titel=XSS_PAYLOAD, beschreibung=XSS_PAYLOAD, s_id=None))
    monkeypatch.setattr("themen.routes.get_dozent_by_id",
        lambda did: {"d_id": 1, "vorname": "Pascal", "nachname": "Reuss"})
    login_as(client, 5)

    body = client.get("/themen/thema_detail/1").data.decode()
    assert "<script>alert('xss')</script>" not in body
    assert "&lt;script&gt;" in body


# ---------------------------------------------------------------------------
# Test 3 (XSS): Der (aus der DB geladene) Studierendenname wird escaped.
# ---------------------------------------------------------------------------
def test_xss_detail_studentenname_escaped(client, monkeypatch):
    monkeypatch.setattr("themen.routes.hole_user_und_rolle", lambda: (5, "stud"))
    monkeypatch.setattr("themen.routes.get_seminarthema",
        lambda tid: thema_dict(s_id=5, status="Vergeben"))
    monkeypatch.setattr("themen.routes.get_student_by_id",
        lambda sid: {"s_id": 5, "matr_nr": "123456", "vorname": XSS_PAYLOAD, "nachname": "Test"})
    monkeypatch.setattr("themen.routes.get_dozent_by_id",
        lambda did: {"d_id": 1, "vorname": "Pascal", "nachname": "Reuss"})
    login_as(client, 5)

    body = client.get("/themen/thema_detail/1").data.decode()
    assert "<script>alert('xss')</script>" not in body
    assert "&lt;script&gt;" in body


# ---------------------------------------------------------------------------
# Test 4 (XSS): Das Bearbeiten-Formular escaped den zurueckgegebenen Titel
# im value-Attribut.
# ---------------------------------------------------------------------------
def test_xss_bearbeiten_titel_value_escaped(client, monkeypatch):
    monkeypatch.setattr("themen.routes.hole_user_und_rolle", lambda: (1, "doz"))
    monkeypatch.setattr("themen.routes.get_seminarthema",
        lambda tid: thema_dict(titel=XSS_PAYLOAD, s_id=None))
    monkeypatch.setattr("themen.routes.get_dozierenden", lambda: DOZIERENDE)
    login_as(client, 1)

    body = client.get("/themen/1/bearbeiten").data.decode()
    assert "<script>alert('xss')</script>" not in body
    assert "&lt;script&gt;" in body


# ---------------------------------------------------------------------------
# Test 5 (XSS): Der zurueckgespiegelte Filterwert (Titel) wird escaped.
# ---------------------------------------------------------------------------
def test_xss_filter_reflektiert_escaped(client, monkeypatch):
    monkeypatch.setattr("themen.routes.hole_user_und_rolle", lambda: (5, "stud"))
    monkeypatch.setattr("themen.routes.get_seminarthemen_by_filter", lambda *a, **k: [])
    monkeypatch.setattr("themen.routes.get_semester", lambda: [])
    monkeypatch.setattr("themen.routes.get_dozierenden", lambda: [])
    monkeypatch.setattr("themen.routes.get_status_optionen", lambda: [])
    login_as(client, 5)

    body = client.get("/themen/uebersicht", query_string={"titel": XSS_PAYLOAD}).data.decode()
    assert "<script>alert('xss')</script>" not in body
    assert "&lt;script&gt;" in body


# ===========================================================================
# SQL-Injection-Tests
# ===========================================================================

# ---------------------------------------------------------------------------
# Test 6 (SQLi): Der Textfilter setzt den Suchbegriff parametrisiert ein.
# ---------------------------------------------------------------------------
def test_sqli_filter_titel_parametrisiert(fake_db):
    calls = fake_db()
    queries.get_seminarthemen_by_filter(titel=SQLI_PAYLOAD)
    query, params = calls[-1]
    assert "ILIKE %s" in query
    assert SQLI_PAYLOAD not in query                 # nicht in die Query eingebaut ...
    assert f"%{SQLI_PAYLOAD}%" in params             # ... sondern als Parameter


# ---------------------------------------------------------------------------
# Test 7 (SQLi): thema_anlegen nutzt eine parametrisierte INSERT-Anweisung.
# ---------------------------------------------------------------------------
def test_sqli_thema_anlegen_parametrisiert(fake_db):
    calls = fake_db()
    queries.thema_anlegen(SQLI_DROP, d_id=1, oberbegriff="Galaxis", beschreibung="Text")
    insert = [c for c in calls if "INSERT INTO seminarthema" in c[0]]
    assert len(insert) == 1
    query, params = insert[0]
    assert "%s" in query
    assert SQLI_DROP not in query
    assert SQLI_DROP in params


# ---------------------------------------------------------------------------
# Test 8 (SQLi): thema_bearbeiten nutzt ein parametrisiertes UPDATE.
# ---------------------------------------------------------------------------
def test_sqli_thema_bearbeiten_parametrisiert(fake_db):
    calls = fake_db()
    queries.thema_bearbeiten(1, SQLI_DROP, d_id=1, oberbegriff="O", beschreibung="B",
                             s_id=None, status="Frei", semester=6, pdf_pfad=None, vorgetragen=False)
    update = [c for c in calls if "UPDATE seminarthema" in c[0]]
    assert len(update) == 1
    query, params = update[0]
    assert "%s" in query
    assert SQLI_DROP not in query
    assert SQLI_DROP in params


# ---------------------------------------------------------------------------
# Test 9 (SQLi): get_seminarthema und student_hinzufuegen sind parametrisiert.
# ---------------------------------------------------------------------------
def test_sqli_lese_und_belegen_parametrisiert(fake_db):
    calls = fake_db(results=[None])  # get_seminarthema fetchone
    queries.get_seminarthema(SQLI_PAYLOAD)
    queries.student_hinzufuegen(SQLI_PAYLOAD, s_id=5, status="Vergeben")

    for query, params in calls:
        assert "%s" in query
        assert SQLI_PAYLOAD not in query
        assert SQLI_PAYLOAD in (params or ())


# ---------------------------------------------------------------------------
# Test 10 (SQLi): End-to-End ueber die Uebersichts-Route. Ein Injection-
# Suchbegriff wird bis in die DB-Schicht nur als Parameter durchgereicht.
# ---------------------------------------------------------------------------
def test_sqli_uebersicht_route_end_to_end(client, monkeypatch, fake_db):
    monkeypatch.setattr("themen.routes.hole_user_und_rolle", lambda: (5, "stud"))
    # Dropdown-Queries neutralisieren, damit nur die Filter-Query die Fake-DB trifft.
    monkeypatch.setattr("themen.routes.get_semester", lambda: [])
    monkeypatch.setattr("themen.routes.get_dozierenden", lambda: [])
    monkeypatch.setattr("themen.routes.get_status_optionen", lambda: [])
    calls = fake_db()  # get_seminarthemen_by_filter laeuft echt gegen die Fake-DB
    login_as(client, 5)

    resp = client.get("/themen/uebersicht", query_string={"titel": SQLI_PAYLOAD})
    assert resp.status_code == 200  # keine Server-Exception

    select = [c for c in calls if "FROM seminarthema" in c[0]]
    assert len(select) == 1
    query, params = select[0]
    assert "ILIKE %s" in query
    assert SQLI_PAYLOAD not in query
    assert f"%{SQLI_PAYLOAD}%" in params
