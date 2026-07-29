from django.urls import path

from . import api, api_photos, views

app_name = "cards"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("kartu-saya/", views.my_cards, name="my_cards"),
    # Halaman informasi — tiap bagian landing punya alamat sendiri.
    path("template/", views.page_templates, name="page_templates"),
    path("cara-kerja/", views.page_how, name="page_how"),
    path("harga/", views.page_pricing, name="page_pricing"),
    path("testimoni/", views.page_testimonials, name="page_testimonials"),
    path("faq/", views.page_faq, name="page_faq"),
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
    path("pay/<uuid:card_id>/kode/", views.redeem_code, name="redeem_code"),
    path("sukses/<uuid:card_id>/", views.success, name="success"),
    path("g/<str:ref>/", views.public_card, name="public"),
    path("sukses/<uuid:card_id>/link/", views.set_slug, name="set_slug"),
    path("qr/<uuid:card_id>.png", views.qr_png, name="qr"),
    path("api/cards/<uuid:card_id>/pay/", api.create_charge, name="api_pay"),
    path("api/cards/<uuid:card_id>/status/", api.card_status, name="api_status"),
]
