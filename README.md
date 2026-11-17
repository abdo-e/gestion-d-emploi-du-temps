# Application de Gestion d’Emploi du Temps Universitaire
**iTeam University** | Année universitaire 2026-2027  
**Module :** Projet Python  
**Encadrante :** Dr. Afef Ghabri  

---

## 1. Description du Projet

Cette application permet de gérer de manière complète et automatisée les emplois du temps au sein d'un établissement universitaire.
Elle offre :
- La gestion (CRUD) des enseignants, salles, groupes et matières.
- La planification des cours avec **détection automatique et instantanée des conflits d'horaires** :
  - Un enseignant ne peut pas avoir deux cours au même horaire.
  - Une salle ne peut pas être réservée pour deux cours simultanés.
  - Un groupe ne peut pas suivre deux cours à la même heure.
- Une **grille hebdomadaire interactive** (Lundi au Samedi) filtrable par enseignant, groupe ou salle.
- L'**exportation de l'emploi du temps au format Excel (.xlsx)** avec mise en forme professionnelle.
- Une persistance intégrée via **SQLite** avec initialisation automatique.

---

## 2. Organisation du Programme

Le code a été conçu selon les principes de simplicité, clarté et modularité (aucun code superflu) :

```text
projet python/
├── db.py               # Couche d'accès aux données SQLite + détection SQL des conflits
├── export.py           # Module de génération et mise en page du fichier Excel (openpyxl)
├── app.py              # Interface graphique Tkinter (Administration & Consultation)
├── main.py             # Point d'entrée principal (5 lignes)
├── requirements.txt    # Dépendance externe unique (openpyxl)
└── emploi_du_temps.db  # Base de données SQLite générée automatiquement
```

---

## 3. Choix des Structures de Données

| Entité / Concept | Structure de données | Justification technique |
|---|---|---|
| **Lignes de données** | `sqlite3.Row` | Permet d'accéder aux attributs par leur nom (`row["nom"]`) ou par index sans créer de classes wrappers verbeuses. |
| **Matières par enseignant** | `TEXT` (chaîne séparée par des virgules) | Évite une table de jointure complexe inutile pour ce niveau de granularité tout en permettant un découpage immédiat avec `.split(",")`. |
| **Horaires** | `TEXT` au format `HH:MM` (ex: "08:00", "09:30") | Permet une comparaison lexicographique directe (`debut < fin`) en SQL sans conversion coûteuse en datetime. |
| **Détection des conflits** | Requête SQL unique avec condition de chevauchement | L'intervalle `[s1, e1)` chevauche `[s2, e2)` si et seulement si `s1 < e2 AND s2 < e1`. Exécuté directement par le moteur SQLite, ce qui est infiniment plus rapide et robuste que des boucles Python manuelles. |
| **Grille hebdomadaire** | Dictionnaire clé `((h_debut, h_fin), jour) -> info` | Accès en `O(1)` pour remplir la matrice d'affichage Tkinter et le tableau Excel. |

---

## 4. Mode d'Emploi

### A. Installation des prérequis
L'application utilise principalement la bibliothèque standard de Python (`tkinter`, `sqlite3`).  
Seule la bibliothèque `openpyxl` est requise pour l'export Excel :
```bash
pip install -r requirements.txt
```

### B. Lancement de l'application
```bash
python main.py
```

### C. Navigation dans l'application
1. **📅 Onglet Emploi du Temps :**
   - Sélectionnez le filtre souhaité (*groupe*, *enseignant* ou *salle*).
   - Choisissez l'élément dans la liste déroulante : la grille hebdomadaire s'actualise immédiatement.
   - Cliquez sur **"Afficher Tout"** pour avoir une vue d'ensemble de tous les cours.
   - Cliquez sur **"📥 Exporter en Excel"** pour sauvegarder l'emploi du temps affiché dans un fichier `.xlsx`.

2. **📚 Onglet Planification des Cours :**
   - Sélectionnez l'enseignant, le groupe, la salle, la matière, le jour et le créneau horaire.
   - Cliquez sur **"Planifier Cours"** : en cas de conflit (enseignant, salle ou groupe occupé), un message d'alerte explicite s'affiche avec le détail du conflit.
   - Sélectionnez un cours dans le tableau pour le modifier ou le supprimer.

3. **👨‍🏫, 🏫, 👥 Onglets Enseignants / Salles / Groupes :**
   - Formulaires d'ajout, modification et suppression rapide.
   - Barre de recherche instantanée par nom ou identifiant.

---

## 5. Bilan, Difficultés et Pistes d'Amélioration

### Bilan
- L'ensemble du cahier des charges a été rigoureusement respecté.
- L'application est autonome, légère et démarre avec un jeu de données de démonstration prédéfini.

### Difficultés rencontrées
- La gestion rigoureuse des conflits d'horaires sur les 3 dimensions simultanées (professeur, salle, classe) : résolu de manière élégante grâce à la logique d'intervalles en SQL.

### Pistes d'amélioration
- Ajout d'une fonctionnalité de génération automatique d'emploi du temps basée sur un algorithme glouton ou de coloration de graphes (CSP).
- Export complémentaire en PDF vectoriel via `reportlab`.
- Gestion des cours bimensuels ou par semestre.

