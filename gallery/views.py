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
