#Author Deniz Rahnefeld (409637)
import db
from auth.utils import hash_passwort


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

            passwort_hash = hash_passwort(data.get("passwort", ''))
            cur.execute('INSERT INTO account (email, passwort, rolle) '
                        'VALUES (%s, %s, %s) '
                        'RETURNING id',
                        (data.get("email", ''),
                         passwort_hash,
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

#Diese Funktion gibt bei richtigem Passwort die User_ID zurück, um diese in der
#   Session zu speichern und später mit der DB abzugleichen.
#TODO Dieser Version funtkioniert mit gehashten Passwörtern -> Fragen ob erlaubt ist.
def check_password(data)-> int | None:
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            user_id = None
            email = data.get("email", '').strip()
            inp_passwort = data.get("passwort", '')

            cur.execute("SELECT passwort FROM account WHERE email = %s", (email,))
            passwort = cur.fetchone()[0]


            #Nur wenn das Passwort übereinstimmt, wird die user_id zurückgegeben.
            # Ohne user_id merkt sich die Session nicht, dass man eingeloggt ist.
            if hash_passwort(inp_passwort) == passwort:
                cur.execute("SELECT id FROM account WHERE email = %s", (email,))
                user_id = cur.fetchone()[0]

            return user_id #Kann None sein und somit False in If-Abfragen

def get_user_role(user_id):
    with db.connect_to_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT rolle FROM account WHERE id = %s", (user_id,))
            user_role = cur.fetchone()[0]
            return user_role

