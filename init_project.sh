#!/bin/bash

# Script d'initialisation du projet après reset (docker down -v)
# À exécuter depuis le dossier 'backend/'

PYTHON_EXEC="/home/mbogneng-junior/djangoenv/bin/python3"
# Fallback si le venv n'est pas là, on essaie 'python3' du path (si activé manuellement)
if [ ! -f "$PYTHON_EXEC" ]; then
    PYTHON_EXEC="python3"
fi

echo "🚀 --- RESTAURATION DU PROJET STI ---"
echo "Utilisation de : $PYTHON_EXEC"

# 1. Migrations de la base de données
echo -e "\n📦 1. Application des migrations..."
$PYTHON_EXEC manage.py migrate

# 2. Données de base (Domaines médicaux + Cas test)
echo -e "\n🏥 2. Initialisation des domaines et données de base..."
$PYTHON_EXEC manage.py init_data

# 3. Chargement des questions de profiling (QCM)
echo -e "\n📋 3. Chargement du QCM de profiling..."
$PYTHON_EXEC manage.py load_questions

# 4. Import des cas cliniques supplémentaires
echo -e "\n📂 4. Import des cas cliniques supplémentaires..."
$PYTHON_EXEC manage.py import_cas_cliniques

echo -e "\n✅ --- FIN DE L'INITIALISATION ---"
echo "Vous pouvez maintenant lancer le serveur (python3 manage.py runserver) ou utiliser l'app."
