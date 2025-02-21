import pygame
import sounddevice as sd
import numpy as np
import threading
from pydub import AudioSegment
import requests
import os

# Initialisation de Pygame
pygame.init()
# Configuration de la fenêtre en plein écran
WIDTH = 1512
HEIGHT = 982
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
WIDTH, HEIGHT = screen.get_size()

pygame.display.set_caption("Scène de crime - Cluedo")

# Charger l'image de fond
background = pygame.image.load("res/Background/background.png").convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))  # Adapter à l'écran

# Position et taille du bouton d'enregistrement
record_button_rect = pygame.Rect(WIDTH - 120, HEIGHT - 120, 80, 80)  # Bouton en bas à droite

# Charger l'image du bouton Report (assure-toi que le fichier existe)
report_button_image = pygame.image.load("res/ui/report_button.png").convert_alpha()
report_button_image = pygame.transform.scale(report_button_image, (80, 80))  # Adapter à la taille souhaitée

# Position du bouton Report (à gauche du bouton d'enregistrement)
report_button_rect = pygame.Rect(WIDTH - 220, HEIGHT - 120, 80, 80)

# Charger l'image du bouton Record (assure-toi que le fichier existe)
record_button_image = pygame.image.load("res/ui/record_button.png").convert_alpha()
record_button_image = pygame.transform.scale(record_button_image, (80, 80))  # Adapter à la taille souhaitée



# Dossier de sauvegarde
AUDIO_FOLDER = "audios"
AUDIO_FILE = os.path.join(AUDIO_FOLDER, "new_recording.wav")
MP3_FILE = os.path.join(AUDIO_FOLDER, "new_recording.mp3")

# Initialiser le module mixer de Pygame
pygame.mixer.init()

# Charger la musique de fond (assure-toi d'avoir un fichier "background_music.mp3" dans res/audio/)
pygame.mixer.music.load("res/audio/background_music.mp3")

# Jouer la musique en boucle avec un volume initial de 0.5
pygame.mixer.music.set_volume(0.5)  # Volume entre 0.0 et 1.0
pygame.mixer.music.play(-1)  # -1 pour boucle infinie


player_message = ""  # Contiendra le message transcrit
message_display_time = 0  # Timestamp pour gérer l'affichage du message
final_confession = "..."  
waiting_for_murderer_response = False  # 🔥 Indique si on attend la réponse

# Vérifier et créer le dossier si nécessaire
if not os.path.exists(AUDIO_FOLDER):
    os.makedirs(AUDIO_FOLDER)

# Variables pour gérer l'enregistrement
is_recording = False  # Indicateur d'enregistrement
recording = False
audio_data = []
samplerate = 44100  # Qualité d'enregistrement standard
game_context = "..."  # Par défaut on affiche "..." tant qu'on ne l'a pas.
waiting_for_context = True  # Indique si on attend toujours la réponse.

closest_pnj = None  # Pour stocker le PNJ le plus proche
interaction_range = 120  # Distance en pixels pour activer l'interaction
pnj_responses = {0: "", 1: "", 2: ""}  # Stocke la réponse du serveur pour chaque PNJ
waiting_for_response = {0: False, 1: False, 2: False}  # Indique si un PNJ attend une réponse

def fetch_game_context():
    """Récupère le contexte du jeu depuis l'API."""
    global game_context, waiting_for_context

    startprompt_url = "http://localhost:8000/startpromptgamemaster"

    try:
        response = requests.get(startprompt_url)
        response.raise_for_status()
        response_json = response.json()
        if "message" in response_json:
            game_context = response_json["message"]
        else:
            game_context = "Erreur : Impossible de récupérer le contexte."

    except requests.exceptions.RequestException as e:
        game_context = f"Erreur : {str(e)}"

    finally:
        waiting_for_context = False  # On a fini d'attendre la réponse.

