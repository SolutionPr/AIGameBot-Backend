from rest_framework import serializers
from .models import GameConfig


class DifficultySerializer(serializers.Serializer):
    """Validates and represents dynamic difficulty config."""
    level = serializers.CharField()
    enemySpeed = serializers.IntegerField(min_value=1, max_value=10)
    playerLives = serializers.IntegerField(min_value=1, max_value=10)
    spawnRate = serializers.IntegerField(min_value=1, max_value=10)
    extraMechanics = serializers.ListField(child=serializers.CharField(), default=list)


class ThemeSerializer(serializers.Serializer):
    """Validates and represents dynamic theme config."""
    style = serializers.CharField()
    primaryColor = serializers.CharField()
    accentColor = serializers.CharField()
    environment = serializers.CharField()
    atmosphere = serializers.CharField(required=False, default="")


class RulesSerializer(serializers.Serializer):
    """Validates and represents dynamic rules config."""
    objective = serializers.CharField()
    timeLimit = serializers.IntegerField(allow_null=True, required=False)
    scoring = serializers.CharField()
    specialMechanics = serializers.ListField(child=serializers.CharField(), default=list)
    playerAbilities = serializers.ListField(child=serializers.CharField(), default=list)


class AssetsSerializer(serializers.Serializer):
    """Validates and represents dynamic assets config."""
    playerSprite = serializers.CharField()
    background = serializers.CharField()
    enemies = serializers.ListField(child=serializers.CharField(), default=list)
    powerUps = serializers.ListField(child=serializers.CharField(), default=list)
    soundtrack = serializers.CharField(required=False, default="")


class GameConfigSerializer(serializers.ModelSerializer):
    """Full serializer for a saved GameConfig — all fields dynamic."""

    created_by = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = GameConfig
        fields = [
            'id',
            'created_by',
            'prompt',
            'template',
            'title',
            'difficulty',
            'theme',
            'rules',
            'assets',
            'raw_config',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class GameConfigListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing configs."""

    created_by = serializers.StringRelatedField(read_only=True)
    difficulty_level = serializers.SerializerMethodField()
    theme_style = serializers.SerializerMethodField()
    special_mechanics_count = serializers.SerializerMethodField()

    class Meta:
        model = GameConfig
        fields = [
            'id',
            'created_by',
            'title',
            'template',
            'difficulty_level',
            'theme_style',
            'special_mechanics_count',
            'prompt',
            'created_at',
        ]

    def get_difficulty_level(self, obj):
        return obj.difficulty.get('level', 'N/A') if isinstance(obj.difficulty, dict) else 'N/A'

    def get_theme_style(self, obj):
        return obj.theme.get('style', 'N/A') if isinstance(obj.theme, dict) else 'N/A'

    def get_special_mechanics_count(self, obj):
        if isinstance(obj.rules, dict):
            return len(obj.rules.get('specialMechanics', []))
        return 0


class GenerateGameConfigRequestSerializer(serializers.Serializer):
    """Validates the incoming generation request."""

    prompt = serializers.CharField(
        min_length=5,
        max_length=1000,
        help_text="Describe the game you want to generate — be as creative as you like!"
    )
    save = serializers.BooleanField(
        default=True,
        help_text="Whether to save the generated config to the database"
    )
