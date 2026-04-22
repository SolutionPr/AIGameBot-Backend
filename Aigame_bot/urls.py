from django.contrib import admin
from django.urls import include, path
from accounts.views import (
    ForgotPasswordView,
    LoginView,
    LogoutView,
    ProfileView,
    ResetPasswordView,
    RegisterView,
    VerifyOTPView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.auth_urls")),
    path("api/accounts/", include("accounts.urls")),
    path("api/", include("Game.urls")),
    path("register", RegisterView.as_view(), name="register-alias"),
    path("login", LoginView.as_view(), name="login-alias"),
    path("logout", LogoutView.as_view(), name="logout-alias"),
    path("profile", ProfileView.as_view(), name="profile-alias"),
    path("forget-password", ForgotPasswordView.as_view(), name="forget-password-alias"),
    path("forget/password", ForgotPasswordView.as_view(), name="forget-password-legacy-alias"),
    path("confirm-password", VerifyOTPView.as_view(), name="confirm-password-alias"),
    path("password-reset/request", ForgotPasswordView.as_view(), name="password-reset-request-legacy-alias"),
    path("password-reset/confirm", VerifyOTPView.as_view(), name="password-reset-confirm-legacy-alias"),
    path("reset-password", ResetPasswordView.as_view(), name="reset-password-alias"),
]
