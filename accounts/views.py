from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.authtoken.models import Token
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Profile
from .serializers import (
    AccountUpdateSerializer,
    ChangePasswordSerializer,
    LoginSerializer,
    ProfileSerializer,
    ProfileUpdateSerializer,
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
        login_value = serializer.validated_data["login"]

        user_obj = User.objects.filter(username__iexact=login_value).first()
        if user_obj is None:
            user_obj = User.objects.filter(email__iexact=login_value).first()

        user = authenticate(
            request,
            username=user_obj.username if user_obj else login_value,
            password=serializer.validated_data["password"],
        )
        if not user:
            return Response(
                {"message": "Invalid username or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request, user)
        token, _ = Token.objects.get_or_create(user=user)
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
                "user": UserSerializer(request.user).data,
                "profile": ProfileSerializer(profile).data,
            }
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        profile = self.get_object()
        user_serializer = AccountUpdateSerializer(request.user, data=request.data, partial=partial)
        profile_serializer = self.get_serializer(profile, data=request.data, partial=partial)
        user_serializer.is_valid(raise_exception=True)
        profile_serializer.is_valid(raise_exception=True)
        user_serializer.save()
        profile_serializer.save()
        return Response(
            {
                "message": "Profile updated successfully.",
                "user": UserSerializer(request.user).data,
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
