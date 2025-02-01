from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from forms import LoginForm  # Importa il form

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'chiave_segreta'
db = SQLAlchemy(app)

# Modello per utenti dell'app (admin)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)

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
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        first_user_mode = False
        return redirect(url_for("index"))

    return render_template("register_first_user.html")

# ** Login degli amministratori **
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()  # Crea l'istanza del form

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data, password=form.password.data).first()
        if user:
            session["user"] = user.username
            return redirect(url_for("index"))

    return render_template("login.html", form=form)

# ** Logout **
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ** Controllo autenticazione **
def is_logged_in():
    return "user" in session

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