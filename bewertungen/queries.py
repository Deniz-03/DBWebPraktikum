#Author Tim Deppe (413323)
import db
import psycopg

def is_seminar_vorgetragen(themen_id):
    """
    Gibt an, ob ein Vortrag zu einem bestimmten Seminarthema bereits gegeben wurde.
    :param themen_id: themen_id des Seminarthemas
    :return: Boolean
    """
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT vorgetragen FROM seminarthema WHERE themen_id = %s", (int(themen_id),))
            vorgetragen = cur.fetchone()

            if not vorgetragen:
                return False

            return bool(vorgetragen["vorgetragen"])

def create_bew_vortrag(data):
    """
    Erstellt eine neue Bewertung mittels Angabe einer Dict
    :param data: Dict mit Keys: 't_id', 'vortrag_nr', 'bewertender_id', 'foliengestaltung',
    'sprachliche_praesentation', 'stil', 'zeitliche_gestaltung', 'verstaendnis', 'inhalt', 'verknuepfung',
    'diskussion', 'beteiligung', evtl. 'kommentar'
    :return: True oder 'bereits_bewertet'"""
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:

            erlaubt = is_seminar_vorgetragen(data.get('t_id'))
            if not erlaubt:
                return False

            try:
                cur.execute(
                    "INSERT INTO bew_vortrag ("
                    "t_id, vortrag_nr, bewertender_id, foliengestaltung, sprachliche_praesentation, "
                    "stil, zeitliche_gestaltung, verstaendnis, inhalt, verknuepfung, "
                    "diskussion, beteiligung, kommentar) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (data.get("t_id"),
                        data.get("vortrag_nr"),
                        data.get("bewertender_id"),
                        data.get("foliengestaltung"),
                        data.get("sprachliche_praesentation"),
                        data.get("stil"),
                        data.get("zeitliche_gestaltung"),
                        data.get("verstaendnis"),
                        data.get("inhalt"),
                        data.get("verknuepfung"),
                        data.get("diskussion"),
                        data.get("beteiligung"),
                        #Hier wird der eingegebene Kommentar bewusst nicht mit Regex geprüft, da eine zu strikte Überprüfung
                        #legitime Kommentare blockieren könnte, aber eine entspannte Überprüfung wird gut getarnte
                        #Injections/Scripts eh nicht effektiv verhindern. Lediglich werden parametrisierte Queries
                        #verwendet um diese Gefahr zu vermindern
                        data.get("kommentar") or None,)
                    )
                conn.commit()
                return True

            except psycopg.errors.UniqueViolation:
                conn.rollback()
                return "bereits_bewertet"

def get_bewertbare_vortraege(exclude_account_id=None):
    """
    Gibt alle bewertbaren Vorträge aus (status='Vergeben' und vorgetragen>0).
    Da ein Thema mehrere Vorträge haben kann, wird jedes Thema mittels generate_series in seine einzelnen
    Vorträge 1..vorgetragen aufgefächert. Zusätzlich werden Vorträge, die dem angegebenen Nutzer gehören oder von
    ihm bereits bewertet wurden, ausgefiltert.
    :param exclude_account_id: account_id des Nutzers
    :return: Liste von Dicts mit Keys: 't_id', 'vortrag_nr', 'titel', 'vorname', 'nachname'
    """
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT st.themen_id, gs.nr AS vortrag_nr, st.titel, s.vorname, s.nachname
                FROM seminarthema st
                JOIN studierende s ON st.s_id = s.s_id
                CROSS JOIN LATERAL generate_series(1, st.vorgetragen) AS gs(nr)
                WHERE st.status = 'Vergeben' AND st.vorgetragen > 0
            """
            params = []
            if exclude_account_id is not None:
                query += " AND st.s_id != %s"
                query += (" AND NOT EXISTS (SELECT 1 FROM bew_vortrag bv "
                          "WHERE bv.t_id = st.themen_id AND bv.vortrag_nr = gs.nr AND bv.bewertender_id = %s)")
                params.extend([exclude_account_id, exclude_account_id])
            query += " ORDER BY s.nachname, s.vorname, gs.nr"

            cur.execute(query, params)
            rows = cur.fetchall()
            return [
                {'t_id': r['themen_id'], 'vortrag_nr': r['vortrag_nr'], 'titel': r['titel'],
                    'vorname': r['vorname'], 'nachname': r['nachname']}
                for r in rows
            ]

def ist_vortrag_bewertbar(t_id, vortrag_nr, account_id=None):
    """
    Hilfsfunktion um zu prüfen, ob ein konkreter Vortrag eines Seminarthemas bewertbar ist. Der Vortrag muss
    existieren (1 <= vortrag_nr <= vorgetragen), das Thema muss vergeben sein und der Nutzer darf diesen Vortrag
    noch nicht bewertet haben.
    :param t_id: themen_id des Seminarthemas
    :param vortrag_nr: Nummer des Vortrags innerhalb des Themas
    :param account_id: account_id des Nutzers
    :return: Boolean
    """
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
            SELECT 1 FROM seminarthema st
            WHERE st.themen_id = %s AND st.status = 'Vergeben'
            AND %s BETWEEN 1 AND st.vorgetragen
            AND NOT EXISTS (
                SELECT 1 FROM bew_vortrag bv
                WHERE bv.t_id = st.themen_id AND bv.vortrag_nr = %s AND bv.bewertender_id = %s
            )
            """,
            (t_id, vortrag_nr, vortrag_nr, account_id)
            )
            return cur.fetchone() is not None

