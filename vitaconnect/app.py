from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
import sqlite3
import hashlib
import os
from datetime import datetime, date

app = Flask(__name__)
app.secret_key = 'vitaconnect-secret-2026'

DB_PATH = os.path.join(os.path.dirname(__file__), 'vitaconnect.db')

# ─────────────────────────────────────────
# BASE DE DONNÉES
# ─────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript('''
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('patient','medecin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utilisateur_id INTEGER UNIQUE NOT NULL,
            date_naissance TEXT,
            pathologie TEXT,
            medecin_id INTEGER,
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id),
            FOREIGN KEY (medecin_id) REFERENCES utilisateurs(id)
        );

        CREATE TABLE IF NOT EXISTS medecins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            utilisateur_id INTEGER UNIQUE NOT NULL,
            specialite TEXT DEFAULT 'Médecin généraliste',
            cabinet TEXT,
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        );

        CREATE TABLE IF NOT EXISTS mesures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            date_mesure TEXT NOT NULL,
            heure_mesure TEXT NOT NULL,
            tension_sys INTEGER,
            tension_dia INTEGER,
            pouls INTEGER,
            glycemie REAL,
            poids REAL,
            note TEXT,
            statut TEXT DEFAULT 'normale',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        );

        CREATE TABLE IF NOT EXISTS alertes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            mesure_id INTEGER,
            type_alerte TEXT NOT NULL,
            valeur TEXT NOT NULL,
            seuil TEXT NOT NULL,
            message TEXT,
            traitee INTEGER DEFAULT 0,
            date_alerte TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (mesure_id) REFERENCES mesures(id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expediteur_id INTEGER NOT NULL,
            destinataire_id INTEGER NOT NULL,
            contenu TEXT NOT NULL,
            lu INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (expediteur_id) REFERENCES utilisateurs(id),
            FOREIGN KEY (destinataire_id) REFERENCES utilisateurs(id)
        );
    ''')

    # Données de démo
    def hash_pw(pw):
        return hashlib.sha256(pw.encode()).hexdigest()

    # Vérifier si les données existent déjà
    existing = c.execute("SELECT COUNT(*) FROM utilisateurs").fetchone()[0]
    if existing == 0:
        # Médecin
        c.execute("""INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role)
                     VALUES (?, ?, ?, ?, ?)""",
                  ('Ouhimmou', 'Ilham', 'ouhimmou@vitaconnect.fr', hash_pw('demo123'), 'medecin'))
        med_uid = c.lastrowid
        c.execute("""INSERT INTO medecins (utilisateur_id, specialite, cabinet)
                     VALUES (?, ?, ?)""",
                  (med_uid, 'Médecin généraliste', 'Cabinet médical Lyon 3'))

        # Patient Lyly
        c.execute("""INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role)
                     VALUES (?, ?, ?, ?, ?)""",
                  ('Fontaine', 'Lyly', 'lyly@vitaconnect.fr', hash_pw('demo123'), 'patient'))
        pat_uid = c.lastrowid
        c.execute("""INSERT INTO patients (utilisateur_id, date_naissance, pathologie, medecin_id)
                     VALUES (?, ?, ?, ?)""",
                  (pat_uid, '1958-03-14', 'Hypertension artérielle', med_uid))
        pat_id = c.lastrowid

        # Patient Fatima
        c.execute("""INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role)
                     VALUES (?, ?, ?, ?, ?)""",
                  ('Ouali', 'Fatima', 'fatima@vitaconnect.fr', hash_pw('demo123'), 'patient'))
        fat_uid = c.lastrowid
        c.execute("""INSERT INTO patients (utilisateur_id, date_naissance, pathologie, medecin_id)
                     VALUES (?, ?, ?, ?)""",
                  (fat_uid, '1966-07-22', 'Diabète de type 2', med_uid))
        fat_id = c.lastrowid

        # Mesures de Marcel
        mesures_demo = [
            (pat_id, '2026-04-14', '08:12', 130, 80, 68, None, 78.0, None, 'normale'),
            (pat_id, '2026-04-13', '07:55', 140, 90, 72, None, 78.2, None, 'normale'),
            (pat_id, '2026-04-12', '08:30', 160, 100, 76, None, 78.1, 'Mauvaise nuit', 'elevee'),
            (pat_id, '2026-04-11', '09:01', 150, 90, 70, None, 77.9, 'Stressé au travail', 'limite'),
            (pat_id, '2026-04-10', '08:00', 130, 80, 67, None, 78.0, None, 'normale'),
            (pat_id, '2026-04-09', '07:45', 130, 70, 65, None, 78.0, 'Bien dormi', 'normale'),
            (pat_id, '2026-04-08', '08:20', 140, 90, 71, None, 78.3, None, 'normale'),
        ]
        c.executemany("""INSERT INTO mesures
            (patient_id, date_mesure, heure_mesure, tension_sys, tension_dia, pouls, glycemie, poids, note, statut)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""", mesures_demo)

        # Mesures Fatima
        c.execute("""INSERT INTO mesures
            (patient_id, date_mesure, heure_mesure, tension_sys, tension_dia, pouls, glycemie, poids, note, statut)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (fat_id, '2026-04-15', '07:42', None, None, None, 2.1, 68.5, 'À jeun', 'critique'))

        # Alertes
        c.execute("""INSERT INTO alertes (patient_id, type_alerte, valeur, seuil, message, traitee)
                     VALUES (?, ?, ?, ?, ?, ?)""",
                  (fat_id, 'glycemie', '2.1 g/L', '1.8 g/L', 'Glycémie élevée ce matin à jeun', 0))

        # Messages
        c.execute("""INSERT INTO messages (expediteur_id, destinataire_id, contenu)
                     VALUES (?, ?, ?)""",
                  (med_uid, pat_uid, "Bonjour Lyly, j'ai vu que votre tension était un peu élevée vendredi. Rien d'alarmant. Continuez à prendre vos mesures et évitez le sel cette semaine. On en parle le 22."))
        c.execute("""INSERT INTO messages (expediteur_id, destinataire_id, contenu)
                     VALUES (?, ?, ?)""",
                  (pat_uid, med_uid, "Bonjour Docteur, merci pour le message. J'avais mal dormi ce soir-là. Ce matin c'est revenu à 13/8."))
        c.execute("""INSERT INTO messages (expediteur_id, destinataire_id, contenu)
                     VALUES (?, ?, ?)""",
                  (med_uid, pat_uid, "Parfait, c'est exactement ce genre d'information qui m'aide. Continuez comme ça, à vendredi !"))

    conn.commit()
    conn.close()

# ─────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────
def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def get_statut_tension(sys, dia):
    if sys is None or dia is None:
        return 'normale'
    if sys >= 180 or dia >= 110:
        return 'critique'
    if sys >= 160 or dia >= 100:
        return 'elevee'
    if sys >= 140 or dia >= 90:
        return 'limite'
    return 'normale'

def check_alertes(conn, patient_id, mesure_id, tension_sys, tension_dia, glycemie):
    alertes_creees = []
    if tension_sys and tension_sys >= 160:
        conn.execute("""INSERT INTO alertes (patient_id, mesure_id, type_alerte, valeur, seuil, message)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                     (patient_id, mesure_id, 'tension', f'{tension_sys}/{tension_dia} mmHg',
                      '160/100', f'Tension systolique élevée : {tension_sys} mmHg'))
        alertes_creees.append('tension')
    if glycemie and glycemie >= 1.8:
        conn.execute("""INSERT INTO alertes (patient_id, mesure_id, type_alerte, valeur, seuil, message)
                        VALUES (?, ?, ?, ?, ?, ?)""",
                     (patient_id, mesure_id, 'glycemie', f'{glycemie} g/L',
                      '1.8 g/L', f'Glycémie élevée : {glycemie} g/L'))
        alertes_creees.append('glycemie')
    return alertes_creees

# ─────────────────────────────────────────
# AUTH
# ─────────────────────────────────────────
@app.route('/')
def index():
    if 'user_id' in session:
        if session['role'] == 'patient':
            return redirect(url_for('patient_dashboard'))
        else:
            return redirect(url_for('medecin_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM utilisateurs WHERE email = ? AND mot_de_passe = ?",
            (email, hash_pw(password))
        ).fetchone()
        conn.close()
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['nom'] = f"{user['prenom']} {user['nom']}"
            if user['role'] == 'patient':
                return redirect(url_for('patient_dashboard'))
            else:
                return redirect(url_for('medecin_dashboard'))
        flash('Email ou mot de passe incorrect.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/inscription', methods=['GET', 'POST'])
def inscription():
    if request.method == 'POST':
        nom = request.form.get('nom', '').strip()
        prenom = request.form.get('prenom', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'patient')
        pathologie = request.form.get('pathologie', '')
        date_naissance = request.form.get('date_naissance', '')

        if not all([nom, prenom, email, password]):
            flash('Tous les champs obligatoires doivent être remplis.', 'error')
            return render_template('inscription.html')

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO utilisateurs (nom, prenom, email, mot_de_passe, role) VALUES (?, ?, ?, ?, ?)",
                (nom, prenom, email, hash_pw(password), role)
            )
            uid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            if role == 'patient':
                # Trouver le premier médecin disponible
                med = conn.execute("SELECT utilisateur_id FROM medecins LIMIT 1").fetchone()
                med_id = med['utilisateur_id'] if med else None
                conn.execute(
                    "INSERT INTO patients (utilisateur_id, date_naissance, pathologie, medecin_id) VALUES (?, ?, ?, ?)",
                    (uid, date_naissance, pathologie, med_id)
                )
            else:
                specialite = request.form.get('specialite', 'Médecin généraliste')
                cabinet = request.form.get('cabinet', '')
                conn.execute(
                    "INSERT INTO medecins (utilisateur_id, specialite, cabinet) VALUES (?, ?, ?)",
                    (uid, specialite, cabinet)
                )
            conn.commit()
            flash('Compte créé avec succès ! Vous pouvez vous connecter.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Cet email est déjà utilisé.', 'error')
        finally:
            conn.close()

    return render_template('inscription.html')

# ─────────────────────────────────────────
# PATIENT ROUTES
# ─────────────────────────────────────────
@app.route('/patient')
def patient_dashboard():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))
    conn = get_db()
    patient = conn.execute(
        "SELECT p.*, u.nom, u.prenom FROM patients p JOIN utilisateurs u ON p.utilisateur_id = u.id WHERE p.utilisateur_id = ?",
        (session['user_id'],)
    ).fetchone()
    derniere = conn.execute(
        "SELECT * FROM mesures WHERE patient_id = ? ORDER BY date_mesure DESC, heure_mesure DESC LIMIT 1",
        (patient['id'],)
    ).fetchone()
    mesures_semaine = conn.execute(
        "SELECT * FROM mesures WHERE patient_id = ? ORDER BY date_mesure DESC LIMIT 7",
        (patient['id'],)
    ).fetchall()
    nb_mesures_mois = conn.execute(
        "SELECT COUNT(*) as c FROM mesures WHERE patient_id = ? AND date_mesure >= date('now','-30 days')",
        (patient['id'],)
    ).fetchone()['c']
    medecin = None
    if patient['medecin_id']:
        medecin = conn.execute(
            "SELECT u.nom, u.prenom, m.specialite FROM utilisateurs u JOIN medecins m ON m.utilisateur_id = u.id WHERE u.id = ?",
            (patient['medecin_id'],)
        ).fetchone()
    nb_messages = conn.execute(
        "SELECT COUNT(*) as c FROM messages WHERE destinataire_id = ? AND lu = 0",
        (session['user_id'],)
    ).fetchone()['c']
    conn.close()
    return render_template('patient_dashboard.html',
                           patient=patient, derniere=derniere,
                           mesures_semaine=mesures_semaine,
                           nb_mesures_mois=nb_mesures_mois,
                           medecin=medecin, nb_messages=nb_messages)

@app.route('/patient/saisir', methods=['GET', 'POST'])
def patient_saisir():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))
    conn = get_db()
    patient = conn.execute(
        "SELECT * FROM patients WHERE utilisateur_id = ?", (session['user_id'],)
    ).fetchone()

    if request.method == 'POST':
        tension_sys = request.form.get('tension_sys') or None
        tension_dia = request.form.get('tension_dia') or None
        pouls = request.form.get('pouls') or None
        glycemie = request.form.get('glycemie') or None
        poids = request.form.get('poids') or None
        note = request.form.get('note', '').strip() or None

        if tension_sys: tension_sys = int(tension_sys)
        if tension_dia: tension_dia = int(tension_dia)
        if pouls: pouls = int(pouls)
        if glycemie: glycemie = float(glycemie)
        if poids: poids = float(poids)

        statut = get_statut_tension(tension_sys, tension_dia)
        now = datetime.now()

        conn.execute("""INSERT INTO mesures
            (patient_id, date_mesure, heure_mesure, tension_sys, tension_dia, pouls, glycemie, poids, note, statut)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (patient['id'], now.strftime('%Y-%m-%d'), now.strftime('%H:%M'),
             tension_sys, tension_dia, pouls, glycemie, poids, note, statut))
        mesure_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        check_alertes(conn, patient['id'], mesure_id, tension_sys, tension_dia, glycemie)
        conn.commit()
        conn.close()
        flash('Mesures enregistrées ! Votre médecin a été informé.', 'success')
        return redirect(url_for('patient_dashboard'))

    conn.close()
    return render_template('patient_saisir.html', patient=patient)

@app.route('/patient/historique')
def patient_historique():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))
    conn = get_db()
    patient = conn.execute(
        "SELECT * FROM patients WHERE utilisateur_id = ?", (session['user_id'],)
    ).fetchone()
    mesures = conn.execute(
        "SELECT * FROM mesures WHERE patient_id = ? ORDER BY date_mesure DESC, heure_mesure DESC",
        (patient['id'],)
    ).fetchall()
    conn.close()
    return render_template('patient_historique.html', mesures=mesures)

@app.route('/patient/messages', methods=['GET', 'POST'])
def patient_messages():
    if 'user_id' not in session or session['role'] != 'patient':
        return redirect(url_for('login'))
    conn = get_db()
    patient = conn.execute(
        "SELECT * FROM patients WHERE utilisateur_id = ?", (session['user_id'],)
    ).fetchone()

    if request.method == 'POST':
        contenu = request.form.get('contenu', '').strip()
        if contenu and patient['medecin_id']:
            conn.execute(
                "INSERT INTO messages (expediteur_id, destinataire_id, contenu) VALUES (?, ?, ?)",
                (session['user_id'], patient['medecin_id'], contenu)
            )
            conn.commit()

    msgs = conn.execute("""
        SELECT m.*, u.nom, u.prenom, u.role
        FROM messages m
        JOIN utilisateurs u ON m.expediteur_id = u.id
        WHERE (m.expediteur_id = ? AND m.destinataire_id = ?)
           OR (m.expediteur_id = ? AND m.destinataire_id = ?)
        ORDER BY m.created_at ASC
    """, (session['user_id'], patient['medecin_id'],
          patient['medecin_id'], session['user_id'])).fetchall()

    conn.execute("UPDATE messages SET lu = 1 WHERE destinataire_id = ?", (session['user_id'],))
    medecin = conn.execute(
        "SELECT u.nom, u.prenom FROM utilisateurs u WHERE u.id = ?", (patient['medecin_id'],)
    ).fetchone() if patient['medecin_id'] else None
    conn.commit()
    conn.close()
    return render_template('patient_messages.html', messages=msgs, medecin=medecin)

# ─────────────────────────────────────────
# MÉDECIN ROUTES
# ─────────────────────────────────────────
@app.route('/medecin')
def medecin_dashboard():
    if 'user_id' not in session or session['role'] != 'medecin':
        return redirect(url_for('login'))
    conn = get_db()
    alertes = conn.execute("""
        SELECT a.*, u.nom, u.prenom FROM alertes a
        JOIN patients p ON a.patient_id = p.id
        JOIN utilisateurs u ON p.utilisateur_id = u.id
        WHERE p.medecin_id = ? AND a.traitee = 0
        ORDER BY a.date_alerte DESC
    """, (session['user_id'],)).fetchall()
    patients_actifs = conn.execute("""
        SELECT p.*, u.nom, u.prenom,
               (SELECT COUNT(*) FROM mesures m WHERE m.patient_id = p.id
                AND m.date_mesure >= date('now','-7 days')) as mesures_semaine,
               (SELECT tension_sys FROM mesures m WHERE m.patient_id = p.id
                ORDER BY m.date_mesure DESC, m.heure_mesure DESC LIMIT 1) as last_sys,
               (SELECT tension_dia FROM mesures m WHERE m.patient_id = p.id
                ORDER BY m.date_mesure DESC, m.heure_mesure DESC LIMIT 1) as last_dia,
               (SELECT date_mesure FROM mesures m WHERE m.patient_id = p.id
                ORDER BY m.date_mesure DESC LIMIT 1) as last_date,
               (SELECT statut FROM mesures m WHERE m.patient_id = p.id
                ORDER BY m.date_mesure DESC LIMIT 1) as last_statut
        FROM patients p
        JOIN utilisateurs u ON p.utilisateur_id = u.id
        WHERE p.medecin_id = ?
        ORDER BY last_statut DESC
    """, (session['user_id'],)).fetchall()
    nb_patients = len(patients_actifs)
    nb_alertes = len(alertes)
    conn.close()
    return render_template('medecin_dashboard.html',
                           alertes=alertes, patients=patients_actifs,
                           nb_patients=nb_patients, nb_alertes=nb_alertes)

@app.route('/medecin/patients')
def medecin_patients():
    if 'user_id' not in session or session['role'] != 'medecin':
        return redirect(url_for('login'))
    conn = get_db()
    patients = conn.execute("""
        SELECT p.*, u.nom, u.prenom, u.email,
               (SELECT tension_sys FROM mesures m WHERE m.patient_id = p.id
                ORDER BY m.date_mesure DESC LIMIT 1) as last_sys,
               (SELECT tension_dia FROM mesures m WHERE m.patient_id = p.id
                ORDER BY m.date_mesure DESC LIMIT 1) as last_dia,
               (SELECT date_mesure FROM mesures m WHERE m.patient_id = p.id
                ORDER BY m.date_mesure DESC LIMIT 1) as last_date,
               (SELECT statut FROM mesures m WHERE m.patient_id = p.id
                ORDER BY m.date_mesure DESC LIMIT 1) as last_statut,
               (SELECT COUNT(*) FROM mesures m WHERE m.patient_id = p.id) as nb_mesures
        FROM patients p
        JOIN utilisateurs u ON p.utilisateur_id = u.id
        WHERE p.medecin_id = ?
        ORDER BY last_statut DESC
    """, (session['user_id'],)).fetchall()
    conn.close()
    return render_template('medecin_patients.html', patients=patients)

@app.route('/medecin/patient/<int:patient_id>')
def medecin_patient_detail(patient_id):
    if 'user_id' not in session or session['role'] != 'medecin':
        return redirect(url_for('login'))
    conn = get_db()
    patient = conn.execute("""
        SELECT p.*, u.nom, u.prenom, u.email FROM patients p
        JOIN utilisateurs u ON p.utilisateur_id = u.id
        WHERE p.id = ? AND p.medecin_id = ?
    """, (patient_id, session['user_id'])).fetchone()
    if not patient:
        return redirect(url_for('medecin_patients'))
    mesures = conn.execute(
        "SELECT * FROM mesures WHERE patient_id = ? ORDER BY date_mesure DESC LIMIT 20",
        (patient_id,)
    ).fetchall()
    alertes = conn.execute(
        "SELECT * FROM alertes WHERE patient_id = ? ORDER BY date_alerte DESC LIMIT 5",
        (patient_id,)
    ).fetchall()
    conn.close()
    return render_template('medecin_patient_detail.html',
                           patient=patient, mesures=mesures, alertes=alertes)

@app.route('/medecin/alertes')
def medecin_alertes():
    if 'user_id' not in session or session['role'] != 'medecin':
        return redirect(url_for('login'))
    conn = get_db()
    alertes = conn.execute("""
        SELECT a.*, u.nom, u.prenom, p.pathologie, p.id as pat_id
        FROM alertes a
        JOIN patients p ON a.patient_id = p.id
        JOIN utilisateurs u ON p.utilisateur_id = u.id
        WHERE p.medecin_id = ?
        ORDER BY a.traitee ASC, a.date_alerte DESC
    """, (session['user_id'],)).fetchall()
    conn.close()
    return render_template('medecin_alertes.html', alertes=alertes)

@app.route('/medecin/alerte/<int:alerte_id>/traiter', methods=['POST'])
def traiter_alerte(alerte_id):
    if 'user_id' not in session or session['role'] != 'medecin':
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute("UPDATE alertes SET traitee = 1 WHERE id = ?", (alerte_id,))
    conn.commit()
    conn.close()
    flash('Alerte marquée comme traitée.', 'success')
    return redirect(url_for('medecin_alertes'))

@app.route('/medecin/messages', methods=['GET', 'POST'])
def medecin_messages():
    if 'user_id' not in session or session['role'] != 'medecin':
        return redirect(url_for('login'))
    conn = get_db()
    patients_list = conn.execute("""
        SELECT p.id, u.id as uid, u.nom, u.prenom,
               (SELECT COUNT(*) FROM messages m WHERE m.expediteur_id = u.id
                AND m.destinataire_id = ? AND m.lu = 0) as non_lus
        FROM patients p JOIN utilisateurs u ON p.utilisateur_id = u.id
        WHERE p.medecin_id = ?
    """, (session['user_id'], session['user_id'])).fetchall()

    selected_uid = request.args.get('patient', type=int)
    if not selected_uid and patients_list:
        selected_uid = patients_list[0]['uid']

    if request.method == 'POST':
        contenu = request.form.get('contenu', '').strip()
        dest_id = request.form.get('destinataire_id', type=int)
        if contenu and dest_id:
            conn.execute(
                "INSERT INTO messages (expediteur_id, destinataire_id, contenu) VALUES (?, ?, ?)",
                (session['user_id'], dest_id, contenu)
            )
            conn.commit()

    msgs = []
    selected_patient = None
    if selected_uid:
        msgs = conn.execute("""
            SELECT m.*, u.nom, u.prenom, u.role FROM messages m
            JOIN utilisateurs u ON m.expediteur_id = u.id
            WHERE (m.expediteur_id = ? AND m.destinataire_id = ?)
               OR (m.expediteur_id = ? AND m.destinataire_id = ?)
            ORDER BY m.created_at ASC
        """, (session['user_id'], selected_uid, selected_uid, session['user_id'])).fetchall()
        conn.execute("UPDATE messages SET lu = 1 WHERE expediteur_id = ? AND destinataire_id = ?",
                     (selected_uid, session['user_id']))
        conn.commit()
        selected_patient = conn.execute(
            "SELECT nom, prenom FROM utilisateurs WHERE id = ?", (selected_uid,)
        ).fetchone()

    conn.close()
    return render_template('medecin_messages.html',
                           patients_list=patients_list, messages=msgs,
                           selected_uid=selected_uid, selected_patient=selected_patient)

# ─────────────────────────────────────────
# API JSON (pour AJAX)
# ─────────────────────────────────────────
@app.route('/api/mesures/<int:patient_id>')
def api_mesures(patient_id):
    conn = get_db()
    mesures = conn.execute(
        "SELECT date_mesure, tension_sys, tension_dia, pouls, glycemie, statut FROM mesures WHERE patient_id = ? ORDER BY date_mesure DESC LIMIT 30",
        (patient_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(m) for m in mesures])

init_db()

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  VitaConnect — Démarrage du serveur")
    print("="*50)
    print("  URL : http://localhost:5000")
    print("\n  Comptes de démonstration :")
    print("  Patient  : lyly@vitaconnect.fr      / demo123")
    print("  Médecin  : ouhimmou@vitaconnect.fr  / demo123")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)
