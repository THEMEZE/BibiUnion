import os
import uuid
from io import BytesIO

from django.db import models
from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ExifTags

# Active le support HEIC/HEIF via pillow-heif
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


def photo_upload_path(instance, filename):
    """Génère un nom de fichier unique pour éviter les collisions."""
    ext = filename.split('.')[-1].lower()
    new_name = f"{uuid.uuid4().hex}.{ext}"
    return os.path.join('photos', new_name)


def thumbnail_upload_path(instance, filename):
    ext = filename.split('.')[-1].lower()
    new_name = f"{uuid.uuid4().hex}_thumb.{ext}"
    return os.path.join('thumbnails', new_name)


class Photo(models.Model):
    """Photo déposée par un invité du mariage."""

    image = models.ImageField(
        upload_to=photo_upload_path,
        verbose_name="Photo originale"
    )
    thumbnail = models.ImageField(
        upload_to=thumbnail_upload_path,
        blank=True,
        null=True,
        verbose_name="Miniature"
    )
    date_upload = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date d'envoi"
    )
    auteur = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Nom de l'invité"
    )
    table = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        choices=settings.TABLE_CHOICES,
        verbose_name="Table"
    )

    class Meta:
        ordering = ['-date_upload']
        verbose_name = "Photo"
        verbose_name_plural = "Photos"

    def __str__(self):
        nom = self.auteur if self.auteur else "Anonyme"
        return f"Photo de {nom} - {self.date_upload.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        """
        À la sauvegarde :
        1. Corrige l'orientation EXIF (photos prises avec smartphone)
        2. Redimensionne l'original si > 1920px de large
        3. Génère une miniature de 400px de large
        """
        # Sauvegarde initiale pour avoir un fichier sur le disque
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new and self.image:
            self._process_image()

    def _process_image(self):
        """Traite l'image : correction EXIF, redimensionnement, miniature."""
        try:
            img = Image.open(self.image.path)

            # Correction de l'orientation selon les données EXIF
            img = self._fix_orientation(img)

            # Conversion en RGB si nécessaire (HEIC, PNG avec transparence -> JPEG)
            if img.mode in ('RGBA', 'P'):
                if self.image.name.lower().endswith(('.png', '.webp')):
                    pass  # on garde le mode pour PNG/WEBP
                else:
                    img = img.convert('RGB')
            elif img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')

            # Redimensionnement de l'original si trop large
            max_width = settings.MAX_IMAGE_WIDTH
            if img.width > max_width:
                ratio = max_width / float(img.width)
                new_height = int(img.height * ratio)
                img_resized = img.resize((max_width, new_height), Image.LANCZOS)
            else:
                img_resized = img

            # Sauvegarde de l'original redimensionné (écrase le fichier)
            self._save_image_to_field(img_resized, self.image, is_original=True)

            # Génération de la miniature
            thumb_width = settings.THUMBNAIL_WIDTH
            ratio_thumb = thumb_width / float(img_resized.width)
            thumb_height = int(img_resized.height * ratio_thumb)
            thumb_img = img_resized.copy()
            thumb_img.thumbnail((thumb_width, thumb_height), Image.LANCZOS)

            self._save_image_to_field(thumb_img, self.thumbnail, is_original=False, is_thumbnail=True)

            # Sauvegarde finale des champs sans re-déclencher save() en boucle
            super().save(update_fields=['image', 'thumbnail'])

        except Exception as e:
            # En cas d'erreur de traitement, on garde l'image originale
            print(f"Erreur de traitement d'image pour Photo {self.pk}: {e}")

    def _fix_orientation(self, img):
        """Corrige automatiquement l'orientation selon les métadonnées EXIF."""
        try:
            exif = img.getexif()
            orientation_key = None
            for key, val in ExifTags.TAGS.items():
                if val == 'Orientation':
                    orientation_key = key
                    break

            if orientation_key and orientation_key in exif:
                orientation = exif[orientation_key]
                rotations = {
                    3: 180,
                    6: 270,
                    8: 90,
                }
                if orientation in rotations:
                    img = img.rotate(rotations[orientation], expand=True)
        except Exception:
            pass
        return img

    def _save_image_to_field(self, pil_image, field, is_original=False, is_thumbnail=False):
        """Sauvegarde une image PIL dans un champ Django ImageField (écrase l'existant)."""
        buffer = BytesIO()

        # Détermine le format de sortie
        original_ext = os.path.splitext(self.image.name)[1].lower().lstrip('.')
        if original_ext == 'heic':
            # On convertit toujours le HEIC en JPEG pour compatibilité web
            save_format = 'JPEG'
            ext = 'jpg'
            if pil_image.mode == 'RGBA':
                pil_image = pil_image.convert('RGB')
        elif original_ext in ('jpg', 'jpeg'):
            save_format = 'JPEG'
            ext = 'jpg'
        elif original_ext == 'png':
            save_format = 'PNG'
            ext = 'png'
        elif original_ext == 'webp':
            save_format = 'WEBP'
            ext = 'webp'
        else:
            save_format = 'JPEG'
            ext = 'jpg'

        if save_format == 'JPEG':
            pil_image.save(buffer, format=save_format, quality=85, optimize=True)
        elif save_format == 'WEBP':
            pil_image.save(buffer, format=save_format, quality=85)
        else:
            pil_image.save(buffer, format=save_format, optimize=True)

        buffer.seek(0)

        if is_original:
            # On écrase le fichier existant sans changer le nom
            filename = os.path.basename(self.image.name)
            if ext != original_ext and original_ext == 'heic':
                # renomme l'extension pour heic -> jpg
                filename = os.path.splitext(filename)[0] + '.jpg'
                # supprime l'ancien fichier heic
                old_path = self.image.path
                self.image.name = os.path.join('photos', filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
            field.save(filename, ContentFile(buffer.read()), save=False)
        elif is_thumbnail:
            base_name = os.path.splitext(os.path.basename(self.image.name))[0]
            thumb_filename = f"{base_name}_thumb.{ext}"
            field.save(thumb_filename, ContentFile(buffer.read()), save=False)

    def delete(self, *args, **kwargs):
        """Supprime aussi les fichiers physiques (image + miniature)."""
        if self.image and os.path.isfile(self.image.path):
            os.remove(self.image.path)
        if self.thumbnail and os.path.isfile(self.thumbnail.path):
            os.remove(self.thumbnail.path)
        super().delete(*args, **kwargs)

    @property
    def filename(self):
        return os.path.basename(self.image.name)
