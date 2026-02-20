from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from keysmith.drf.permissions import HasKeysmithScopes, RequireKeysmithToken
from tests.models import TestResource


class TokenStatusAPIView(APIView):
    """Return authentication status and token details."""

    permission_classes = [RequireKeysmithToken]

    def get(self, request):
        token = getattr(request, "auth", None)
        user = request.user if request.user.is_authenticated else None
        return Response(
            {
                "authenticated": True,
                "token_prefix": getattr(token, "prefix", None),
                "token_hint": getattr(token, "hint", None),
                "user_id": getattr(user, "pk", None),
                "user": str(user) if user else None,
            }
        )


class ResourceCollectionAPIView(APIView):
    """Handle collection operations on TestResource."""

    permission_classes = [RequireKeysmithToken]

    def get(self, request):
        resources = TestResource.objects.all()
        data = [
            {
                "id": r.pk,
                "name": r.name,
                "description": r.description,
                "created_at": r.created_at,
                "updated_at": r.updated_at,
            }
            for r in resources
        ]
        return Response({"items": data})

    def post(self, request):
        name = request.data.get("name", "").strip()
        description = request.data.get("description", "").strip()

        if not name:
            return Response({"error": "'name' is required"}, status=status.HTTP_400_BAD_REQUEST)

        resource = TestResource.objects.create(name=name, description=description)
        return Response(
            {
                "id": resource.pk,
                "name": resource.name,
                "description": resource.description,
                "created_at": resource.created_at,
                "updated_at": resource.updated_at,
            },
            status=status.HTTP_201_CREATED,
        )


class ResourceDetailAPIView(APIView):
    """Handle individual resource operations."""

    permission_classes = [RequireKeysmithToken]

    def get_object(self, pk: int) -> TestResource | None:
        try:
            return TestResource.objects.get(pk=pk)
        except TestResource.DoesNotExist:
            return None

    def get(self, request, pk: int):
        resource = self.get_object(pk)
        if resource is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(
            {
                "id": resource.pk,
                "name": resource.name,
                "description": resource.description,
                "created_at": resource.created_at,
                "updated_at": resource.updated_at,
            }
        )

    def put(self, request, pk: int):
        resource = self.get_object(pk)
        if resource is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get("name", "").strip()
        if not name:
            return Response({"error": "'name' is required"}, status=status.HTTP_400_BAD_REQUEST)

        resource.name = name
        resource.description = request.data.get("description", "").strip()
        resource.save()

        return Response(
            {
                "id": resource.pk,
                "name": resource.name,
                "description": resource.description,
                "created_at": resource.created_at,
                "updated_at": resource.updated_at,
            }
        )

    def patch(self, request, pk: int):
        resource = self.get_object(pk)
        if resource is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        name = request.data.get("name")
        if name is not None:
            name = str(name).strip()
            if not name:
                return Response(
                    {"error": "'name' cannot be empty"}, status=status.HTTP_400_BAD_REQUEST
                )
            resource.name = name

        if "description" in request.data:
            resource.description = str(request.data.get("description"))

        resource.save()
        return Response(
            {
                "id": resource.pk,
                "name": resource.name,
                "description": resource.description,
                "created_at": resource.created_at,
                "updated_at": resource.updated_at,
            }
        )

    def delete(self, request, pk: int):
        resource = self.get_object(pk)
        if resource is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        resource.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ScopedResourceAPIView(APIView):
    """View requiring specific scope."""

    permission_classes = [RequireKeysmithToken, HasKeysmithScopes]
    required_scopes = {"write"}

    def get(self, request):
        return Response({"scoped": True})
