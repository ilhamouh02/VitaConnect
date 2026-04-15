# VitaConnect — Plateforme de suivi médical numérique

Application web full-stack — Python Flask + SQLite

---

## Lancer l'application en 3 étapes

### Étape 1 — Installer Python (si pas déjà installé)
Télécharger sur https://python.org (version 3.10 ou supérieure)

### Étape 2 — Installer Flask
Ouvrez un terminal dans le dossier `vitaconnect/` et tapez :
```
pip install flask
```

### Étape 3 — Lancer l'appli
```
python app.py
```
Puis ouvrez votre navigateur sur : **http://localhost:5000**

---

## Comptes de démonstration

| Rôle | Email | Mot de passe |
|------|-------|-------------|
| Patient | marcel@vitaconnect.fr | demo123 |
| Médecin | benali@vitaconnect.fr | demo123 |

---

## Fonctionnalités

### Espace Patient
- Tableau de bord avec dernières mesures
- Saisie de mesures (tension, glycémie, poids, note)
- Détection automatique des valeurs anormales
- Historique complet de toutes les mesures
- Messagerie avec le médecin traitant

### Espace Médecin
- Tableau de bord avec vue d'ensemble patients
- Liste des patients triée par criticité
- Alertes automatiques quand un patient dépasse les seuils
- Dossier détaillé par patient (historique + alertes)
- Messagerie avec les patients
- Marquer les alertes comme traitées

### Inscription
- Création de compte patient ou médecin
- Attribution automatique du premier médecin disponible

---

## Base de données

L'application utilise SQLite — le fichier `vitaconnect.db` est créé automatiquement au premier lancement.

Tables :
- `utilisateurs` — comptes patients et médecins
- `patients` — profils patients avec pathologie et médecin référent
- `medecins` — profils médecins avec spécialité
- `mesures` — toutes les mesures saisies
- `alertes` — alertes générées automatiquement
- `messages` — messagerie entre patients et médecins

---

## Stack technique

- **Backend** : Python 3 + Flask
- **Base de données** : SQLite (via sqlite3 natif Python)
- **Frontend** : HTML5 + CSS3 + JavaScript vanilla
- **Templates** : Jinja2 (inclus avec Flask)
- **Fonts** : Google Fonts (Playfair Display + DM Sans)

---

Projet MDPD-100 · B3/M1 2025-2026 · Ilham
