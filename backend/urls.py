# backend/urls.py

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from app.views import CardDetailView, CardListCreateView

urlpatterns = [
    
    path('admin/', admin.site.urls),

    path('api/', include('app.urls')),
    path('admin/', admin.site.urls),

    path('api/', include('app.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('cards/', CardListCreateView.as_view(), name='card_list_create'),
    path('cards/<int:pk>/', CardDetailView.as_view(), name='card_detail'),

]