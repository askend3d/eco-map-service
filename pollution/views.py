from rest_framework import viewsets, permissions
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


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
