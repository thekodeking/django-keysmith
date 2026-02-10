from django.urls import path

from tokenlab import views

urlpatterns = [
    path("status/", views.TokenStatusAPIView.as_view(), name="token_status"),
    path("notes/", views.NotesCollectionAPIView.as_view(), name="notes_collection"),
    path("notes/<int:pk>/", views.NoteDetailAPIView.as_view(), name="note_detail"),
]
