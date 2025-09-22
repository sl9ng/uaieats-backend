# app/urls.py

from django.urls import path, include
from rest_framework import generics, permissions 
from rest_framework.routers import SimpleRouter
from rest_framework_nested import routers
from .views import ChangePasswordView 

from .views import (
    RestaurantViewSet, DishViewSet, OrderViewSet, OrderItemViewSet,
    RegisterView, LoginView, UserProfileView,
    CardListCreateView, CardDetailView,
    VerifyEmailView, ChangePasswordView, UserViewSet,
) 

router = SimpleRouter()
router.register(r'restaurants', RestaurantViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'users', UserViewSet)

restaurants_router = routers.NestedSimpleRouter(router, r'restaurants', lookup='restaurant')
restaurants_router.register(r'dishes', DishViewSet, basename='restaurant-dishes')

orders_router = routers.NestedSimpleRouter(router, r'orders', lookup='order')
orders_router.register(r'items', OrderItemViewSet, basename='order-items')

urlpatterns = [
    # Rotas de autenticação e verificação
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'), 
    path('profile/', UserProfileView.as_view(), name='user_profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('', include(router.urls)),
    
    # Rotas para cartões
    path('cards/', CardListCreateView.as_view(), name='card_list_create'),
    path('cards/<int:pk>/', CardDetailView.as_view(), name='card_detail'),
    
    # Rotas dos routers (restaurantes, pratos, pedidos)
    path('', include(router.urls)),
    path('', include(restaurants_router.urls)),
    path('', include(orders_router.urls)),
     path('profile/', UserProfileView.as_view(), name='user_profile'), 
    path('change-password/', ChangePasswordView.as_view(), name='change-password'), 
]