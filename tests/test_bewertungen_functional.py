#Author Deniz Rahnefeld (409637)
#
# SCHRITT 2 - Funktionale Tests des bewertungen-Bereichs.
#
# Geprueft werden die funktionalen Anforderungen der Spezifikation:
#   ANF 6: Vortrag bewerten (Studierende UND Dozenten, Skala --,-,o,+,++, 9 Kriterien)
#   ANF 8: Ausarbeitung bewerten (nur Dozenten, 5 Kriterien)
#   ANF 9: Seminarleistung bewerten (nur Dozenten, Notenskala 1.0-5.0)
#
# Hier geht es AUSSCHLIESSLICH um funktionale Korrektheit, nicht um Sicherheit.
# Alle DB-Zugriffe sind gemockt (siehe conftest.py).

from unittest.mock import MagicMock

from bewertungen import queries
from bewertungen.queries import SKALA_LABELS


def login_as(client, user_id=1):
    """Setzt eine user_id in die Session (simuliert einen eingeloggten Nutzer)."""
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


# ---------------------------------------------------------------------------
# Test 1 (ANF 6/8): Die Bewertungsskala bildet 1..5 korrekt auf --,-,o,+,++ ab.
# ---------------------------------------------------------------------------
def test_skala_labels_mapping():
    assert SKALA_LABELS == {1: "--", 2: "-", 3: "o", 4: "+", 5: "++"}


# ---------------------------------------------------------------------------
# Test 2 (ANF 6): get_vortragsstatistiken liefert Anzahl + Durchschnitte und
# wandelt die gerundeten Zahlen in die Symbole der Skala um.
# ---------------------------------------------------------------------------
def test_vortragsstatistik_wandelt_durchschnitte_in_symbole(fake_db):
    fake_db(results=[{
        "anzahl_bewertungen": 3,
        "foliengestaltung": 4,          # -> +
        "sprachliche_praesentation": 5, # -> ++
        "stil": 3,                      # -> o
        "zeitliche_gestaltung": 1,      # -> --
        "verstaendnis": 2,              # -> -
        "inhalt": 4,
        "verknuepfung": 3,
        "diskussion": 4,
        "beteiligung": 5,
    }])

    stat = queries.get_vortragsstatistiken(1)
    assert stat["anzahl_bewertungen"] == 3
    assert stat["foliengestaltung"] == "+"
    assert stat["sprachliche_praesentation"] == "++"
    assert stat["stil"] == "o"
    assert stat["zeitliche_gestaltung"] == "--"
    assert stat["verstaendnis"] == "-"


# ---------------------------------------------------------------------------
# Test 3 (ANF 6): Ein Studierender darf das Vortragsformular sehen. Alle 9
# Kriterien werden angezeigt (Studierende UND Dozenten duerfen bewerten).
# ---------------------------------------------------------------------------
def test_vortrag_formular_zeigt_alle_kriterien_fuer_studierende(client, monkeypatch):
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "stud")
    monkeypatch.setattr(
        "bewertungen.routes.get_bewertbare_vortraege",
        lambda exclude_account_id=None: [
            {"t_id": 1, "titel": "Star Wars", "vorname": "Max", "nachname": "Mustermann"}
        ],
    )
    login_as(client, 5)

    resp = client.get("/bewertungen/vortrag")
    body = resp.data.decode()
    assert resp.status_code == 200
    # Stichproben aus den 9 Vortragskriterien (ANF 6)
    for label in ["Foliengestaltung", "Verständnis", "Beteiligung an Diskussionen"]:
        assert label in body
    # Die Skala-Symbole sind vorhanden
    assert "++" in body


# ---------------------------------------------------------------------------
# Test 4 (ANF 6): Ein gueltiger Vortrags-POST speichert die Bewertung
# (alle 9 Kriterien + Kommentar) und leitet weiter.
# ---------------------------------------------------------------------------
def test_vortrag_post_speichert_bewertung(client, monkeypatch):
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "stud")
    monkeypatch.setattr("bewertungen.routes.ist_vortrag_bewertbar", lambda t, u: True)
    monkeypatch.setattr("bewertungen.routes.ist_eigener_vortrag", lambda t, u: False)

    captured = {}

    def fake_create(data):
        captured["data"] = data
        return True

    monkeypatch.setattr("bewertungen.routes.create_bew_vortrag", fake_create)
    login_as(client, 5)

    form = {
        "t_id": "1",
        "foliengestaltung": "4", "sprachliche_praesentation": "5", "stil": "3",
        "zeitliche_gestaltung": "2", "verstaendnis": "4", "inhalt": "3",
        "verknuepfung": "4", "diskussion": "5", "beteiligung": "3",
        "kommentar": "Guter Vortrag",
    }
    resp = client.post("/bewertungen/vortrag", data=form)

    assert resp.status_code == 302  # Weiterleitung nach erfolgreicher Speicherung
    # Alle 9 Kriterien wurden als int uebergeben
    for feld in ["foliengestaltung", "sprachliche_praesentation", "stil",
                 "zeitliche_gestaltung", "verstaendnis", "inhalt",
                 "verknuepfung", "diskussion", "beteiligung"]:
        assert isinstance(captured["data"][feld], int)
    assert captured["data"]["kommentar"] == "Guter Vortrag"


