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
