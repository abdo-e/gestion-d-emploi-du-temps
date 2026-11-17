"""
main.py — Point d'entrée de l'application de gestion d'emploi du temps.
Initialise la base de données SQLite et lance l'interface graphique Tkinter.
"""

from db import init_db
from app import App

if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()

