#Author Deniz Rahnefeld (409637)
#
# SCHRITT 2 - Funktionale Tests des themen-Bereichs.
#
# Geprueft werden die funktionalen Anforderungen der Spezifikation:
#   ANF 4: Seminarthemen ansehen und belegen (Studierende + Dozenten)
#   ANF 5: Seminarthemen filtern (Textsuche case-insensitive + Wildcard, Dropdowns)
#   ANF 7: Seminarthemen verwalten (nur Dozenten; Pflichtfelder Titel/Oberbegriff/Beschreibung)
#
# Hier geht es AUSSCHLIESSLICH um funktionale Korrektheit, nicht um Sicherheit.
# Alle DB-Zugriffe sind gemockt (siehe conftest.py).

from unittest.mock import MagicMock

from themen import queries
from themen.utils import (
    validiere_thema_form,
    ist_gueltige_dozent_id,
    ist_gueltiges_pdf,
    ist_gueltiges_semester,
    pruefe_dozent,
    pruefe_student,
    thema_belegen_status_pruefen,
)

DOZIERENDE = [{"d_id": 1, "vorname": "Klaus-Dieter", "nachname": "Althoff"},
              {"d_id": 2, "vorname": "Pascal", "nachname": "Reuss"}]


def login_as(client, user_id=1):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


# ---------------------------------------------------------------------------
# Test 1 (ANF 7): validiere_thema_form prueft die Pflichtfelder (Whitespace),
# Feldlaengen und den gueltigen Dozenten.
# Hinweis: Ein komplett LEERES Feld ("") wird von ist_gueltiger_text bewusst
# als gueltig behandelt - das eigentliche Pflichtfeld-Verbot erzwingt der
# Route-Guard (if not titel ...), siehe test_thema_anlegen_post. Siehe auch
# den Analyse-Hinweis im Chat.
# ---------------------------------------------------------------------------
def test_validiere_thema_form_pflichtfelder():
    # Vollstaendig gueltig -> None (kein Fehler)
    assert validiere_thema_form("Titel", "Oberbegriff", "Beschreibung",
                                d_id=1, semester="3", pdf_dateiname=None,
                                dozierenden_liste=DOZIERENDE) is None

    # Pflichtfeld nur aus Leerzeichen -> Fehlermeldung
    assert validiere_thema_form("   ", "Oberbegriff", "Beschreibung", 1, "3", None, DOZIERENDE)
    assert validiere_thema_form("Titel", "   ", "Beschreibung", 1, "3", None, DOZIERENDE)
    assert validiere_thema_form("Titel", "Oberbegriff", "   ", 1, "3", None, DOZIERENDE)

    # Zu langer Titel (> 255 Zeichen) -> Fehlermeldung
    assert validiere_thema_form("x" * 256, "Oberbegriff", "Beschreibung", 1, "3", None, DOZIERENDE)

    # Ungueltiger Dozent -> Fehlermeldung
    assert validiere_thema_form("Titel", "Oberbegriff", "Beschreibung", 999, "3", None, DOZIERENDE)


# ---------------------------------------------------------------------------
# Test 2 (ANF 7): Nur eine existierende, gueltige Dozenten-ID wird akzeptiert.
# ---------------------------------------------------------------------------
def test_ist_gueltige_dozent_id():
    assert ist_gueltige_dozent_id(1, DOZIERENDE) is True
    assert ist_gueltige_dozent_id("2", DOZIERENDE) is True   # String wird konvertiert
    assert ist_gueltige_dozent_id(999, DOZIERENDE) is False  # existiert nicht
    assert ist_gueltige_dozent_id("abc", DOZIERENDE) is False
    assert ist_gueltige_dozent_id(None, DOZIERENDE) is False


