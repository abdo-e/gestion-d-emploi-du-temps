"""
app.py — Interface graphique Tkinter pour la gestion d'emploi du temps universitaire.
Fournit la gestion CRUD des entités, la planification avec détection des conflits,
la consultation hebdomadaire filtrée et l'export Excel.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import db
import export

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]
CRENEAUX_DEFAUT = [
    ("08:00", "09:30"),
    ("09:45", "11:15"),
    ("11:30", "13:00"),
    ("14:00", "15:30"),
    ("15:45", "17:15")
]


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestion d'Emploi du Temps Universitaire - iTeam University")
        self.geometry("1100x700")
        self.minsize(900, 600)

        # Style moderne avec bordures visibles pour les tableaux
        self.style = ttk.Style(self)
        self.style.theme_use("clam")
        self.style.configure(
            "Treeview",
            rowheight=28,
            font=("Segoe UI", 9),
            background="#FFFFFF",
            foreground="#1E293B",
            fieldbackground="#FFFFFF",
            borderwidth=1,
            relief="solid",
            lightcolor="#94A3B8",
            darkcolor="#94A3B8",
            bordercolor="#94A3B8"
        )
        self.style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#E2E8F0",
            foreground="#0F172A",
            relief="solid",
            borderwidth=1,
            bordercolor="#94A3B8"
        )
        self.style.map(
            "Treeview.Heading",
            background=[("active", "#CBD5E1")]
        )
        self.style.map(
            "Treeview",
            background=[("selected", "#2563EB")],
            foreground=[("selected", "#FFFFFF")]
        )
        self.style.configure("TLabel", font=("Segoe UI", 9))
        self.style.configure("TButton", font=("Segoe UI", 9))

        # Onglets principaux
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Construction des onglets
        self._build_consultation_tab()
        self._build_cours_tab()
        self._build_enseignants_tab()
        self._build_salles_tab()
        self._build_groupes_tab()

        # Configurer les lignes alternées (effet quadrillage / bordures)
        for tree in [self.tree_edt, self.tree_cours, self.tree_ens, self.tree_salle, self.tree_grp]:
            tree.tag_configure("evenrow", background="#F1F5F9")
            tree.tag_configure("oddrow", background="#FFFFFF")

        # Écouter le changement d'onglet pour rafraîchir les listes
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Charger des données de test si la base est vide
        self._verifier_donnees_initiales()

    def _on_tab_changed(self, event):
        tab_idx = self.notebook.index(self.notebook.select())
        if tab_idx == 0:
            self._actualiser_filtre_consultation()
            self._actualiser_grille_consultation()
        elif tab_idx == 1:
            self._charger_combos_cours()
            self._actualiser_table_cours()
        elif tab_idx == 2:
            self._actualiser_table_enseignants()
        elif tab_idx == 3:
            self._actualiser_table_salles()
        elif tab_idx == 4:
            self._actualiser_table_groupes()

    def _verifier_donnees_initiales(self):
        """Remplit la base avec un jeu d'essai minimal si elle est vide."""
        if not db.get_all_enseignants():
            db.add_enseignant("Ben Salem", "Karim", "Python,Algorithmique")
            db.add_enseignant("Trabelsi", "Amira", "Bases de données,SQL")
            db.add_enseignant("Gharbi", "Mohamed", "Réseaux,Systèmes")

            db.add_salle("Labo 1", 25, "TP")
            db.add_salle("Amphi A", 120, "cours")
            db.add_salle("Salle 102", 35, "TD")

            db.add_groupe("L1-INFO", "Licence 1", 30)
            db.add_groupe("L2-DSI", "Licence 2", 25)

        if not db.get_all_cours():
            ens = db.get_all_enseignants()
            salles = db.get_all_salles()
            groupes = db.get_all_groupes()
            if ens and salles and groupes:
                db.add_cours(ens[0]["id_ens"], groupes[0]["id_groupe"], salles[0]["id_salle"], "Lundi", "08:00", "09:30", "Python")
                if len(ens) > 1 and len(salles) > 2:
                    db.add_cours(ens[1]["id_ens"], groupes[0]["id_groupe"], salles[2]["id_salle"], "Lundi", "09:45", "11:15", "Bases de données")
                if len(ens) > 2 and len(groupes) > 1 and len(salles) > 1:
                    db.add_cours(ens[2]["id_ens"], groupes[1]["id_groupe"], salles[1]["id_salle"], "Mardi", "14:00", "15:30", "Réseaux")

        self._actualiser_filtre_consultation()
        self._actualiser_grille_consultation()

    # =========================================================================
    # ONGLET 1: CONSULTATION / EMPLOI DU TEMPS HEBDOMADAIRE
    # =========================================================================
    def _build_consultation_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="📅 Emploi du Temps")

        # Barre supérieure : Filtres & Actions
        filter_frame = ttk.LabelFrame(tab, text="Filtres de consultation", padding=10)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(filter_frame, text="Consulter par :").pack(side=tk.LEFT, padx=5)
        self.cons_type_var = tk.StringVar(value="groupe")
        combo_type = ttk.Combobox(
            filter_frame, textvariable=self.cons_type_var,
            values=["groupe", "enseignant", "salle"], state="readonly", width=12
        )
        combo_type.pack(side=tk.LEFT, padx=5)
        combo_type.bind("<<ComboboxSelected>>", lambda e: self._actualiser_filtre_consultation())

        ttk.Label(filter_frame, text="Sélectionner :").pack(side=tk.LEFT, padx=(15, 5))
        self.cons_cible_combo = ttk.Combobox(filter_frame, state="readonly", width=35)
        self.cons_cible_combo.pack(side=tk.LEFT, padx=5)
        self.cons_cible_combo.bind("<<ComboboxSelected>>", lambda e: self._actualiser_grille_consultation())

        btn_tous = ttk.Button(filter_frame, text="Afficher Tout", command=self._afficher_tous_cours_grille)
        btn_tous.pack(side=tk.LEFT, padx=10)

        btn_export = ttk.Button(filter_frame, text="📥 Exporter en Excel", command=self._exporter_excel)
        btn_export.pack(side=tk.RIGHT, padx=5)

        # Label d'information sur la sélection courante
        self.lbl_titre_edt = ttk.Label(tab, text="Emploi du temps", font=("Segoe UI", 12, "bold"))
        self.lbl_titre_edt.pack(anchor=tk.W, pady=(0, 5))

        # Tableau de grille hebdomadaire (Heure | Lundi | ... | Samedi) avec bordure
        table_frame = tk.Frame(tab, bd=1, relief="solid", bg="#94A3B8")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        cols = ["Horaire"] + JOURS
        self.tree_edt = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree_edt.heading("Horaire", text="Horaire")
        self.tree_edt.column("Horaire", width=110, anchor=tk.CENTER)
        for j in JOURS:
            self.tree_edt.heading(j, text=j)
            self.tree_edt.column(j, width=150, anchor=tk.CENTER)

        scrollbar_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree_edt.yview)
        scrollbar_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self.tree_edt.xview)
        self.tree_edt.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.tree_edt.pack(fill=tk.BOTH, expand=True)

        self.current_edt_courses = []

    def _actualiser_filtre_consultation(self):
        f_type = self.cons_type_var.get()
        items = []
        self._cons_map = {}

        if f_type == "enseignant":
            for r in db.get_all_enseignants():
                txt = f"{r['id_ens']} - {r['prenom']} {r['nom']}"
                items.append(txt)
                self._cons_map[txt] = r["id_ens"]
        elif f_type == "salle":
            for r in db.get_all_salles():
                txt = f"{r['id_salle']} - {r['nom_salle']} ({r['type']})"
                items.append(txt)
                self._cons_map[txt] = r["id_salle"]
        else:
            for r in db.get_all_groupes():
                txt = f"{r['id_groupe']} - {r['nom_groupe']} ({r['niveau']})"
                items.append(txt)
                self._cons_map[txt] = r["id_groupe"]

        self.cons_cible_combo["values"] = items
        if items:
            self.cons_cible_combo.current(0)
            self._actualiser_grille_consultation()
        else:
            self.cons_cible_combo.set("")
            self.tree_edt.delete(*self.tree_edt.get_children())
            self.current_edt_courses = []

    def _actualiser_grille_consultation(self):
        choix = self.cons_cible_combo.get()
        if not choix or choix not in self._cons_map:
            return

        filtre_id = self._cons_map[choix]
        filtre_type = self.cons_type_var.get()
        courses = db.get_emploi_du_temps(filtre_type, filtre_id)
        self.current_edt_courses = courses
        self.lbl_titre_edt.config(text=f"Emploi du temps : {choix}")
        self._remplir_arbre_grille(courses)

    def _afficher_tous_cours_grille(self):
        courses = db.get_all_cours()
        self.current_edt_courses = courses
        self.lbl_titre_edt.config(text="Emploi du temps : Vue Globale (Tous les cours)")
        self._remplir_arbre_grille(courses)

    def _remplir_arbre_grille(self, courses):
        self.tree_edt.delete(*self.tree_edt.get_children())

        # Créneaux utilisés ou par défaut
        creneaux_cours = {(c["heure_debut"], c["heure_fin"]) for c in courses}
        tous_creneaux = sorted(creneaux_cours.union(set(CRENEAUX_DEFAUT)))

        # Dictionnaire grille (créneau, jour) -> texte
        grid = {}
        for c in courses:
            key = ((c["heure_debut"], c["heure_fin"]), c["jour"])
            info = f"{c['matiere']} ({c['nom_groupe']}, {c['nom_salle']}, {c['ens_nom']})"
            if key in grid:
                grid[key] += " | " + info
            else:
                grid[key] = info

        for idx, slot in enumerate(tous_creneaux):
            row_vals = [f"{slot[0]} - {slot[1]}"]
            for j in JOURS:
                row_vals.append(grid.get((slot, j), ""))
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree_edt.insert("", tk.END, values=row_vals, tags=(tag,))

    def _exporter_excel(self):
        if not self.current_edt_courses:
            messagebox.showinfo("Exportation", "Aucun cours à exporter dans la vue actuelle.")
            return

        titre = self.lbl_titre_edt.cget("text")
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Fichier Excel", "*.xlsx")],
            initialfile="Emploi_du_temps.xlsx",
            title="Enregistrer l'emploi du temps"
        )
        if filename:
            try:
                export.export_excel(self.current_edt_courses, filename, titre=titre)
                messagebox.showinfo("Succès", f"Emploi du temps exporté avec succès dans :\n{filename}")
            except Exception as e:
                messagebox.showerror("Erreur d'exportation", f"Impossible d'exporter le fichier :\n{e}")

    # =========================================================================
    # ONGLET 2: PLANIFICATION DES COURS
    # =========================================================================
    def _build_cours_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="📚 Planification des Cours")

        # Formulaire
        form = ttk.LabelFrame(tab, text="Planifier / Modifier un cours", padding=10)
        form.pack(fill=tk.X, pady=(0, 10))

        # Ligne 1
        ttk.Label(form, text="Enseignant :").grid(row=0, column=0, sticky=tk.W, padx=5, pady=4)
        self.cb_cours_ens = ttk.Combobox(form, state="readonly", width=28)
        self.cb_cours_ens.grid(row=0, column=1, padx=5, pady=4)
        self.cb_cours_ens.bind("<<ComboboxSelected>>", self._on_ens_selected_in_cours)

        ttk.Label(form, text="Groupe :").grid(row=0, column=2, sticky=tk.W, padx=5, pady=4)
        self.cb_cours_grp = ttk.Combobox(form, state="readonly", width=25)
        self.cb_cours_grp.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(form, text="Salle :").grid(row=0, column=4, sticky=tk.W, padx=5, pady=4)
        self.cb_cours_salle = ttk.Combobox(form, state="readonly", width=25)
        self.cb_cours_salle.grid(row=0, column=5, padx=5, pady=4)

        # Ligne 2
        ttk.Label(form, text="Matière :").grid(row=1, column=0, sticky=tk.W, padx=5, pady=4)
        self.cb_cours_mat = ttk.Combobox(form, width=26)
        self.cb_cours_mat.grid(row=1, column=1, padx=5, pady=4)

        ttk.Label(form, text="Jour :").grid(row=1, column=2, sticky=tk.W, padx=5, pady=4)
        self.cb_cours_jour = ttk.Combobox(form, values=JOURS, state="readonly", width=23)
        self.cb_cours_jour.set("Lundi")
        self.cb_cours_jour.grid(row=1, column=3, padx=5, pady=4)

        ttk.Label(form, text="Créneau horaire :").grid(row=1, column=4, sticky=tk.W, padx=5, pady=4)
        horaires_box = ttk.Frame(form)
        horaires_box.grid(row=1, column=5, sticky=tk.W, padx=5, pady=4)

        self.cb_h_debut = ttk.Combobox(
            horaires_box, values=["08:00", "09:45", "11:30", "14:00", "15:45"], width=7
        )
        self.cb_h_debut.set("08:00")
        self.cb_h_debut.pack(side=tk.LEFT)
        ttk.Label(horaires_box, text=" à ").pack(side=tk.LEFT)
        self.cb_h_fin = ttk.Combobox(
            horaires_box, values=["09:30", "11:15", "13:00", "15:30", "17:15"], width=7
        )
        self.cb_h_fin.set("09:30")
        self.cb_h_fin.pack(side=tk.LEFT)

        # Boutons d'action
        btn_box = ttk.Frame(form)
        btn_box.grid(row=2, column=0, columnspan=6, pady=8)

        self.btn_cours_add = ttk.Button(btn_box, text="Planifier Cours", command=self._action_ajouter_cours)
        self.btn_cours_add.pack(side=tk.LEFT, padx=5)

        self.btn_cours_mod = ttk.Button(btn_box, text="Modifier Sélection", command=self._action_modifier_cours)
        self.btn_cours_mod.pack(side=tk.LEFT, padx=5)

        self.btn_cours_del = ttk.Button(btn_box, text="Supprimer Sélection", command=self._action_supprimer_cours)
        self.btn_cours_del.pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_box, text="Réinitialiser", command=self._reset_form_cours).pack(side=tk.LEFT, padx=5)

        # Liste des cours
        list_frame = ttk.LabelFrame(tab, text="Liste des cours planifiés", padding=5)
        list_frame.pack(fill=tk.BOTH, expand=True)

        cols = ["id", "jour", "debut", "fin", "matiere", "enseignant", "groupe", "salle"]
        table_frame = tk.Frame(list_frame, bd=1, relief="solid", bg="#94A3B8")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        self.tree_cours = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree_cours.heading("id", text="ID")
        self.tree_cours.column("id", width=40, anchor=tk.CENTER)
        self.tree_cours.heading("jour", text="Jour")
        self.tree_cours.column("jour", width=90)
        self.tree_cours.heading("debut", text="Début")
        self.tree_cours.column("debut", width=70, anchor=tk.CENTER)
        self.tree_cours.heading("fin", text="Fin")
        self.tree_cours.column("fin", width=70, anchor=tk.CENTER)
        self.tree_cours.heading("matiere", text="Matière")
        self.tree_cours.column("matiere", width=140)
        self.tree_cours.heading("enseignant", text="Enseignant")
        self.tree_cours.column("enseignant", width=140)
        self.tree_cours.heading("groupe", text="Groupe")
        self.tree_cours.column("groupe", width=110)
        self.tree_cours.heading("salle", text="Salle")
        self.tree_cours.column("salle", width=110)

        sb_cours = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree_cours.yview)
        self.tree_cours.configure(yscrollcommand=sb_cours.set)
        sb_cours.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_cours.pack(fill=tk.BOTH, expand=True)
        self.tree_cours.bind("<<TreeviewSelect>>", self._on_cours_row_select)

        self.selected_cours_id = None
        self._map_ens = {}
        self._map_grp = {}
        self._map_salle = {}

    def _charger_combos_cours(self):
        # Enseignants
        self._map_ens = {}
        ens_items = []
        for r in db.get_all_enseignants():
            txt = f"{r['id_ens']} - {r['prenom']} {r['nom']}"
            ens_items.append(txt)
            self._map_ens[txt] = (r["id_ens"], r["matieres"].split(","))
        self.cb_cours_ens["values"] = ens_items

        # Groupes
        self._map_grp = {}
        grp_items = []
        for r in db.get_all_groupes():
            txt = f"{r['id_groupe']} - {r['nom_groupe']}"
            grp_items.append(txt)
            self._map_grp[txt] = r["id_groupe"]
        self.cb_cours_grp["values"] = grp_items

        # Salles
        self._map_salle = {}
        salle_items = []
        for r in db.get_all_salles():
            txt = f"{r['id_salle']} - {r['nom_salle']} ({r['type']}, cap:{r['capacite']})"
            salle_items.append(txt)
            self._map_salle[txt] = r["id_salle"]
        self.cb_cours_salle["values"] = salle_items

    def _on_ens_selected_in_cours(self, event):
        txt = self.cb_cours_ens.get()
        if txt in self._map_ens:
            _, mats = self._map_ens[txt]
            self.cb_cours_mat["values"] = [m.strip() for m in mats if m.strip()]
            if mats:
                self.cb_cours_mat.set(mats[0].strip())

    def _actualiser_table_cours(self):
        self.tree_cours.delete(*self.tree_cours.get_children())
        for idx, c in enumerate(db.get_all_cours()):
            ens_nom = f"{c['ens_prenom']} {c['ens_nom']}"
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree_cours.insert("", tk.END, values=[
                c["id_cours"], c["jour"], c["heure_debut"], c["heure_fin"],
                c["matiere"], ens_nom, c["nom_groupe"], c["nom_salle"]
            ], tags=(tag,))

    def _on_cours_row_select(self, event):
        sel = self.tree_cours.selection()
        if not sel:
            return
        vals = self.tree_cours.item(sel[0], "values")
        self.selected_cours_id = int(vals[0])

        self.cb_cours_jour.set(vals[1])
        self.cb_h_debut.set(vals[2])
        self.cb_h_fin.set(vals[3])
        self.cb_cours_mat.set(vals[4])

        # Trouver et sélectionner dans les combos
        for txt in self.cb_cours_ens["values"]:
            if txt.startswith(str(self.selected_cours_id)):
                pass
        for txt, (e_id, _) in self._map_ens.items():
            if vals[5] in txt:
                self.cb_cours_ens.set(txt)
                break
        for txt, g_id in self._map_grp.items():
            if vals[6] == txt.split(" - ")[-1]:
                self.cb_cours_grp.set(txt)
                break
        for txt, s_id in self._map_salle.items():
            if vals[7] in txt:
                self.cb_cours_salle.set(txt)
                break

    def _reset_form_cours(self):
        self.selected_cours_id = None
        self.cb_cours_ens.set("")
        self.cb_cours_grp.set("")
        self.cb_cours_salle.set("")
        self.cb_cours_mat.set("")
        self.cb_cours_jour.set("Lundi")
        self.cb_h_debut.set("08:00")
        self.cb_h_fin.set("09:30")
        self.tree_cours.selection_remove(self.tree_cours.selection())

    def _action_ajouter_cours(self):
        try:
            ens_txt = self.cb_cours_ens.get()
            grp_txt = self.cb_cours_grp.get()
            salle_txt = self.cb_cours_salle.get()
            matiere = self.cb_cours_mat.get().strip()
            jour = self.cb_cours_jour.get()
            h_deb = self.cb_h_debut.get().strip()
            h_fin = self.cb_h_fin.get().strip()

            if not (ens_txt and grp_txt and salle_txt and matiere and h_deb and h_fin):
                messagebox.showwarning("Champs requis", "Veuillez remplir tous les champs du cours.")
                return

            if h_deb >= h_fin:
                messagebox.showerror("Horaire invalide", "L'heure de fin doit être postérieure à l'heure de début.")
                return

            id_ens = self._map_ens[ens_txt][0]
            id_grp = self._map_grp[grp_txt]
            id_salle = self._map_salle[salle_txt]

            db.add_cours(id_ens, id_grp, id_salle, jour, h_deb, h_fin, matiere)
            messagebox.showinfo("Succès", "Cours planifié avec succès !")
            self._reset_form_cours()
            self._actualiser_table_cours()
        except ValueError as e:
            messagebox.showerror("Conflit d'horaire détecté", str(e))
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de l'ajout : {e}")

    def _action_modifier_cours(self):
        if not self.selected_cours_id:
            messagebox.showwarning("Sélection", "Veuillez d'abord sélectionner un cours dans la liste.")
            return
        try:
            ens_txt = self.cb_cours_ens.get()
            grp_txt = self.cb_cours_grp.get()
            salle_txt = self.cb_cours_salle.get()
            matiere = self.cb_cours_mat.get().strip()
            jour = self.cb_cours_jour.get()
            h_deb = self.cb_h_debut.get().strip()
            h_fin = self.cb_h_fin.get().strip()

            if h_deb >= h_fin:
                messagebox.showerror("Horaire invalide", "L'heure de fin doit être postérieure à l'heure de début.")
                return

            id_ens = self._map_ens[ens_txt][0]
            id_grp = self._map_grp[grp_txt]
            id_salle = self._map_salle[salle_txt]

            db.update_cours(self.selected_cours_id, id_ens, id_grp, id_salle, jour, h_deb, h_fin, matiere)
            messagebox.showinfo("Succès", "Cours modifié avec succès !")
            self._reset_form_cours()
            self._actualiser_table_cours()
        except ValueError as e:
            messagebox.showerror("Conflit d'horaire détecté", str(e))
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la modification : {e}")

    def _action_supprimer_cours(self):
        if not self.selected_cours_id:
            messagebox.showwarning("Sélection", "Veuillez d'abord sélectionner un cours dans la liste.")
            return
        if messagebox.askyesno("Confirmation", "Voulez-vous vraiment supprimer ce cours ?"):
            db.delete_cours(self.selected_cours_id)
            self._reset_form_cours()
            self._actualiser_table_cours()

    # =========================================================================
    # ONGLET 3: ENSEIGNANTS
    # =========================================================================
    def _build_enseignants_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="👨‍🏫 Enseignants")

        # Formulaire
        form = ttk.LabelFrame(tab, text="Gestion des enseignants", padding=10)
        form.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(form, text="Nom :").grid(row=0, column=0, sticky=tk.W, padx=5, pady=4)
        self.ent_ens_nom = ttk.Entry(form, width=20)
        self.ent_ens_nom.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(form, text="Prénom :").grid(row=0, column=2, sticky=tk.W, padx=5, pady=4)
        self.ent_ens_prenom = ttk.Entry(form, width=20)
        self.ent_ens_prenom.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(form, text="Matières (séparées par virgule) :").grid(row=0, column=4, sticky=tk.W, padx=5, pady=4)
        self.ent_ens_mat = ttk.Entry(form, width=30)
        self.ent_ens_mat.grid(row=0, column=5, padx=5, pady=4)

        btn_box = ttk.Frame(form)
        btn_box.grid(row=1, column=0, columnspan=6, pady=8)

        ttk.Button(btn_box, text="Ajouter", command=self._action_ajouter_ens).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Modifier", command=self._action_modifier_ens).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Supprimer", command=self._action_supprimer_ens).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Effacer", command=self._reset_form_ens).pack(side=tk.LEFT, padx=5)

        # Recherche
        search_box = ttk.Frame(tab)
        search_box.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_box, text="🔍 Rechercher (nom, prénom ou ID) :").pack(side=tk.LEFT, padx=5)
        self.ent_search_ens = ttk.Entry(search_box, width=25)
        self.ent_search_ens.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_box, text="Rechercher", command=self._rechercher_ens).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_box, text="Tous", command=self._actualiser_table_enseignants).pack(side=tk.LEFT, padx=5)

        # Table
        cols = ["id", "nom", "prenom", "matieres"]
        table_frame = tk.Frame(tab, bd=1, relief="solid", bg="#94A3B8")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.tree_ens = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree_ens.heading("id", text="ID")
        self.tree_ens.column("id", width=50, anchor=tk.CENTER)
        self.tree_ens.heading("nom", text="Nom")
        self.tree_ens.column("nom", width=150)
        self.tree_ens.heading("prenom", text="Prénom")
        self.tree_ens.column("prenom", width=150)
        self.tree_ens.heading("matieres", text="Matières enseignées")
        self.tree_ens.column("matieres", width=350)

        sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree_ens.yview)
        self.tree_ens.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_ens.pack(fill=tk.BOTH, expand=True)
        self.tree_ens.bind("<<TreeviewSelect>>", self._on_ens_row_select)

        self.selected_ens_id = None

    def _actualiser_table_enseignants(self, data=None):
        self.tree_ens.delete(*self.tree_ens.get_children())
        rows = data if data is not None else db.get_all_enseignants()
        for idx, r in enumerate(rows):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree_ens.insert("", tk.END, values=[r["id_ens"], r["nom"], r["prenom"], r["matieres"]], tags=(tag,))

    def _on_ens_row_select(self, event):
        sel = self.tree_ens.selection()
        if not sel:
            return
        vals = self.tree_ens.item(sel[0], "values")
        self.selected_ens_id = int(vals[0])
        self.ent_ens_nom.delete(0, tk.END)
        self.ent_ens_nom.insert(0, vals[1])
        self.ent_ens_prenom.delete(0, tk.END)
        self.ent_ens_prenom.insert(0, vals[2])
        self.ent_ens_mat.delete(0, tk.END)
        self.ent_ens_mat.insert(0, vals[3])

    def _reset_form_ens(self):
        self.selected_ens_id = None
        self.ent_ens_nom.delete(0, tk.END)
        self.ent_ens_prenom.delete(0, tk.END)
        self.ent_ens_mat.delete(0, tk.END)
        self.tree_ens.selection_remove(self.tree_ens.selection())

    def _action_ajouter_ens(self):
        nom = self.ent_ens_nom.get().strip()
        prenom = self.ent_ens_prenom.get().strip()
        mat = self.ent_ens_mat.get().strip()
        if not (nom and prenom and mat):
            messagebox.showwarning("Champs requis", "Tous les champs sont obligatoires.")
            return
        db.add_enseignant(nom, prenom, mat)
        self._reset_form_ens()
        self._actualiser_table_enseignants()

    def _action_modifier_ens(self):
        if not self.selected_ens_id:
            messagebox.showwarning("Sélection", "Sélectionnez un enseignant à modifier.")
            return
        nom = self.ent_ens_nom.get().strip()
        prenom = self.ent_ens_prenom.get().strip()
        mat = self.ent_ens_mat.get().strip()
        if not (nom and prenom and mat):
            messagebox.showwarning("Champs requis", "Tous les champs sont obligatoires.")
            return
        db.update_enseignant(self.selected_ens_id, nom, prenom, mat)
        self._reset_form_ens()
        self._actualiser_table_enseignants()

    def _action_supprimer_ens(self):
        if not self.selected_ens_id:
            messagebox.showwarning("Sélection", "Sélectionnez un enseignant à supprimer.")
            return
        if messagebox.askyesno("Confirmation", "Supprimer cet enseignant ? (Ses cours associés seront affectés)"):
            try:
                db.delete_enseignant(self.selected_ens_id)
                self._reset_form_ens()
                self._actualiser_table_enseignants()
            except Exception as e:
                messagebox.showerror("Erreur", f"Suppression impossible : {e}")

    def _rechercher_ens(self):
        q = self.ent_search_ens.get().strip()
        if q:
            self._actualiser_table_enseignants(db.search_enseignants(q))
        else:
            self._actualiser_table_enseignants()

    # =========================================================================
    # ONGLET 4: SALLES
    # =========================================================================
    def _build_salles_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="🏫 Salles")

        form = ttk.LabelFrame(tab, text="Gestion des salles", padding=10)
        form.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(form, text="Nom salle :").grid(row=0, column=0, sticky=tk.W, padx=5, pady=4)
        self.ent_salle_nom = ttk.Entry(form, width=20)
        self.ent_salle_nom.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(form, text="Capacité :").grid(row=0, column=2, sticky=tk.W, padx=5, pady=4)
        self.ent_salle_cap = ttk.Entry(form, width=15)
        self.ent_salle_cap.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(form, text="Type :").grid(row=0, column=4, sticky=tk.W, padx=5, pady=4)
        self.cb_salle_type = ttk.Combobox(form, values=["cours", "TP", "TD"], state="readonly", width=15)
        self.cb_salle_type.set("cours")
        self.cb_salle_type.grid(row=0, column=5, padx=5, pady=4)

        btn_box = ttk.Frame(form)
        btn_box.grid(row=1, column=0, columnspan=6, pady=8)

        ttk.Button(btn_box, text="Ajouter", command=self._action_ajouter_salle).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Modifier", command=self._action_modifier_salle).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Supprimer", command=self._action_supprimer_salle).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Effacer", command=self._reset_form_salle).pack(side=tk.LEFT, padx=5)

        search_box = ttk.Frame(tab)
        search_box.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_box, text="🔍 Rechercher (nom ou ID) :").pack(side=tk.LEFT, padx=5)
        self.ent_search_salle = ttk.Entry(search_box, width=25)
        self.ent_search_salle.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_box, text="Rechercher", command=self._rechercher_salle).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_box, text="Toutes", command=self._actualiser_table_salles).pack(side=tk.LEFT, padx=5)

        cols = ["id", "nom", "capacite", "type"]
        table_frame = tk.Frame(tab, bd=1, relief="solid", bg="#94A3B8")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.tree_salle = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree_salle.heading("id", text="ID")
        self.tree_salle.column("id", width=50, anchor=tk.CENTER)
        self.tree_salle.heading("nom", text="Nom de la salle")
        self.tree_salle.column("nom", width=200)
        self.tree_salle.heading("capacite", text="Capacité")
        self.tree_salle.column("capacite", width=120, anchor=tk.CENTER)
        self.tree_salle.heading("type", text="Type (cours, TP, TD)")
        self.tree_salle.column("type", width=150, anchor=tk.CENTER)

        sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree_salle.yview)
        self.tree_salle.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_salle.pack(fill=tk.BOTH, expand=True)
        self.tree_salle.bind("<<TreeviewSelect>>", self._on_salle_row_select)

        self.selected_salle_id = None

    def _actualiser_table_salles(self, data=None):
        self.tree_salle.delete(*self.tree_salle.get_children())
        rows = data if data is not None else db.get_all_salles()
        for idx, r in enumerate(rows):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree_salle.insert("", tk.END, values=[r["id_salle"], r["nom_salle"], r["capacite"], r["type"]], tags=(tag,))

    def _on_salle_row_select(self, event):
        sel = self.tree_salle.selection()
        if not sel:
            return
        vals = self.tree_salle.item(sel[0], "values")
        self.selected_salle_id = int(vals[0])
        self.ent_salle_nom.delete(0, tk.END)
        self.ent_salle_nom.insert(0, vals[1])
        self.ent_salle_cap.delete(0, tk.END)
        self.ent_salle_cap.insert(0, vals[2])
        self.cb_salle_type.set(vals[3])

    def _reset_form_salle(self):
        self.selected_salle_id = None
        self.ent_salle_nom.delete(0, tk.END)
        self.ent_salle_cap.delete(0, tk.END)
        self.cb_salle_type.set("cours")
        self.tree_salle.selection_remove(self.tree_salle.selection())

    def _action_ajouter_salle(self):
        nom = self.ent_salle_nom.get().strip()
        cap_str = self.ent_salle_cap.get().strip()
        t_salle = self.cb_salle_type.get()
        if not (nom and cap_str):
            messagebox.showwarning("Champs requis", "Tous les champs sont obligatoires.")
            return
        try:
            cap = int(cap_str)
            if cap <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Format invalide", "La capacité doit être un entier positif.")
            return

        db.add_salle(nom, cap, t_salle)
        self._reset_form_salle()
        self._actualiser_table_salles()

    def _action_modifier_salle(self):
        if not self.selected_salle_id:
            messagebox.showwarning("Sélection", "Sélectionnez une salle à modifier.")
            return
        nom = self.ent_salle_nom.get().strip()
        cap_str = self.ent_salle_cap.get().strip()
        t_salle = self.cb_salle_type.get()
        try:
            cap = int(cap_str)
        except ValueError:
            messagebox.showerror("Format invalide", "La capacité doit être un entier.")
            return
        db.update_salle(self.selected_salle_id, nom, cap, t_salle)
        self._reset_form_salle()
        self._actualiser_table_salles()

    def _action_supprimer_salle(self):
        if not self.selected_salle_id:
            messagebox.showwarning("Sélection", "Sélectionnez une salle à supprimer.")
            return
        if messagebox.askyesno("Confirmation", "Supprimer cette salle ?"):
            try:
                db.delete_salle(self.selected_salle_id)
                self._reset_form_salle()
                self._actualiser_table_salles()
            except Exception as e:
                messagebox.showerror("Erreur", f"Suppression impossible : {e}")

    def _rechercher_salle(self):
        q = self.ent_search_salle.get().strip()
        if q:
            self._actualiser_table_salles(db.search_salles(q))
        else:
            self._actualiser_table_salles()

    # =========================================================================
    # ONGLET 5: GROUPES
    # =========================================================================
    def _build_groupes_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="👥 Groupes")

        form = ttk.LabelFrame(tab, text="Gestion des groupes", padding=10)
        form.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(form, text="Nom groupe :").grid(row=0, column=0, sticky=tk.W, padx=5, pady=4)
        self.ent_grp_nom = ttk.Entry(form, width=20)
        self.ent_grp_nom.grid(row=0, column=1, padx=5, pady=4)

        ttk.Label(form, text="Niveau :").grid(row=0, column=2, sticky=tk.W, padx=5, pady=4)
        self.ent_grp_niv = ttk.Entry(form, width=15)
        self.ent_grp_niv.grid(row=0, column=3, padx=5, pady=4)

        ttk.Label(form, text="Effectif :").grid(row=0, column=4, sticky=tk.W, padx=5, pady=4)
        self.ent_grp_eff = ttk.Entry(form, width=15)
        self.ent_grp_eff.grid(row=0, column=5, padx=5, pady=4)

        btn_box = ttk.Frame(form)
        btn_box.grid(row=1, column=0, columnspan=6, pady=8)

        ttk.Button(btn_box, text="Ajouter", command=self._action_ajouter_grp).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Modifier", command=self._action_modifier_grp).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Supprimer", command=self._action_supprimer_grp).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_box, text="Effacer", command=self._reset_form_grp).pack(side=tk.LEFT, padx=5)

        search_box = ttk.Frame(tab)
        search_box.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(search_box, text="🔍 Rechercher (nom, niveau ou ID) :").pack(side=tk.LEFT, padx=5)
        self.ent_search_grp = ttk.Entry(search_box, width=25)
        self.ent_search_grp.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_box, text="Rechercher", command=self._rechercher_grp).pack(side=tk.LEFT, padx=5)
        ttk.Button(search_box, text="Tous", command=self._actualiser_table_groupes).pack(side=tk.LEFT, padx=5)

        cols = ["id", "nom", "niveau", "effectif"]
        table_frame = tk.Frame(tab, bd=1, relief="solid", bg="#94A3B8")
        table_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.tree_grp = ttk.Treeview(table_frame, columns=cols, show="headings")
        self.tree_grp.heading("id", text="ID")
        self.tree_grp.column("id", width=50, anchor=tk.CENTER)
        self.tree_grp.heading("nom", text="Nom du groupe")
        self.tree_grp.column("nom", width=200)
        self.tree_grp.heading("niveau", text="Niveau")
        self.tree_grp.column("niveau", width=150)
        self.tree_grp.heading("effectif", text="Effectif")
        self.tree_grp.column("effectif", width=120, anchor=tk.CENTER)

        sb = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree_grp.yview)
        self.tree_grp.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_grp.pack(fill=tk.BOTH, expand=True)
        self.tree_grp.bind("<<TreeviewSelect>>", self._on_grp_row_select)

        self.selected_grp_id = None

    def _actualiser_table_groupes(self, data=None):
        self.tree_grp.delete(*self.tree_grp.get_children())
        rows = data if data is not None else db.get_all_groupes()
        for idx, r in enumerate(rows):
            tag = "evenrow" if idx % 2 == 0 else "oddrow"
            self.tree_grp.insert("", tk.END, values=[r["id_groupe"], r["nom_groupe"], r["niveau"], r["effectif"]], tags=(tag,))

    def _on_grp_row_select(self, event):
        sel = self.tree_grp.selection()
        if not sel:
            return
        vals = self.tree_grp.item(sel[0], "values")
        self.selected_grp_id = int(vals[0])
        self.ent_grp_nom.delete(0, tk.END)
        self.ent_grp_nom.insert(0, vals[1])
        self.ent_grp_niv.delete(0, tk.END)
        self.ent_grp_niv.insert(0, vals[2])
        self.ent_grp_eff.delete(0, tk.END)
        self.ent_grp_eff.insert(0, vals[3])

    def _reset_form_grp(self):
        self.selected_grp_id = None
        self.ent_grp_nom.delete(0, tk.END)
        self.ent_grp_niv.delete(0, tk.END)
        self.ent_grp_eff.delete(0, tk.END)
        self.tree_grp.selection_remove(self.tree_grp.selection())

    def _action_ajouter_grp(self):
        nom = self.ent_grp_nom.get().strip()
        niv = self.ent_grp_niv.get().strip()
        eff_str = self.ent_grp_eff.get().strip()
        if not (nom and niv and eff_str):
            messagebox.showwarning("Champs requis", "Tous les champs sont obligatoires.")
            return
        try:
            eff = int(eff_str)
            if eff <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Format invalide", "L'effectif doit être un entier positif.")
            return
        db.add_groupe(nom, niv, eff)
        self._reset_form_grp()
        self._actualiser_table_groupes()

    def _action_modifier_grp(self):
        if not self.selected_grp_id:
            messagebox.showwarning("Sélection", "Sélectionnez un groupe à modifier.")
            return
        nom = self.ent_grp_nom.get().strip()
        niv = self.ent_grp_niv.get().strip()
        eff_str = self.ent_grp_eff.get().strip()
        try:
            eff = int(eff_str)
        except ValueError:
            messagebox.showerror("Format invalide", "L'effectif doit être un entier.")
            return
        db.update_groupe(self.selected_grp_id, nom, niv, eff)
        self._reset_form_grp()
        self._actualiser_table_groupes()

    def _action_supprimer_grp(self):
        if not self.selected_grp_id:
            messagebox.showwarning("Sélection", "Sélectionnez un groupe à supprimer.")
            return
        if messagebox.askyesno("Confirmation", "Supprimer ce groupe ?"):
            try:
                db.delete_groupe(self.selected_grp_id)
                self._reset_form_grp()
                self._actualiser_table_groupes()
            except Exception as e:
                messagebox.showerror("Erreur", f"Suppression impossible : {e}")

    def _rechercher_grp(self):
        q = self.ent_search_grp.get().strip()
        if q:
            self._actualiser_table_groupes(db.search_groupes(q))
        else:
            self._actualiser_table_groupes()


if __name__ == "__main__":
    db.init_db()
    app = App()
    app.mainloop()

