from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from datetime import datetime
from forms import LoginForm, RegisterForm  # Aggiungi l'import per i form

# Configura l'app
app = Flask(__name__)
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_FILE_DIR"] = "./flask_session"
Session(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SECRET_KEY"] = "chiave_segreta"
db = SQLAlchemy(app)

# Configura LoginManager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Modello per utenti amministratori
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
    data_registrazione = db.Column(db.DateTime, default=datetime.utcnow)
    data_scadenza = db.Column(db.DateTime, nullable=True)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return redirect(url_for("index"))

@app.route("/index")
@login_required
def index():
    utenti = Utente.query.all()
    return render_template("index.html", utenti=utenti)

@app.route("/add_utente", methods=["GET", "POST"])
@login_required
def add_utente():
    if request.method == "POST":
        nome = request.form["nome"]
        cognome = request.form["cognome"]
        email = request.form["email"]
        piano = request.form["piano"]
        stato = request.form["stato"]
        data_scadenza = request.form["data_scadenza"]

        nuovo_utente = Utente(
            nome=nome,
            cognome=cognome,
            email=email,
            piano=piano,
            stato=stato,
            data_scadenza=datetime.strptime(data_scadenza, "%Y-%m-%d")
            if data_scadenza
            else None,
        )
        db.session.add(nuovo_utente)
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("add_utente.html")

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
        data_scadenza = request.form["data_scadenza"]
        utente.data_scadenza = datetime.strptime(data_scadenza, "%Y-%m-%d") if data_scadenza else None

        db.session.commit()
        return redirect(url_for("index"))

    return render_template("edit_utente.html", utente=utente)

@app.route("/delete_utente/<int:id>")
@login_required
def delete_utente(id):
    utente = Utente.query.get_or_404(id)
    db.session.delete(utente)
    db.session.commit()
    return redirect(url_for("index"))