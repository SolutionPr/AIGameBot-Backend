from django.urls import path

from .views import ForgotPasswordView, ResetPasswordView, VerifyOTPView


urlpatterns = [
    path("forgot-password/", ForgotPasswordView.as_view(), name="forgot-password"),
    path("password-reset/request/", ForgotPasswordView.as_view(), name="password-reset-request"),
    path("confirm-password/", VerifyOTPView.as_view(), name="confirm-password"),
    path("password-reset/confirm/", VerifyOTPView.as_view(), name="password-reset-confirm"),
    path("reset-password/", ResetPasswordView.as_view(), name="reset-password"),
]
