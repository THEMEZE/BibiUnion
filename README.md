
# Application Photos de Mariage

Application Django permettant aux invités de déposer leurs photos
via un QR Code, hébergée sur un Raspberry Pi 2 B et exposée publiquement
via Cloudflare Tunnel.

## Démarrage rapide

1. `./install.sh` — installe tout et configure les services
2. Configurer Cloudflare Tunnel (voir section dédiée)
3. Mettre à jour `mariage/settings.py` :
   - `ALLOWED_HOSTS`
   - `CSRF_TRUSTED_ORIGINS`
   - `SITE_PUBLIC_URL`
4. `python manage.py generate_qrcode`
5. Imprimer le QR Code (disponible dans `/admin-gallery/`) et l'afficher pendant le mariage

## Parcours invité

1. Scan du QR Code -> arrive directement sur `/upload/`
2. Saisit son nom (optionnel) et sa table (optionnel)
3. Sélectionne ou glisse ses photos
4. Envoi automatique avec barre de progression
5. Peut consulter `/gallery/` pour voir toutes les photos

## Administration

- `/admin-gallery/` : suppression, téléchargement, ZIP, QR Code
- `/admin/` : interface Django native

## Sauvegarde

Voir `backup.sh` — exécution automatique quotidienne via cron.

## Maintenance

```bash
sudo systemctl restart gunicorn-mariage nginx cloudflared
sudo journalctl -u gunicorn-mariage -f
```

> Le projet est complet et déployable. Points d'attention avant la mise en production : remplacer `SECRET_KEY`, `mondomaine.fr` et l'UUID du tunnel par vos valeurs réelles, et tester l'upload HEIC depuis un iPhone (le décodage HEIC requiert `libheif-dev` installé via `install.sh`).



# 1. Architecture du projet

```bash
mkdir -p BibiUnion/{mariage,gallery/{templates/gallery,migrations,management/commands},templates,static/{css,js},media/{photos,thumbnails,qrcodes}}
cd BibiUnion
```
Arborescence finale :

```
BibiUnion/
├── manage.py
├── requirements.txt
├── install.sh
├── README.md
├── db.sqlite3 (généré)
│
├── mariage/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── gallery/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── migrations/__init__.py
│   └── management/commands/
│       ├── __init__.py
│       └── generate_qrcode.py
│
├── templates/
│   ├── base.html
│   ├── upload.html
│   ├── gallery.html
│   └── admin_gallery.html
│
├── static/
│   ├── css/style.css
│   └── js/app.js
│
└── media/
    ├── photos/
    ├── thumbnails/
    └── qrcodes/
```

# 2. Backend Django

## `requirements.txt`

```text
Django==5.0.7
Pillow==10.4.0
gunicorn==22.0.0
qrcode==7.4.2
pillow-heif==0.18.0
```

## `manage.py`

```python
#!/usr/bin/env python
import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mariage.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
```

## `mariage/__init__.py`

```python
```

## `mariage/settings.py`

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================
# SÉCURITÉ
# ============================================
# IMPORTANT : changez cette clé en production
SECRET_KEY = 'django-insecure-CHANGEZ-MOI-AVEC-UNE-VRAIE-CLE-SECRETE-AVANT-DEPLOIEMENT'

DEBUG = False

# Domaines autorisés (ajoutez votre domaine Cloudflare)
ALLOWED_HOSTS = [
    'photos.bibiunion.fr',
    'localhost',
    '127.0.0.1',
]

# Cloudflare Tunnel transmet en HTTPS -> faire confiance au header proxy
CSRF_TRUSTED_ORIGINS = [
    'https://photos.bibiunion.fr',
]

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# ============================================
# APPLICATIONS
# ============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'gallery',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mariage.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mariage.wsgi.application'

# ============================================
# BASE DE DONNÉES
# ============================================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ============================================
# VALIDATION MOTS DE PASSE (admin)
# ============================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ============================================
# INTERNATIONALISATION
# ============================================
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

# ============================================
# FICHIERS STATIQUES ET MEDIA
# ============================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# UPLOAD - LIMITES DE TAILLE
# ============================================
# 50 Mo par fichier (photos HEIC peuvent être volumineuses)
FILE_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 50 * 1024 * 1024
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 Mo

# Extensions et types MIME autorisés
ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'jpeg', 'png', 'heic', 'webp']
ALLOWED_IMAGE_MIME_TYPES = [
    'image/jpeg',
    'image/png',
    'image/heic',
    'image/heif',
    'image/webp',
]

# Redimensionnement max
MAX_IMAGE_WIDTH = 1920
THUMBNAIL_WIDTH = 400

# URL publique du site (pour le QR Code)
SITE_PUBLIC_URL = 'https://photos.bibiunion.fr'

# Liste des tables (modifiable selon votre plan de salle)
TABLE_CHOICES = [
    ('', 'Aucune table'),
    ('1', 'Table 1'),
    ('2', 'Table 2'),
    ('3', 'Table 3'),
    ('4', 'Table 4'),
    ('5', 'Table 5'),
    ('6', 'Table 6'),
    ('7', 'Table 7'),
    ('8', 'Table 8'),
    ('honneur', "Table d'honneur"),
]

# Session settings - login admin
LOGIN_URL = '/admin/login/'
```

## `mariage/urls.py`

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gallery.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

## `mariage/wsgi.py`

```python
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mariage.settings')

application = get_wsgi_application()
```

## `mariage/asgi.py`

```python
import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mariage.settings')

application = get_asgi_application()
```

## `gallery/__init__.py`

```python
```

## `gallery/apps.py`

```python 
from django.apps import AppConfig


class GalleryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gallery'
    verbose_name = 'Galerie Mariage'
```

## `gallery/migrations/__init__.py`

```python
```

## `gallery/management/__init__.py`

```python
```
## `gallery/management/commands/__init__.py`

```python
```

# 3. Modèle Django (Photo)

## `gallery/models.py`

```python
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
```

## `gallery/forms.py`

```python 
import os
from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from .models import Photo


def validate_image_extension(value):
    """Valide que l'extension du fichier est autorisée."""
    ext = os.path.splitext(value.name)[1].lower().lstrip('.')
    if ext not in settings.ALLOWED_IMAGE_EXTENSIONS:
        raise ValidationError(
            f"Format de fichier non autorisé : .{ext}. "
            f"Formats acceptés : {', '.join(settings.ALLOWED_IMAGE_EXTENSIONS)}"
        )


def validate_image_size(value):
    """Valide que la taille du fichier ne dépasse pas la limite."""
    if value.size > settings.MAX_UPLOAD_SIZE:
        max_mo = settings.MAX_UPLOAD_SIZE / (1024 * 1024)
        raise ValidationError(f"Le fichier dépasse la taille maximale autorisée ({max_mo:.0f} Mo).")


class PhotoUploadForm(forms.ModelForm):
    """Formulaire d'upload d'une photo (utilisé en interne, un par fichier)."""

    image = forms.ImageField(
        validators=[validate_image_extension, validate_image_size],
        required=True,
    )

    class Meta:
        model = Photo
        fields = ['image', 'auteur', 'table']
        widgets = {
            'auteur': forms.TextInput(attrs={
                'placeholder': 'Votre nom (optionnel)',
                'class': 'input-field',
                'maxlength': '100',
            }),
            'table': forms.Select(attrs={'class': 'input-field'}),
        }

    def clean_image(self):
        """Validation supplémentaire du contenu réel de l'image."""
        image = self.cleaned_data.get('image')
        if image:
            from PIL import Image as PILImage
            try:
                img = PILImage.open(image)
                img.verify()
            except Exception:
                raise ValidationError("Le fichier envoyé n'est pas une image valide.")
            image.seek(0)
        return image
```

# 4. Base de données

## Création des migrations

```bash
python manage.py makemigrations gallery
python manage.py migrate
```

Contenu généré attendu : `gallery/migrations/0001_initial.py` (auto-généré, non modifié manuellement).



# 5. Upload (avec QR Code -> formulaire simplifié)

Le scan du QR Code amène directement sur `/upload`, où l'invité **saisit juste** son nom puis **sélectionne ses photos**.


## `gallery/views.py`

```python
import os
import zipfile
import tempfile
from datetime import datetime

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_POST, require_GET
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.conf import settings
from django.db.models import Q
from django.utils.dateparse import parse_date

