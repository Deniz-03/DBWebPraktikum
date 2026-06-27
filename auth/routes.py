#Author Deniz Rahnefeld (409637)
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from auth.queries import *
from auth.utils import *

auth_bp = Blueprint('auth', __name__, template_folder='templates')

@auth_bp.route('/')
def index():
    if 'user_id' in session:
        user_id = int(session.get('user_id', '-1'))
        rolle = get_user_role(user_id)
        if rolle is None:
            flash('Fehler beim laden der Session', 'error')
        return render_template('index.html', rolle=rolle)
    else:
        return render_template("index.html")

#Um zu prüfen, ob ein Nutzer angemeldet ist, wird geschaut,
# ob eine user_id in der Session enthalten ist.
#Ein User ist angemeldet genau dann, wenn eine user_id in der Session vermerkt ist.
#Diese user_id kann dann verwendet werden, um userspezifische Informationen aus der DB
# abzufragen.
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('auth.profile'))
        else:
            return render_template('auth/login.html', values={})

    else:
        data = request.form

        empty_input_found, leere_felder = check_login_input(data)
        if empty_input_found:
            for feld in leere_felder:
                flash(f'Das Feld {feld} ist leer!', 'error')
            return render_template('auth/login.html', values=data)

        valid_input, flash_messages = validate_login(data)
        if not valid_input:
            for message in flash_messages:
                flash(message, 'error')
            return render_template("auth/login.html", values=data)

        #Ab hier ist der Input geprüft.

        if check_account(data):
            if user_id := check_password(data):
                session.clear()
                session['user_id'] = user_id
                return redirect(url_for('auth.profile'))
            else:
                flash('Das Passwort ist falsch!', 'error')
                return render_template("auth/login.html", values=data)
        else:
            flash('Der Account existiert nicht!', 'error')
            return render_template("auth/login.html", values=data)
@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # Felder: Vorname, Nachname, Matrikelnummer, Email, Passwort, Passwort wiederholen
    #   seminar, studiengang_name, abschluss, seminar_thema
    if request.method == 'GET':
        seminarthemen = get_seminarthemen()
        return render_template("auth/register.html", values={}, seminarthemen=seminarthemen)
    else:
        data = request.form
        seminarthemen = get_seminarthemen()


        empty_input_found, leere_felder = check_register_input(data)
        if empty_input_found:
            for feld in leere_felder:
                flash(f'Das Feld {feld} ist leer!', 'error')
            return render_template('auth/register.html', values=data, seminarthemen=seminarthemen)

        valid_input, flash_messages = validate_register(data)
        if not valid_input:
            for message in flash_messages:
                flash(message, 'error')
            return render_template("auth/register.html", values=data, seminarthemen=seminarthemen)

        #Hier wird geguckt, ob ein Seminarthema ausgewählt wurde und ob dieses bereits belegt wurde.
        if data.get("seminar_thema", '').strip():
            if is_seminar_occupied(data.get('seminar_thema')):
                flash("Seminar ist bereits belegt!", 'error')
                return render_template("auth/register.html", values=data, seminarthemen=seminarthemen)

        #Ab hier ist der Input validiert.

        #Jetzt wird geprüft, ob der Account bereits existiert
        # und ansonsten wird er erstellt.
        if check_account(data):
            flash('Account existiert bereits!', 'error')
            return render_template("auth/register.html", values=data, seminarthemen=seminarthemen)
        else:
            create_user(data)
            flash('Account erfolgreich erstellt!', 'success')
        return render_template("auth/register.html", values={}, seminarthemen=seminarthemen)








@auth_bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'GET':
        if 'user_id' in session:
            user_id = int(session.get('user_id', '-1'))
            rolle = get_user_role(user_id)
            return render_template("auth/profile.html", values={}, rolle=rolle)
        else:
            return render_template("auth/profile.html", values={})

    else:
        #TODO Authentifikation hinzufügen
        return render_template("auth/profile.html")