def ist_eigener_vortrag(t_id, account_id):
    """
    Hilfsfunktion um zu prüfen ob angemeldeter Nutzer der Vortragende des Seminarthemas t_id ist.
    Gibt True nur dann zurück, wenn der Nutzer der Vortragende ist, sonst False.
    :param t_id: themen_id des Seminarthemas
    :param account_id: account_id des Nutzers
    :return: Boolean
    """
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM seminarthema st
                JOIN studierende s ON st.s_id = s.s_id
                WHERE st.themen_id = %s AND s.s_id = %s
                """,
                (t_id, account_id)
            )
            return cur.fetchone() is not None

#Dict für Werte-Mapping von ints auf zugehörige Symbole
SKALA_LABELS = {1: '--', 2: '-', 3: 'o', 4: '+', 5: '++'}

def get_vortragsstatistiken(s_id):
    """Gibt mittels Angabe einer s_id eine Dict aus. Die Strings sind je nach Durchschnittswert entweder
    '--', '-', 'o', '+' oder '++'
    :param s_id: s_id des Studierenden dessen Statistik gefragt ist
    :return: Dict mit Keys: 'anzahl_bewertungen':int, 'foliengestaltung':str, ...:str,
    'beteiligung':str
    """
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 
                    COUNT(*)                                 AS anzahl_bewertungen,
                    ROUND(AVG(foliengestaltung), 0)          AS foliengestaltung,
                    ROUND(AVG(sprachliche_praesentation), 0) AS sprachliche_praesentation,
                    ROUND(AVG(stil), 0)                      AS stil,
                    ROUND(AVG(zeitliche_gestaltung), 0)      AS zeitliche_gestaltung,
                    ROUND(AVG(verstaendnis), 0)              AS verstaendnis,
                    ROUND(AVG(inhalt), 0)                    AS inhalt,
                    ROUND(AVG(verknuepfung), 0)              AS verknuepfung,
                    ROUND(AVG(diskussion), 0)                AS diskussion,
                    ROUND(AVG(beteiligung), 0)               AS beteiligung   
                FROM bew_vortrag bv
                JOIN seminarthema st ON bv.t_id = st.themen_id
                WHERE st.s_id = %s
                """,
                (s_id,)
            )
            row = cur.fetchone()
            if row is None:
                return {"anzahl_bewertungen": None}

            result = dict(row)

            for feld, wert in result.items():
                if feld == "anzahl_bewertungen":
                    continue

                if wert is None:
                    result[feld] = None
                else:
                    result[feld] = SKALA_LABELS[int(wert)]

            return result

