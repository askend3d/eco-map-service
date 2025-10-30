from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import PollutionPoint, Comment
from .serializers import PollutionPointSerializer, CommentSerializer, PollutionStatusSerializer


class PollutionPointViewSet(viewsets.ModelViewSet):
    queryset = PollutionPoint.objects.all().order_by('-created_at')
    serializer_class = PollutionPointSerializer

    def get_permissions(self):
        """
        Для list и retrieve — доступ открыт всем,
        для остальных действий — только авторизованным.
        """
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

    @action(detail=True, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticated])
    def comments(self, request, pk=None):
        """
        GET: список комментариев к точке
        POST: создать комментарий для точки
        """
        try:
            point = PollutionPoint.objects.get(pk=pk)
        except PollutionPoint.DoesNotExist:
            return Response({"detail": "PollutionPoint not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            comments = point.comments.all().order_by('-created_at')
            serializer = CommentSerializer(comments, many=True)
            return Response(serializer.data)

        elif request.method == 'POST':
            serializer = CommentSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save(author=request.user, point=point)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=['patch'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='set-status',
        serializer_class=PollutionStatusSerializer
    )
    def set_status(self, request, pk=None):
        """Изменить статус точки (в работе / очищено)."""
        point = self.get_object()
        user = request.user

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data['status']

        if not user.organization:
            return Response(
                {"detail": "Вы должны состоять в организации, чтобы менять статус."},
                status=status.HTTP_403_FORBIDDEN
            )

        point.status = new_status
        point.handled_by = user.organization
        point.save()

        return Response(PollutionPointSerializer(point).data)

class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        point_id = self.kwargs.get('point_pk')
        return Comment.objects.filter(point_id=point_id).order_by('-created_at')

    def perform_create(self, serializer):
        point_id = self.kwargs.get('point_pk')
        serializer.save(author=self.request.user, point_id=point_id)