from .models import Photo
from .forms import PhotoUploadForm, validate_image_extension, validate_image_size


def upload_view(request):
    """Page d'upload : invité scanne le QR Code, arrive ici directement."""
    return render(request, 'upload.html', {
        'table_choices': settings.TABLE_CHOICES,
        'max_upload_mo': settings.MAX_UPLOAD_SIZE // (1024 * 1024),
    })


@csrf_protect
@require_POST
def upload_ajax(request):
    """
    Réception AJAX d'une photo unique (le JS frontend envoie un fichier
    à la fois pour permettre la barre de progression individuelle).
    """
    image_file = request.FILES.get('image')
    auteur = request.POST.get('auteur', '').strip()
    table = request.POST.get('table', '').strip()

    if not image_file:
        return JsonResponse({'success': False, 'error': "Aucun fichier reçu."}, status=400)

    # Validation extension
    try:
        validate_image_extension(image_file)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e.message if hasattr(e, "message") else e)}, status=400)

    # Validation taille
    try:
        validate_image_size(image_file)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e.message if hasattr(e, "message") else e)}, status=400)

    # Validation contenu réel de l'image
    from PIL import Image as PILImage
    try:
        img_check = PILImage.open(image_file)
        img_check.verify()
        image_file.seek(0)
    except Exception:
        return JsonResponse({'success': False, 'error': "Fichier image invalide ou corrompu."}, status=400)

    photo = Photo(
        image=image_file,
        auteur=auteur[:100] if auteur else None,
        table=table if table else None,
    )
    photo.save()

    return JsonResponse({
        'success': True,
        'id': photo.id,
        'thumbnail_url': photo.thumbnail.url if photo.thumbnail else photo.image.url,
        'auteur': photo.auteur or 'Anonyme',
    })


def gallery_view(request):
    """Page galerie publique : grille responsive de toutes les photos."""
    return render(request, 'gallery.html', {
        'table_choices': settings.TABLE_CHOICES,
    })


@require_GET
def gallery_data(request):
    """
    API JSON pour le chargement dynamique de la galerie.
    Supporte pagination, filtre par table, et filtre par date.
    """
    page_number = request.GET.get('page', 1)
    table_filter = request.GET.get('table', '').strip()
    date_filter = request.GET.get('date', '').strip()
    since_id = request.GET.get('since_id', '').strip()  # pour temps réel

    photos = Photo.objects.all()

    if table_filter:
        photos = photos.filter(table=table_filter)

    if date_filter:
        parsed_date = parse_date(date_filter)
        if parsed_date:
            photos = photos.filter(date_upload__date=parsed_date)

    # Mode "temps réel" : récupère uniquement les photos plus récentes qu'un ID donné
    if since_id:
        try:
            since_id_int = int(since_id)
            new_photos = photos.filter(id__gt=since_id_int)
            data = [_photo_to_dict(p) for p in new_photos]
            return JsonResponse({'photos': data, 'has_next': False})
        except ValueError:
            pass

    paginator = Paginator(photos, 24)  # 24 photos par page
    page_obj = paginator.get_page(page_number)

    data = [_photo_to_dict(p) for p in page_obj]

    return JsonResponse({
        'photos': data,
        'has_next': page_obj.has_next(),
        'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        'total_count': paginator.count,
    })


def _photo_to_dict(photo):
    return {
        'id': photo.id,
        'thumbnail_url': photo.thumbnail.url if photo.thumbnail else photo.image.url,
        'full_url': photo.image.url,
        'auteur': photo.auteur or 'Anonyme',
        'table': photo.get_table_display() if photo.table else '',
        'date_upload': photo.date_upload.strftime('%d/%m/%Y %H:%M'),
        'date_iso': photo.date_upload.isoformat(),
    }


@staff_member_required
def admin_gallery_view(request):
    """Page d'administration : suppression, téléchargement, ZIP."""
    photos = Photo.objects.all()

    table_filter = request.GET.get('table', '').strip()
    date_filter = request.GET.get('date', '').strip()

    if table_filter:
        photos = photos.filter(table=table_filter)
    if date_filter:
        parsed_date = parse_date(date_filter)
        if parsed_date:
            photos = photos.filter(date_upload__date=parsed_date)

    paginator = Paginator(photos, 48)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    qr_url = os.path.join(settings.MEDIA_URL, 'qrcodes', 'qrcode.png')
    qr_path = os.path.join(settings.MEDIA_ROOT, 'qrcodes', 'qrcode.png')
    qr_exists = os.path.isfile(qr_path)

    return render(request, 'admin_gallery.html', {
        'page_obj': page_obj,
        'total_count': paginator.count,
        'table_choices': settings.TABLE_CHOICES,
        'qr_url': qr_url if qr_exists else None,
        'site_public_url': settings.SITE_PUBLIC_URL,
        'selected_table': table_filter,
        'selected_date': date_filter,
    })


@staff_member_required
@require_POST
def delete_photo(request, photo_id):
    """Supprime une photo (fichiers + entrée DB)."""
    photo = get_object_or_404(Photo, id=photo_id)
    photo.delete()
    return JsonResponse({'success': True})


