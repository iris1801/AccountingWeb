from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy                        from werkzeug.security import generate_password_hash, check_password_hash
from forms import LoginForm  # Importa il form                 from flask_session import Session

app = Flask(__name__)                                          app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False  # Evita che la sessione venga distrutta subito                                       app.config["SESSION_USE_SIGNER"] = True  # Protegge i cookie della sessione                                                   app.config["SESSION_FILE_DIR"] = "./flask_session"  # Cartella per le sessioni                                                Session(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'chiave_segreta'                    db = SQLAlchemy(app)

# Modello per utenti dell'app (admin)
class User(db.Model):                                              id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)                                                              password_hash = db.Column(db.String(255), nullable=False)  
    def set_password(self, password):                                  self.password_hash = generate_password_hash(password)
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

# ** Registrazione del primo utente **
@app.route("/register_first_user", methods=["GET", "POST"])
def register_first_user():
    global first_user_mode
    if not first_user_mode:
        return redirect(url_for("login"))

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        new_user = User(username=username)
        new_user.set_password(password)  # Salva la password in modo sicuro
        db.session.add(new_user)
        db.session.commit()

        first_user_mode = False
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
            session["user"] = user.username
            session.permanent = True  # Mantiene la sessione attiva
            print("Login effettuato con successo, session:", session)
            return redirect(url_for("index"))
        else:
            print("Errore login: utente non trovato o password errata.")

    print("Sessione attuale:", session)
    return render_template("login.html", form=form)

# ** Logout **
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ** Controllo autenticazione **
def is_logged_in():
    print("Contenuto sessione in is_logged_in():", session)
    return session.get("user") is not None


# Altra route per dashboard
@app.route("/edit_profile", methods=["GET", "POST"])
def edit_profile():
    if not is_logged_in():
        return redirect(url_for("login"))

    user = User.query.filter_by(username=session.get("user")).first()
    if not user:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        new_username = request.form["username"]
        new_password = request.form["password"]

        user.username = new_username
        if new_password:  # Se è stata inserita una nuova password, aggiornarla
            user.set_password(new_password)

        db.session.commit()
        return redirect(url_for("dashboard"))

    return render_template("edit_profile.html", user=user)


# Route per dashboard #
@app.route("/dashboard")
def dashboard():
    if not is_logged_in():
        return redirect(url_for("login"))

    amministratori = User.query.all()  # Prendi la lista degli amministratori
    return render_template("dashboard.html", amministratori=amministratori)


# ** Visualizzazione utenti del servizio Streamland **
@app.route("/index")
def index():
    if not is_logged_in():
        return redirect(url_for("login"))

    utenti = Utente.query.all()
    return render_template("index.html", utenti=utenti)

# ** Aggiunta nuovo utente al servizio Streamland **
@app.route("/add_utente", methods=["GET", "POST"])
def add_utente():
    if not is_logged_in():
        return redirect(url_for("login"))

    if request.method == "POST":
        nome = request.form["nome"]
        cognome = request.form["cognome"]
        email = request.form["email"]
        piano = request.form["piano"]
        stato = request.form["stato"]

        nuovo_utente = Utente(nome=nome, cognome=cognome, email=email, piano=piano, stato=stato)
        db.session.add(nuovo_utente)
        db.session.commit()

        return redirect(url_for("index"))

    return render_template("add_utente.html")

# ** Modifica utente **
@app.route("/edit_utente/<int:id>", methods=["GET", "POST"])
def edit_utente(id):
    if not is_logged_in():
        return redirect(url_for("login"))

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

# ** Eliminazione utente **
@app.route("/delete_utente/<int:id>")
def delete_utente(id):
    if not is_logged_in():
        return redirect(url_for("login"))

    utente = Utente.query.get_or_404(id)
    db.session.delete(utente)
    db.session.commit()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)