from rest_framework.routers import DefaultRouter
from .views import PollutionPointViewSet, CommentViewSet

router = DefaultRouter()
router.register(r'points', PollutionPointViewSet)
router.register(r'comments', CommentViewSet)

urlpatterns = router.urls
