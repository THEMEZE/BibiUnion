#!/bin/bash

# 1. Cloner / copier le projet sur le Pi
#cd /mnt/mariage_data/
#[ -d BibiUnion ] && rm -rf BibiUnion
#git clone https://github.com/THEMEZE/BibiUnion.git   # ou scp depuis votre PC
#cd BibiUnion

#cd /mnt/mariage_data && rm -rf BibiUnion && git clone https://github.com/THEMEZE/BibiUnion.git && cd BibiUnion

# 2. Lancer l'installation
chmod +x install.sh
./install.sh

# 3. Démarrer le tunnel (à chaque redémarrage du Pi)
chmod +x start_tunnel.sh
sudo ./start_tunnel.sh

