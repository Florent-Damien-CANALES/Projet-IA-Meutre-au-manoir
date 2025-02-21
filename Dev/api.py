import os
import asyncio
import random
import ollama
from flask import Flask, request, jsonify, has_request_context
from flask_cors import CORS
from dotenv import load_dotenv
from collections import deque
import subprocess

import json

# create audios folder if not exists
if not os.path.exists("audios"):
    os.makedirs("audios")

# ✅ Charger les variables d'environnement
load_dotenv()

# ✅ Initialisation de Flask
app = Flask(__name__)
CORS(app)

context = ""

# minotaure
# satire
# esprit

personnages = {
    "1": 'Minotaure : l\'apprenti majordome',
    "2": 'Satire : le jardinier',
    "0": 'Esprit : la cuisinière'
}

# roles = {
#     "0": 'un innocent',
#     "1": 'le tueur',
#     "2": 'un innocent'
# }

roles_tag = ['un innocent', 'le tueur', 'un innocent']

random.shuffle(roles_tag)
roles = {str(i): roles_tag[i] for i in range(len(roles_tag))}

prompts_folder = 'prompts/'
PROMPTS_PERSONNAGES = json.load(open(f"{prompts_folder}prompts_v5.json", 'r'))

HISTORIQUE_CONV = deque(maxlen=50)
# create a random dict with the roles and the personnages id

print(roles)
@app.route('/quitueur', methods=['GET'])
def quitueur_api():
    try:
        # return the id of the tueur
        return jsonify({'tueur': int([key for key in roles if roles[key] == 'le tueur'][0])})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/startpromptgamemaster', methods=['GET'])
def startpromptgamemaster_api():
    try:
        # return the id of the tueur
        le_contexte = context
        prompt_gamemaster_debut = PROMPTS_PERSONNAGES['prompt_gamemaster_debut_jeu']

        message = {"role": "system", "content": f"{le_contexte} {prompt_gamemaster_debut}"}
        response = ollama.chat(model="gemma2", messages=[message], options={"temperature": 1})
        return jsonify({"message": response['message']['content'].replace('\n', '')})
        # return jsonify({"message": PROMPTS_PERSONNAGES['prompt_gamemaster']})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/finalpromptgamemaster', methods=['GET'])
def finalpromptgamemaster_api():
    try:
        if "is_personnage" not in request.form:
            return jsonify({"error": "Aucun ID de personnage spécifié."}), 400
        
        is_personnage = request.form['is_personnage']
        id_tueur = [key for key in roles if roles[key] == 'le tueur'][0]
        personnage_from_id = personnages[str(is_personnage)]
        tueur_from_id = personnages[id_tueur]

        prompt_gamemaster_fin_jeu = "Le vrai tueur est " + tueur_from_id + "."


        correct_incorrect = "correct" if id_tueur == is_personnage else "incorrect"
        prompt_gamemaster_fin_jeu += PROMPTS_PERSONNAGES['prompt_gamemaster_fin_jeu'].replace('{{personnage}}', personnage_from_id).replace('{{correct_incorrect}}', correct_incorrect)
        # add the history of the whole conversation to have the context
        prompt_gamemaster_fin_jeu = f"{context} {prompt_gamemaster_fin_jeu}"

        print(prompt_gamemaster_fin_jeu)
        message_last = {"role": "system", "content": prompt_gamemaster_fin_jeu}
        reponse_ollama = ollama.chat(model="gemma2", messages=[message_last], options={"temperature": 1})
        return jsonify({"message": reponse_ollama['message']['content'].replace('\n', '')})
        # return the id of the tueur
        # return jsonify({"message": PROMPTS_PERSONNAGES['prompt_gamemaster']})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ✅ Dictionnaire des personnages avec leurs prompts personnalisés
# read prompts from json prompts_v1.json

# ✅ Fonction de transcription Whisper
def whisper_transcribe(file_path):
    # model = whisper.load_model("./models/whisper-large-v3-french/original_model.pt")  # Utilisation du modèle Whisper (peut être changé)
    # result = model.transcribe(file_path, language="fr")

    # file_path = os.path.join("audios", "recording.mp3")

    WHISPER_MODEL = "ylacombe/whisper-large-v3-turbo"
    transcript_path = os.path.join('.', f"transcript.json")

    command = [
            "insanely-fast-whisper",
            "--file-name", file_path,
            "--device-id", "mps",
            "--model-name", WHISPER_MODEL,
            "--batch-size", "4",
            "--transcript-path", transcript_path
        ]

    # Exécuter la commande
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    # print("Whisper Output:", result.stdout)

    return transcript_path
    # return send_file(transcript_path, as_attachment=True, mimetype="application/json")
    # return result["text"]

