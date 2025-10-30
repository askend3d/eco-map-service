from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import PollutionPoint, Comment
from .serializers import PollutionPointSerializer, CommentSerializer


class PollutionPointViewSet(viewsets.ModelViewSet):
    queryset = PollutionPoint.objects.all().order_by('-created_at')
    serializer_class = PollutionPointSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.role == 'ngo' or user.is_staff:
            return PollutionPoint.objects.all()
        return PollutionPoint.objects.filter(status__in=['new', 'in_progress'])

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


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
