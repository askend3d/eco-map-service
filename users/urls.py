from django.urls import path
from rest_framework.routers import DefaultRouter

from users.views import UserViewSet, OrganizationViewSet

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'', UserViewSet, basename='user')

urlpatterns = router.urls
