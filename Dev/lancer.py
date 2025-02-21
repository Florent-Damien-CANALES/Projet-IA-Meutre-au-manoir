import subprocess
import sys
import os

# 🔥 Récupérer le dossier du script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(BASE_DIR, "venv")

# ✅ Déterminer la commande pour activer l'environnement virtuel
if sys.platform == "win32":  # Windows
    ACTIVATE_CMD = f'venv\\Scripts\\activate && python -u '
else:  # macOS / Linux
    ACTIVATE_CMD = f'source venv/bin/activate && python -u '

def run_api_and_wait():
    """Lance l'API et attend le message 'Press CTRL+C to quit' avant de continuer."""
    print("Démarrage de l'API... En attente du message de confirmation.")

    # Lancer l'API et capturer la sortie
    api_process = subprocess.Popen(
        f'{ACTIVATE_CMD} api.py',
        shell=True,
        cwd=BASE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    # Lire la sortie ligne par ligne
    while True:
        output_line = api_process.stdout.readline()
        if output_line:
            print(output_line.strip())  # Afficher en temps réel
            if "Press CTRL+C to quit" in output_line:  # 🔥 Détection du message clé
                print("✅ API prête ! Lancement du jeu...")
                break

    return api_process

def run_game():
    """Lance le jeu."""
    print("Démarrage du jeu...")
    return subprocess.Popen(
        f'{ACTIVATE_CMD} main.py',
        shell=True,
        cwd=BASE_DIR
    )

if __name__ == "__main__":
    print(f"Dossier d'exécution : {BASE_DIR}")
    print(f"Environnement virtuel : {VENV_DIR}")

    # ✅ Démarrer l'API et attendre qu'elle soit prête
    api_process = run_api_and_wait()

    # ✅ Démarrer le jeu
    game_process = run_game()

    try:
        # 🔥 Garder les processus actifs
        api_process.wait()
        game_process.wait()
    except KeyboardInterrupt:
        print("\nArrêt du programme...")
        api_process.terminate()
        game_process.terminate()