# ---------------------------------------------------------------------------
# Test 5 (ANF 6): Man kann den EIGENEN Vortrag nicht bewerten.
# ---------------------------------------------------------------------------
def test_vortrag_post_eigener_vortrag_wird_abgelehnt(client, monkeypatch):
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "stud")
    monkeypatch.setattr("bewertungen.routes.ist_vortrag_bewertbar", lambda t, u: True)
    monkeypatch.setattr("bewertungen.routes.ist_eigener_vortrag", lambda t, u: True)
    create_mock = MagicMock()
    monkeypatch.setattr("bewertungen.routes.create_bew_vortrag", create_mock)
    login_as(client, 5)

    resp = client.post("/bewertungen/vortrag", data={"t_id": "1"})
    assert resp.status_code == 302  # zurueck zur Auswahl
    create_mock.assert_not_called()  # nichts gespeichert


# ---------------------------------------------------------------------------
# Test 6 (ANF 6): Ein Bewertungswert ausserhalb der Skala (1..5) wird nicht
# gespeichert.
# ---------------------------------------------------------------------------
def test_vortrag_post_ungueltiger_wert_wird_nicht_gespeichert(client, monkeypatch):
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "stud")
    monkeypatch.setattr("bewertungen.routes.ist_vortrag_bewertbar", lambda t, u: True)
    monkeypatch.setattr("bewertungen.routes.ist_eigener_vortrag", lambda t, u: False)
    monkeypatch.setattr(
        "bewertungen.routes.get_bewertbare_vortraege",
        lambda exclude_account_id=None: [],
    )
    create_mock = MagicMock()
    monkeypatch.setattr("bewertungen.routes.create_bew_vortrag", create_mock)
    login_as(client, 5)

    form = {
        "t_id": "1",
        "foliengestaltung": "9",  # ungueltig (nicht in 1..5)
        "sprachliche_praesentation": "5", "stil": "3", "zeitliche_gestaltung": "2",
        "verstaendnis": "4", "inhalt": "3", "verknuepfung": "4",
        "diskussion": "5", "beteiligung": "3",
    }
    resp = client.post("/bewertungen/vortrag", data=form)
    assert resp.status_code == 200  # kein Redirect -> nicht gespeichert
    create_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Test 7 (ANF 8): Ein Dozent sieht das Ausarbeitungsformular mit den 5 Kriterien.
# ---------------------------------------------------------------------------
def test_ausarbeitung_formular_fuer_dozent(client, monkeypatch):
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "doz")
    monkeypatch.setattr(
        "bewertungen.routes.get_bewertbare_ausarbeitungen",
        lambda d_id: [{"t_id": 1, "titel": "Star Wars", "vorname": "Max", "nachname": "Mustermann"}],
    )
    login_as(client, 1)

    resp = client.get("/bewertungen/ausarbeitung")
    body = resp.data.decode()
    assert resp.status_code == 200
    # Kriterien, die es nur bei der Ausarbeitung gibt (ANF 8)
    assert "Umfang" in body
    assert "Referenzen" in body
    assert "Schwierigkeitsgrad" in body


# ---------------------------------------------------------------------------
# Test 8 (ANF 8): Ein Studierender darf die Ausarbeitung NICHT bewerten.
# ---------------------------------------------------------------------------
def test_ausarbeitung_fuer_studierende_gesperrt(client, monkeypatch):
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "stud")
    login_as(client, 5)

    resp = client.get("/bewertungen/ausarbeitung")
    # Das Ausarbeitungsformular darf nicht erscheinen.
    assert "Ausarbeitung auswählen" not in resp.data.decode()


# ---------------------------------------------------------------------------
# Test 9 (ANF 9): Gueltige Note wird gespeichert; ungueltige Note wird abgelehnt.
# ---------------------------------------------------------------------------
def test_seminarleistung_note_validierung(client, monkeypatch):
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "doz")
    monkeypatch.setattr(
        "bewertungen.routes.get_bewertbare_seminarleistungen",
        lambda d_id: [{"t_id": 1, "titel": "Star Wars", "vorname": "Max", "nachname": "Mustermann"}],
    )
    create_mock = MagicMock(return_value=True)
    monkeypatch.setattr("bewertungen.routes.create_seminarleistung", create_mock)
    login_as(client, 1)

    # Gueltige Note (1.0 liegt in der zulaessigen Skala 1.0-5.0)
    resp_ok = client.post("/bewertungen/seminarleistung", data={"t_id": "1", "note": "1.0"})
    assert resp_ok.status_code == 302
    create_mock.assert_called_once()

    # Ungueltige Note (9.9 ist nicht zulaessig)
    create_mock.reset_mock()
    resp_bad = client.post("/bewertungen/seminarleistung", data={"t_id": "1", "note": "9.9"})
    assert resp_bad.status_code == 200
    create_mock.assert_not_called()


# ---------------------------------------------------------------------------
# Test 10 (ANF 9): Ein Studierender darf die Seminarleistung NICHT bewerten.
# ---------------------------------------------------------------------------
def test_seminarleistung_fuer_studierende_gesperrt(client, monkeypatch):
    monkeypatch.setattr("bewertungen.routes.get_user_role", lambda uid: "stud")
    login_as(client, 5)

    resp = client.get("/bewertungen/seminarleistung")
    # Studierende werden weitergeleitet (kein Formular).
    assert resp.status_code == 302
    assert "themen/uebersicht" in resp.headers["Location"]
