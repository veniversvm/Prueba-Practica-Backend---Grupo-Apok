from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

# Creamos un router para mapear automáticamente las acciones CRUD y las acciones personalizadas
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Incluye todas las rutas generadas por el router: 
    # /users/, /users/{id}/, /users/{id}/nodes-created/, /users/me/, etc.
    path('', include(router.urls)),
]