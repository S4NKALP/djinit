"""
API routes for store app.
"""

from rest_framework.routers import DefaultRouter
from . import views

# Create router instance
router = DefaultRouter()

# Register viewsets with router
# Example:
# router.register(r'store', views.StoreViewSet)

# Get URL patterns
urlpatterns = router.urls