@staff_member_required
def download_photo(request, photo_id):
    """Télécharge l'image originale d'une photo."""
    photo = get_object_or_404(Photo, id=photo_id)
    if not os.path.isfile(photo.image.path):
        raise Http404("Fichier introuvable.")

    with open(photo.image.path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{photo.filename}"'
        return response


@staff_member_required
def download_zip(request):
    """
    Télécharge un ZIP contenant toutes les photos (originales),
    avec filtres optionnels par table / date.
    """
    photos = Photo.objects.all()

    table_filter = request.GET.get('table', '').strip()
    date_filter = request.GET.get('date', '').strip()

    if table_filter:
        photos = photos.filter(table=table_filter)
    if date_filter:
        parsed_date = parse_date(date_filter)
        if parsed_date:
            photos = photos.filter(date_upload__date=parsed_date)

    if not photos.exists():
        raise Http404("Aucune photo à télécharger.")

    with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmp:
        tmp_path = tmp.name

    with zipfile.ZipFile(tmp_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for photo in photos:
            if os.path.isfile(photo.image.path):
                arcname = f"{photo.date_upload.strftime('%Y%m%d_%H%M%S')}_{photo.filename}"
                zf.write(photo.image.path, arcname=arcname)

    with open(tmp_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/zip')
        zip_name = f"photos_mariage_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        response['Content-Disposition'] = f'attachment; filename="{zip_name}"'

    os.remove(tmp_path)
    return response
```

## `gallery/urls.py`

```python 
from django.urls import path
from . import views

urlpatterns = [
    path('', views.gallery_view, name='gallery'),
    path('upload/', views.upload_view, name='upload'),
    path('upload/ajax/', views.upload_ajax, name='upload_ajax'),
    path('gallery/', views.gallery_view, name='gallery'),
    path('gallery/data/', views.gallery_data, name='gallery_data'),
    path('admin-gallery/', views.admin_gallery_view, name='admin_gallery'),
    path('admin-gallery/delete/<int:photo_id>/', views.delete_photo, name='delete_photo'),
    path('admin-gallery/download/<int:photo_id>/', views.download_photo, name='download_photo'),
    path('admin-gallery/download-zip/', views.download_zip, name='download_zip'),
]
```

## `gallery/admin.py`

```python 
from django.contrib import admin
from .models import Photo


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'auteur', 'table', 'date_upload', 'thumbnail_preview')
    list_filter = ('table', 'date_upload')
    search_fields = ('auteur',)
    readonly_fields = ('thumbnail_preview', 'date_upload')

    def thumbnail_preview(self, obj):
        from django.utils.html import format_html
        if obj.thumbnail:
            return format_html('<img src="{}" style="max-height: 80px;" />', obj.thumbnail.url)
        return "(pas de miniature)"
    thumbnail_preview.short_description = "Aperçu"
```

# 6. Frontend

## `templates/base.html`

```html 
{% load static %}
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <title>{% block title %}Photos du Mariage{% endblock %}</title>
    <link rel="stylesheet" href="{% static 'css/style.css' %}">
    {% block extra_head %}{% endblock %}
</head>
<body>
    <header class="site-header">
        <div class="header-content">
            <h1 class="site-title">💍 Notre Mariage</h1>
            <nav class="site-nav">
                <a href="{% url 'upload' %}" class="nav-link {% if request.resolver_match.url_name == 'upload' %}active{% endif %}">
                    Déposer une photo
                </a>
                <a href="{% url 'gallery' %}" class="nav-link {% if request.resolver_match.url_name == 'gallery' %}active{% endif %}">
                    Galerie
                </a>
            </nav>
        </div>
    </header>

    <main class="main-content">
        {% block content %}{% endblock %}
    </main>

    <footer class="site-footer">
        <p>Merci de partager vos plus beaux souvenirs avec nous 💛</p>
    </footer>

    <script src="{% static 'js/app.js' %}"></script>
    {% block extra_scripts %}{% endblock %}
</body>
</html>
```

## 'templates/upload.html`

```html
{% extends "base.html" %}
{% load static %}

{% block title %}Déposer une photo - Mariage{% endblock %}

{% block content %}
<div class="upload-container">
    <h2 class="page-title">Partagez vos photos 📸</h2>
    <p class="page-subtitle">Indiquez votre nom, puis sélectionnez vos plus belles photos du mariage.</p>

    <form id="upload-form" class="upload-form">
        {% csrf_token %}

        <div class="form-group">
            <label for="auteur">Votre nom</label>
            <input type="text" id="auteur" name="auteur" class="input-field"
                   placeholder="Votre nom (optionnel)" maxlength="100">
        </div>

        <div class="form-group">
            <label for="table">Votre table</label>
            <select id="table" name="table" class="input-field">
                {% for value, label in table_choices %}
                    <option value="{{ value }}">{{ label }}</option>
                {% endfor %}
            </select>
        </div>

        <div class="form-group">
            <label class="dropzone" id="dropzone">
                <input type="file" id="file-input" name="images" accept="image/*,.heic" multiple hidden>
                <div class="dropzone-content">
                    <span class="dropzone-icon">📷</span>
                    <span class="dropzone-text">Touchez pour choisir vos photos</span>
                    <span class="dropzone-subtext">ou glissez-déposez ici (max {{ max_upload_mo }} Mo / photo)</span>
                </div>
            </label>
        </div>

        <div id="preview-container" class="preview-container"></div>

        <button type="submit" id="submit-btn" class="btn btn-primary" disabled>
            Envoyer les photos
        </button>
    </form>

    <div id="upload-summary" class="upload-summary" style="display:none;">
        <p id="summary-text"></p>
        <a href="{% url 'gallery' %}" class="btn btn-secondary">Voir la galerie</a>
        <button class="btn btn-outline" id="add-more-btn">Ajouter d'autres photos</button>
    </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
    window.UPLOAD_URL = "{% url 'upload_ajax' %}";
</script>
{% endblock %}
```

## `templates/gallery.html`

```html 
{% extends "base.html" %}
{% load static %}

{% block title %}Galerie - Mariage{% endblock %}

{% block content %}
<div class="gallery-container">
    <h2 class="page-title">Galerie des souvenirs ✨</h2>

    <div class="gallery-filters">
        <select id="filter-table" class="input-field">
            <option value="">Toutes les tables</option>
            {% for value, label in table_choices %}
                {% if value %}
                    <option value="{{ value }}">{{ label }}</option>
                {% endif %}
            {% endfor %}
        </select>

        <input type="date" id="filter-date" class="input-field">

        <button id="reset-filters" class="btn btn-outline">Réinitialiser</button>

        <label class="toggle-realtime">
            <input type="checkbox" id="toggle-slideshow">
            <span>Diaporama auto</span>
        </label>
    </div>

    <div id="gallery-grid" class="gallery-grid"></div>

    <div id="gallery-loader" class="gallery-loader" style="display:none;">
        Chargement...
    </div>

    <div id="gallery-empty" class="gallery-empty" style="display:none;">
        Aucune photo pour le moment. Soyez le premier à en partager !
    </div>
</div>

<!-- Lightbox plein écran -->
<div id="lightbox" class="lightbox" style="display:none;">
    <button class="lightbox-close" id="lightbox-close">&times;</button>
    <button class="lightbox-prev" id="lightbox-prev">&#8249;</button>
    <img id="lightbox-img" class="lightbox-img" src="" alt="Photo en plein écran">
    <button class="lightbox-next" id="lightbox-next">&#8250;</button>
    <div class="lightbox-caption" id="lightbox-caption"></div>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
    window.GALLERY_DATA_URL = "{% url 'gallery_data' %}";
</script>
{% endblock %}
```

## `templates/admin_gallery.html`

```html 
{% extends "base.html" %}
{% load static %}

{% block title %}Administration - Mariage{% endblock %}

{% block content %}
<div class="admin-container">
    <h2 class="page-title">Administration de la galerie</h2>

    <div class="admin-stats">
        <p><strong>{{ total_count }}</strong> photo(s) au total</p>
    </div>

    {% if qr_url %}
    <div class="qr-section">
        <h3>QR Code d'accès</h3>
        <img src="{{ qr_url }}" alt="QR Code" class="qr-image">
        <p class="qr-url">{{ site_public_url }}</p>
    </div>
    {% endif %}

    <div class="admin-filters">
        <form method="get" class="filter-form">
            <select name="table" class="input-field">
                <option value="">Toutes les tables</option>
                {% for value, label in table_choices %}
                    {% if value %}
                        <option value="{{ value }}" {% if value == selected_table %}selected{% endif %}>{{ label }}</option>
                    {% endif %}
                {% endfor %}
            </select>

            <input type="date" name="date" value="{{ selected_date }}" class="input-field">

            <button type="submit" class="btn btn-outline">Filtrer</button>
            <a href="{% url 'admin_gallery' %}" class="btn btn-outline">Réinitialiser</a>
        </form>

        <a href="{% url 'download_zip' %}?table={{ selected_table }}&date={{ selected_date }}" class="btn btn-primary">
            Télécharger tout en ZIP
        </a>
    </div>

    <div class="admin-grid">
        {% for photo in page_obj %}
        <div class="admin-card" data-id="{{ photo.id }}">
            <img src="{{ photo.thumbnail.url|default:photo.image.url }}" alt="Photo" class="admin-thumb">
            <div class="admin-card-info">
                <p class="admin-author">{{ photo.auteur|default:"Anonyme" }}</p>
                {% if photo.table %}<p class="admin-table">{{ photo.get_table_display }}</p>{% endif %}
                <p class="admin-date">{{ photo.date_upload|date:"d/m/Y H:i" }}</p>
            </div>
            <div class="admin-actions">
                <a href="{% url 'download_photo' photo.id %}" class="btn-icon" title="Télécharger">⬇️</a>
                <button class="btn-icon delete-btn" data-id="{{ photo.id }}" title="Supprimer">🗑️</button>
            </div>
        </div>
        {% endfor %}
    </div>

    <div class="pagination">
        {% if page_obj.has_previous %}
            <a href="?page={{ page_obj.previous_page_number }}&table={{ selected_table }}&date={{ selected_date }}" class="btn btn-outline">Précédent</a>
        {% endif %}
        <span>Page {{ page_obj.number }} / {{ page_obj.paginator.num_pages }}</span>
        {% if page_obj.has_next %}
            <a href="?page={{ page_obj.next_page_number }}&table={{ selected_table }}&date={{ selected_date }}" class="btn btn-outline">Suivant</a>
        {% endif %}
    </div>
</div>
{% endblock %}

{% block extra_scripts %}
<script>
    window.DELETE_URL_TEMPLATE = "/admin-gallery/delete/0/";
    window.CSRF_TOKEN = "{{ csrf_token }}";
</script>
{% endblock %}
```

## 'static/css/style.css`

```css
/* ============================================
   VARIABLES - Thème Mariage (blanc, or, beige, gris clair)
   ============================================ */
:root {
    --color-white: #ffffff;
    --color-gold: #c9a86a;
    --color-gold-dark: #b08d4f;
    --color-beige: #f5f0e6;
    --color-beige-dark: #e8dfc8;
    --color-gray-light: #f4f4f4;
    --color-gray: #888888;
    --color-text: #3a3a3a;
    --color-success: #7d9d7d;
    --color-error: #c97a7a;

    --shadow-soft: 0 4px 12px rgba(0, 0, 0, 0.08);
    --shadow-medium: 0 8px 24px rgba(0, 0, 0, 0.12);

    --radius: 12px;
    --transition: all 0.25s ease;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    background: linear-gradient(135deg, var(--color-beige) 0%, var(--color-white) 100%);
    color: var(--color-text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
}

/* ============================================
   HEADER
   ============================================ */
.site-header {
    background: var(--color-white);
    box-shadow: var(--shadow-soft);
    padding: 1rem;
    position: sticky;
    top: 0;
    z-index: 100;
}

.header-content {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
}

.site-title {
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--color-gold-dark);
    letter-spacing: 1px;
    text-align: center;
}

.site-nav {
    display: flex;
    gap: 0.5rem;
}

.nav-link {
    text-decoration: none;
    color: var(--color-text);
    padding: 0.5rem 1.25rem;
    border-radius: 999px;
    font-size: 0.9rem;
    font-weight: 500;
    transition: var(--transition);
    border: 1px solid var(--color-beige-dark);
}

.nav-link:hover,
.nav-link.active {
    background: var(--color-gold);
    color: var(--color-white);
    border-color: var(--color-gold);
}

/* ============================================
   MAIN CONTENT
   ============================================ */
.main-content {
    flex: 1;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
    padding: 1.5rem 1rem 3rem;
}

.page-title {
    font-size: 1.6rem;
    font-weight: 600;
    text-align: center;
    color: var(--color-gold-dark);
    margin-bottom: 0.5rem;
}

.page-subtitle {
    text-align: center;
    color: var(--color-gray);
    margin-bottom: 1.5rem;
    font-size: 0.95rem;
}

/* ============================================
   FORM ELEMENTS
   ============================================ */
.form-group {
    margin-bottom: 1.25rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.4rem;
    font-weight: 500;
    font-size: 0.9rem;
    color: var(--color-text);
}

.input-field {
    width: 100%;
    padding: 0.75rem 1rem;
    border: 1px solid var(--color-beige-dark);
    border-radius: var(--radius);
    font-size: 1rem;
    background: var(--color-white);
    color: var(--color-text);
    transition: var(--transition);
}

.input-field:focus {
    outline: none;
    border-color: var(--color-gold);
    box-shadow: 0 0 0 3px rgba(201, 168, 106, 0.15);
}

/* ============================================
   UPLOAD PAGE
   ============================================ */
.upload-container {
    max-width: 600px;
    margin: 0 auto;
    background: var(--color-white);
    padding: 1.5rem;
    border-radius: var(--radius);
    box-shadow: var(--shadow-soft);
}

.dropzone {
    display: block;
    border: 2px dashed var(--color-gold);
    border-radius: var(--radius);
    padding: 2rem 1rem;
    text-align: center;
    cursor: pointer;
    background: var(--color-beige);
    transition: var(--transition);
}

.dropzone.dragover {
    background: var(--color-beige-dark);
    border-color: var(--color-gold-dark);
    transform: scale(1.01);
}

.dropzone-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
}

.dropzone-icon {
    font-size: 2.5rem;
}

.dropzone-text {
    font-weight: 600;
    color: var(--color-text);
}

.dropzone-subtext {
    font-size: 0.8rem;
    color: var(--color-gray);
}

.preview-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(90px, 1fr));
    gap: 0.5rem;
    margin: 1rem 0;
}

.preview-item {
    position: relative;
    aspect-ratio: 1;
    border-radius: 8px;
    overflow: hidden;
    background: var(--color-gray-light);
}

.preview-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.preview-progress {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: rgba(255, 255, 255, 0.5);
}

.preview-progress-bar {
    height: 100%;
    background: var(--color-gold);
    width: 0%;
    transition: width 0.2s ease;
}

.preview-status {
    position: absolute;
    top: 4px;
    right: 4px;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    background: rgba(255, 255, 255, 0.9);
}

.preview-status.success { color: var(--color-success); }
.preview-status.error { color: var(--color-error); }

.preview-remove {
    position: absolute;
    top: 4px;
    left: 4px;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: rgba(0,0,0,0.5);
    color: white;
    border: none;
    cursor: pointer;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    justify-content: center;
}

/* ============================================
   BUTTONS
   ============================================ */
.btn {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    border-radius: 999px;
    border: none;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    text-align: center;
    text-decoration: none;
    transition: var(--transition);
    width: 100%;
}

.btn-primary {
    background: var(--color-gold);
    color: var(--color-white);
}

.btn-primary:hover:not(:disabled) {
    background: var(--color-gold-dark);
}

.btn-primary:disabled {
    background: var(--color-beige-dark);
    color: var(--color-gray);
    cursor: not-allowed;
}

.btn-secondary {
    background: var(--color-beige-dark);
    color: var(--color-text);
    margin-top: 0.5rem;
}

.btn-outline {
    background: transparent;
    color: var(--color-gold-dark);
    border: 1px solid var(--color-gold);
    margin-top: 0.5rem;
    width: auto;
}

.upload-summary {
    text-align: center;
    margin-top: 1.5rem;
}

.upload-summary p {
    margin-bottom: 1rem;
    font-weight: 600;
}

/* ============================================
   GALLERY PAGE
   ============================================ */
.gallery-filters {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    align-items: center;
}

.gallery-filters .input-field,
.gallery-filters .btn-outline {
    flex: 1;
    min-width: 120px;
    width: auto;
}

.toggle-realtime {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.9rem;
    cursor: pointer;
    background: var(--color-white);
    padding: 0.65rem 1rem;
    border-radius: var(--radius);
    border: 1px solid var(--color-beige-dark);
}

.gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.6rem;
}

.gallery-item {
    aspect-ratio: 1;
    border-radius: var(--radius);
    overflow: hidden;
    cursor: pointer;
    background: var(--color-gray-light);
    box-shadow: var(--shadow-soft);
    transition: var(--transition);
    position: relative;
}

.gallery-item:hover {
    transform: scale(1.02);
    box-shadow: var(--shadow-medium);
}

.gallery-item img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.gallery-item .gallery-item-caption {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    background: linear-gradient(transparent, rgba(0,0,0,0.6));
    color: white;
    font-size: 0.7rem;
    padding: 0.3rem 0.4rem;
    opacity: 0;
    transition: opacity 0.2s ease;
}

.gallery-item:hover .gallery-item-caption {
    opacity: 1;
}

.gallery-loader,
.gallery-empty {
    text-align: center;
    padding: 2rem;
    color: var(--color-gray);
}

/* ============================================
   LIGHTBOX
   ============================================ */
.lightbox {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.92);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.lightbox-img {
    max-width: 92%;
    max-height: 85vh;
    object-fit: contain;
    border-radius: 6px;
}

.lightbox-close,
.lightbox-prev,
.lightbox-next {
    position: absolute;
    background: rgba(255,255,255,0.1);
    border: none;
    color: white;
    font-size: 2rem;
    cursor: pointer;
    padding: 0.5rem 1rem;
    border-radius: 8px;
    transition: var(--transition);
}

.lightbox-close:hover,
.lightbox-prev:hover,
.lightbox-next:hover {
    background: rgba(255,255,255,0.25);
}

.lightbox-close {
    top: 1rem;
    right: 1rem;
}

.lightbox-prev {
    left: 1rem;
    top: 50%;
    transform: translateY(-50%);
}

.lightbox-next {
    right: 1rem;
    top: 50%;
    transform: translateY(-50%);
}

.lightbox-caption {
    position: absolute;
    bottom: 1.5rem;
    color: white;
    font-size: 0.9rem;
    background: rgba(0,0,0,0.4);
    padding: 0.4rem 1rem;
    border-radius: 999px;
}

/* ============================================
   ADMIN PAGE
   ============================================ */
.admin-container {
    background: var(--color-white);
    padding: 1.5rem;
    border-radius: var(--radius);
    box-shadow: var(--shadow-soft);
}

.admin-stats {
    text-align: center;
    margin-bottom: 1rem;
    color: var(--color-gray);
}

.qr-section {
    text-align: center;
    margin-bottom: 1.5rem;
    padding: 1rem;
    background: var(--color-beige);
    border-radius: var(--radius);
}

.qr-image {
    max-width: 180px;
    margin: 0.5rem auto;
}

.qr-url {
    font-size: 0.8rem;
    color: var(--color-gray);
    word-break: break-all;
}

.admin-filters {
    display: flex;
    flex-wrap: wrap;
    justify-content: space-between;
    gap: 0.75rem;
    margin-bottom: 1.5rem;
}

.filter-form {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.filter-form .input-field {
    width: auto;
}

.admin-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
    gap: 0.75rem;
}

.admin-card {
    background: var(--color-gray-light);
    border-radius: var(--radius);
    overflow: hidden;
    box-shadow: var(--shadow-soft);
}

.admin-thumb {
    width: 100%;
    aspect-ratio: 1;
    object-fit: cover;
}

.admin-card-info {
    padding: 0.5rem;
    font-size: 0.75rem;
}

.admin-author {
    font-weight: 600;
}

.admin-table,
.admin-date {
    color: var(--color-gray);
}

.admin-actions {
    display: flex;
    justify-content: space-around;
    padding: 0.4rem;
    border-top: 1px solid var(--color-beige-dark);
}

.btn-icon {
    background: none;
    border: none;
    font-size: 1.1rem;
    cursor: pointer;
    text-decoration: none;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    transition: var(--transition);
}

.btn-icon:hover {
    background: var(--color-beige);
}

.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 1rem;
    margin-top: 1.5rem;
    font-size: 0.9rem;
}

/* ============================================
   FOOTER
   ============================================ */
.site-footer {
    text-align: center;
    padding: 1.5rem;
    color: var(--color-gray);
    font-size: 0.85rem;
}

/* ============================================
   RESPONSIVE - Tablette / Desktop
   ============================================ */
@media (min-width: 600px) {
    .header-content {
        flex-direction: row;
        justify-content: space-between;
    }

    .gallery-grid {
        grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
    }

    .admin-grid {
        grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    }
}

@media (min-width: 900px) {
    .gallery-grid {
        grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    }
}
```

## `static/js/app.js`

```js 
/* ============================================
   APPLICATION JS - Mariage
   Gère : upload AJAX, galerie dynamique, lightbox,
   diaporama, administration
   ============================================ */

document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('upload-form')) {
        initUploadPage();
    }
    if (document.getElementById('gallery-grid')) {
        initGalleryPage();
    }
    if (document.querySelector('.admin-container')) {
        initAdminPage();
    }
});

/* ============================================
   PAGE UPLOAD
   ============================================ */
function initUploadPage() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const previewContainer = document.getElementById('preview-container');
    const submitBtn = document.getElementById('submit-btn');
    const form = document.getElementById('upload-form');
    const summary = document.getElementById('upload-summary');
    const summaryText = document.getElementById('summary-text');
    const addMoreBtn = document.getElementById('add-more-btn');

    let selectedFiles = [];

    // Drag & drop
    ['dragenter', 'dragover'].forEach(evt => {
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropzone.classList.add('dragover');
        });
    });

    ['dragleave', 'drop'].forEach(evt => {
        dropzone.addEventListener(evt, (e) => {
            e.preventDefault();
            dropzone.classList.remove('dragover');
        });
    });

    dropzone.addEventListener('drop', (e) => {
        const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/') || f.name.toLowerCase().endsWith('.heic'));
        addFiles(files);
    });

    fileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        addFiles(files);
        fileInput.value = ''; // permet de re-sélectionner les mêmes fichiers
    });

    function addFiles(files) {
        files.forEach(file => {
            const id = 'file_' + Math.random().toString(36).substr(2, 9);
            selectedFiles.push({ id, file, status: 'pending' });
            renderPreview(id, file);
        });
        updateSubmitState();
    }

    function renderPreview(id, file) {
        const item = document.createElement('div');
        item.className = 'preview-item';
        item.dataset.id = id;

        const img = document.createElement('img');
        item.appendChild(img);

        // HEIC ne s'affiche pas nativement dans <img> -> icône générique
        if (file.type.startsWith('image/') && !file.name.toLowerCase().endsWith('.heic')) {
            const reader = new FileReader();
            reader.onload = (e) => { img.src = e.target.result; };
            reader.readAsDataURL(file);
        } else {
            img.src = '';
            img.alt = '📷 HEIC';
            item.style.display = 'flex';
            item.style.alignItems = 'center';
            item.style.justifyContent = 'center';
            item.style.fontSize = '2rem';
            item.textContent = '📷';
        }

        const removeBtn = document.createElement('button');
        removeBtn.className = 'preview-remove';
        removeBtn.innerHTML = '&times;';
        removeBtn.type = 'button';
        removeBtn.addEventListener('click', () => removeFile(id));
        item.appendChild(removeBtn);

        const progressWrap = document.createElement('div');
        progressWrap.className = 'preview-progress';
        const progressBar = document.createElement('div');
        progressBar.className = 'preview-progress-bar';
        progressWrap.appendChild(progressBar);
        item.appendChild(progressWrap);

        previewContainer.appendChild(item);
    }

    function removeFile(id) {
        selectedFiles = selectedFiles.filter(f => f.id !== id);
        const el = previewContainer.querySelector(`[data-id="${id}"]`);
        if (el) el.remove();
        updateSubmitState();
    }

    function updateSubmitState() {
        const pendingFiles = selectedFiles.filter(f => f.status === 'pending' || f.status === 'error');
        submitBtn.disabled = pendingFiles.length === 0;
        submitBtn.textContent = pendingFiles.length > 0
            ? `Envoyer ${pendingFiles.length} photo(s)`
            : 'Envoyer les photos';
    }

    form.addEventListener('submit', function (e) {
        e.preventDefault();
        const auteur = document.getElementById('auteur').value;
        const table = document.getElementById('table').value;
        const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

        const filesToUpload = selectedFiles.filter(f => f.status === 'pending' || f.status === 'error');

        if (filesToUpload.length === 0) return;

        submitBtn.disabled = true;
        submitBtn.textContent = 'Envoi en cours...';

        let completed = 0;
        let successCount = 0;

        filesToUpload.forEach(fileObj => {
            uploadFile(fileObj, auteur, table, csrfToken, () => {
                completed++;
                if (fileObj.status === 'success') successCount++;
                if (completed === filesToUpload.length) {
                    onAllUploadsComplete(successCount, filesToUpload.length);
                }
            });
        });
    });

    function uploadFile(fileObj, auteur, table, csrfToken, callback) {
        const formData = new FormData();
        formData.append('image', fileObj.file);
        formData.append('auteur', auteur);
        formData.append('table', table);

        const xhr = new XMLHttpRequest();
        const item = previewContainer.querySelector(`[data-id="${fileObj.id}"]`);
        const progressBar = item ? item.querySelector('.preview-progress-bar') : null;

        xhr.open('POST', window.UPLOAD_URL, true);
        xhr.setRequestHeader('X-CSRFToken', csrfToken);

        xhr.upload.onprogress = function (e) {
            if (e.lengthComputable && progressBar) {
                const percent = (e.loaded / e.total) * 100;
                progressBar.style.width = percent + '%';
            }
        };

        xhr.onload = function () {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                if (response.success) {
                    fileObj.status = 'success';
                    markPreviewStatus(item, 'success', '✓');
                } else {
                    fileObj.status = 'error';
                    markPreviewStatus(item, 'error', '✗', response.error);
                }
            } else {
                fileObj.status = 'error';
                let errorMsg = "Erreur d'envoi";
                try {
                    const response = JSON.parse(xhr.responseText);
                    errorMsg = response.error || errorMsg;
                } catch (e) {}
                markPreviewStatus(item, 'error', '✗', errorMsg);
            }
            callback();
        };

        xhr.onerror = function () {
            fileObj.status = 'error';
            markPreviewStatus(item, 'error', '✗', 'Erreur réseau');
            callback();
        };

        xhr.send(formData);
    }

    function markPreviewStatus(item, status, icon, errorMsg) {
        if (!item) return;
        const statusEl = document.createElement('div');
        statusEl.className = `preview-status ${status}`;
        statusEl.textContent = icon;
        if (errorMsg) statusEl.title = errorMsg;
        item.appendChild(statusEl);
    }

    function onAllUploadsComplete(successCount, total) {
        form.style.display = 'none';
        summary.style.display = 'block';
        if (successCount === total) {
            summaryText.textContent = `${successCount} photo(s) envoyée(s) avec succès. Merci ! 💛`;
        } else {
            summaryText.textContent = `${successCount}/${total} photo(s) envoyée(s). Certaines ont échoué.`;
        }
    }

    addMoreBtn.addEventListener('click', () => {
        selectedFiles = [];
        previewContainer.innerHTML = '';
        form.style.display = 'block';
        summary.style.display = 'none';
        submitBtn.disabled = true;
        submitBtn.textContent = 'Envoyer les photos';
    });
}

/* ============================================
   PAGE GALERIE
   ============================================ */
function initGalleryPage() {
    const grid = document.getElementById('gallery-grid');
    const loader = document.getElementById('gallery-loader');
    const empty = document.getElementById('gallery-empty');
    const filterTable = document.getElementById('filter-table');
    const filterDate = document.getElementById('filter-date');
    const resetBtn = document.getElementById('reset-filters');
    const toggleSlideshow = document.getElementById('toggle-slideshow');

    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxCaption = document.getElementById('lightbox-caption');
    const lightboxClose = document.getElementById('lightbox-close');
    const lightboxPrev = document.getElementById('lightbox-prev');
    const lightboxNext = document.getElementById('lightbox-next');

    let currentPage = 1;
    let hasNext = true;
    let loading = false;
    let allPhotos = [];
    let lastPhotoId = 0;
    let currentLightboxIndex = 0;
    let slideshowInterval = null;
    let realtimeInterval = null;

    loadPhotos();

    // Scroll infini
    window.addEventListener('scroll', () => {
        if (loading || !hasNext) return;
        if (window.innerHeight + window.scrollY >= document.body.offsetHeight - 300) {
            currentPage++;
            loadPhotos();
        }
    });

    filterTable.addEventListener('change', resetAndReload);
    filterDate.addEventListener('change', resetAndReload);
    resetBtn.addEventListener('click', () => {
        filterTable.value = '';
        filterDate.value = '';
        resetAndReload();
    });

    function resetAndReload() {
        currentPage = 1;
        hasNext = true;
        allPhotos = [];
        lastPhotoId = 0;
        grid.innerHTML = '';
        empty.style.display = 'none';
        loadPhotos();
    }

    function loadPhotos() {
        loading = true;
        loader.style.display = 'block';

        const params = new URLSearchParams({
            page: currentPage,
            table: filterTable.value,
            date: filterDate.value,
        });

        fetch(`${window.GALLERY_DATA_URL}?${params}`)
            .then(res => res.json())
            .then(data => {
                loader.style.display = 'none';
                loading = false;
                hasNext = data.has_next;

                if (data.photos.length === 0 && allPhotos.length === 0) {
                    empty.style.display = 'block';
                    return;
                }

                data.photos.forEach(photo => {
                    allPhotos.push(photo);
                    renderPhoto(photo);
                    if (photo.id > lastPhotoId) lastPhotoId = photo.id;
                });
            })
            .catch(() => {
                loader.style.display = 'none';
                loading = false;
            });
    }

    function renderPhoto(photo) {
        const item = document.createElement('div');
        item.className = 'gallery-item';
        item.dataset.id = photo.id;

        const img = document.createElement('img');
        img.src = photo.thumbnail_url;
        img.loading = 'lazy';
        img.alt = `Photo de ${photo.auteur}`;
        item.appendChild(img);

        const caption = document.createElement('div');
        caption.className = 'gallery-item-caption';
        caption.textContent = `${photo.auteur}${photo.table ? ' • ' + photo.table : ''}`;
        item.appendChild(caption);

        item.addEventListener('click', () => openLightbox(photo.id));

        grid.appendChild(item);
    }

    /* ---------- Temps réel : nouvelles photos ---------- */
    realtimeInterval = setInterval(() => {
        if (!lastPhotoId) return;
        const params = new URLSearchParams({
            since_id: lastPhotoId,
            table: filterTable.value,
            date: filterDate.value,
        });
        fetch(`${window.GALLERY_DATA_URL}?${params}`)
            .then(res => res.json())
            .then(data => {
                if (data.photos && data.photos.length > 0) {
                    // Ajoute les nouvelles photos en haut de la grille
                    data.photos.slice().reverse().forEach(photo => {
                        allPhotos.unshift(photo);
                        if (photo.id > lastPhotoId) lastPhotoId = photo.id;

                        const item = document.createElement('div');
                        item.className = 'gallery-item';
                        item.dataset.id = photo.id;

                        const img = document.createElement('img');
                        img.src = photo.thumbnail_url;
                        img.loading = 'lazy';
                        img.alt = `Photo de ${photo.auteur}`;
                        item.appendChild(img);

                        const caption = document.createElement('div');
                        caption.className = 'gallery-item-caption';
                        caption.textContent = `${photo.auteur}${photo.table ? ' • ' + photo.table : ''}`;
                        item.appendChild(caption);

                        item.addEventListener('click', () => openLightbox(photo.id));

                        grid.insertBefore(item, grid.firstChild);
                        empty.style.display = 'none';
                    });
                }
            })
            .catch(() => {});
    }, 15000); // toutes les 15 secondes

    /* ---------- Lightbox plein écran ---------- */
    function openLightbox(photoId) {
        currentLightboxIndex = allPhotos.findIndex(p => p.id === photoId);
        if (currentLightboxIndex === -1) return;
        showLightboxPhoto();
        lightbox.style.display = 'flex';
    }

    function showLightboxPhoto() {
        const photo = allPhotos[currentLightboxIndex];
        lightboxImg.src = photo.full_url;
        lightboxCaption.textContent = `${photo.auteur}${photo.table ? ' • ' + photo.table : ''} - ${photo.date_upload}`;
    }

    lightboxClose.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) closeLightbox();
    });

    function closeLightbox() {
        lightbox.style.display = 'none';
        stopSlideshow();
    }

    lightboxPrev.addEventListener('click', () => {
        currentLightboxIndex = (currentLightboxIndex - 1 + allPhotos.length) % allPhotos.length;
        showLightboxPhoto();
    });

    lightboxNext.addEventListener('click', () => {
        currentLightboxIndex = (currentLightboxIndex + 1) % allPhotos.length;
        showLightboxPhoto();
    });

    document.addEventListener('keydown', (e) => {
        if (lightbox.style.display === 'flex') {
            if (e.key === 'Escape') closeLightbox();
            if (e.key === 'ArrowLeft') lightboxPrev.click();
            if (e.key === 'ArrowRight') lightboxNext.click();
        }
    });

    /* ---------- Diaporama automatique ---------- */
    toggleSlideshow.addEventListener('change', () => {
        if (toggleSlideshow.checked) {
            startSlideshow();
        } else {
            stopSlideshow();
        }
    });

    function startSlideshow() {
        if (allPhotos.length === 0) return;
        currentLightboxIndex = 0;
        showLightboxPhoto();
        lightbox.style.display = 'flex';
        slideshowInterval = setInterval(() => {
            currentLightboxIndex = (currentLightboxIndex + 1) % allPhotos.length;
            showLightboxPhoto();
        }, 4000);
    }

    function stopSlideshow() {
        if (slideshowInterval) {
            clearInterval(slideshowInterval);
            slideshowInterval = null;
            toggleSlideshow.checked = false;
        }
    }
}

/* ============================================
   PAGE ADMINISTRATION
   ============================================ */
function initAdminPage() {
    const deleteButtons = document.querySelectorAll('.delete-btn');

    deleteButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const photoId = this.dataset.id;
            if (!confirm('Supprimer cette photo définitivement ?')) return;

            const url = `/admin-gallery/delete/${photoId}/`;

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': window.CSRF_TOKEN,
                },
            })
                .then(res => res.json())
                .then(data => {
                    if (data.success) {
                        const card = document.querySelector(`.admin-card[data-id="${photoId}"]`);
                        if (card) card.remove();
                    } else {
                        alert('Erreur lors de la suppression.');
                    }
                })
                .catch(() => alert('Erreur réseau.'));
        });
    });
}
```

# 7. Compression (déjà intégrée)

La compression et la génération de miniatures sont gérées dans `gallery/models.py` via `Photo.save()` :

- Correction de l'orientation EXIF
- Redimensionnement à 1920px max (largeur)
- Génération d'une miniature à 400px

Aucun code supplémentaire requis.

# 8. QR Code

## `gallery/management/commands/generate_qrcode.py`

```python 
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
```

Génération du QR Code (à exécuter après configuration du domaine) :

```bash
source venv/bin/activate
python manage.py generate_qrcode
```

Le QR Code pointe vers `/upload/` directement : l'invité scanne → arrive sur le formulaire → saisit son nom → sélectionne ses photos.

# 9. Administration

Déjà implémentée : `/admin-gallery/` (suppression, téléchargement individuel, téléchargement ZIP, affichage du QR Code) + interface Django native `/admin/`.

Création du compte administrateur :

```bash 
source venv/bin/activate
python manage.py createsuperuser
```

# 10. Nginx

## /etc/nginx/sites-available/mariage


```nginx
server {
    listen 80;
    server_name photos-mariage.mondomaine.fr localhost 127.0.0.1;

    client_max_body_size 60M;

    access_log /var/log/nginx/mariage_access.log;
    error_log /var/log/nginx/mariage_error.log;

    location /static/ {
        alias /mnt/mariage_data/BibiUnion/staticfiles/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location /media/ {
        alias /mnt/mariage_data/BibiUnion/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://unix:/run/gunicorn-mariage.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_send_timeout 300;
    }
}
```

```bash
mkdir -p deploy
```

```bash
cat > ./deploy/nginx-mariage.conf << 'EOF'
server {
    listen 80;
    server_name photos-mariage.mondomaine.fr localhost 127.0.0.1;

    client_max_body_size 60M;

    access_log /var/log/nginx/mariage_access.log;
    error_log /var/log/nginx/mariage_error.log;

    location /static/ {
        alias /mnt/mariage_data/BibiUnion/staticfiles/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location /media/ {
        alias /mnt/mariage_data/BibiUnion/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://unix:/run/gunicorn-mariage.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
        proxy_send_timeout 300;
    }
}
EOF
```

Activation Nginx :

```bash 
sudo ln -sf /mnt/mariage_data/BibiUnion/deploy/nginx-mariage.conf /etc/nginx/sites-available/mariage
sudo ln -sf /etc/nginx/sites-available/mariage /etc/nginx/sites-enabled/mariage
sudo rm -f /etc/nginx/sites-enabled/default

sudo nginx -t
sudo systemctl restart nginx
```

# 11. Gunicorn (architecture correcte socket systemd)

👉 IMPORTANT : on utilise socket activation systemd uniquement
❌ PAS de --bind unix: dans gunicorn service

## /etc/systemd/system/gunicorn-mariage.socket

```ìni 
[Unit]
Description=Socket Gunicorn pour mariage

[Socket]
ListenStream=/run/gunicorn-mariage.sock
SocketUser=www-data
SocketGroup=www-data
SocketMode=0660

[Install]
WantedBy=sockets.target
```


```bash
cat > ./deploy/gunicorn-mariage.socket << 'EOF'
[Unit]
Description=Socket Gunicorn pour mariage

[Socket]
ListenStream=/run/gunicorn-mariage.sock
SocketUser=www-data
SocketGroup=www-data
SocketMode=0660

[Install]
WantedBy=sockets.target
EOF
```


## /etc/systemd/system/gunicorn-mariage.service

```ìni 
[Unit]
Description=Gunicorn daemon pour le site mariage
Requires=gunicorn-mariage.socket
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/mnt/mariage_data/BibiUnion

ExecStart=/mnt/mariage_data/BibiUnion/venv/bin/gunicorn \
          --access-logfile /mnt/mariage_data/BibiUnion/logs/gunicorn-access.log \
          --error-logfile /mnt/mariage_data/BibiUnion/logs/gunicorn-error.log \
          --workers 2 \
          --timeout 120 \
          mariage.wsgi:application

[Install]
WantedBy=multi-user.target
```

```bash
cat > ./deploy/gunicorn-mariage.service << 'EOF'
[Unit]
Description=Gunicorn daemon pour le site mariage
Requires=gunicorn-mariage.socket
After=network.target

[Service]
User=pi
Group=www-data
WorkingDirectory=/mnt/mariage_data/BibiUnion

ExecStart=/mnt/mariage_data/BibiUnion/venv/bin/gunicorn \
          --access-logfile /mnt/mariage_data/BibiUnion/logs/gunicorn-access.log \
          --error-logfile /mnt/mariage_data/BibiUnion/logs/gunicorn-error.log \
          --workers 2 \
          --timeout 120 \
          mariage.wsgi:application

[Install]
WantedBy=multi-user.target
EOF
```



Activation :

```bash 
#📁 Préparation des logs
mkdir -p /mnt/mariage_data/BibiUnion/logs
#🚀 Activation complète
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn-mariage.socket
sudo systemctl enable --now gunicorn-mariage.service
sudo systemctl status gunicorn-mariage.service
```

# 12. Cloudflare Tunnel — Guide complet

## 12.1 Création du compte Cloudflare

1. Aller sur (https://dash.cloudflare.com) et créer un compte gratuit.
2. Ajouter votre domaine (`mondomaine.fr`) — suivre les instructions pour changer les serveurs DNS chez votre registrar vers ceux fournis par Cloudflare.
3. Attendre l'activation du domaine (DNS propagé, peut prendre jusqu'à 24h, souvent quelques minutes).

## 12.2 Installation de cloudflared sur le Raspberry Pi

```bash
# Raspberry Pi 2 B = architecture ARM (armhf généralement, vérifier avec `uname -m`)
uname -m
# Si armv7l :
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-armhf.deb
# Si aarch64 (64 bits) :
# curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb

sudo dpkg -i cloudflared.deb
cloudflared --version
```

## 12.3 Authentification et création du tunnel

```bash 
# Connexion au compte Cloudflare (ouvre un lien à copier dans un navigateur)
cloudflared tunnel login

# Création du tunnel nommé "mariage"
cloudflared tunnel create mariage

# Note l'UUID du tunnel affiché, ex : 1234abcd-5678-efgh-9012-ijklmnopqrst
# Un fichier de credentials est créé dans ~/.cloudflared/<UUID>.json
```

## 12.4 Configuration du tunnel
Créer le fichier `~/.cloudflared/config.yml` :

```yaml
tunnel: 1234abcd-5678-efgh-9012-ijklmnopqrst
credentials-file: /home/pi/.cloudflared/1234abcd-5678-efgh-9012-ijklmnopqrst.json

ingress:
  - hostname: photos-mariage.mondomaine.fr
    service: http://localhost:80
  - service: http_status:404
```

Remplacer l'UUID par celui généré à l'étape précédente.

## 12.5 Configuration DNS

```bash 
# Crée automatiquement l'enregistrement CNAME dans Cloudflare DNS
cloudflared tunnel route dns mariage photos-mariage.mondomaine.fr
```

Vérification sur le dashboard Cloudflare (DNS > Records) : un enregistrement `CNAME` vers `<UUID>.cfargotunnel.com` doit apparaître.

## 12.6 Service systemd pour cloudflared (démarrage auto au boot)

```bash 
sudo cloudflared service install
sudo systemctl enable --now cloudflared
sudo systemctl status cloudflared
```

Le fichier `/etc/cloudflared/config.yml` est utilisé par le service. Copier la configuration :

```bash 
sudo mkdir -p /etc/cloudflared
sudo cp ~/.cloudflared/config.yml /etc/cloudflared/config.yml
sudo cp ~/.cloudflared/*.json /etc/cloudflared/
sudo systemctl restart cloudflared
```

## 12.7 Vérification
```bash 
sudo systemctl status cloudflared
sudo journalctl -u cloudflared -f
```

Tester depuis un téléphone (4G/5G, différent du réseau du Pi) : ouvrir `https://photos-mariage.mondomaine.fr/upload/`.

**Avantage clé** : l'URL reste identique même si le Raspberry change de réseau (Wi-Fi maison → partage de connexion), car le tunnel est une connexion sortante initiée par le Pi — aucune redirection de port ni IP fixe nécessaire.

## 12.8 Start_tunnel

```bash
#!/bin/bash

SETTINGS="/mnt/mariage_data/BibiUnion/mariage/settings.py"

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
sed -i "s|'[^']*\.trycloudflare\.com'|'$HOSTNAME'|g" "$SETTINGS"
sed -i "s|SITE_PUBLIC_URL = '.*'|SITE_PUBLIC_URL = '$URL'|g" "$SETTINGS"

echo "settings.py mis à jour avec : $HOSTNAME"

# Redémarre gunicorn
sudo systemctl restart gunicorn-mariage
echo "Gunicorn redémarré ✅"

# Régénère le QR Code avec la nouvelle URL
cd /mnt/mariage_data/BibiUnion
source venv/bin/activate
python manage.py generate_qrcode
echo "QR Code régénéré ✅"

echo ""
echo "========================================"
echo "  Site accessible sur : $URL/upload/"
echo "========================================"

# Garde le tunnel en premier plan
wait $TUNNEL_PID
```

```bash
cat > start_tunnel.sh << 'EOF'
#!/bin/bash

SETTINGS="/mnt/mariage_data/BibiUnion/mariage/settings.py"

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
sed -i "s|'[^']*\.trycloudflare\.com'|'$HOSTNAME'|g" "$SETTINGS"
sed -i "s|https://[^']*\.trycloudflare\.com|$URL|g" "$SETTINGS"
sed -i "s|SITE_PUBLIC_URL = '.*'|SITE_PUBLIC_URL = '$URL'|g" "$SETTINGS"


echo "settings.py mis à jour avec : $HOSTNAME"

# Redémarre gunicorn
sudo systemctl restart gunicorn-mariage
echo "Gunicorn redémarré ✅"

# Régénère le QR Code avec la nouvelle URL
cd /mnt/mariage_data/BibiUnion
source venv/bin/activate
python manage.py generate_qrcode
echo "QR Code régénéré ✅"

echo ""
echo "========================================"
echo "  Site accessible sur : $URL/upload/"
echo "========================================"

# Garde le tunnel en premier plan
wait $TUNNEL_PID
EOF

chmod +x ./start_tunnel.sh
```

```bash
cat > ./start_tunnel.sh << 'EOF'
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
EOF

chmod +x ./start_tunnel.sh
```


Utilisation

```bash
chmod +x ./start_tunnel.sh
sudo ./start_tunnel.sh
```


# 13. Installation Raspberry Pi

## `install.sh`

```bash 
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
```

```bash
chmod +x install.sh
```

> Remarque : créez les sous-dossiers `deploy/` avec les fichiers `gunicorn-mariage.socket`, `gunicorn-mariage.service, nginx-mariage.conf` listés aux sections 10 et 11 avant d'exécuter `install.sh`.

```bash 
mkdir -p deploy
# copier le contenu des sections 10 et 11 dans :
# deploy/nginx-mariage.conf
# deploy/gunicorn-mariage.socket
# deploy/gunicorn-mariage.service
```

# Déploiement complet — séquence de commandes

```bash 
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
```

```bash
cat > run_reset.sh << 'EOF'
#!/bin/bash

# 1. Cloner / copier le projet sur le Pi
cd /mnt/mariage_data/
[ -d BibiUnion ] && rm -rf BibiUnion
git clone https://github.com/THEMEZE/BibiUnion.git   # ou scp depuis votre PC
cd BibiUnion

#cd /mnt/mariage_data && rm -rf BibiUnion && git clone https://github.com/THEMEZE/BibiUnion.git && cd BibiUnion

# 2. Lancer l'installation
chmod +x install.sh
./install.sh

# 3. Démarrer le tunnel (à chaque redémarrage du Pi)
chmod +x start_tunnel.sh
sudo ./start_tunnel.sh

EOF
```

```bash
cat > run.sh << 'EOF'
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

EOF
```

> `start_tunnel.sh` fait automatiquement : tunnel Cloudflare + mise à jour 
> `settings.py` + redémarrage Gunicorn + régénération du QR Code.

Démarrage automatique au boot (optionnel)

```bash
sudo crontab -e
# Ajouter :
@reboot sleep 15 && /mnt/mariage_data/BibiUnion/start_tunnel.sh >> /mnt/mariage_data/BibiUnion/logs/tunnel.log 2>&1
```

### Si dommain fixe

```bash 
# 3. Configurer Cloudflare Tunnel (section 12)
cloudflared tunnel login
cloudflared tunnel create mariage
nano ~/.cloudflared/config.yml
cloudflared tunnel route dns mariage bibiunion.fr
sudo cloudflared service install
sudo systemctl enable --now cloudflared

# 4. Mettre à jour settings.py avec le vrai domaine, puis :
sudo systemctl restart gunicorn-mariage
sudo systemctl restart nginx
sudo systemctl restart cloudflared

# 5. Régénérer le QR Code avec l'URL finale
source venv/bin/activate
python manage.py generate_qrcode
```

# Tests de validation

```bash 
# 1. Vérifier que Django démarre sans erreur
source venv/bin/activate
python manage.py check

# 2. Vérifier les migrations
python manage.py showmigrations gallery

# 3. Test du serveur de développement (avant Gunicorn)
python manage.py runserver 0.0.0.0:8000
# -> ouvrir http://<IP_du_Pi>:8000/upload/

# 4. Vérifier le statut des services en production
sudo systemctl status gunicorn-mariage.socket
sudo systemctl status gunicorn-mariage.service
sudo systemctl status nginx
sudo systemctl status cloudflared

# 5. Vérifier les logs en cas d'erreur
sudo journalctl -u gunicorn-mariage -n 50 --no-pager
sudo tail -f /var/log/nginx/mariage_error.log
sudo journalctl -u cloudflared -n 50 --no-pager

# 6. Test fonctionnel via curl (en local sur le Pi)
curl -I http://localhost/upload/
curl -I http://localhost/gallery/

# 7. Test fonctionnel via le tunnel (depuis un autre réseau, ex: 4G)
curl -I https://photos-mariage.mondomaine.fr/upload/

# 8. Test d'upload via curl (simulation)
curl -X POST https://photos-mariage.mondomaine.fr/upload/ajax/ \
  -F "image=@test.jpg" \
  -F "auteur=TestUser" \
  -F "table=1" \
  -H "X-CSRFToken: <token recuperé via cookie>"

# 9. Vérifier la génération des miniatures
ls -la media/photos/
ls -la media/thumbnails/

# 10. Test du QR Code
ls -la media/qrcodes/qrcode.png
```

# Procédures de sauvegarde des photos

## Sauvegarde manuelle ponctuelle

```bash
# Sauvegarde complète (media + base de données) vers un disque USB
mkdir -p /mnt/usb/backup_mariage
DATE=$(date +%Y%m%d_%H%M%S)

tar -czf /mnt/usb/backup_mariage/mariage_backup_$DATE.tar.gz \
    /mnt/usb/backup_mariage/media \
    /mnt/usb/backup_mariage/db.sqlite3

echo "Sauvegarde créée : /mnt/usb/backup_mariage/mariage_backup_$DATE.tar.gz"
```

## Script de sauvegarde automatique

Créer `/mnt/mariage_data/backup.sh` :

```bash 
#!/bin/bash
set -e

SOURCE_DIR="/mnt/mariage_data/BibiUnion"
BACKUP_DIR="/mnt/usb/backup_mariage"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

# Sauvegarde des médias et de la base
tar -czf "$BACKUP_DIR/mariage_backup_$DATE.tar.gz" \
    "$SOURCE_DIR/media" \
    "$SOURCE_DIR/db.sqlite3"

# Suppression des sauvegardes de plus de 30 jours
find "$BACKUP_DIR" -name "mariage_backup_*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Sauvegarde terminée : mariage_backup_$DATE.tar.gz"
```

## Automatisation via cron (sauvegarde quotidienne à 3h du matin)

```bash
crontab -e
```

Ajouter la ligne :

```cron
0 3 * * * /mnt/mariage_data/BibiUnion/backup.sh >> /mnt/mariage_data/BibiUnion/logs/backup.log 2>&1
```

## Restauration

```bash 
# Arrêter les services
sudo systemctl stop gunicorn-mariage

# Restaurer depuis une archive
cd /mnt/mariage_data/BibiUnion
tar -xzf /mnt/usb/backup_mariage/mariage_backup_YYYYMMDD_HHMMSS.tar.gz -C /

# Redémarrer
sudo systemctl start gunicorn-mariage
```

# ⚙️ Git Mise à jour

```
git add .
git commit -m "Mise à jour"
git push
```









