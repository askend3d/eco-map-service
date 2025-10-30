from django.urls import path
from rest_framework.routers import DefaultRouter

from users.views import UserViewSet, OrganizationViewSet

user_router = DefaultRouter()
user_router.register(r'', UserViewSet, basename='user')

organization_router = DefaultRouter()
organization_router.register(r'', OrganizationViewSet, basename='organization')

