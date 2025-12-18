#!/bin/bash
set -e # Sortir immédiatement si une commande échoue

# --- CONFIGURATION ---
# Adresse IP publique de ton Droplet DigitalOcean
DROPLET_IP="104.236.244.230" 
# Utilisateur SSH (généralement root sur DigitalOcean)
SSH_USER="root"
# Chemin vers la racine de ton projet sur le Droplet
REMOTE_PROJECT_PATH="/STI_projet_backend"
# Nom de la branche Git à déployer
GIT_BRANCH="master" # Ou "main" si c'est ta branche principale
# Fichier docker-compose pour la production
DOCKER_COMPOSE_FILE="docker-compose.yml"

echo "=== Démarrage du déploiement sur le Droplet ${DROPLET_IP} ==="

# --- 1. Vérification et Push Git (depuis la machine locale) ---
echo -e "\n--- 1. Vérification et Push Git local ---"
# Assure-toi que toutes les modifications sont poussées avant le déploiement
git add .
git commit -m "Déploiement automatique: $(date)" || true # '|| true' pour ne pas échouer si pas de modifs
git push origin $GIT_BRANCH

echo "Code poussé sur ${GIT_BRANCH}. Connexion au Droplet..."

# --- 2. Connexion SSH et Exécution des commandes à distance ---
ssh ${SSH_USER}@${DROPLET_IP} << EOF
    set -e # Sortir immédiatement si une commande échoue sur le serveur distant

    echo -e "\n--- 2.1. Navigation vers le répertoire du projet (${REMOTE_PROJECT_PATH}) ---"
    cd ${REMOTE_PROJECT_PATH}

    echo -e "\n--- 2.2. Récupération des dernières modifications depuis Git ---"
    # Ceci écrase toute modification locale sur le serveur et synchronise avec le dépôt distant
    git pull

    echo -e "\n--- Déploiement distant terminé ! ---"
    echo "Votre application devrait être accessible via http://${DROPLET_IP}/api/docs/"
    echo "Pour voir les logs : docker compose -f ${DOCKER_COMPOSE_FILE} logs -f"
EOF

echo -e "\n=== Script de déploiement local terminé ==="
echo "Accédez à l'application via http://${DROPLET_IP}/api/docs/"