def get_einfache_vortragsstatistik(s_id):
    """Gibt mittels Angabe einer s_id eine Dict aus.
    Die Strings sind je nach Durchschnittswert entweder '--', '-', 'o', '+' oder '++'
    :param s_id: s_id des Studierenden dessen Statistik gefragt ist
    :return: Dict mit Keys: 'anzahl_bewertungen':int, 'gesamtdurchschnitt':str"""
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) AS anzahl_bewertungen,
                ROUND(
                (AVG(foliengestaltung) + AVG(sprachliche_praesentation) + AVG(stil) + AVG(zeitliche_gestaltung) + 
                 AVG(verstaendnis) + AVG(inhalt) + AVG(verknuepfung) + AVG(diskussion) + AVG(beteiligung)) / 9, 0
                ) AS gesamtdurchschnitt
                FROM bew_vortrag bv
                JOIN seminarthema st ON bv.t_id = st.themen_id
                WHERE st.s_id = %s
                """,
                (s_id,)
            )
            row = cur.fetchone()
            if row is None:
                return {"anzahl_bewertungen": 0}

            result = dict(row)

            if result["gesamtdurchschnitt"] is not None:
                result["gesamtdurchschnitt"] = SKALA_LABELS[int(result["gesamtdurchschnitt"])]

            return result

def create_bew_ausarbeitung(data):
    """Erstellt eine neue Ausarbeitung mittels Angabe einer Dict
    :param data: Dict mit Keys: 't_id', 'umfang', 'referenzen',
    'sprachliche_gestaltung', 'inhalt', 'schwierigkeitsgrad', evtl. 'kommentar'
    :return: Boolean"""
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "INSERT INTO bew_ausarbeitung ("
                    "t_id, umfang, referenzen, sprachliche_gestaltung, inhalt, schwierigkeitsgrad, kommentar) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (data.get("t_id"),
                    data.get("umfang"),
                    data.get("referenzen"),
                    data.get("sprachliche_gestaltung"),
                    data.get("inhalt"),
                    data.get("schwierigkeitsgrad"),
                    # Hier wird der eingegebene Kommentar bewusst nicht mit Regex geprüft, da eine zu strikte Überprüfung
                    # legitime Kommentare blockieren könnte, aber eine entspannte Überprüfung wird gut getarnte
                    # Injections/Scripts eh nicht effektiv verhindern. Lediglich werden parametrisierte Queries
                    # verwendet um diese Gefahr zu vermindern
                    data.get("kommentar") or None,)
                    )
                conn.commit()
                return True

            except psycopg.errors.UniqueViolation:
                conn.rollback()
                return False

def get_bewertbare_ausarbeitungen(d_id):
    """Gibt mittels Angabe einer d_id alle Ausarbeitungen
    (als Liste von Dicts) aus, die von dem Dozenten bewertbar
    (haben Status:'Vergeben', gehören zum Seminar des Dozenten, wurden noch nicht bewertet) sind.
    :param d_id: d_id des Dozenten der für die Bewertung zuständig ist
    :return: Liste von Dicts mit Keys: 'themen_id', 'titel', 'vorname', 'nachname'"""
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT st.themen_id, st.titel, s.vorname, s.nachname
                FROM seminarthema st
                JOIN studierende s ON st.s_id = s.s_id
                JOIN dozierende d ON st.d_id = d.d_id
                WHERE st.status = 'Vergeben' AND d.d_id = %s AND st.themen_id NOT IN (SELECT t_id FROM bew_ausarbeitung)
                """,
                (d_id,)
            )
            rows = cur.fetchall()
            return [
                {'t_id': r['themen_id'], 'titel': r['titel'], 'vorname': r['vorname'],
                    'nachname': r['nachname']}
                for r in rows
            ]

def ist_ausarbeitung_bewertbar(t_id):
    """Gibt True aus wenn ein Seminarthema status:'Vergeben' hat und noch nicht bewertet wurde, sonst False.
    :param t_id: themen_id des Seminarthemas
    :return: Boolean"""
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
            SELECT 1 FROM seminarthema
            WHERE themen_id = %s AND status = 'Vergeben'
            AND themen_id NOT IN (
                SELECT t_id FROM bew_ausarbeitung
            )
            """,
            (t_id,)
            )
            return cur.fetchone() is not None

def get_ausarbeitung_statistiken(s_id):
    """
    Gibt die Dict mit Symbolwerten (--, ..., ++) zur Bewertung der Ausarbeitung eines Studierenden.
    :param s_id: s_id des Studierenden dessen Statistik gefragt ist
    :return: Dict mit Keys: 'titel', 'vorname', 'nachname', 'umfang', 'referenzen', 'sprachliche_gestaltung',
    'inhalt', 'schwierigkeitsgrad', 'kommentar'
    """
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT st.titel, s.vorname, s.nachname, ba.umfang, ba.referenzen, ba.sprachliche_gestaltung,
                    ba.inhalt, ba.schwierigkeitsgrad, ba.kommentar
                FROM bew_ausarbeitung ba
                JOIN seminarthema st ON ba.t_id = st.themen_id
                JOIN studierende s ON st.s_id = s.s_id
                WHERE st.s_id = %s
                """,
                (s_id,)
            )
            row = cur.fetchone()

            if row is None:
                return {"t_id": None}

            result = dict(row)

            for feld, wert in result.items():
                if feld in ("titel", "vorname", "nachname", "kommentar"):
                    continue

                if wert is None:
                    result[feld] = None
                else:
                    result[feld] = SKALA_LABELS[int(wert)]

            return result

