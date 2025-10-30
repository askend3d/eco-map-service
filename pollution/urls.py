from rest_framework_nested import routers
from .views import PollutionPointViewSet, CommentViewSet

# основной роутер
router = routers.SimpleRouter()
router.register(r'points', PollutionPointViewSet, basename='points')

# вложенный роутер для комментариев
points_router = routers.NestedSimpleRouter(router, r'points', lookup='point')
points_router.register(r'comments', CommentViewSet, basename='point-comments')

urlpatterns = router.urls + points_router.urls
