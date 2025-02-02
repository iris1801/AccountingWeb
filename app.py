from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_session import Session
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from forms import LoginForm, RegisterForm  # Aggiungi l'import per i form

# Configura l'app
app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_FILE_DIR"] = "./flask_session"  # Cartella per le sessioni
Session(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "chiave_segreta"
db = SQLAlchemy(app)
# Configura LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"  # Definisce la vista di login

# Modello per utenti amministratori (UserMixin permette l'integrazione con Flask-Login)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Modello per utenti del servizio Streamland
class Utente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    piano = db.Column(db.String(50), nullable=False)
    stato = db.Column(db.String(50), nullable=False)
    data_registrazione = db.Column(db.DateTime, default=datetime.utcnow)  # Nuovo campo
    data_scadenza = db.Column(db.DateTime, nullable=True)  # Nuovo campo, opzionale

    def __repr__(self):
        return f"<Utente {self.nome} {self.cognome}>"

# Carica l'utente
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Variabile per la modalità del primo utente
first_user_mode = (
    None  # Rimuovere la dichiarazione dentro la route, deve essere globale
)

with app.app_context():
    db.create_all()
    if not User.query.first():
        print("Nessun utente trovato, reindirizzamento alla registrazione.")
        first_user_mode = True
    else:
        first_user_mode = False


@app.route("/")
def home():
    if first_user_mode:
        return redirect(url_for("register_first_user"))
    return redirect(url_for("index"))


# ** Registrazione Nuovo Amministratore (Accessibile dalla Dashboard) **
@app.route("/register", methods=["GET", "POST"])
def register():
    if not is_logged_in():
        return redirect(url_for("login"))

    form = RegisterForm()  # Usa il form di registrazione

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Controlla se la password e la conferma della password sono uguali
        if password != confirm_password:
            return "Le password non corrispondono"

        # Verifica se l'utente già esiste
        if User.query.filter_by(username=username).first():
            return "Nome utente già esistente"

        # Crea il nuovo amministratore
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("dashboard"))

    return render_template("register.html", form=form)


# ** Registrazione del primo utente **
@app.route("/register_first_user", methods=["GET", "POST"])
def register_first_user():
    global first_user_mode  # Usa la variabile globale

    if not first_user_mode:
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        new_user = User(username=username)
        new_user.set_password(password)  # Salva la password in modo sicuro
        db.session.add(new_user)
        db.session.commit()

        first_user_mode = False  # Cambia lo stato della variabile
        return redirect(url_for("login"))

    return render_template("register_first_user.html")


# ** Login degli amministratori **
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()  # Crea l'istanza del form

    if request.method == "POST":  # Non usare solo validate_on_submit()
        username = request.form["username"]
        password = request.form["password"]
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)  # Login dell'utente
            return redirect(url_for("index"))
        else:
            return "Errore login: utente non trovato o password errata."

    return render_template("login.html", form=form)


# ** Logout **
@app.route("/logout")
def logout():
    logout_user()  # Logout dell'utente
    return redirect(url_for("login"))


# ** Controllo autenticazione **
def is_logged_in():
    return current_user.is_authenticated


# Route per dashboard
@app.route("/dashboard")
@login_required  # Aggiungi il decoratore per proteggere la dashboard
def dashboard():
    amministratori = User.query.all()  # Prendi la lista degli amministratori
    return render_template("dashboard.html", amministratori=amministratori)


# ** Visualizzazione utenti del servizio Streamland **
@app.route("/index")
@login_required
def index():
    utenti = Utente.query.all()
    return render_template("index.html", utenti=utenti)


# ** Aggiunta nuovo utente al servizio Streamland **
@app.route("/add_utente", methods=["GET", "POST"])
@login_required
def add_utente():
    if request.method == "POST":
        nome = request.form["nome"]
        cognome = request.form["cognome"]
        email = request.form["email"]
        piano = request.form["piano"]
        stato = request.form["stato"]

        nuovo_utente = Utente(
            nome=nome, cognome=cognome, email=email, piano=piano, stato=stato
        )
        db.session.add(nuovo_utente)
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("add_utente.html")


# ** Modifica utente **
@app.route("/edit_utente/<int:id>", methods=["GET", "POST"])
@login_required
def edit_utente(id):
    utente = Utente.query.get_or_404(id)

    if request.method == "POST":
        utente.nome = request.form["nome"]
        utente.cognome = request.form["cognome"]
        utente.email = request.form["email"]
        utente.piano = request.form["piano"]
        utente.stato = request.form["stato"]

        db.session.commit()
        return redirect(url_for("index"))

    return render_template("edit_utente.html", utente=utente)


# ** Modifica Profilo Amministratore **
@app.route("/edit_profile/<int:id>", methods=["GET", "POST"])
@login_required
def edit_profile(id):
    amministratore = User.query.get_or_404(id)

    if request.method == "POST":
        amministratore.username = request.form["username"]
        amministratore.password_hash = generate_password_hash(request.form["password"])

        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("edit_profile.html", amministratore=amministratore)


# ** Eliminazione utente **
@app.route("/delete_utente/<int:id>")
@login_required
def delete_utente(id):
    utente = Utente.query.get_or_404(id)
    db.session.delete(utente)
    db.session.commit()
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True)
