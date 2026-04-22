from django.contrib.auth import get_user_model, login, logout, update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.db import transaction
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import secrets
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PasswordResetOTP, Profile
from .serializers import (
    AccountUpdateSerializer,
    ForgotPasswordSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ResetPasswordSerializer,
    ProfileSerializer,
    ProfileAccountUpdateSerializer,
    ProfileUpdateSerializer,
    ProfileResponseUserSerializer,
    VerifyOTPSerializer,
    RegisterSerializer,
    UserSerializer,
)


User = get_user_model()


def get_or_create_profile(user):
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            user = serializer.save()
            get_or_create_profile(user)
            token, _ = Token.objects.get_or_create(user=user)

        return Response(
            {
                "message": "Registration successful.",
                "user": UserSerializer(user).data,
                "token": token.key,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        identifier = (
            serializer.validated_data.get("email")
            or serializer.validated_data.get("username")
            or serializer.validated_data.get("login")
        )

        if "@" in identifier:
            user = User.objects.filter(email__iexact=identifier).first()
        else:
            user = User.objects.filter(username__iexact=identifier).first()

        if not user or not user.check_password(serializer.validated_data["password"]):
            return Response(
                {"message": "Invalid login credentials."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        return Response(
            {
                "message": "Login successful.",
                "user": UserSerializer(user).data,
                "token": token.key,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    def post(self, request):
        if request.auth:
            request.auth.delete()
        logout(request)
        return Response({"message": "Logout successful."}, status=status.HTTP_200_OK)


class ProfileView(RetrieveUpdateAPIView):
    serializer_class = ProfileUpdateSerializer

    def get_object(self):
        profile = get_or_create_profile(self.request.user)
        return profile

    def retrieve(self, request, *args, **kwargs):
        profile = self.get_object()
        return Response(
            {
                "user": ProfileResponseUserSerializer(request.user).data,
                "profile": ProfileSerializer(profile).data,
            }
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        profile = self.get_object()
        payload = request.data.copy()
        payload.pop("email", None)

        user_serializer = ProfileAccountUpdateSerializer(request.user, data=payload, partial=partial)
        profile_serializer = self.get_serializer(profile, data=payload, partial=partial)
        user_serializer.is_valid(raise_exception=True)
        profile_serializer.is_valid(raise_exception=True)
        user_serializer.save()
        profile_serializer.save()
        return Response(
            {
                "message": "Profile updated successfully.",
                "user": ProfileResponseUserSerializer(request.user).data,
                "profile": ProfileSerializer(profile).data,
            }
        )

    def patch(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)


class ChangePasswordView(APIView):
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"message": "Old password is incorrect."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        update_session_auth_hash(request, user)
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)

        return Response(
            {
                "message": "Password updated successfully.",
                "token": token.key,
            },
            status=status.HTTP_200_OK,
        )


def _generate_reset_otp():
    return f"{secrets.randbelow(1000000):06d}"


def _get_user_by_email(email):
    return User.objects.filter(email__iexact=email).first()


def _get_active_reset_otp(user):
    return PasswordResetOTP.objects.filter(user=user, is_used=False).first()


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = _get_user_by_email(email)

        if user and user.email:
            otp = _generate_reset_otp()
            PasswordResetOTP.objects.update_or_create(
                user=user,
                defaults={
                    "otp_hash": make_password(otp),
                    "expires_at": timezone.now() + timedelta(minutes=10),
                    "is_verified": False,
                    "verified_at": None,
                    "is_used": False,
                },
            )
            subject = "Password reset OTP"
            message = (
                f"Hello {user.username},\n\n"
                "Use this OTP to reset your password:\n\n"
                f"OTP: {otp}\n\n"
                "This OTP expires in 10 minutes.\n"
                "If you did not request this, you can ignore this email."
            )
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=False)

            response_data = {"message": "OTP sent successfully to the registered email address."}
            if settings.DEBUG:
                response_data["debug_otp"] = otp
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(
            {"message": "If the email is registered, an OTP has been sent successfully."},
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = _get_user_by_email(serializer.validated_data["email"])
        if not user:
            return Response(
                {"message": "Invalid OTP details."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_otp = _get_active_reset_otp(user)
        if not reset_otp or reset_otp.has_expired():
            return Response(
                {"message": "Invalid or expired OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not check_password(serializer.validated_data["otp"], reset_otp.otp_hash):
            return Response(
                {"message": "Invalid or expired OTP."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_otp.is_verified = True
        reset_otp.verified_at = timezone.now()
        reset_otp.save(update_fields=["is_verified", "verified_at", "updated_at"])

        return Response(
            {"message": "OTP verified successfully."},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = _get_user_by_email(serializer.validated_data["email"])
        if not user:
            return Response(
                {"message": "Invalid reset details."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        reset_otp = _get_active_reset_otp(user)
        if (
            not reset_otp
            or reset_otp.has_expired()
            or not reset_otp.is_verified
            or reset_otp.verified_at is None
        ):
            return Response(
                {"message": "OTP must be verified before resetting the password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        reset_otp.is_used = True
        reset_otp.is_verified = False
        reset_otp.verified_at = None
        reset_otp.save(update_fields=["is_used", "is_verified", "verified_at", "updated_at"])
        Token.objects.filter(user=user).delete()

        return Response(
            {"message": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class PasswordResetRequestView(ForgotPasswordView):
    pass


class PasswordResetConfirmView(VerifyOTPView):
    pass


class PasswordResetAPIView(ResetPasswordView):
    pass