def get_einfache_ausarbeitungsstatistik(s_id):
    """Gibt mittels Angabe einer s_id eine Dict aus.
    Die String ist je nach Durchschnittswert entweder '--', '-', 'o', '+' oder '++'
    :param s_id: s_id des Studierenden dessen Statistik gefragt ist
    :return: Dict mit Key: 'gesamtdurchschnitt':str"""
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                ROUND(
                (AVG(umfang) + AVG(referenzen) + AVG(sprachliche_gestaltung) + AVG(inhalt) + AVG(schwierigkeitsgrad)) 
                    / 5, 0
                ) AS gesamtdurchschnitt
                FROM bew_ausarbeitung ba
                JOIN seminarthema st ON ba.t_id = st.themen_id
                WHERE st.s_id = %s
                """,
                (s_id,)
            )
            row = cur.fetchone()
            if row is None:
                return {"gesamtdurchschnitt": None}

            result = dict(row)

            if result["gesamtdurchschnitt"] is not None:
                result["gesamtdurchschnitt"] = SKALA_LABELS[int(result["gesamtdurchschnitt"])]

            return result

def create_seminarleistung(data):
    """
    Erstellt eine neue Seminarleistung mittels Angabe einer Dict. Anschließlich wird der Status des Seminarthemas
    von 'Vergeben' auf 'Abgeschlossen' gesetzt.
    :param data: Dict mit Keys: 't_id', 'note'
    :return: Boolean"""
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            try:
                cur.execute(
                    """
                    INSERT INTO seminarleistung (t_id, note)
                    VALUES (%s, %s)
                    """,
                    (data['t_id'], data['note'])
                )
                cur.execute(
                    """
                    UPDATE seminarthema SET status = 'Abgeschlossen' WHERE themen_id = %s
                    """,
                    (data['t_id'],)
                )
                conn.commit()
                return True
            except psycopg.errors.UniqueViolation:
                conn.rollback()
                return False

def get_bewertbare_seminarleistungen(dozent_id):
    """
    Liefert alle Seminarthemen, für die der Dozent dozent_id verantwortlich ist,
    bei denen bereits mindestens eine Vortragsbewertung UND eine Ausarbeitungsbewertung
    existieren, und für die noch KEINE Seminarleistung vergeben wurde.
    Inkl. Titel sowie Vor- und Nachname des Studierenden.
    :param dozent_id: d_id des Dozenten
    :return: Liste von Dicts mit Keys: 'themen_id', 'titel', 'vorname', 'nachname'
    """
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT st.themen_id, st.titel, s.vorname, s.nachname
                FROM seminarthema st
                JOIN studierende s ON st.s_id = s.s_id
                WHERE st.d_id = %s
                AND EXISTS (SELECT 1 FROM bew_vortrag bv WHERE bv.t_id = st.themen_id)
                AND EXISTS (SELECT 1 FROM bew_ausarbeitung ba WHERE ba.t_id = st.themen_id)
                AND NOT EXISTS (SELECT 1 FROM seminarleistung sl WHERE sl.t_id = st.themen_id)
                ORDER BY s.nachname, s.vorname
                """,
                (dozent_id,)
            )
            rows = cur.fetchall()
            return [
                {'t_id': r['themen_id'], 'titel': r['titel'], 'vorname': r['vorname'], 'nachname': r['nachname']}
                for r in rows
            ]

def get_seminarleistung(s_id):
    """
    Gibt mittels Angabe einer s_id die zugehörige Seminarleistung aus.
    :param s_id: s_id des Studierenden dessen Seminarleistung gefragt ist
    :return: None OR Dict mit Key: 'note'
    """
    with (db.connect_to_db() as conn):
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT sl.note 
                FROM seminarleistung sl
                JOIN seminarthema st ON sl.t_id = st.themen_id
                WHERE st.s_id = %s
                """,
                (s_id,)
            )
            result = cur.fetchone()
            if result:
                return result
            return None