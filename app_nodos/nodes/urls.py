# app_nodos/nodes/urls.py
from rest_framework.routers import DefaultRouter
from nodes.views import NodeViewSet

# Creamos un router específico para los nodos
router = DefaultRouter()
router.register(r'nodes', NodeViewSet, basename='node')

# El router generará automáticamente las rutas básicas (CRUD)
# y las rutas personalizadas que definiste en el ViewSet (depth, soft_delete, etc.)
# ej: GET /nodes/, POST /nodes/, DELETE /nodes/{pk}/

urlpatterns = router.urls

# NOTA IMPORTANTE DE ARQUITECTURA:
# Este archivo NO debe incluir el 'admin/', ni las rutas de JWT.
# Esas rutas van en el urls.py principal del proyecto (app_nodos/urls.py).