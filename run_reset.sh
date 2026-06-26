#!/bin/bash

# 1. Aller dans le répertoire cible
cd /mnt/mariage_data/

# 2. Choix du dépôt
echo "Quel dépôt veux-tu cloner ?"
echo "1) BibiUnion"
echo "2) BibiUnion2"
read -p "Choix (1 ou 2) : " choice

# 3. Définir l'URL selon le choix
if [ "$choice" = "1" ]; then
    REPO="https://github.com/THEMEZE/BibiUnion.git"
elif [ "$choice" = "2" ]; then
    REPO="https://github.com/THEMEZE/BibiUnion2.git"
else
    echo "Choix invalide"
    exit 1
fi

# 4. Nettoyage du dossier cible
[ -d BibiUnion ] && rm -rf BibiUnion

# 5. Clone toujours dans le même dossier
git clone "$REPO" BibiUnion

cd BibiUnion
echo "Clone terminé : $REPO"

#cd /mnt/mariage_data && rm -rf BibiUnion && git clone https://github.com/THEMEZE/BibiUnion.git && cd BibiUnion

# 2. Lancer l'installation
chmod +x install.sh
./install.sh

# 3. Démarrer le tunnel (à chaque redémarrage du Pi)
chmod +x start_tunnel.sh
sudo ./start_tunnel.sh

