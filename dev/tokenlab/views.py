from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from tokenlab.models import Note
from tokenlab.serializers import NoteSerializer

from keysmith.drf.permissions import RequireKeysmithToken


class TokenStatusAPIView(APIView):
    permission_classes = [RequireKeysmithToken]

    def get(self, request):
        token = getattr(request, "auth", None)
        user = request.user if request.user.is_authenticated else None
        return Response(
            {
                "ok": True,
                "message": "Token authentication successful",
                "token_id": getattr(token, "prefix", None),
                "hint": getattr(token, "hint", None),
                "user_id": getattr(user, "pk", None),
                "user": str(user) if user else None,
            }
        )


class NotesCollectionAPIView(APIView):
    permission_classes = [RequireKeysmithToken]

    def get(self, request):
        notes = Note.objects.all()
        serializer = NoteSerializer(notes, many=True)
        return Response({"items": serializer.data})

    def post(self, request):
        serializer = NoteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NoteDetailAPIView(APIView):
    permission_classes = [RequireKeysmithToken]

    def get_object(self, pk: int) -> Note | None:
        try:
            return Note.objects.get(pk=pk)
        except Note.DoesNotExist:
            return None

    def get(self, request, pk: int):
        note = self.get_object(pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(NoteSerializer(note).data)

    def put(self, request, pk: int):
        note = self.get_object(pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = NoteSerializer(note, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk: int):
        note = self.get_object(pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = NoteSerializer(note, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk: int):
        note = self.get_object(pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
