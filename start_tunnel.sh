#!/bin/bash

SETTINGS="./mariage/settings.py"

echo "Démarrage du tunnel Cloudflare..."

# Lance cloudflared en arrière-plan et capture l'URL
cloudflared tunnel --url http://localhost:80 2>&1 &
TUNNEL_PID=$!

# Attend que l'URL apparaisse dans les logs
URL=""
echo "En attente de l'URL du tunnel..."
while [ -z "$URL" ]; do
    sleep 2
    URL=$(curl -s http://127.0.0.1:20241/metrics 2>/dev/null | grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' | head -1)
done

echo "URL détectée : $URL"
HOSTNAME=$(echo $URL | sed 's|https://||')
# Met à jour settings.py

# ALLOWED_HOSTS : sans https://
sed -i "/ALLOWED_HOSTS/,/\]/{s|'[^']*\.trycloudflare\.com'|'$HOSTNAME'|g}" "$SETTINGS"

# CSRF_TRUSTED_ORIGINS : avec https://
sed -i "/CSRF_TRUSTED_ORIGINS/,/\]/{s|'[^']*\.trycloudflare\.com'|'$URL'|g}" "$SETTINGS"

# SITE_PUBLIC_URL : avec https://
sed -i "s|SITE_PUBLIC_URL = '.*'|SITE_PUBLIC_URL = '$URL'|g" "$SETTINGS"

echo "settings.py mis à jour avec : $HOSTNAME"

sudo systemctl restart gunicorn-mariage
echo "Gunicorn redémarré ✅"

# Redémarre gunicorn
#cd /mnt/mariage_data/BibiUnion
source venv/bin/activate
python manage.py generate_qrcode
echo "QR Code régénéré ✅"

echo ""
echo "========================================"
echo "  Site accessible sur : $URL/upload/"
echo "========================================"

# Garde le tunnel en premier plan
wait $TUNNEL_PID
