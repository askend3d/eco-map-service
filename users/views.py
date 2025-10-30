from rest_framework import mixins, viewsets, status, permissions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth import login, logout
from django.contrib.auth import get_user_model
from .models import User, Organization
from .serializers import UserSerializer, RegisterSerializer, OrganizationSerializer, LoginSerializer, \
    AddMemberSerializer, UserProfileSerializer

User = get_user_model()


class UserViewSet(mixins.CreateModelMixin,
                  mixins.RetrieveModelMixin,
                  mixins.UpdateModelMixin,
                  viewsets.GenericViewSet):
    """
    Управление пользователями: регистрация, просмотр и редактирование профиля
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'register':
            return RegisterSerializer
        elif self.action == 'login':
            return LoginSerializer
        return UserSerializer

    @action(detail=False, methods=['post'], permission_classes=[])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['post'], permission_classes=[])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        login(request, user)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response({"detail": "Вы успешно вышли."}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get', 'patch', 'put'])
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = UserProfileSerializer(user)
            return Response(serializer.data)
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[permissions.IsAuthenticated],
        url_path='upload-photo'
    )
    def upload_photo(self, request):
        """Загрузка или обновление фото профиля"""
        user = request.user
        photo = request.FILES.get('photo')

        if not photo:
            return Response(
                {"detail": "Необходимо передать файл 'photo'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.photo:
            user.photo.delete(save=False)

        user.photo = photo
        user.save()

        return Response(
            {
                "detail": "Фото успешно обновлено.",
                "photo": request.build_absolute_uri(user.photo.url)
            },
            status=status.HTTP_200_OK
        )


class OrganizationViewSet(viewsets.ModelViewSet):
    """
    Управление организациями: просмотр списка, создание, редактирование,
    добавление участников.
    """
    queryset = Organization.objects.all().order_by('-created_at')
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        org = serializer.save()
        request_user = self.request.user
        request_user.organization = org
        request_user.save()

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def add_member(self, request, pk=None):
        """
        Добавить пользователя по username или email в организацию.
        """
        org = self.get_object()
        # Только члены организации могут добавлять новых
        if request.user.organization != org and request.user.role != 'admin':
            return Response({"detail": "Нет прав добавлять участников в эту организацию."},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = AddMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(organization=org)
        return Response(
            {"detail": f"Пользователь {user.username} добавлен в организацию {org.name}."},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        """
        Получить список участников организации.
        """
        org = self.get_object()
        members = org.members
        serializer = UserSerializer(members, many=True)
        return Response(serializer.data)
