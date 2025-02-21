import ollama
import requests
# import nltk
from bert_score import BERTScorer
# from transformers import BertTokenizer, BertModel
import ssl

import nltk

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# nltk.download()

nltk.download('wordnet')
nltk.download('omw-1.4')

from rouge_score import rouge_scorer
import sacrebleu
from nltk.translate.meteor_score import meteor_score
from nltk.tokenize import word_tokenize

def calculate_nlp_scores(reference, candidate):
    """
    Calcule les scores ROUGE, BLEU et METEOR entre deux textes.
    """
    # 1️⃣ **Calcul du score ROUGE (ROUGE-L utilisé)**
    scorer = rouge_scorer.RougeScorer(['rougeL'], use_stemmer=True)
    rouge_scores = scorer.score(reference, candidate)
    rouge_l = rouge_scores['rougeL'].fmeasure  # ROUGE-L F1 score

    # 2️⃣ **Calcul du score BLEU**
    bleu_score = sacrebleu.sentence_bleu(candidate, [reference]).score / 100  # Normalisé entre 0 et 1

    # 3️⃣ **Calcul du score METEOR**
    meteor = meteor_score([word_tokenize(reference)], word_tokenize(candidate))

    return rouge_l, bleu_score, meteor



def evaluate_creativity(prompt1, prompt2, model="gemma2"):
    """
    Évalue lequel des deux prompts est le plus créatif avec une évaluation qualitative
    et des métriques quantitatives (ROUGE, BLEU, METEOR, BERTScore).
    """
    
    # **1. Évaluation qualitative avec Ollama**
    evaluation_prompt = f"""
    Je vais te donner deux versions d'un contexte narratif pour un jeu de rôle.
    Ta tâche est d'évaluer lequel est le plus créatif. 
    Critères de créativité : originalité, richesse du vocabulaire, diversité des idées.

    Contexte 1 :
    {prompt1}

    Contexte 2 :
    {prompt2}

    Donne-moi une évaluation comparative et désigne le plus créatif avec une explication détaillée.
    """

    response = ollama.chat(model=model, messages=[{"role": "system", "content": evaluation_prompt}])
    qualitative_analysis = response["message"]["content"]

    # **2. Évaluation quantitative avec des métriques NLP**
    return qualitative_analysis


# **Récupérer les contextes depuis l'API Flask**
prompt_1 = requests.get("http://localhost:8000/context?from_app=true").json()["context"]
prompt_2 = requests.get("http://localhost:8000/context?from_app=false").json()["context"]

scorer = BERTScorer(model_type='bert-base-uncased')
P, R, F1 = scorer.score([prompt_1], [prompt_2])

rouge_l, bleu, meteor = calculate_nlp_scores(prompt_1, prompt_2)

# **Évaluer la créativité et calculer les métriques**
qualitative_result = evaluate_creativity(prompt_1, prompt_2)

print('--- Les prompts récupérés ---')
print(prompt_1)
print(prompt_2)
print('--- Fin des prompts ---')
print('\n\n\n\n')
print('--- Calcul des scores ---')
print(f"BERTScore Precision: {P.mean():.4f}, Recall: {R.mean():.4f}, F1: {F1.mean():.4f}")
print(f"ROUGE-L: {rouge_l:.4f}, BLEU: {bleu:.4f}, METEOR: {meteor:.4f}")
print('--- Fin des scores ---')
print('\n\n\n\n')
print('--- Évaluation par Gemma2 ---')
print(qualitative_result)
print('--- Fin de l\'évaluation ---')
