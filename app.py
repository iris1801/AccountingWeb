from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'supersecretkey'

db = SQLAlchemy(app)

# Modello del database
class Utente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cognome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=True)  # Permette valori NULL
    piano = db.Column(db.String(50), nullable=False)
    stato = db.Column(db.String(20), nullable=False)

# Rotte dell'app
@app.route('/')
def index():
    utenti = Utente.query.all()
    return render_template('index.html', utenti=utenti)

@app.route('/add', methods=['GET', 'POST'])
def add_utente():
    if request.method == 'POST':
        nome = request.form['nome']
        cognome = request.form['cognome']
        email = request.form['email'].strip() or None  # Salva None se il campo è vuoto
        piano = request.form['piano']
        stato = request.form['stato']

        nuovo_utente = Utente(nome=nome, cognome=cognome, email=email, piano=piano, stato=stato)
        
        db.session.add(nuovo_utente)
        try:
            db.session.commit()
            flash("Utente aggiunto con successo.")
        except Exception as e:
            db.session.rollback()
            flash(f"Errore: {e}")

        return redirect(url_for('index'))

    return render_template('add.html')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_utente(id):
    utente = Utente.query.get(id)

    if not utente:
        flash("Utente non trovato.")
        return redirect(url_for('index'))

    if request.method == 'POST':
        utente.nome = request.form['nome']
        utente.cognome = request.form['cognome']
        utente.email = request.form['email'].strip() or None  # Salva None se vuoto
        utente.piano = request.form['piano']
        utente.stato = request.form['stato']

        try:
            db.session.commit()
            flash("Utente aggiornato con successo.")
        except Exception as e:
            db.session.rollback()
            flash(f"Errore: {e}")

        return redirect(url_for('index'))

    return render_template('edit.html', utente=utente)

@app.route('/delete/<int:id>')
def delete_utente(id):
    utente = Utente.query.get(id)
    
    if utente:
        db.session.delete(utente)
        try:
            db.session.commit()
            flash("Utente eliminato con successo.")
        except Exception as e:
            db.session.rollback()
            flash(f"Errore: {e}")

    return redirect(url_for('index'))

if __name__ == '__main__':
    db.create_all()  # Crea il database se non esiste
    app.run(debug=True)
