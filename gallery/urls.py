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
