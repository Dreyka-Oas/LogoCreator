# ✨ LogoCreator - Générateur de Dégradés Premium

**LogoCreator** est une application de bureau moderne développée en Python permettant de générer des logos, des icônes et des fonds d'écran haute résolution avec des dégradés esthétiques, des contours multiples et des superpositions d'images.

![Python](https://img.shields.io/badge/Python-3.x-blue.svg) ![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-green.svg) ![Pillow](https://img.shields.io/badge/Image-Pillow-yellow.svg)

## 🚀 Fonctionnalités Principales

*   **🎨 Palette de Couleurs Modernes :** Une sélection de couleurs tendances 2025 (Sage, Cosmic Blue, Rose Gold, etc.) ou choix par code HEX personnalisé.
*   **🖼️ Gestion des Dégradés :**
    *   Direction personnalisable (Diagonales, Radial, Verticale, Horizontale).
    *   Ajustement de la luminosité et du facteur d'assombrissement.
*   **🖌️ Formes et Contours :**
    *   Coins arrondis ajustables (jusqu'à la rondeur parfaite).
    *   Système de **contours en cascade** (multiples couches de bordures colorées).
*   **🧩 Superposition d'Image (Overlay) :**
    *   Importation de logos ou icônes (PNG, JPG, etc.).
    *   Redimensionnement intelligent.
    *   **Recoloration** de l'icône (changement de couleur unie).
    *   Inversion des couleurs.
    *   Lien direct vers Flaticon pour trouver des ressources.
*   **⚡ Performance :**
    *   Utilisation du **Multiprocessing** pour ne pas figer l'interface lors de la génération de grandes images (4K+).
    *   Affichage de l'utilisation CPU en temps réel.
*   **👁️ Aperçu en Temps Réel :** Visualisation immédiate des changements avant le rendu final.
*   **💾 Formats de Sortie :** PNG (transparence), JPG, WEBP, ICO, GIF, TIFF, BMP.
*   **⚙️ Sauvegarde Automatique :** Les paramètres sont sauvegardés dans `settings.json` entre les sessions.

## 📋 Prérequis

Avant de lancer l'application, assurez-vous d'avoir **Python 3.x** installé. Vous aurez besoin des bibliothèques suivantes :

*   `customtkinter` (Interface graphique)
*   `Pillow` (Traitement d'image)
*   `psutil` (Monitoring CPU)

## 🛠️ Installation

1.  **Cloner ou télécharger le projet** dans votre répertoire local.

2.  **Installer les dépendances** via pip :

```bash
pip install customtkinter Pillow psutil
```

3.  **Lancer l'application :**

```bash
python start.py
```

## 📖 Guide d'Utilisation

1.  **Sélection de la Couleur :**
    *   Au lancement, choisissez une couleur de base parmi la palette proposée ou entrez un code HEX.
2.  **Configuration :**
    *   **Dimensions :** Définissez la largeur et la hauteur (ex: 4096 x 4096).
    *   **Image Superposée :** Importez une image (logo) si souhaité, ajustez sa taille et sa couleur.
    *   **Luminosité :** Réglez l'intensité du dégradé.
    *   **Contours :** Ajoutez des couches de bordures (padding) et choisissez leurs couleurs.
    *   **Arrondi :** Ajustez le radius des coins (ou cochez "Rondeur parfaite" pour un cercle/ovale).
3.  **Génération :**
    *   Choisissez le format de fichier (ex: PNG).
    *   Cliquez sur **🚀 Générer l'image**.
    *   Choisissez l'emplacement de sauvegarde.

## 📂 Structure du Projet

```text
LogoCreator/
│
├── start.py           # Le code source principal de l'application
├── settings.json      # Fichier de sauvegarde des configurations (généré auto)
├── .gitattributes     # Configuration Git (normalisation des fins de ligne)
└── README.md          # Documentation du projet
```

## ⚙️ Détails Techniques

*   **Multiprocessing :** Le calcul des pixels, des dégradés et des masques d'arrondi est déporté dans un processus séparé (`ProcessPoolExecutor` / `multiprocessing.Process`) pour garantir la fluidité de l'interface utilisateur.
*   **Sauvegarde (`settings.json`) :** Vos préférences (taille, padding, rayon, format, etc.) sont stockées localement. Si le fichier est corrompu ou manquant, il sera régénéré avec les valeurs par défaut.

## 📝 Auteur

Projet généré et maintenu pour la création rapide d'assets graphiques.

---