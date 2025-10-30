from django.contrib.auth import authenticate
from rest_framework import serializers
from users.models import User, Organization


class UserSerializer(serializers.ModelSerializer):
    organization = serializers.PrimaryKeyRelatedField(
        read_only=True
    )

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'organization']


class OrganizationSerializer(serializers.ModelSerializer):
    members = UserSerializer(read_only=True, many=True)

    class Meta:
        model = Organization
        fields = [
            'id', 'name', 'kind', 'contact_email',
            'description', 'region', 'is_active', 'members'
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    pollution_reports = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'organization', 'pollution_reports']

    def get_pollution_reports(self, obj):
        from pollution.serializers import PollutionPointSerializer
        pollution_points = obj.pollution_reports.all()
        return PollutionPointSerializer(pollution_points, many=True).data


class AddMemberSerializer(serializers.Serializer):
    """Сериализатор для добавления пользователя по username или email"""
    username_or_email = serializers.CharField()

    @staticmethod
    def validate_username_or_email(value):
        user = User.objects.filter(username=value).first() or User.objects.filter(email=value).first()
        if not user:
            raise serializers.ValidationError("Пользователь не найден.")
        return user

    def save(self, organization):
        user = self.validated_data['username_or_email']
        if isinstance(user, str):
            user = User.objects.filter(username=user).first() or User.objects.filter(email=user).first()
        user.organization = organization
        user.save()
        return user


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'citizen'),
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Неверные учетные данные.")
        data['user'] = user
        return data