def show_game_context_screen():
    """Affiche l'écran du contexte avant de commencer le jeu, avec le texte aligné à gauche."""
    
    global game_context, waiting_for_context

    # Charger l'image de fond
    background = pygame.image.load("res/title/title.png").convert()
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))

    # Définir les polices
    font_text = pygame.font.Font(None, 32)
    font_button = pygame.font.Font(None, 40)

    # Définition du bouton Continuer
    continue_button_rect = pygame.Rect(WIDTH // 2 - 150, HEIGHT - 100, 300, 60)

    # Paramètres d'affichage du texte
    max_text_width = WIDTH - 400
    text_padding = 20
    text_y_position = HEIGHT // 3
    text_x_start = WIDTH // 2 - max_text_width // 2

    context_active = True
    while context_active:
        screen.blit(background, (0, 0))

        # ✅ Récupération du texte et wrapping
        if waiting_for_context:
            wrapped_text = ["Chargement du contexte..."]
        else:
            wrapped_text = wrap_text(game_context, font_text, max_text_width)

        # ✅ Calcul de la hauteur totale du texte pour centrer verticalement
        total_text_height = len(wrapped_text) * 40
        text_y_start = HEIGHT // 2 - total_text_height // 2

        # ✅ Dessiner le fond semi-transparent derrière le texte
        box_width = max_text_width + 2 * text_padding
        box_height = total_text_height + 2 * text_padding
        box_x = text_x_start - text_padding
        box_y = text_y_start - text_padding

        box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        box_surface.fill((0, 0, 0, 180))
        screen.blit(box_surface, (box_x, box_y))

        # ✅ Afficher le texte aligné à gauche
        for i, line in enumerate(wrapped_text):
            text_surface = font_text.render(line, True, (255, 255, 255))
            screen.blit(text_surface, (text_x_start, text_y_start + i * 40))

        # ✅ Afficher le bouton "Continuer" UNIQUEMENT si le texte est chargé
        if not waiting_for_context:
            pygame.draw.rect(screen, (0, 150, 0), continue_button_rect, border_radius=15)
            pygame.draw.rect(screen, (0, 0, 0), continue_button_rect, width=3, border_radius=15)

            text_continue = font_button.render("Continuer", True, (255, 255, 255))
            screen.blit(text_continue, (continue_button_rect.x + continue_button_rect.width // 2 - text_continue.get_width() // 2, 
                                        continue_button_rect.y + continue_button_rect.height // 2 - text_continue.get_height() // 2))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and not waiting_for_context:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if continue_button_rect.collidepoint(mouse_x, mouse_y):
                    context_active = False  # Quitter cet écran et démarrer le jeu

def show_main_menu():
    """Affiche l'écran titre avec un titre, un bouton Jouer et Quitter."""
    
    # Lancer la récupération du contexte en thread
    threading.Thread(target=fetch_game_context, daemon=True).start()

    title_screen = pygame.image.load("res/title/title.png").convert()
    title_screen = pygame.transform.scale(title_screen, (WIDTH, HEIGHT))

    spooky_font = pygame.font.Font("res/fonts/Creepster-Regular.ttf", 80)
    font_menu = pygame.font.Font(None, 50)

    title_text = spooky_font.render("Meurtre au Manoir", True, (0, 255, 0))
    shadow_text = spooky_font.render("Meurtre au Manoir", True, (0, 0, 0))

    button_width, button_height = 220, 80
    play_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 100, button_width, button_height)
    quit_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, HEIGHT // 2 + 220, button_width, button_height)

    menu_active = True
    while menu_active:
        screen.blit(title_screen, (0, 0))
        screen.blit(shadow_text, (WIDTH // 2 - title_text.get_width() // 2 + 3, HEIGHT // 5 + 3))
        screen.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 5))

        pygame.draw.rect(screen, (50, 50, 50), play_button_rect, border_radius=10)
        pygame.draw.rect(screen, (150, 0, 0), quit_button_rect, border_radius=10)

        text_play = font_menu.render("Jouer", True, (255, 255, 255))
        text_quit = font_menu.render("Quitter", True, (255, 255, 255))

        screen.blit(text_play, (play_button_rect.x + 60, play_button_rect.y + 20))
        screen.blit(text_quit, (quit_button_rect.x + 50, quit_button_rect.y + 20))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if play_button_rect.collidepoint(mouse_x, mouse_y):
                    show_game_context_screen()  # 🔥 Aller à l'écran de contexte
                    menu_active = False
                elif quit_button_rect.collidepoint(mouse_x, mouse_y):
                    pygame.quit()
                    exit()

def audio_callback(indata, frames, time, status):
    """Callback pour capturer l'audio en temps réel."""
    if recording:
        audio_data.append(indata.copy())

def start_recording():
    """Démarre l'enregistrement audio et baisse le volume de la musique."""
    global recording, audio_data, is_recording
    if not recording:
        print("Début de l'enregistrement...")
        recording = True
        is_recording = True
        audio_data = []

        # 🔽 Baisser le volume de la musique à 20% pendant l'enregistrement
        pygame.mixer.music.set_volume(0.2)

        threading.Thread(target=record_audio).start()

def stop_recording():
    """Arrête l'enregistrement et remet le volume normal."""
    global recording, is_recording
    if recording:
        print("Arrêt de l'enregistrement...")
        recording = False
        is_recording = False

        # 🔼 Remettre le volume de la musique à 50% après l'enregistrement
        pygame.mixer.music.set_volume(0.5)

        save_audio()

def record_audio():
    """Enregistre l'audio tant que `recording` est True."""
    with sd.InputStream(callback=audio_callback, samplerate=samplerate, channels=1):
        while recording:
            sd.sleep(100)  # Évite de surcharger le CPU

def save_audio():
    """Sauvegarde l'audio en WAV puis en MP3 et envoie une requête à localhost en arrière-plan."""
    if audio_data:
        print("Sauvegarde de l'audio...")
        np_audio = np.concatenate(audio_data, axis=0)  # Fusionner les fragments
        
        # Convertir les données en int16 (format attendu par pydub)
        np_audio = (np_audio * 32767).astype(np.int16)

        # Vérifier que la longueur est un multiple de channels
        num_channels = 1  # Mono
        if len(np_audio) % num_channels != 0:
            np_audio = np_audio[:-(len(np_audio) % num_channels)]  # Tronquer les données pour éviter l'erreur

        # Créer un fichier WAV temporaire
        wav_file = AUDIO_FILE
        wav_audio = AudioSegment(
            np_audio.tobytes(), 
            frame_rate=samplerate, 
            sample_width=2,  # int16 = 2 bytes
            channels=num_channels
        )
        wav_audio.export(wav_file, format="wav")

        # Convertir en MP3
        mp3_file = MP3_FILE
        audio = AudioSegment.from_wav(wav_file)
        audio.export(mp3_file, format="mp3")
        print(f"Enregistrement terminé : {mp3_file}")

        # Envoyer la requête en arrière-plan
        thread = threading.Thread(target=send_audio_to_server, args=(mp3_file,))
        thread.start()

def fetch_final_gamemaster_text(selected_murderer):
    """Récupère le texte final du game master via l'API."""
    global final_gamemaster_text, waiting_for_final_text

    waiting_for_final_text = True  # ✅ Afficher "..." en attendant
    finalprompt_url = "http://localhost:8000/finalpromptgamemaster"

    try:
        data = {"is_personnage": selected_murderer}
        response = requests.get(finalprompt_url, data=data)
        response.raise_for_status()

        response_json = response.json()
        if "message" in response_json:
            final_gamemaster_text = response_json["message"].replace("\\n", "\n")  # ✅ Gestion correcte des sauts de ligne
        else:
            final_gamemaster_text = "Erreur : Impossible de récupérer le texte final."

    except requests.exceptions.RequestException as e:
        final_gamemaster_text = f"Erreur : {str(e)}"

    finally:
        waiting_for_final_text = False  # ✅ Désactiver "..."


def send_audio_to_server(file_path):
    """Envoie l'audio à whisperiser, puis la réponse à /repondre et affiche la réponse finale."""
    global pnj_responses, waiting_for_response, player_message, message_display_time

    if interacting_pnj is None:
        print("Aucun PNJ sélectionné, envoi annulé.")
        return

    pnj_responses[interacting_pnj] = "..."  # Afficher l'attente ("...")
    waiting_for_response[interacting_pnj] = True  # Activer le mode attente

    whisper_url = "http://localhost:8000/whisperiser"
    respond_url = "http://localhost:8000/repondre"

    try:
        # Étape 1 : Envoi du fichier audio à whisperiser
        with open(file_path, "rb") as audio_file:
            files = {"file": audio_file}
            response = requests.post(whisper_url, files=files)
            response.raise_for_status()

            response_json = response.json()
            if "message" in response_json:
                transcribed_message = response_json["message"]
                player_message = transcribed_message  # 🔥 Affiche le message du joueur
                message_display_time = float('inf')  # 🔥 Garde l'affichage jusqu'à la réponse
                print(f"Message transcrit : {transcribed_message}")
            else:
                raise ValueError("Réponse invalide de whisperiser")

        # Étape 2 : Envoyer la transcription au PNJ via /repondre
        data = {
            "query": transcribed_message,
            "id_personnage": interacting_pnj
        }
        response = requests.post(respond_url, data=data)
        response.raise_for_status()

        response_json = response.json()
        if "message" in response_json:
            final_response = response_json["message"][0]['text']
            pnj_responses[interacting_pnj] = final_response
            print(f"Réponse du PNJ {interacting_pnj} : {final_response}")

            player_message = ""  # 🔥 Supprime la bulle du joueur immédiatement
        else:
            raise ValueError("Réponse invalide de repondre")

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de l'envoi des fichiers : {e}")
        pnj_responses[interacting_pnj] = "Erreur : impossible d'obtenir la réponse."

    finally:
        waiting_for_response[interacting_pnj] = False  # Désactiver le mode attente

def draw_large_speech_bubble(screen, text, position):
    """Affiche une grande bulle de dialogue pour le tueur dans l'écran final."""
    if not text:
        return

    padding = 20
    max_text_width = 600  # ✅ Augmenté pour accueillir des textes longs
    lines = wrap_text(text, font, max_text_width)
    text_height = font.get_height()
    
    bubble_width = max_text_width + padding * 2
    bubble_height = len(lines) * text_height + padding * 2
    bubble_x = position[0] - bubble_width // 2
    bubble_y = position[1] - 150  # ✅ Ajusté pour être plus haut

    # ✅ Dessiner la bulle avec des bordures arrondies
    pygame.draw.rect(screen, (255, 255, 255), (bubble_x, bubble_y, bubble_width, bubble_height), border_radius=15)
    pygame.draw.rect(screen, (0, 0, 0), (bubble_x, bubble_y, bubble_width, bubble_height), width=2, border_radius=15)

    for i, line in enumerate(lines):
        text_surface = font.render(line, True, (0, 0, 0))
        screen.blit(text_surface, (bubble_x + padding, bubble_y + padding + i * text_height))


def draw_speech_bubble(screen, text, position):
    padding = 10
    max_text_width = 400

    lines = wrap_text(text, font, max_text_width)
    text_height = font.get_height()
    bubble_width = max_text_width + padding * 2
    bubble_height = len(lines) * text_height + padding * 2
    bubble_x = position[0] - bubble_width // 2
    bubble_y = position[1] - 200  

    pygame.draw.rect(screen, (255, 255, 255), (bubble_x, bubble_y, bubble_width, bubble_height), border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0), (bubble_x, bubble_y, bubble_width, bubble_height), width=2, border_radius=10)

    for i, line in enumerate(lines):
        text_surface = font.render(line, True, (0, 0, 0))
        screen.blit(text_surface, (bubble_x + padding, bubble_y + padding + i * text_height))

def draw_player_speech_bubble(screen, text, position):
    """Affiche une bulle de dialogue au-dessus du joueur"""
    if not text:
        return

    padding = 10
    max_text_width = 300
    lines = wrap_text(text, font, max_text_width)
    text_height = font.get_height()
    bubble_width = max_text_width + padding * 2
    bubble_height = len(lines) * text_height + padding * 2
    bubble_x = position[0] - bubble_width // 2
    bubble_y = position[1] - 100  # Position au-dessus du joueur

    pygame.draw.rect(screen, (255, 255, 255), (bubble_x, bubble_y, bubble_width, bubble_height), border_radius=10)
    pygame.draw.rect(screen, (0, 0, 0), (bubble_x, bubble_y, bubble_width, bubble_height), width=2, border_radius=10)

    for i, line in enumerate(lines):
        text_surface = font.render(line, True, (0, 0, 0))
        screen.blit(text_surface, (bubble_x + padding, bubble_y + padding + i * text_height))


# Charger le corps au sol
corp_image = pygame.image.load("res/dead/corp.png").convert_alpha()
corp_image = pygame.transform.scale(corp_image, (corp_image.get_width() // 2, corp_image.get_height() // 2))
corp_image = pygame.transform.flip(corp_image, True, False)

corp_pos = (WIDTH - 200, HEIGHT // 2 + 150)

# Définition de la hitbox du corps
corp_hitbox = pygame.Rect(corp_pos[0] - 70, corp_pos[1] - 60, 200, 60)

# Police pour les dialogues
font = pygame.font.Font(None, 25)

# Fonction pour découper un message en plusieurs lignes
def wrap_text(text, font, max_width):
    words = text.split(" ")
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " "
        test_width, _ = font.size(test_line)

        if test_width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + " "

    lines.append(current_line.strip())  
    return lines


def get_correct_murderer():
    """Récupère dynamiquement l'identité du meurtrier depuis l'API."""
    url = "http://localhost:8000/quitueur"  # URL de l'API
    try:
        response = requests.get(url)
        response.raise_for_status()  # Vérifie que la requête a réussi
        data = response.json()
        return data.get("tueur", 1)  # Retourne l'ID du tueur, sinon 1 par défaut
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors de la récupération du tueur : {e}")
        return 1  # Valeur par défaut en cas d'erreur
    
# Fonction pour afficher une bulle de dialogue
def choose_murderer():
    """Affiche la scène de choix du meurtrier avec animations alignées aux pieds des PNJ."""
    
    # ✅ Récupération dynamique de l'ID du tueur depuis l'API
    correct_murderer = get_correct_murderer()
    print(f"Le tueur est : {correct_murderer}")  # Debug

    suspects = ["Fantôme", "Minotaure", "Satyre"]
    suspect_animations = [pnj_1_frames, pnj_2_frames, pnj_3_frames]  

    choosing = True
    selected_murderer = None
    animation_index = 0
    animation_speed = 100
    last_animation_update = pygame.time.get_ticks()

    foot_y_position = HEIGHT // 1.4  # Position de base des pieds
    pnj_heights = [animation[0].get_height() for animation in suspect_animations]

    selection_boxes = []

    while choosing:
        screen.fill((30, 30, 30))

        font_title = pygame.font.Font(None, 60)
        text_title = font_title.render("Qui est le meurtrier ?", True, (255, 255, 255))
        screen.blit(text_title, (WIDTH // 2 - text_title.get_width() // 2, 200))

        current_time = pygame.time.get_ticks()
        if current_time - last_animation_update > animation_speed:
            animation_index = (animation_index + 1) % len(pnj_1_frames)
            last_animation_update = current_time

        font_choice = pygame.font.Font(None, 40)
        spacing_x = WIDTH // 4
        name_y_offset = 80  # Position du nom

        selection_boxes.clear()

        for i, (suspect, animation) in enumerate(zip(suspects, suspect_animations)):
            x_position = spacing_x * (i + 1)
            sprite = animation[animation_index]
            sprite_y = foot_y_position - pnj_heights[i]

            screen.blit(sprite, (x_position - sprite.get_width() // 2, sprite_y))

            text_suspect = font_choice.render(suspect, True, (255, 255, 255))
            screen.blit(text_suspect, (x_position - text_suspect.get_width() // 2, foot_y_position + name_y_offset))

            box_width = sprite.get_width() * 0.8
            box_height = pnj_heights[i] * 1.1
            box_x = x_position - box_width // 2
            box_y = foot_y_position - box_height

            selection_boxes.append(pygame.Rect(box_x, box_y, box_width, box_height))

            if selected_murderer == i:
                pygame.draw.rect(screen, (255, 0, 0), selection_boxes[i], 5, border_radius=10)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    selected_murderer = 0
                elif event.key == pygame.K_2:
                    selected_murderer = 1
                elif event.key == pygame.K_3:
                    selected_murderer = 2
                elif event.key == pygame.K_RETURN and selected_murderer is not None:
                    choosing = False

    show_victory_screen(selected_murderer, correct_murderer)



def show_victory_screen(selected_murderer, correct_murderer):
    """Affiche l'écran final avec le PNJ en bas à gauche et son animation idle plus rapide."""

    global final_gamemaster_text, waiting_for_final_text

    screen.fill((30, 30, 30))
    font_result = pygame.font.Font(None, 50)
    font_text = pygame.font.Font(None, 28)
    font_name = pygame.font.Font(None, 32)

    is_victory = selected_murderer == correct_murderer
    result_text = "Bravo ! Vous avez trouvé le meurtrier." if is_victory else "Dommage... Ce n'était pas le bon suspect."
    color = (0, 255, 0) if is_victory else (255, 0, 0)

    text_result = font_result.render(result_text, True, color)
    screen.blit(text_result, (WIDTH // 2 - text_result.get_width() // 2, 50))

    # ✅ Lancer la requête pour récupérer le texte du game master
    threading.Thread(target=fetch_final_gamemaster_text, args=(selected_murderer,)).start()

    murderer_idle_animation = [pnj_1_frames, pnj_2_frames, pnj_3_frames][selected_murderer]
    animation_index = 0
    animation_speed = 100
    last_animation_update = pygame.time.get_ticks()

    murderer_x = 50
    murderer_y = HEIGHT - 220
    scale_factor = 0.45
    quit_button_rect = pygame.Rect(WIDTH - 220, HEIGHT - 100, 200, 50)

    pnj_names = ["Fantôme", "Minotaure", "Satyre"]
    murderer_name = pnj_names[selected_murderer]

    screen_active = True

    while screen_active:
        current_time = pygame.time.get_ticks()

        if current_time - last_animation_update > animation_speed:
            animation_index = (animation_index + 1) % len(murderer_idle_animation)
            last_animation_update = current_time

        screen.fill((30, 30, 30))
        screen.blit(text_result, (WIDTH // 2 - text_result.get_width() // 2, 50))

        murderer_sprite = pygame.transform.scale(murderer_idle_animation[animation_index], 
                                                 (int(murderer_idle_animation[animation_index].get_width() * scale_factor),
                                                  int(murderer_idle_animation[animation_index].get_height() * scale_factor)))
        screen.blit(murderer_sprite, (murderer_x, murderer_y))

        text_name = font_name.render(murderer_name, True, (255, 255, 255))
        screen.blit(text_name, (murderer_x + murderer_sprite.get_width() // 2 - text_name.get_width() // 2, murderer_y + murderer_sprite.get_height() + 5))

        text_y_position = 150
        max_text_width = WIDTH - 100

        if waiting_for_final_text:
            loading_text = font_text.render("Le MAITRE DU JEU prépare la fin de partie...", True, (255, 255, 255))
            screen.blit(loading_text, (WIDTH // 2 - loading_text.get_width() // 2, text_y_position))
        else:
            wrapped_text = wrap_text(final_gamemaster_text, font_text, max_text_width)
            for i, line in enumerate(wrapped_text):
                text_surface = font_text.render(line, True, (255, 255, 255))
                screen.blit(text_surface, (50, text_y_position + i * 50))

            # ✅ Dessiner le bouton "Quitter" UNIQUEMENT si le texte final est chargé
            pygame.draw.rect(screen, (200, 0, 0), quit_button_rect, border_radius=10)
            font_quit = pygame.font.Font(None, 35)
            text_quit = font_quit.render("Quitter", True, (255, 255, 255))
            screen.blit(text_quit, (quit_button_rect.x + 50, quit_button_rect.y + 10))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN and not waiting_for_final_text:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if quit_button_rect.collidepoint(mouse_x, mouse_y):
                    pygame.quit()
                    exit()

# Fonction pour charger les animations
def load_animation(folder, name, frame_count):
    frames = []
    for i in range(frame_count):
        img_path = f"{folder}/{name}_{i:03d}.png"
        if os.path.exists(img_path):
            img = pygame.image.load(img_path).convert_alpha()
            img = pygame.transform.scale(img, (img.get_width() // 2, img.get_height() // 2))
            frames.append(img)
    if not frames:
        raise Exception(f"Aucune image trouvée pour {name} dans {folder}")
    return frames

# Charger les animations des PNJ
pnj_1_frames = load_animation("res/png1/idle", "Wraith_01_Idle", 11)
pnj_2_frames = load_animation("res/png2/idle", "Minotaur_03_Idle", 11)
pnj_3_frames = load_animation("res/png3/idle", "Satyr_02_Idle", 11)

# Charger les animations du player
player_idle_frames = [pygame.transform.scale(img, (img.get_width() * 2 // 3, img.get_height() * 2 // 3)) for img in load_animation("res/player/idle", "0_Fallen_Angels_Idle", 17)]
player_walk_frames = [pygame.transform.scale(img, (img.get_width() * 2 // 3, img.get_height() * 2 // 3)) for img in load_animation("res/player/walk", "0_Fallen_Angels_Walking", 23)]

# Paramètres d'animation
clock = pygame.time.Clock()
frame_index = 0
animation_speed = 300  

# Positions des PNJ
positions = [
    (WIDTH // 4, HEIGHT // 3),
    (WIDTH // 2, HEIGHT // 3),
    (3 * WIDTH // 4, HEIGHT // 3)
]

# Création des hitbox des PNJ sur mesure
pnj_hitboxes = [
    pygame.Rect(positions[0][0] - 60, positions[0][1] - 100, 120, 60),
    pygame.Rect(positions[1][0] - 60, positions[1][1] - 60, 120, 60),
    pygame.Rect(positions[2][0] - 60, positions[2][1] - 100, 120, 60)
]

# Paramètres du player
player_pos = [WIDTH // 2, HEIGHT - 200]
player_speed = 5
player_direction = 1  
player_moving = False
interacting_pnj = None

# Boucle du jeu
show_main_menu()  # Affichage du menu principal avant de lancer le jeu
running = True
while running:
    screen.blit(background, (0, 0))  
    screen.blit(corp_image, corp_image.get_rect(center=corp_pos))  

    closest_pnj = None  # Réinitialise la détection de proximité
    
    # Détection du PNJ le plus proche dans la range d'interaction
    for i, npc_pos in enumerate(positions):
        distance = ((player_pos[0] - npc_pos[0]) ** 2 + (player_pos[1] - npc_pos[1]) ** 2) ** 0.5
        if distance < interaction_range:
            closest_pnj = i  # Stocke l'indice du PNJ proche
            break  # Un seul PNJ à la fois

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False  
            elif event.key == pygame.K_SPACE:
                if closest_pnj is not None:  # Vérifie si un PNJ est proche
                    interacting_pnj = closest_pnj  # Active le dialogue avec ce PNJ
            elif event.key == pygame.K_e:  
                choose_murderer()  # → Lancer la scène de sélection du tueur
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if report_button_rect.collidepoint(mouse_x, mouse_y):  # Si le bouton est cliqué
                    choose_murderer()
            elif event.key == pygame.K_a and closest_pnj is not None:  
                interacting_pnj = closest_pnj
                start_recording()
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_a and closest_pnj is not None:
                stop_recording()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if record_button_rect.collidepoint(mouse_x, mouse_y) and closest_pnj is not None:
                start_recording()
        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            if record_button_rect.collidepoint(mouse_x, mouse_y) and closest_pnj is not None:
                stop_recording()



    old_player_pos = player_pos[:]

    keys = pygame.key.get_pressed()
    player_moving = False

    if keys[pygame.K_LEFT] or keys[pygame.K_q]:
        player_pos[0] -= player_speed
        player_direction = -1
        player_moving = True
        if player_pos[0] < 75:  # Bord gauche
            player_pos[0] = 75
    if keys[pygame.K_UP] or keys[pygame.K_z]:
        player_pos[1] -= player_speed
        player_moving = True
        if player_pos[1] < HEIGHT * 0.30:  # Ajustement pour empêcher le joueur d'aller trop haut
            player_pos[1] = HEIGHT * 0.30
    if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
        player_pos[0] += player_speed
        player_direction = 1
        player_moving = True
        if player_pos[0] > WIDTH - 75:  # Bord droit
            player_pos[0] = WIDTH - 75
    if keys[pygame.K_DOWN] or keys[pygame.K_s]:
        player_pos[1] += player_speed
        player_moving = True
        if player_pos[1] > HEIGHT - 100:  # Bord bas
            player_pos[1] = HEIGHT - 100

    current_frames = player_walk_frames if player_moving else player_idle_frames
    current_index = (pygame.time.get_ticks() // (animation_speed // 4)) % len(current_frames)
    player_frame = current_frames[current_index]

    if player_direction == -1:
        player_frame = pygame.transform.flip(player_frame, True, False)

    player_hitbox = pygame.Rect(player_pos[0] - 20, player_pos[1] - 30, 40, 60)

    for hitbox in pnj_hitboxes:
        if player_hitbox.colliderect(hitbox):
            player_pos = old_player_pos[:]

    if player_hitbox.colliderect(corp_hitbox):
        player_pos = old_player_pos[:]

    for i, npc_frames in enumerate([pnj_1_frames, pnj_2_frames, pnj_3_frames]):
        npc_frame = npc_frames[frame_index % len(npc_frames)]
        npc_pos = positions[i]
        screen.blit(npc_frame, npc_frame.get_rect(center=npc_pos))

        if interacting_pnj == i:
            if waiting_for_response[i]:  # Si on attend la réponse, afficher "..."
                draw_speech_bubble(screen, "...", npc_pos)
            elif pnj_responses[i]:  # Si la réponse est arrivée, afficher le texte
                draw_speech_bubble(screen, pnj_responses[i], npc_pos)

    screen.blit(player_frame, player_frame.get_rect(center=player_pos))

    # Afficher la bulle du joueur si le message n'a pas expiré
    if player_message and pygame.time.get_ticks() < message_display_time:
        draw_player_speech_bubble(screen, player_message, player_pos)

    # Affichage de l'indicateur d'enregistrement
    if is_recording:
        pygame.draw.circle(screen, (255, 0, 0), (WIDTH - 50, 50), 10)  # Cercle rouge en haut à droite
        font_recording = pygame.font.Font(None, 30)
        text_surface = font_recording.render("Enregistrement...", True, (255, 0, 0))
        screen.blit(text_surface, (WIDTH - 250, 40))

    frame_index = (pygame.time.get_ticks() // (animation_speed // 4)) % len(pnj_1_frames)

    # Déterminer l'opacité du bouton (transparence si aucun PNJ proche)
    button_alpha = 255 if closest_pnj is not None else 100  # Opaque si PNJ proche, sinon semi-transparent

    # Afficher le bouton Record en tant qu'image PNG
    screen.blit(record_button_image, record_button_rect.topleft)

    # Ajouter la lettre "A" sur le bouton Record
    font_button = pygame.font.Font(None, 40)
    text_A = font_button.render("A", True, (0, 0, 0))  # Noir pour plus de contraste
    screen.blit(text_A, (record_button_rect.centerx - text_A.get_width() // 2, record_button_rect.centery - text_A.get_height() // 2))


    # Afficher le bouton Report en tant qu'image PNG
    screen.blit(report_button_image, report_button_rect.topleft)

    # Ajouter la lettre "E" en blanc ou rouge selon la lisibilité
    font_button = pygame.font.Font(None, 40)
    text_E = font_button.render("E", True, (0, 0, 0))  # Blanc pour plus de contraste
    screen.blit(text_E, (report_button_rect.centerx - text_E.get_width() // 2, report_button_rect.centery - text_E.get_height() // 2))


    pygame.display.flip()
    clock.tick(60)
