from rest_framework import serializers
from .models import PollutionPoint, Comment
from users.serializers import UserSerializer


class CommentSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'text', 'photo', 'created_at']


class PollutionPointSerializer(serializers.ModelSerializer):
    reporter = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = PollutionPoint
        fields = [
            'id', 'reporter', 'pollution_type', 'description',
            'latitude', 'longitude', 'photo', 'status',
            'created_at', 'updated_at', 'comments'
        ]