# ---------------------------------------------------------------------------
# Test 3 (ANF 7): Optionale Felder - PDF nur .pdf, Semester optional/ganzzahlig.
# ---------------------------------------------------------------------------
def test_optionale_felder_pdf_und_semester():
    assert ist_gueltiges_pdf(None) is True          # kein Upload erlaubt
    assert ist_gueltiges_pdf("thema.pdf") is True
    assert ist_gueltiges_pdf("thema.PDF") is True    # Gross-/Kleinschreibung egal
    assert ist_gueltiges_pdf("schadcode.exe") is False

    assert ist_gueltiges_semester("") is True        # optional
    assert ist_gueltiges_semester("3") is True
    assert ist_gueltiges_semester("3.5") is False    # keine Kommazahl
    assert ist_gueltiges_semester("abc") is False


# ---------------------------------------------------------------------------
# Test 4 (ANF 7): Rollenpruefung - nur Dozenten duerfen verwalten.
# ---------------------------------------------------------------------------
def test_rollenpruefung():
    assert pruefe_dozent(1, "doz") is True
    assert pruefe_dozent(1, "stud") is False   # Student ist kein Dozent
    assert pruefe_dozent(None, "doz") is False # nicht eingeloggt
    assert pruefe_student("stud") is True
    assert pruefe_student("doz") is False


# ---------------------------------------------------------------------------
# Test 5 (ANF 7): "Thema anlegen" ist fuer Studierende gesperrt, fuer Dozenten
# wird das Formular mit dem Dozenten-Dropdown angezeigt.
# ---------------------------------------------------------------------------
def test_thema_anlegen_seite_nur_fuer_dozent(client, monkeypatch):
    # Als Student -> Weiterleitung zur Startseite
    monkeypatch.setattr("themen.routes.hole_user_und_rolle", lambda: (5, "stud"))
    resp_stud = client.get("/themen/neu")
    assert resp_stud.status_code == 302
    assert "index" in resp_stud.headers["Location"] or resp_stud.headers["Location"].endswith("/")

    # Als Dozent -> Formular mit Dozentenauswahl
    monkeypatch.setattr("themen.routes.hole_user_und_rolle", lambda: (1, "doz"))
    monkeypatch.setattr("themen.routes.get_dozierenden", lambda: DOZIERENDE)
    resp_doz = client.get("/themen/neu")
    assert resp_doz.status_code == 200
    assert "Althoff" in resp_doz.data.decode()


# ---------------------------------------------------------------------------
# Test 6 (ANF 7): Gueltiger POST legt ein Thema an; fehlendes Pflichtfeld nicht.
# ---------------------------------------------------------------------------
def test_thema_anlegen_post(client, monkeypatch):
    monkeypatch.setattr("themen.routes.hole_user_und_rolle", lambda: (1, "doz"))
    monkeypatch.setattr("themen.routes.get_dozierenden", lambda: DOZIERENDE)
    monkeypatch.setattr("themen.routes.speichere_pdf", lambda pdf: None)
    anlegen_mock = MagicMock()
    monkeypatch.setattr("themen.routes.thema_anlegen", anlegen_mock)

    # Gueltig -> gespeichert + Redirect zur Uebersicht
    resp_ok = client.post("/themen/neu", data={
        "titel": "Star Wars", "oberbegriff": "Galaxis",
        "beschreibung": "Beschreibe die Schlacht", "d_id": "1", "semester": "6",
    })
    assert resp_ok.status_code == 302
    assert "uebersicht" in resp_ok.headers["Location"]
    anlegen_mock.assert_called_once()

    # Titel fehlt -> nicht gespeichert, Formular mit Fehler
    anlegen_mock.reset_mock()
    resp_bad = client.post("/themen/neu", data={
        "titel": "", "oberbegriff": "Galaxis", "beschreibung": "Text", "d_id": "1",
    })
    assert resp_bad.status_code == 200
    anlegen_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Test 7 (ANF 4): Die Themenuebersicht erfordert Login und listet Themen auf.
