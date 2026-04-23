from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GameConfig
from .serializers import (
    GameConfigListSerializer,
    GameConfigSerializer,
    GenerateGameConfigRequestSerializer,
)
from .services import GameConfigGenerationError, generate_game_config_with_groq


class GenerateGameConfigView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    """
    POST /api/generate/
   
    Accepts a natural language prompt and returns a structured game config JSON.
    Optionally saves the config to the database.
 
    Request body:
        {
            "prompt": "Create a hard space shooter with boss waves",
            "save": true   // optional, default: true
        }
 
    Response:
        {
            "success": true,
            "saved": true,
            "config": { ...game config... },
            "id": 1   // only if saved
        }
    """
 
    def post(self, request):
        # Validate request
        request_serializer = GenerateGameConfigRequestSerializer(data=request.data)
        if not request_serializer.is_valid():
            return Response(
                {"success": False, "errors": request_serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )
 
        prompt = request_serializer.validated_data['prompt']
        should_save = request_serializer.validated_data['save']
 
        # Generate config via AI
        try:
            config = generate_game_config_with_groq(prompt)
        except GameConfigGenerationError as e:
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )
 
        response_data = {
            "success": True,
            "saved": False,
            "config": config,
            "authenticated_user": getattr(request.user, "username", None),
        }
 
        # Save to DB if requested
        if should_save:
            created_by = request.user if getattr(request.user, "is_authenticated", False) else None
            game_config = GameConfig.objects.create(
                created_by=created_by,
                prompt=prompt,
                template=config.get('template', ''),
                title=config.get('title', ''),
                difficulty=config.get('difficulty', {}),
                theme=config.get('theme', {}),
                rules=config.get('rules', {}),
                assets=config.get('assets', {}),
                raw_config=config,
            )
            response_data["saved"] = True
            response_data["id"] = game_config.id
 
        return Response(response_data, status=status.HTTP_201_CREATED)
 
 
class GameConfigListView(APIView):
    """
    GET /api/configs/
   
    Returns a list of all saved game configs (lightweight).
 
    Optional query params:
        ?template=shooter     → filter by template (any string, AI-generated)
        ?difficulty=hard      → filter by difficulty level (any string, AI-generated)
        ?search=space         → search in title or prompt
 
    Response:
        {
            "count": 5,
            "results": [ ...configs... ]
        }
    """
 
    def get(self, request):
        queryset = GameConfig.objects.all()
 
        # Dynamic filters — no hardcoded choices
        template = request.query_params.get('template')
        difficulty = request.query_params.get('difficulty')
        search = request.query_params.get('search')
 
        if template:
            queryset = queryset.filter(template__icontains=template)
 
        if difficulty:
            # Filter inside JSON field
            queryset = queryset.filter(difficulty__level__icontains=difficulty)
 
        if search:
            from django.db.models import Q
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(prompt__icontains=search)
            )
 
        serializer = GameConfigListSerializer(queryset, many=True)
        return Response({
            "count": queryset.count(),
            "results": serializer.data
        })
 
 
class GameConfigDetailView(APIView):
    """
    GET  /api/configs/<id>/   → Retrieve full config
    DELETE /api/configs/<id>/ → Delete config
    """
 
    def get_object(self, pk):
        try:
            pk = int(pk)
        except (TypeError, ValueError):
            return None

        try:
            return GameConfig.objects.get(pk=pk)
        except GameConfig.DoesNotExist:
            return None

    def invalid_id_response(self, pk):
        return Response(
            {
                "error": (
                    f"Invalid config id '{pk}'. Use a real numeric id like "
                    f"/api/configs/1/ instead of the placeholder /api/configs/<id>/."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
 
    def get(self, request, pk):
        """
        GET /api/configs/<id>/

        Returns the full game config including raw_config JSON.
        """
        if not str(pk).isdigit():
            return self.invalid_id_response(pk)

        config = self.get_object(pk)
        if config is None:
            return Response(
                {"error": f"GameConfig with id={pk} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = GameConfigSerializer(config)
        return Response(serializer.data)
 
    def delete(self, request, pk):
        """
        DELETE /api/configs/<id>/

        Deletes a saved game config.
        """
        if not str(pk).isdigit():
            return self.invalid_id_response(pk)

        config = self.get_object(pk)
        if config is None:
            return Response(
                {"error": f"GameConfig with id={pk} not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        config.delete()
        return Response(
            {"success": True, "message": f"GameConfig {pk} deleted."},
            status=status.HTTP_200_OK
        )
 
 
class TemplatesListView(APIView):
    """
    GET /api/templates/
 
    Returns all unique templates and difficulty levels that have been
    AI-generated and saved so far. Fully dynamic — no hardcoded values.
 
    Response:
        {
            "templates": ["shooter", "runner", "survival-horror", ...],
            "difficulty_levels": ["easy", "nightmare", "insane", ...],
            "total_configs": 12
        }
    """
 
    def get(self, request):
        configs = GameConfig.objects.all()
 
        # Collect unique templates from DB (all AI-generated)
        templates = sorted(set(
            c.template.strip().lower()
            for c in configs
            if c.template
        ))
 
        # Collect unique difficulty levels from JSON field
        difficulty_levels = sorted(set(
            c.difficulty.get('level', '').strip().lower()
            for c in configs
            if isinstance(c.difficulty, dict) and c.difficulty.get('level')
        ))
 
        return Response({
            "templates": templates,
            "difficulty_levels": difficulty_levels,
            "total_configs": configs.count(),
            "note": "All values are AI-generated dynamically from user prompts."
        })
