import json

from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from tokenlab.models import Note

from keysmith.django.decorator import keysmith_required


def _json_body(request: HttpRequest) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid JSON payload") from exc


@keysmith_required
@csrf_exempt
def token_status(request: HttpRequest) -> JsonResponse:
    token = getattr(request, "keysmith_token", None)
    user = getattr(request, "keysmith_user", None)
    return JsonResponse(
        {
            "ok": True,
            "message": "Token authentication successful",
            "token_id": getattr(token, "prefix", None),
            "hint": getattr(token, "hint", None),
            "user_id": getattr(user, "pk", None),
            "user": str(user) if user else None,
        }
    )


@keysmith_required
@csrf_exempt
def notes_collection(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        notes = list(Note.objects.values("id", "title", "content", "created_at", "updated_at"))
        return JsonResponse({"items": notes})

    if request.method == "POST":
        try:
            payload = _json_body(request)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        title = str(payload.get("title", "")).strip()
        content = str(payload.get("content", "")).strip()
        if not title:
            return JsonResponse({"error": "'title' is required"}, status=400)

        note = Note.objects.create(title=title, content=content)
        return JsonResponse(
            {
                "id": note.pk,
                "title": note.title,
                "content": note.content,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
            },
            status=201,
        )

    return JsonResponse({"error": "Method not allowed"}, status=405)


@keysmith_required
@csrf_exempt
def note_detail(request: HttpRequest, pk: int) -> JsonResponse:
    try:
        note = Note.objects.get(pk=pk)
    except Note.DoesNotExist:
        return JsonResponse({"error": "Not found"}, status=404)

    if request.method == "GET":
        return JsonResponse(
            {
                "id": note.pk,
                "title": note.title,
                "content": note.content,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
            }
        )

    if request.method in {"PUT", "PATCH"}:
        try:
            payload = _json_body(request)
        except ValueError as exc:
            return JsonResponse({"error": str(exc)}, status=400)

        title = payload.get("title")
        content = payload.get("content")

        if title is not None:
            title = str(title).strip()
            if not title:
                return JsonResponse({"error": "'title' cannot be empty"}, status=400)
            note.title = title

        if content is not None:
            note.content = str(content)

        note.save()
        return JsonResponse(
            {
                "id": note.pk,
                "title": note.title,
                "content": note.content,
                "created_at": note.created_at,
                "updated_at": note.updated_at,
            }
        )

    if request.method == "DELETE":
        note.delete()
        return JsonResponse({}, status=204)

    return JsonResponse({"error": "Method not allowed"}, status=405)
