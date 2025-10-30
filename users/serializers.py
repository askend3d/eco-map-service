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
    organization_id = serializers.PrimaryKeyRelatedField(
        queryset=Organization.objects.all(),
        source='organization',
        required=False,
        allow_null=True
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password', 'role', 'organization_id']

    def create(self, validated_data):
        user = User.objects.create_user(
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'citizen'),
            organization=validated_data.get('organization', None)
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
