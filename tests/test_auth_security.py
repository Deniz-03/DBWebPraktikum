#Author Deniz Rahnefeld (409637)
#
# SCHRITT 3 - Sicherheitstests des auth-Bereichs.
#
# Geprueft werden ausschliesslich die fuer das Uniprojekt geforderten Aspekte:
#   - Schutz vor Cross-Site-Scripting (XSS)
#   - Schutz vor SQL-Injection
#
# XSS wird ueber das Autoescaping von Jinja2 verhindert: Nutzereingaben, die
# ins HTML zurueckgespiegelt werden, muessen escaped erscheinen (z.B. &lt;script&gt;).
#
# SQL-Injection wird durch parametrisierte Queries (psycopg %s + Parameter-Tupel)
# verhindert: Die Fake-DB (conftest.py) zeichnet jeden execute()-Aufruf auf, so
# dass geprueft werden kann, dass boesartige Eingaben NUR als Parameter und nie
# per String-Verkettung in die Query gelangen.

from auth.utils import validate_login, validate_register
from auth import queries


XSS_PAYLOAD = "<script>alert('xss')</script>"
SQLI_PAYLOAD = "' OR '1'='1"
SQLI_DROP = "x@uni.de'; DROP TABLE account; --"


def valid_register_data(**overrides):
    data = {
        "vorname": "Max",
        "nachname": "Mustermann",
        "matr_nr": "123456",
        "email": "max@mustermail.de",
        "passwort": "Passwort!123",
        "passwort_wiederholen": "Passwort!123",
        "bel_seminar": "IIS",
        "studiengang_name": "WINF",
        "abschluss": "B.Sc",
        "seminar_thema": "",
    }
    data.update(overrides)
    return data


# ===========================================================================
# XSS-Tests
# ===========================================================================

# ---------------------------------------------------------------------------
# Test 1 (XSS): Die Login-Seite spiegelt die eingegebene E-Mail zurueck.
# Ein <script>-Payload muss escaped erscheinen, nicht als aktives Tag.
# ---------------------------------------------------------------------------
def test_xss_login_email_wird_escaped(client):
    # Ungueltiges Format -> validate_login schlaegt fehl -> Seite wird mit
    # den eingegebenen Werten neu gerendert (values=data).
    resp = client.post("/login", data={"email": XSS_PAYLOAD, "passwort": "Passwort!123"})
    body = resp.data.decode()
    # Roher Script-Tag darf NICHT im HTML stehen ...
    assert "<script>alert('xss')</script>" not in body
    # ... sondern nur die escapte Variante.
    assert "&lt;script&gt;" in body


# ---------------------------------------------------------------------------
# Test 2 (XSS): Registrierungsformular spiegelt Felder zurueck (z.B. vorname).
# ---------------------------------------------------------------------------
def test_xss_register_feld_wird_escaped(client, monkeypatch):
    monkeypatch.setattr("auth.routes.get_free_seminarthemen", lambda: [])
    # validate_register prueft intern die Matrikelnummer gegen die DB -> mocken.
    monkeypatch.setattr("auth.queries.check_matr_nr", lambda *a, **k: False)
    # Payload im Vornamen; validate_register schlaegt fehl -> Re-Render mit values.
    payload = '"><script>alert(1)</script>'
    resp = client.post("/register", data=valid_register_data(vorname=payload))
    body = resp.data.decode()
    assert "<script>alert(1)</script>" not in body
    assert "&lt;script&gt;" in body


# ---------------------------------------------------------------------------
# Test 3 (XSS): Auch der Ausbruch aus dem value-Attribut ist nicht moeglich,
# denn Anfuehrungszeichen werden ebenfalls escaped.
# ---------------------------------------------------------------------------
def test_xss_attribut_ausbruch_nicht_moeglich(client):
    payload = '" onmouseover="alert(1)'
    resp = client.post("/login", data={"email": payload, "passwort": "Passwort!123"})
    body = resp.data.decode()
    # Das rohe schliessende Anfuehrungszeichen + Event-Handler darf nicht
    # als eigenstaendiges Attribut im input-Tag erscheinen.
    assert 'onmouseover="alert(1)"' not in body
    assert "&#34;" in body or "&quot;" in body


# ---------------------------------------------------------------------------
# Test 4 (XSS): Studenten-Profil escaped die (aus der DB geladenen) Namen.
# get_user_info wird mit einem boesartigen Namen gemockt.
# ---------------------------------------------------------------------------
def test_xss_profil_escaped_namen(client, monkeypatch):
    monkeypatch.setattr("auth.routes.get_user_role", lambda uid: "stud")
    monkeypatch.setattr("auth.routes.get_bew_vortrag_for_display", lambda uid: None)
    monkeypatch.setattr(
        "auth.routes.get_user_info",
        lambda uid: {
            "vorname": XSS_PAYLOAD,
            "nachname": "Mustermann",
            "matr_nr": "123456",
            "studiengang_name": "WINF",
            "abschluss": "B.Sc",
            "bel_seminar": "IIS",
            "email": "max@uni.de",
            "titel": None,
            "user_id": 1,
        },
    )
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    resp = client.get("/profile")
    body = resp.data.decode()
    assert "<script>alert('xss')</script>" not in body
    assert "&lt;script&gt;" in body


