#Author Deniz Rahnefeld (409637)
#
# SCHRITT 2 - Funktionale Tests des auth-Bereichs.
#
# Geprueft werden die funktionalen Anforderungen der Spezifikation:
#   ANF 1: Benutzerregistrierung und -anmeldung
#   ANF 2: Profil (Aenderung nur nach Authentifizierung)
#   ANF 3: Login (Kombination aus E-Mail und Passwort)
#
# Hier geht es AUSSCHLIESSLICH um funktionale Korrektheit, nicht um Sicherheit.
# Alle DB-Zugriffe sind gemockt (siehe conftest.py).

import hashlib

from auth.utils import (
    check_register_input,
    validate_register,
    check_login_input,
    validate_login,
    hash_passwort,
)


# --- Basisdaten fuer eine gueltige Registrierung -----------------------------
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


# ---------------------------------------------------------------------------
# Test 1 (ANF 1/3): hash_passwort erzeugt einen korrekten, stabilen SHA-256-Hash.
# Der Login vergleicht Hashes, daher muss diese Funktion deterministisch sein.
# ---------------------------------------------------------------------------
def test_hash_passwort_ist_korrekter_sha256():
    passwort = "Passwort!123"
    erwartet = hashlib.sha256(passwort.encode("utf-8")).hexdigest()
    assert hash_passwort(passwort) == erwartet
    # Gleiche Eingabe -> gleicher Hash (deterministisch)
    assert hash_passwort(passwort) == hash_passwort(passwort)
    # Unterschiedliche Passwoerter -> unterschiedliche Hashes
    assert hash_passwort("Passwort!123") != hash_passwort("Passwort!124")


# ---------------------------------------------------------------------------
# Test 2 (ANF 1): Leere Pflichtfelder bei der Registrierung werden erkannt.
# ---------------------------------------------------------------------------
def test_check_register_input_erkennt_leere_pflichtfelder():
    data = valid_register_data(vorname="", email="   ")  # nur Leerzeichen
    empty_found, leere_felder = check_register_input(data)
    assert empty_found is True
    assert "vorname" in leere_felder
    assert "email" in leere_felder
    # Vollstaendige Daten -> keine leeren Felder
    empty_found2, leere_felder2 = check_register_input(valid_register_data())
    assert empty_found2 is False
    assert leere_felder2 == []


# ---------------------------------------------------------------------------
# Test 3 (ANF 1): Eine vollstaendig korrekte Registrierung wird akzeptiert.
# check_matr_nr/check_seminarthema werden gemockt (kein DB-Zugriff).
# ---------------------------------------------------------------------------
def test_validate_register_akzeptiert_gueltige_daten(monkeypatch):
    monkeypatch.setattr("auth.queries.check_matr_nr", lambda *a, **k: False)
    monkeypatch.setattr("auth.queries.check_seminarthema", lambda *a, **k: True)

    valid, messages = validate_register(valid_register_data())
    assert valid is True, f"Erwartet gueltig, aber: {messages}"
    assert messages == []


# ---------------------------------------------------------------------------
# Test 4 (ANF 1): Namensregeln (Grossbuchstabe am Anfang, Bindestrich/Leerzeichen).
# ---------------------------------------------------------------------------
def test_validate_register_namensregeln(monkeypatch):
    monkeypatch.setattr("auth.queries.check_matr_nr", lambda *a, **k: False)
    monkeypatch.setattr("auth.queries.check_seminarthema", lambda *a, **k: True)

    # Gueltige Namen laut Spezifikation (Ann-Kathrin, Jakob Michael)
    ok, _ = validate_register(valid_register_data(vorname="Ann-Kathrin", nachname="Jakob Michael"))
    assert ok is True

    # Kleinbuchstabe am Anfang -> ungueltig
    bad, msgs = validate_register(valid_register_data(vorname="max"))
    assert bad is False
    assert any("Vorname" in m for m in msgs)

    # Ziffern im Namen -> ungueltig
    bad2, _ = validate_register(valid_register_data(nachname="Muster3"))
    assert bad2 is False


# ---------------------------------------------------------------------------
# Test 5 (ANF 1): Matrikelnummer muss aus 6-8 Ziffern bestehen.
# ---------------------------------------------------------------------------
def test_validate_register_matrikelnummer(monkeypatch):
    monkeypatch.setattr("auth.queries.check_matr_nr", lambda *a, **k: False)
    monkeypatch.setattr("auth.queries.check_seminarthema", lambda *a, **k: True)

    for gut in ["123456", "12345678"]:
        ok, _ = validate_register(valid_register_data(matr_nr=gut))
        assert ok is True, f"{gut} sollte gueltig sein"

    for schlecht in ["12345", "123456789", "12a456", ""]:
        bad, msgs = validate_register(valid_register_data(matr_nr=schlecht))
        assert bad is False, f"{schlecht} sollte ungueltig sein"


