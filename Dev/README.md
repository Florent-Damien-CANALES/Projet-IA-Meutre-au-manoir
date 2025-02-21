# 🏰 Meurtre au Manoir - Le Jeu

Bienvenue dans **Meurtre au Manoir**, un jeu d'enquête interactif où vous devez interroger les suspects et découvrir qui est le tueur ! Inspiré de Cluedo et de Colombo, ce jeu utilise **Ollama** et **Gemma2** pour rendre les dialogues immersifs.

---

## 🚀 Installation du Projet

### 1️⃣ **Cloner le projet**

### 2️⃣ **Créer un environnement virtuel**
On utilise un **venv** pour garder un environnement propre :
```sh
python -m venv venv
```

### 3️⃣ **Activer l'environnement virtuel**
Selon votre OS :
- **Windows** :
  ```sh
  venv\Scripts\activate
  ```
- **macOS / Linux** :
  ```sh
  source venv/bin/activate
  ```

### 4️⃣ **Installer les dépendances**
Dans l'environnement activé, installez les bibliothèques nécessaires :
```sh
pip install -r requirements.txt
```

---

## 🎮 Lancer le Jeu
Tout est automatisé avec **launcher.py**, qui démarre l'API et le jeu :
```sh
python lancer.py
```
Cela va :
1. Lancer l'**API Flask** dans un terminal.
2. Attendre qu'elle démarre.
3. Lancer le **jeu Pygame** dans un autre terminal.

---

## 🕹️ Comment Jouer ?

### 🎭 **Interroger les suspects**
1. **Déplacez-vous** vers un PNJ.
2. **Maintenez la touche `A`** pour parler.
3. **Votre voix est transcrite** et envoyée à l'IA.
4. **Le PNJ répond grâce à Ollama et Gemma2**.

### 🕵️ **Trouver le tueur**
- Chaque PNJ a une **histoire et un rôle**.
- Recueillez des **indices** et **analysez leurs réponses**.

### 🔴 **Accuser le coupable !**
1. Quand vous êtes convaincu, appuyez sur **`E`**.
2. Sélectionnez le suspect.
3. Vérifiez si vous avez trouvé **le véritable meurtrier** !

---

## ❓ Problèmes et Dépannage
- **L'API ne démarre pas ?** Vérifiez que **Ollama et Flask sont bien installés**.
- **Le jeu ne se lance pas ?** Assurez-vous que votre **venv est activé**.
- **Erreur avec `gemma2` ?** Vérifiez que le modèle est bien disponible avec Ollama.

---

## 🎯 Objectif
Découvrez **qui est le tueur** en interrogeant les suspects et en utilisant votre sens de la déduction. Bonne chance, détective ! 🕵️‍♂️