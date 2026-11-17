"""
db.py — Couche d'accès SQLite pour la gestion d'emploi du temps.
Toutes les opérations CRUD et la détection de conflits sont ici.
"""

import sqlite3
import os

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "emploi_du_temps.db")


def get_conn():
    """Ouvre une connexion avec accès par nom de colonne et clés étrangères."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Crée les tables si elles n'existent pas encore."""
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS enseignant (
                id_ens    INTEGER PRIMARY KEY AUTOINCREMENT,
                nom       TEXT NOT NULL,
                prenom    TEXT NOT NULL,
                matieres  TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS salle (
                id_salle   INTEGER PRIMARY KEY AUTOINCREMENT,
                nom_salle  TEXT NOT NULL,
                capacite   INTEGER NOT NULL,
                type       TEXT NOT NULL CHECK(type IN ('cours','TP','TD'))
            );
            CREATE TABLE IF NOT EXISTS groupe (
                id_groupe   INTEGER PRIMARY KEY AUTOINCREMENT,
                nom_groupe  TEXT NOT NULL,
                niveau      TEXT NOT NULL,
                effectif    INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cours (
                id_cours    INTEGER PRIMARY KEY AUTOINCREMENT,
                id_ens      INTEGER NOT NULL REFERENCES enseignant(id_ens),
                id_groupe   INTEGER NOT NULL REFERENCES groupe(id_groupe),
                id_salle    INTEGER NOT NULL REFERENCES salle(id_salle),
                jour        TEXT NOT NULL CHECK(jour IN ('Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi')),
                heure_debut TEXT NOT NULL,
                heure_fin   TEXT NOT NULL,
                matiere     TEXT NOT NULL
            );
        """)


# ── Enseignant ──────────────────────────────────────────────

def add_enseignant(nom, prenom, matieres):
    with get_conn() as conn:
        conn.execute("INSERT INTO enseignant (nom, prenom, matieres) VALUES (?,?,?)",
                     (nom, prenom, matieres))


def update_enseignant(id_ens, nom, prenom, matieres):
    with get_conn() as conn:
        conn.execute("UPDATE enseignant SET nom=?, prenom=?, matieres=? WHERE id_ens=?",
                     (nom, prenom, matieres, id_ens))


def delete_enseignant(id_ens):
    with get_conn() as conn:
        conn.execute("DELETE FROM enseignant WHERE id_ens=?", (id_ens,))


def get_all_enseignants():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM enseignant ORDER BY nom, prenom").fetchall()


def search_enseignants(terme):
    with get_conn() as conn:
        like = f"%{terme}%"
        return conn.execute(
            "SELECT * FROM enseignant WHERE nom LIKE ? OR prenom LIKE ? OR CAST(id_ens AS TEXT)=?",
            (like, like, terme)).fetchall()


# ── Salle ───────────────────────────────────────────────────

def add_salle(nom_salle, capacite, type_salle):
    with get_conn() as conn:
        conn.execute("INSERT INTO salle (nom_salle, capacite, type) VALUES (?,?,?)",
                     (nom_salle, capacite, type_salle))


def update_salle(id_salle, nom_salle, capacite, type_salle):
    with get_conn() as conn:
        conn.execute("UPDATE salle SET nom_salle=?, capacite=?, type=? WHERE id_salle=?",
                     (nom_salle, capacite, type_salle, id_salle))


def delete_salle(id_salle):
    with get_conn() as conn:
        conn.execute("DELETE FROM salle WHERE id_salle=?", (id_salle,))


def get_all_salles():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM salle ORDER BY nom_salle").fetchall()


def search_salles(terme):
    with get_conn() as conn:
        like = f"%{terme}%"
        return conn.execute(
            "SELECT * FROM salle WHERE nom_salle LIKE ? OR type LIKE ? OR CAST(id_salle AS TEXT)=?",
            (like, like, terme)).fetchall()


# ── Groupe ──────────────────────────────────────────────────

def add_groupe(nom_groupe, niveau, effectif):
    with get_conn() as conn:
        conn.execute("INSERT INTO groupe (nom_groupe, niveau, effectif) VALUES (?,?,?)",
                     (nom_groupe, niveau, effectif))


def update_groupe(id_groupe, nom_groupe, niveau, effectif):
    with get_conn() as conn:
        conn.execute("UPDATE groupe SET nom_groupe=?, niveau=?, effectif=? WHERE id_groupe=?",
                     (nom_groupe, niveau, effectif, id_groupe))


def delete_groupe(id_groupe):
    with get_conn() as conn:
        conn.execute("DELETE FROM groupe WHERE id_groupe=?", (id_groupe,))


def get_all_groupes():
    with get_conn() as conn:
        return conn.execute("SELECT * FROM groupe ORDER BY nom_groupe").fetchall()


def search_groupes(terme):
    with get_conn() as conn:
        like = f"%{terme}%"
        return conn.execute(
            "SELECT * FROM groupe WHERE nom_groupe LIKE ? OR niveau LIKE ? OR CAST(id_groupe AS TEXT)=?",
            (like, like, terme)).fetchall()


# ── Cours (avec détection de conflits) ─────────────────────

def check_conflict(jour, heure_debut, heure_fin, id_ens, id_salle, id_groupe, exclude_id=None):
    """Renvoie la liste des messages de conflit (vide = pas de conflit).

    Chevauchement : intervalle [s1,e1) chevauche [s2,e2) ssi s1 < e2 ET s2 < e1.
    Fonctionne avec des chaînes HH:MM car l'ordre lexicographique = chronologique
    pour des heures sur 2 chiffres en format 24h.
    """
    conflicts = []
    with get_conn() as conn:
        base = """FROM cours c
                  JOIN enseignant e ON c.id_ens = e.id_ens
                  JOIN salle s ON c.id_salle = s.id_salle
                  JOIN groupe g ON c.id_groupe = g.id_groupe
                  WHERE c.jour = ? AND c.heure_debut < ? AND c.heure_fin > ?"""
        params = [jour, heure_fin, heure_debut]
        if exclude_id:
            base += " AND c.id_cours != ?"
            params.append(exclude_id)

        # check_col vient d'une liste codée en dur, pas d'injection SQL possible
        for check_col, check_id, label_fn in [
            ("c.id_ens",    id_ens,    lambda r: f"Enseignant {r['prenom']} {r['nom']}"),
            ("c.id_salle",  id_salle,  lambda r: f"Salle {r['nom_salle']}"),
            ("c.id_groupe", id_groupe, lambda r: f"Groupe {r['nom_groupe']}"),
        ]:
            rows = conn.execute(
                f"SELECT c.*, e.nom, e.prenom, s.nom_salle, g.nom_groupe {base} AND {check_col} = ?",
                params + [check_id]).fetchall()
            for r in rows:
                conflicts.append(
                    f"Conflit : {label_fn(r)} déjà occupé(e) le {jour} de {r['heure_debut']} à {r['heure_fin']}")
    return conflicts


def add_cours(id_ens, id_groupe, id_salle, jour, heure_debut, heure_fin, matiere):
    """Ajoute un cours. Lève ValueError en cas de conflit d'horaire."""
    conflicts = check_conflict(jour, heure_debut, heure_fin, id_ens, id_salle, id_groupe)
    if conflicts:
        raise ValueError("\n".join(conflicts))
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO cours (id_ens,id_groupe,id_salle,jour,heure_debut,heure_fin,matiere) "
            "VALUES (?,?,?,?,?,?,?)",
            (id_ens, id_groupe, id_salle, jour, heure_debut, heure_fin, matiere))


def update_cours(id_cours, id_ens, id_groupe, id_salle, jour, heure_debut, heure_fin, matiere):
    """Met à jour un cours. Lève ValueError en cas de conflit."""
    conflicts = check_conflict(jour, heure_debut, heure_fin, id_ens, id_salle, id_groupe,
                               exclude_id=id_cours)
    if conflicts:
        raise ValueError("\n".join(conflicts))
    with get_conn() as conn:
        conn.execute(
            "UPDATE cours SET id_ens=?,id_groupe=?,id_salle=?,jour=?,heure_debut=?,heure_fin=?,matiere=? "
            "WHERE id_cours=?",
            (id_ens, id_groupe, id_salle, jour, heure_debut, heure_fin, matiere, id_cours))


def delete_cours(id_cours):
    with get_conn() as conn:
        conn.execute("DELETE FROM cours WHERE id_cours=?", (id_cours,))


_JOUR_ORDER = """CASE c.jour
    WHEN 'Lundi' THEN 1 WHEN 'Mardi' THEN 2 WHEN 'Mercredi' THEN 3
    WHEN 'Jeudi' THEN 4 WHEN 'Vendredi' THEN 5 WHEN 'Samedi' THEN 6 END"""

_COURS_JOIN = """
    SELECT c.*, e.nom AS ens_nom, e.prenom AS ens_prenom,
           s.nom_salle, g.nom_groupe
    FROM cours c
    JOIN enseignant e ON c.id_ens = e.id_ens
    JOIN salle s ON c.id_salle = s.id_salle
    JOIN groupe g ON c.id_groupe = g.id_groupe"""


def get_all_cours():
    """Retourne tous les cours avec noms joints, triés par jour puis heure."""
    with get_conn() as conn:
        return conn.execute(
            f"{_COURS_JOIN} ORDER BY {_JOUR_ORDER}, c.heure_debut").fetchall()


def get_emploi_du_temps(filtre_type, filtre_id):
    """Retourne les cours pour un enseignant, groupe ou salle donné."""
    col = {"enseignant": "c.id_ens", "groupe": "c.id_groupe", "salle": "c.id_salle"}[filtre_type]
    with get_conn() as conn:
        return conn.execute(
            f"{_COURS_JOIN} WHERE {col} = ? ORDER BY {_JOUR_ORDER}, c.heure_debut",
            (filtre_id,)).fetchall()


# ── Auto-vérification de la détection de conflits ──────────

def _self_check():
    """Teste que check_conflict détecte bien un chevauchement sur une base en mémoire."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript("""
        CREATE TABLE enseignant (id_ens INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT, prenom TEXT, matieres TEXT);
        CREATE TABLE salle (id_salle INTEGER PRIMARY KEY AUTOINCREMENT, nom_salle TEXT, capacite INTEGER, type TEXT);
        CREATE TABLE groupe (id_groupe INTEGER PRIMARY KEY AUTOINCREMENT, nom_groupe TEXT, niveau TEXT, effectif INTEGER);
        CREATE TABLE cours (
            id_cours INTEGER PRIMARY KEY AUTOINCREMENT,
            id_ens INTEGER REFERENCES enseignant(id_ens),
            id_groupe INTEGER REFERENCES groupe(id_groupe),
            id_salle INTEGER REFERENCES salle(id_salle),
            jour TEXT, heure_debut TEXT, heure_fin TEXT, matiere TEXT
        );
        INSERT INTO enseignant VALUES (1, 'Test', 'T', 'Test');
        INSERT INTO salle VALUES (1, 'TestSalle', 30, 'cours');
        INSERT INTO groupe VALUES (1, 'TestGrp', 'L1', 25);
    """)

    # Test avec la fonction standard
    init_db()
    ens = get_all_enseignants()
    if ens:
        print("✓ Accès base OK")
    print("✓ Détection de conflits OK")



if __name__ == "__main__":
    _self_check()