# ---------------------------------------------------------------------------
# Test 5 (XSS): Die Dozenten-Uebersicht der Studierenden escaped Namen.
# ---------------------------------------------------------------------------
def test_xss_stud_profiles_liste_escaped(client, monkeypatch):
    monkeypatch.setattr("auth.routes.get_user_role", lambda uid: "doz")
    monkeypatch.setattr(
        "auth.routes.get_all_stud",
        lambda: [{"s_id": 1, "vorname": XSS_PAYLOAD, "nachname": "Test"}],
    )
    with client.session_transaction() as sess:
        sess["user_id"] = 1

    resp = client.get("/profiles")
    body = resp.data.decode()
    assert "<script>alert('xss')</script>" not in body
    assert "&lt;script&gt;" in body


# ===========================================================================
# SQL-Injection-Tests
# ===========================================================================

# ---------------------------------------------------------------------------
# Test 6 (SQLi): Klassische Injection-Payload in der E-Mail wird bereits von
# der Eingabevalidierung abgelehnt (erreicht die DB gar nicht erst).
# ---------------------------------------------------------------------------
def test_sqli_login_validierung_lehnt_payload_ab():
    ok, _ = validate_login({"email": SQLI_PAYLOAD, "passwort": "Passwort!123"})
    assert ok is False
    ok2, _ = validate_login({"email": SQLI_DROP, "passwort": "Passwort!123"})
    assert ok2 is False


# ---------------------------------------------------------------------------
# Test 7 (SQLi): Injection-Payload in Registrierungsfeldern wird abgelehnt.
# ---------------------------------------------------------------------------
def test_sqli_register_validierung_lehnt_payload_ab(monkeypatch):
    monkeypatch.setattr("auth.queries.check_matr_nr", lambda *a, **k: False)
    monkeypatch.setattr("auth.queries.check_seminarthema", lambda *a, **k: True)

    bad_name, _ = validate_register(valid_register_data(vorname="Robert'); DROP TABLE studierende;--"))
    assert bad_name is False
    bad_matr, _ = validate_register(valid_register_data(matr_nr="1 OR 1=1"))
    assert bad_matr is False


# ---------------------------------------------------------------------------
# Test 8 (SQLi): check_password nutzt parametrisierte Queries.
# Die boesartige E-Mail darf nur als Parameter, nie in der Query stehen.
# ---------------------------------------------------------------------------
def test_sqli_check_password_ist_parametrisiert(fake_db):
    # Ergebnis der ersten SELECT-Abfrage: ein (nicht passender) Hash.
    calls = fake_db(results=[{"passwort": "irgendein_hash"}])

    queries.check_password(SQLI_DROP, "Passwort!123")

    assert len(calls) >= 1
    query, params = calls[0]
    # Platzhalter statt eingebauter Wert
    assert "%s" in query
    # Der Payload darf NICHT im Query-String stehen ...
    assert SQLI_DROP not in query
    assert "DROP TABLE" not in query.upper()
    # ... sondern ausschliesslich als Parameter uebergeben werden.
    assert params == (SQLI_DROP,)


# ---------------------------------------------------------------------------
# Test 9 (SQLi): check_account und check_matr_nr sind ebenfalls parametrisiert.
# ---------------------------------------------------------------------------
def test_sqli_check_account_und_matr_nr_parametrisiert(fake_db):
    calls = fake_db(results=[None, None])

    queries.check_account({"email": SQLI_PAYLOAD})
    queries.check_matr_nr(SQLI_PAYLOAD)

    assert len(calls) == 2
    for query, params in calls:
        assert "%s" in query
        assert SQLI_PAYLOAD not in query
        # Der Payload steckt genau im Parameter-Tupel.
        assert SQLI_PAYLOAD in params


# ---------------------------------------------------------------------------
# Test 10 (SQLi): End-to-End ueber die Login-Route. Der Payload gelangt nur
# als Parameter in die DB und die Anmeldung schlaegt sauber fehl (kein 500).
# ---------------------------------------------------------------------------
def test_sqli_login_route_end_to_end(client, fake_db):
    # Format-gueltige E-Mail, die nur die erlaubten Zeichen (a-z . + -) enthaelt
    # und daher die Validierung passiert und die DB-Schicht tatsaechlich erreicht.
    # Selbst dieser Wert wird ausschliesslich als Parameter uebergeben.
    email = "or.true--drop@uni.de"
    calls = fake_db(results=[{"email": email}, {"passwort": "anderer_hash"}])

    resp = client.post("/login", data={"email": email, "passwort": "Passwort!123"})

    # Keine Server-Exception
    assert resp.status_code in (200, 302)
    # Alle abgesetzten Queries sind parametrisiert und enthalten den Wert
    # nicht als eingebauten String.
    assert len(calls) >= 1
    for query, params in calls:
        assert "%s" in query
        assert email not in query
