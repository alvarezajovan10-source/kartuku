from django.urls import path

from . import api, api_photos, views

app_name = "cards"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("template/<slug:category>/", views.template_gallery, name="gallery"),
    path("preview/<slug:template_slug>/", views.preview, name="preview"),
    path("create/<slug:template_slug>/", views.editor, name="editor"),
    # Isi iframe preview di editor — kartu asli, tapi bisa diklik.
    path("create/<slug:template_slug>/frame/", views.editor_frame, name="editor_frame"),
    path(
        "api/templates/<slug:template_slug>/draft/",
        api_photos.ensure_draft,
        name="api_draft",
    ),
    path(
        "api/cards/<uuid:card_id>/content/",
        api_photos.save_content,
        name="api_content",
    ),
    path(
        "api/cards/<uuid:card_id>/photos/",
        api_photos.upload_photo,
        name="api_photo_upload",
    ),
    path(
        "api/cards/<uuid:card_id>/photos/<int:photo_id>/delete/",
        api_photos.delete_photo,
        name="api_photo_delete",
    ),
    path(
        "api/cards/<uuid:card_id>/photos/<int:photo_id>/caption/",
        api_photos.set_caption,
        name="api_photo_caption",
    ),
    path("pay/<uuid:card_id>/", views.pay, name="pay"),
    path("pay/<uuid:card_id>/gratis/", views.mark_paid, name="mark_paid"),
    path("sukses/<uuid:card_id>/", views.success, name="success"),
    path("g/<uuid:card_id>/", views.public_card, name="public"),
    path("api/cards/<uuid:card_id>/pay/", api.create_charge, name="api_pay"),
    path("api/cards/<uuid:card_id>/status/", api.card_status, name="api_status"),
]
