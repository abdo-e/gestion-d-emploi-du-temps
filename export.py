"""
export.py — Export de l'emploi du temps au format Excel (.xlsx).
Utilise openpyxl (seule dépendance externe du projet).
"""

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

JOURS = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi"]


def export_excel(courses, filename, titre="Emploi du temps"):
    """Crée un fichier Excel avec une grille hebdomadaire depuis une liste de cours."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Emploi du temps"

    # Styles
    thin = Side(style="thin")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)
    center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    header_fill = PatternFill("solid", fgColor="4472C4")
    header_font = Font(bold=True, size=11, color="FFFFFF")

    # Titre
    ws.merge_cells("A1:G1")
    ws["A1"] = titre
    ws["A1"].font = Font(bold=True, size=14)
    ws["A1"].alignment = center

    # En-têtes : Horaire | Lundi | ... | Samedi
    for col, header in enumerate(["Horaire"] + JOURS, 1):
        cell = ws.cell(row=2, column=col, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center
        cell.border = border

    # Créneaux uniques, triés chronologiquement
    slots = sorted({(c["heure_debut"], c["heure_fin"]) for c in courses})

    # Grille (créneau, jour) → texte multi-lignes
    grid = {}
    for c in courses:
        key = ((c["heure_debut"], c["heure_fin"]), c["jour"])
        grid[key] = (f"{c['matiere']}\n"
                     f"{c['ens_prenom']} {c['ens_nom']}\n"
                     f"{c['nom_salle']}\n"
                     f"{c['nom_groupe']}")

    # Remplissage des lignes
    for i, slot in enumerate(slots, 3):
        cell = ws.cell(row=i, column=1, value=f"{slot[0]} - {slot[1]}")
        cell.font = Font(bold=True)
        cell.alignment = center
        cell.border = border
        for j, jour in enumerate(JOURS, 2):
            cell = ws.cell(row=i, column=j, value=grid.get((slot, jour), ""))
            cell.alignment = center
            cell.border = border
        ws.row_dimensions[i].height = 65

    # Largeurs de colonnes
    ws.column_dimensions["A"].width = 16
    for letter in "BCDEFG":
        ws.column_dimensions[letter].width = 22

    wb.save(filename)

