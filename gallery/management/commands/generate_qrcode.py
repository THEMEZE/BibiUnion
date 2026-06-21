import os
import qrcode
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Génère le QR Code pointant vers la page d'upload du site mariage."

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default=None,
            help="URL personnalisée (par défaut : SITE_PUBLIC_URL/upload/)"
        )

    def handle(self, *args, **options):
        url = options['url'] or f"{settings.SITE_PUBLIC_URL}/upload/"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#b08d4f", back_color="white")

        qr_dir = os.path.join(settings.MEDIA_ROOT, 'qrcodes')
        os.makedirs(qr_dir, exist_ok=True)

        qr_path = os.path.join(qr_dir, 'qrcode.png')
        img.save(qr_path)

        self.stdout.write(self.style.SUCCESS(f"QR Code généré : {qr_path}"))
        self.stdout.write(self.style.SUCCESS(f"URL encodée : {url}"))
