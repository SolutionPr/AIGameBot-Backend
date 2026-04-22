from django.contrib import admin
from .models import GameConfig


@admin.register(GameConfig)
class GameConfigAdmin(admin.ModelAdmin):
    list_display = ("title", "template", "created_at", "updated_at")
    search_fields = ("title", "template", "prompt")
    list_filter = ("template", "created_at")
