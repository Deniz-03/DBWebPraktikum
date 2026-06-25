#Author Deniz Rahnefeld (409637)
import db


def check_account(data) -> bool:
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            acc_exists = False

            email = data.get("email", '').strip()
            cur.execute("SELECT email FROM account WHERE email = %s", (email,))
            result = cur.fetchone()

            if result is not None:
                acc_exists = True

            return acc_exists


def create_user(data):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:

            cur.execute('INSERT INTO account (email, passwort, rolle) '
                        'VALUES (%s, %s, %s) '
                        'RETURNING id',
                        (data.get("email", ''),
                         data.get("passwort", ''),
                         'stud'))
            acc_id = cur.fetchone()[0]

            #Hier fange ich den Fall ab, dass das Formular einen leeren String für
            # Seminarthema mitschickt, statt es zu ignorieren.

            seminar_thema = data.get("seminar_thema", '')
            if seminar_thema.strip() == "":
                seminar_thema = None

            cur.execute("INSERT INTO studierende (s_id, matr_nr, vorname, nachname, "
                        "studiengang_name, abschluss, bel_seminar, seminar_thema)"
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                        (acc_id,
                         data.get("matr_nr", ''),
                         data.get("vorname", ''),
                         data.get("nachname", ''),
                         data.get('studiengang_name', ''),
                         data.get('abschluss', ''),
                         data.get('bel_seminar', ''),
                         seminar_thema,))
            conn.commit()

            cur.close()
            conn.close()