async def chatbot(query, id_personnage):  
    # ✅ Récupérer l'historique de la conversation du personnage
    # backstory = HISTORIQUE_CONV[0]

    # ✅ Sélectionner le prompt en fonction du personnage
    # backstory = PROMPTS_PERSONNAGES.get('backstory').replace('\n', '')
    # personnage = PROMPTS_PERSONNAGES.get(str(id_personnage)).replace('\n', '')
    formattage = PROMPTS_PERSONNAGES.get('prompt_system_format').replace('\n', '')
    personnage = personnages[str(id_personnage)]
    format_question = PROMPTS_PERSONNAGES.get('prompt_prefix_question').replace('\n', '').replace('{{personnage}}', personnage).replace('{{role}}', roles[str(id_personnage)])

    # system_prompt = f"{formattage} {format_question}"

    tosend = f"{formattage} {format_question} {query}"

    # ✅ Construire le message utilisateur
    user_message = {"role": "user", "content": f"Répond à ça : '{tosend}'"}

    # ✅ Ajouter le message actuel à l'historique
    HISTORIQUE_CONV.append(user_message)

    # ✅ Construire la conversation complète
    # conversation = [{"role": "system", "content": system_prompt}] + list(HISTORIQUE_CONV)

    conversation = list(HISTORIQUE_CONV)
    # print(conversation)

    # print(conversation)

    # print('yes')
    # ✅ Générer une réponse avec DeepSeek
    # print("Conversation envoyée à Ollama:", json.dumps(conversation, indent=2, ensure_ascii=False))
    response = ollama.chat(model="gemma2", messages=conversation, options={"temperature": 1})
    # print('yes2')
    # print(response)
    # print(response)
    # print('yes')

    # ✅ Ajouter la réponse au fil de la conversation
    reponse_message = {"role": "assistant", "content": response['message']['content']}
    HISTORIQUE_CONV.append(reponse_message)

    # print(HISTORIQUE_CONV)

    return response['message']['content']


@app.route('/whisperiser', methods=['POST'])
def whisperiser_api():
    try:
        if "file" not in request.files:
            return jsonify({"error": "Aucun fichier MP3 reçu."}), 400
        
        audio_file = request.files['file']
        temp_path = "audios/temp_audio.mp3"
        audio_file.save(temp_path)

        # ✅ Transcrire l'audio en texte
        # query = whisper_transcribe(temp_path)
        query = whisper_transcribe(temp_path)
        json_data = json.load(open(query, 'r'))
        print(json_data)
        os.remove(temp_path)
        return jsonify({"message": str(json_data['text']).strip()})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/repondre', methods=['POST'])
def repondre_api():
    try:
        if "query" not in request.form:
            return jsonify({"error": "Aucune question reçue."}), 400
        if "id_personnage" not in request.form:
            return jsonify({"error": "Aucun ID de personnage spécifié."}), 400
        
        query = request.form['query']
        id_personnage = request.form['id_personnage']

        response = asyncio.run(chatbot(query, id_personnage))

        return jsonify({"message": [{"text": str(response).strip().replace('\n', '')}]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route('/context', methods=['GET'])
def gen_context():

    if has_request_context():
        from_app = request.args.get("from_app", "false").lower() == "true"
    else:
        from_app = False

    if from_app:
        global context
        return jsonify({"context": context})
    else:
        prompt_gamemaster = PROMPTS_PERSONNAGES['prompt_gamemaster']
        le_tueur_est = PROMPTS_PERSONNAGES['prompt_tueur']
        # tueur nom est égal au personnage pour lequel la valeur du tableau role est 'Tueur'
        tueur_nom = [personnages[key] for key in roles if roles[key] == 'le tueur'][0]
        prompt_initial = f"{prompt_gamemaster} {le_tueur_est} {tueur_nom}"

        message = {"role": "system", "content":prompt_initial}
        response = ollama.chat(model="gemma2", messages=[message], options={"temperature": 1})
        cont = response['message']['content']
        return jsonify({"context": cont})

# ✅ Démarrer l'application Flask
if __name__ == "__main__":
    # from huggingface_hub import hf_hub_download
    # hf_hub_download(repo_id='bofenghuang/whisper-large-v3-french', filename='original_model.pt', local_dir='./models/whisper-large-v3-french')
    # preload the ollama model
    # print()
    with app.app_context():
        context = gen_context().json['context']
        print(context)
        ollama_context = {"role": "system", "content": context}
        # print(context)
        print(ollama_context)
        HISTORIQUE_CONV.append(ollama_context)
    # print(HISTORIQUE_CONV)
    # print(context)
    # print(tueur_nom)
    app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)
