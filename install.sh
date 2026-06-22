#!/bin/bash
set -e

echo "=========================================="
echo "  Installation - Application Mariage"
echo "=========================================="

PROJECT_DIR="/mnt/mariage_data/BibiUnion"
VENV_DIR="$PROJECT_DIR/venv"

# ============================================
# 1. Mise à jour système et dépendances
# ============================================
echo "[1/8] Mise à jour du système..."
sudo apt update
sudo apt upgrade -y

echo "[2/8] Installation des paquets système..."
sudo apt install -y python3 python3-pip python3-venv nginx git \
    libjpeg-dev zlib1g-dev libwebp-dev libheif-dev \
    build-essential libssl-dev libffi-dev

# ============================================
# 2. Création de l'environnement virtuel
# ============================================
echo "[3/8] Création de l'environnement virtuel..."
cd "$PROJECT_DIR"
python3 -m venv venv
source venv/bin/activate

# ============================================
# 3. Installation des dépendances Python
# ============================================
echo "[4/8] Installation des dépendances Python..."
pip install --upgrade pip
pip install -r requirements.txt

# ============================================
# 4. Configuration Django
# ============================================
echo "[5/8] Configuration de la base de données..."
mkdir -p media/photos media/thumbnails media/qrcodes staticfiles logs
python manage.py makemigrations gallery
python manage.py migrate
python manage.py collectstatic --noinput

echo ""
echo "Création du compte administrateur :"
python manage.py createsuperuser

# ============================================
# 5. Génération du QR Code
# ============================================
echo "[6/8] Génération du QR Code..."
python manage.py generate_qrcode

# ============================================
# 6. Configuration des permissions
# ============================================
echo "[7/8] Configuration des permissions..."
sudo chown -R pi:www-data "$PROJECT_DIR"
sudo chmod -R 750 "$PROJECT_DIR"
sudo chmod -R 770 "$PROJECT_DIR/media"

# ============================================
# 7. Configuration Gunicorn + Nginx
# ============================================
echo "[8/8] Configuration de Gunicorn et Nginx..."

sudo cp deploy/gunicorn-mariage.socket /etc/systemd/system/
sudo cp deploy/gunicorn-mariage.service /etc/systemd/system/
sudo cp deploy/nginx-mariage.conf /etc/nginx/sites-available/mariage

sudo ln -sf /etc/nginx/sites-available/mariage /etc/nginx/sites-enabled/mariage
sudo rm -f /etc/nginx/sites-enabled/default

sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn-mariage.socket
sudo systemctl enable --now gunicorn-mariage.service

sudo nginx -t
sudo systemctl restart nginx

echo "=========================================="
echo "  Installation terminée !"
echo "=========================================="
echo ""
echo "Étapes suivantes :"
echo "1. Configurer Cloudflare Tunnel (voir README.md section 12)"
echo "2. Mettre à jour ALLOWED_HOSTS et SITE_PUBLIC_URL dans settings.py"
echo "3. Régénérer le QR Code : python manage.py generate_qrcode"
echo "4. Tester l'accès depuis un téléphone en 4G"