# ---------------------------------------------------------------------------
def test_themen_uebersicht_login_und_liste(client, monkeypatch):
    # Nicht eingeloggt -> Weiterleitung
    monkeypatch.setattr("themen.routes.hole_user_und_rolle", lambda: (None, None))
    assert client.get("/themen/uebersicht").status_code == 302

    # Eingeloggt -> Liste sichtbar
    monkeypatch.setattr("themen.routes.hole_user_und_rolle", lambda: (5, "stud"))
    monkeypatch.setattr("themen.routes.get_seminarthemen_by_filter",
        lambda *a, **k: [{"themen_id": 1, "titel": "Star Wars", "semester": 6,
                          "status": "Frei", "doz_vorname": "Pascal", "doz_nachname": "Reuss"}])
    monkeypatch.setattr("themen.routes.get_semester", lambda: [{"semester": 6}])
    monkeypatch.setattr("themen.routes.get_dozierenden", lambda: DOZIERENDE)
    monkeypatch.setattr("themen.routes.get_status_optionen", lambda: [{"status": "Frei"}])

    resp = client.get("/themen/uebersicht")
    assert resp.status_code == 200
    assert "Star Wars" in resp.data.decode()


# ---------------------------------------------------------------------------
# Test 8 (ANF 4): Ein Studierender belegt ein freies Thema -> es wird belegt.
# ---------------------------------------------------------------------------
def test_thema_belegen_erfolgreich(client, monkeypatch):
    monkeypatch.setattr("themen.routes.hole_user_und_rolle", lambda: (5, "stud"))
    monkeypatch.setattr("themen.routes.get_seminarthema",
        lambda tid: {"themen_id": 1, "s_id": None, "status": "Frei"})
    # Student hat noch kein Thema und das Thema ist frei
    monkeypatch.setattr("themen.routes.thema_belegen_status_pruefen", lambda thema: True)
    monkeypatch.setattr("themen.routes.thema_belegen_s_id_pruefen", lambda uid: True)
    hinzu_mock = MagicMock(return_value=True)
    monkeypatch.setattr("themen.routes.student_hinzufuegen", hinzu_mock)

    resp = client.post("/themen/thema_detail/1")
    assert resp.status_code == 302  # zurueck zur Detailansicht
    hinzu_mock.assert_called_once_with(1, 5, "Vergeben")


# ---------------------------------------------------------------------------
# Test 9 (ANF 4): Belegungsregeln - freies Thema ist belegbar, belegtes nicht;
# ein Student mit bereits belegtem Thema darf kein weiteres belegen.
# ---------------------------------------------------------------------------
def test_belegungsregeln(fake_db):
    # thema_belegen_status_pruefen: nur 'Frei' ohne Student ist belegbar
    assert thema_belegen_status_pruefen({"s_id": None, "status": "Frei"}) is True
    assert thema_belegen_status_pruefen({"s_id": 3, "status": "Vergeben"}) is False

    # thema_belegen_s_id_pruefen: Student (id 5) hat bereits ein Thema -> False
    from themen.utils import thema_belegen_s_id_pruefen
    fake_db(results=[[{"s_id": 5}, {"s_id": 7}]])  # get_sid_aus_themen -> belegte s_ids
    assert thema_belegen_s_id_pruefen(5) is False   # 5 ist schon vergeben
    fake_db(results=[[{"s_id": 7}]])
    assert thema_belegen_s_id_pruefen(5) is True    # 5 noch frei


# ---------------------------------------------------------------------------
# Test 10 (ANF 5): Der Textfilter nutzt ILIKE (case-insensitive) mit Wildcards,
# Dropdown-Filter nutzen Gleichheit. Ohne Filter gibt es keine WHERE-Klausel.
# ---------------------------------------------------------------------------
def test_filter_query_ilike_und_gleichheit(fake_db):
    # Mit Titelfilter -> ILIKE + %wert%
    calls = fake_db()
    queries.get_seminarthemen_by_filter(titel="krypto")
    query, params = calls[-1]
    assert "ILIKE %s" in query
    assert "%krypto%" in params      # Wildcards liegen im Parameter, Suche unscharf

    # Mit Semester -> Gleichheit
    calls2 = fake_db()
    queries.get_seminarthemen_by_filter(semester=6, status="Frei")
    query2, params2 = calls2[-1]
    assert "sem.semester = %s" in query2
    assert 6 in params2 and "Frei" in params2

    # Ganz ohne Filter -> keine WHERE-Klausel
    calls3 = fake_db()
    queries.get_seminarthemen_by_filter()
    query3, _ = calls3[-1]
    assert "WHERE" not in query3
