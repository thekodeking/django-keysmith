from django.urls import path
from tokenlab import plain_views

urlpatterns = [
    path("status/", plain_views.token_status, name="plain_token_status"),
    path("notes/", plain_views.notes_collection, name="plain_notes_collection"),
    path("notes/<int:pk>/", plain_views.note_detail, name="plain_note_detail"),
]
