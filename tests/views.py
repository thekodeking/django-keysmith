"""Plain Django views for testing Keysmith authentication."""

import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from keysmith.django.decorator import keysmith_required
from keysmith.django.permissions import keysmith_scopes

from tests.models import TestResource


def _json_body(request: HttpRequest) -> dict:
    """Parse JSON request body."""
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON payload") from exc


@keysmith_required
@csrf_exempt
def token_status_view(request: HttpRequest) -> JsonResponse:
    """Return authentication status and token details."""
    token = getattr(request, "keysmith_token", None)
    user = getattr(request, "keysmith_user", None)
    return JsonResponse(
        {
            "authenticated": True,
            "token_prefix": getattr(token, "prefix", None),
            "token_hint": getattr(token, "hint", None),
            "user_id": getattr(user, "pk", None),
            "user": str(user) if user else None,
        }
    )


@keysmith_required
@csrf_exempt
def resource_collection_view(request: HttpRequest) -> JsonResponse:
    """Handle collection operations on TestResource."""
    if request.method == "GET":
        resources = list(
            TestResource.objects.values("id", "name", "description", "created_at", "updated_at")
        )
        return JsonResponse({"items": resources})

    if request.method == "POST":
        try:
            payload = _json_body(request)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        name = str(payload.get("name", "")).strip()
        description = str(payload.get("description", "")).strip()

        if not name:
            return JsonResponse({"error": "'name' is required"}, status=400)

        resource = TestResource.objects.create(name=name, description=description)
        return JsonResponse(
            {
                "id": resource.pk,
                "name": resource.name,
                "description": resource.description,
                "created_at": resource.created_at,
                "updated_at": resource.updated_at,
            },
            status=201,
        )

    return JsonResponse({"error": "Method not allowed"}, status=405)


@keysmith_required
@csrf_exempt
def resource_detail_view(request: HttpRequest, pk: int) -> JsonResponse:
    """Handle individual resource operations."""
    try:
        resource = TestResource.objects.get(pk=pk)
    except TestResource.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    if request.method == "GET":
        return JsonResponse(
            {
                "id": resource.pk,
                "name": resource.name,
                "description": resource.description,
                "created_at": resource.created_at,
                "updated_at": resource.updated_at,
            }
        )

    if request.method in {"PUT", "PATCH"}:
        try:
            payload = _json_body(request)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        name = payload.get("name")
        description = payload.get("description")

        if name is not None:
            name = str(name).strip()
            if not name:
                return JsonResponse({"error": "'name' cannot be empty"}, status=400)
            resource.name = name

        if description is not None:
            resource.description = str(description)

        resource.save()
        return JsonResponse(
            {
                "id": resource.pk,
                "name": resource.name,
                "description": resource.description,
                "created_at": resource.created_at,
                "updated_at": resource.updated_at,
            }
        )

    if request.method == "DELETE":
        resource.delete()
        return JsonResponse({}, status=204)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@keysmith_required
@keysmith_scopes("write")
@csrf_exempt
def scoped_resource_view(request: HttpRequest) -> JsonResponse:
    """View requiring specific scope."""
    return JsonResponse({"scoped": True})
