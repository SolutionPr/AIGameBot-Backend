from django.urls import path, re_path

from .views import (
    GameConfigDetailView,
    GameConfigListView,
    GenerateGameConfigView,
    TemplatesListView,
)


urlpatterns = [
    path("generate/", GenerateGameConfigView.as_view(), name="generate-game-config"),
    path("configs/", GameConfigListView.as_view(), name="game-config-list"),
    path("configs/<int:pk>/", GameConfigDetailView.as_view(), name="game-config-detail"),
    re_path(
        r"^configs/(?P<pk><[^/]+>)/?$",
        GameConfigDetailView.as_view(),
        name="game-config-detail-placeholder",
    ),
    path("templates/", TemplatesListView.as_view(), name="game-templates"),
]
