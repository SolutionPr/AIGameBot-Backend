from django.contrib import admin
from .models import PasswordResetOTP, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "games_created", "games_played", "is_active", "updated_at")


@admin.register(PasswordResetOTP)
class PasswordResetOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "expires_at", "is_verified", "is_used", "created_at", "updated_at")
    search_fields = ("user__username", "user__email")
    list_filter = ("is_verified", "is_used", "created_at")
