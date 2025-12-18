#!/bin/bash
set -e # Sortir immédiatement si une commande échoue

# --- CONFIGURATION COMMUNE ---
DROPLET_IP="104.236.244.230" 
SSH_USER="root"
REMOTE_PROJECT_PATH="/root/STI_projet_backend"
GIT_BRANCH="master" # Ou "main"
DOCKER_COMPOSE_FILE="docker-compose.yml"

echo "=== Démarrage du déploiement RAPIDE du code sur ${DROPLET_IP} ==="

# --- 1. Vérification et Push Git (depuis la machine locale) ---
echo -e "\n--- 1. Vérification et Push Git local ---"
git add .
git commit -m "Déploiement rapide du code: $(date)" || true # '|| true' pour ne pas échouer si pas de modifs
git push origin $GIT_BRANCH

echo "Code poussé sur ${GIT_BRANCH}. Connexion au Droplet pour mise à jour rapide..."

# --- 2. Connexion SSH et Exécution des commandes à distance ---
ssh ${SSH_USER}@${DROPLET_IP} << EOF
    set -e # Sortir immédiatement si une commande échoue sur le serveur distant

    echo -e "\n--- 2.1. Navigation vers le répertoire du projet (${REMOTE_PROJECT_PATH}) ---"
    cd ${REMOTE_PROJECT_PATH}

    echo -e "\n--- 2.2. Récupération des dernières modifications de code ---"
    git pull origin ${GIT_BRANCH}

    echo -e "\n--- 2.3. Application des migrations (au cas où les modèles ont changé) ---"
    # C'est une bonne pratique de toujours migrer, même pour une mise à jour rapide
    docker compose -f ${DOCKER_COMPOSE_FILE} exec web python manage.py migrate --noinput

    echo -e "\n--- 2.4. Collecte des fichiers statiques (au cas où il y a des changements) ---"
    docker compose -f ${DOCKER_COMPOSE_FILE} exec web python manage.py collectstatic --noinput

    echo -e "\n--- 2.5. Redémarrage du service web (Gunicorn) pour recharger le code ---"
    # Seul le service 'web' est redémarré, c'est plus rapide
    docker compose -f ${DOCKER_COMPOSE_FILE} restart web

    echo -e "\n--- Déploiement rapide distant terminé ! ---"
    echo "L'application devrait être à jour. Pour voir les logs : docker compose -f ${DOCKER_COMPOSE_FILE} logs -f web"
EOF

echo -e "\n=== Script de déploiement rapide local terminé ==="
echo "Accédez à l'application via http://${DROPLET_IP}/api/docs/"