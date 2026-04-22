from django.urls import path

from .views import (
    ForgotPasswordView,
    LoginView,
    LogoutView,
    ProfileView,
    ResetPasswordView,
    RegisterView,
    VerifyOTPView,
)


urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("forget-password/", ForgotPasswordView.as_view(), name="forget-password"),
    path("confirm-password/", VerifyOTPView.as_view(), name="confirm-password"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
]