# ---------------------------------------------------------------------------
# Test 6 (ANF 1): E-Mail- und Passwortregeln aus den Spezifikations-Fussnoten.
# ---------------------------------------------------------------------------
def test_validate_register_email_und_passwort(monkeypatch):
    monkeypatch.setattr("auth.queries.check_matr_nr", lambda *a, **k: False)
    monkeypatch.setattr("auth.queries.check_seminarthema", lambda *a, **k: True)

    # Lokaler Teil laenger als 63 Zeichen -> ungueltig
    langer_lokalteil = "a" * 64 + "@uni.de"
    bad_mail, _ = validate_register(valid_register_data(email=langer_lokalteil))
    assert bad_mail is False

    # Grossbuchstaben in der E-Mail sind laut Spezifikation nicht erlaubt
    bad_mail2, _ = validate_register(valid_register_data(email="Max@uni.de"))
    assert bad_mail2 is False

    # Passwort ohne Sonderzeichen -> ungueltig
    bad_pw, msgs = validate_register(valid_register_data(passwort="Passwort123", passwort_wiederholen="Passwort123"))
    assert bad_pw is False
    assert any("Passwort" in m for m in msgs)


# ---------------------------------------------------------------------------
# Test 7 (ANF 1): Nicht uebereinstimmende Passwoerter werden abgelehnt;
# ungueltige Auswahlwerte (Seminar/Studiengang/Abschluss) ebenfalls.
# ---------------------------------------------------------------------------
def test_validate_register_passwortwiederholung_und_auswahlwerte(monkeypatch):
    monkeypatch.setattr("auth.queries.check_matr_nr", lambda *a, **k: False)
    monkeypatch.setattr("auth.queries.check_seminarthema", lambda *a, **k: True)

    bad_pw, msgs = validate_register(valid_register_data(passwort_wiederholen="Anderes!123"))
    assert bad_pw is False
    assert any("stimmen nicht" in m for m in msgs)

    for feld, wert in [("bel_seminar", "XYZ"), ("studiengang_name", "JURA"), ("abschluss", "Diplom")]:
        bad, _ = validate_register(valid_register_data(**{feld: wert}))
        assert bad is False, f"{feld}={wert} sollte ungueltig sein"


# ---------------------------------------------------------------------------
# Test 8 (ANF 1): Bereits vergebene Matrikelnummer wird abgelehnt.
# ---------------------------------------------------------------------------
def test_validate_register_doppelte_matrikelnummer(monkeypatch):
    # check_matr_nr liefert True -> Nummer existiert bereits
    monkeypatch.setattr("auth.queries.check_matr_nr", lambda *a, **k: True)
    monkeypatch.setattr("auth.queries.check_seminarthema", lambda *a, **k: True)

    bad, msgs = validate_register(valid_register_data())
    assert bad is False
    assert any("existiert bereits" in m for m in msgs)


# ---------------------------------------------------------------------------
# Test 9 (ANF 3): Login-Eingabevalidierung (Format von E-Mail und Passwort).
# ---------------------------------------------------------------------------
def test_login_eingabepruefung():
    # Leere Felder werden erkannt
    empty, felder = check_login_input({"email": "", "passwort": ""})
    assert empty is True
    assert "email" in felder and "passwort" in felder

    # Gueltiges Format
    ok, _ = validate_login({"email": "max@uni.de", "passwort": "Passwort!123"})
    assert ok is True

    # Ungueltiges Format
    bad, _ = validate_login({"email": "keine-mail", "passwort": "schwach"})
    assert bad is False


# ---------------------------------------------------------------------------
# Test 10 (ANF 3): Erfolgreicher Login setzt die Session und leitet zum Profil.
# check_account/check_password werden gemockt.
# ---------------------------------------------------------------------------
def test_login_route_erfolgreich_setzt_session(client, monkeypatch):
    monkeypatch.setattr("auth.routes.check_account", lambda data: True)
    monkeypatch.setattr("auth.routes.check_password", lambda email, pw: 42)

    resp = client.post(
        "/login",
        data={"email": "max@uni.de", "passwort": "Passwort!123"},
    )
    # Weiterleitung auf die Profilseite
    assert resp.status_code == 302
    assert "/profile" in resp.headers["Location"]
    with client.session_transaction() as sess:
        assert sess["user_id"] == 42


# ---------------------------------------------------------------------------
# Test 10b als eigener Fall (ANF 3): Falsches Passwort -> keine Session.
# ---------------------------------------------------------------------------
def test_login_route_falsches_passwort(client, monkeypatch):
    monkeypatch.setattr("auth.routes.check_account", lambda data: True)
    monkeypatch.setattr("auth.routes.check_password", lambda email, pw: None)

    resp = client.post(
        "/login",
        data={"email": "max@uni.de", "passwort": "Passwort!123"},
    )
    assert resp.status_code == 200  # bleibt auf der Login-Seite
    assert "Passwort ist falsch".encode() in resp.data
    with client.session_transaction() as sess:
        assert "user_id" not in sess
