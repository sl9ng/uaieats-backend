# app/urls.py

from django.urls import path, include
from rest_framework_nested import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RestaurantViewSet, DishViewSet, OrderViewSet, OrderItemViewSet,
    RegisterView, LoginView, UserProfileView,
    CardListCreateView, CardDetailView,
    VerifyEmailView, ChangePasswordView, UserViewSet,
)

# Cria o router principal para os endpoints principais
router = routers.SimpleRouter()
router.register(r'restaurants', RestaurantViewSet, basename='restaurants')
router.register(r'orders', OrderViewSet, basename='orders')
router.register(r'users', UserViewSet, basename='users')

# Cria routers aninhados para sub-recursos (ex: pratos de um restaurante)
restaurants_router = routers.NestedSimpleRouter(router, r'restaurants', lookup='restaurant')
restaurants_router.register(r'dishes', DishViewSet, basename='restaurant-dishes')

orders_router = routers.NestedSimpleRouter(router, r'orders', lookup='order')
orders_router.register(r'items', OrderItemViewSet, basename='order-items')

# Define a lista final de URLs da API
urlpatterns = [
    # Inclui as rotas geradas pelos routers
    path('', include(router.urls)),
    path('', include(restaurants_router.urls)),
    path('', include(orders_router.urls)),

    # Rotas de Autenticação JWT (token)
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Rotas de Registro, Login e Perfil
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),

    # Rotas para Cartões
    path('cards/', CardListCreateView.as_view(), name='card_list_create'),
    path('cards/<int:pk>/', CardDetailView.as_view(), name='card_detail'),
]