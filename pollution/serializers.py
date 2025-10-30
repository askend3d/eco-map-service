from rest_framework import serializers
from .models import PollutionPoint, Comment
from users.serializers import UserSerializer, OrganizationSerializer


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'text', 'photo', 'created_at']


class PollutionPointSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)
    handled_by = OrganizationSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = PollutionPoint
        fields = [
            'id', 'reporter', 'pollution_type', 'description',
            'latitude', 'longitude', 'photo', 'status',
            'handled_by',
            'created_at', 'updated_at', 'comments'
        ]


class PollutionStatusSerializer(serializers.Serializer):
    STATUS_CHOICES = [
        ('in_progress', 'В работе'),
        ('cleaned', 'Очищено'),
    ]
    status = serializers.ChoiceField(choices=STATUS_CHOICES)
