from django.contrib import admin

from tokenlab.models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "created_at", "updated_at")
    search_fields = ("title", "content")
    readonly_fields = ("created_at", "updated_at")
