import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from django.contrib.auth import authenticate, get_user_model
from rest_framework import viewsets, status, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import action

# Importação de todos os modelos e serializers
from .models import Restaurant, Dish, Order, OrderItem, Profile, Card
from .serializers import (
    RestaurantSerializer, DishSerializer, OrderSerializer, OrderItemSerializer,
    UserSerializer, ProfileSerializer, CardSerializer, ChangePasswordSerializer,
    UserAndProfileSerializer 
)

User = get_user_model()

class ChangePasswordView(generics.UpdateAPIView):
    """
    Endpoint para um usuário logado alterar sua própria senha.
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "Senha alterada com sucesso!"}, status=status.HTTP_200_OK)


# ===================================================================
# VIEWS DE AUTENTICAÇÃO E VERIFICAÇÃO DE E-MAIL
# ===================================================================

class RegisterView(APIView):
    """
    Registra um novo usuário, o deixa inativo e envia um e-mail com 
    um código de verificação para ativar a conta.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        data = request.data.copy()
        data['username'] = data.get('email', '')
        data['first_name'] = data.get('name', '')

        serializer = UserSerializer(data=data)
        if serializer.is_valid():
            user = serializer.save()
            user.is_active = False
            user.save()

            profile, created = Profile.objects.get_or_create(user=user)

            code = str(random.randint(100000, 999999))
            expiry_time = timezone.now() + timedelta(minutes=15)
            profile.verification_code = code
            profile.code_expiry = expiry_time
            profile.save()

            try:
                subject = 'Seu Código de Verificação Foody'
                message = f'Olá {user.first_name},\n\nSeu código para ativar sua conta é: {code}\n\nEle expira em 15 minutos.'
                from_email = settings.EMAIL_HOST_USER
                recipient_list = [user.email]
                send_mail(subject, message, from_email, recipient_list)
            except Exception as e:
                user.delete()
                return Response({'error': f'Falha ao enviar e-mail de verificação: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({'message': 'Cadastro realizado! Verifique seu e-mail para o código de ativação.'}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    """
    Verifica o código enviado pelo usuário para ativar a conta.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            email = request.data.get('email')
            code = request.data.get('code')
            user = User.objects.get(email=email)

            if user.profile.is_verified:
                return Response({'error': 'Este e-mail já foi verificado.'}, status=status.HTTP_400_BAD_REQUEST)
            if user.profile.code_expiry < timezone.now():
                return Response({'error': 'Código de verificação expirado.'}, status=status.HTTP_400_BAD_REQUEST)
            if user.profile.verification_code == code:
                user.is_active = True
                user.save()
                user.profile.is_verified = True
                user.profile.verification_code = ''
                user.profile.save()
                return Response({'message': 'E-mail verificado com sucesso! Você já pode fazer login.'}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Código de verificação inválido.'}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({'error': 'Usuário não encontrado.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(username=email, password=password)
        
        if user is not None and user.is_active:
            profile, created = Profile.objects.get_or_create(user=user)
            refresh = RefreshToken.for_user(user)
            
            role = 'admin' if user.is_superuser or user.is_staff else profile.role

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'role': role, 
                'name': user.first_name, 
                'email': user.email, 
                'id': user.id
            })
            
        return Response({'error': 'Credenciais inválidas ou conta não verificada.'}, status=status.HTTP_401_UNAUTHORIZED)


# ===================================================================
# VIEWS DE PERFIL DE USUÁRIO E CARTÕES
# ===================================================================

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ProfileSerializer(request.user.profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        profile = user.profile
        data = request.data

        user_serializer = UserSerializer(instance=user, data=data, partial=True)
        if user_serializer.is_valid(raise_exception=True):
            user_serializer.save()

        profile_serializer = ProfileSerializer(instance=profile, data=data, partial=True)
        if profile_serializer.is_valid(raise_exception=True):
            profile_serializer.save()

        return self.get(request)


class CardListCreateView(generics.ListCreateAPIView):
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Card.objects.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CardDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CardSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Card.objects.filter(user=self.request.user)


# ===================================================================
# VIEWSETS PARA RESTAURANTES, PRATOS E PEDIDOS
# ===================================================================

class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class DishViewSet(viewsets.ModelViewSet):
    serializer_class = DishSerializer

    def get_queryset(self):
        restaurant_id = self.kwargs.get('restaurant_pk')
        
        if restaurant_id:
            return Dish.objects.filter(restaurant_id=restaurant_id)
        
        return Dish.objects.none()

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('-created_at')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class OrderItemViewSet(viewsets.ModelViewSet):
    serializer_class = OrderItemSerializer
    permission_classes = [IsAuthenticated]
    queryset = OrderItem.objects.all()

    def get_queryset(self):
        return self.queryset.filter(order__user=self.request.user)

class ChangePasswordView(generics.UpdateAPIView):
    serializer_class = ChangePasswordSerializer
    model = User
    permission_classes = [IsAuthenticated]

    def get_object(self, queryset=None):
        return self.request.user

    def update(self, request, *args, **kwargs):
        self.object = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            if not self.object.check_password(serializer.data.get("old_password")):
                return Response({"old_password": ["Senha atual incorreta."]}, status=status.HTTP_400_BAD_REQUEST)
            
            self.object.set_password(serializer.data.get("new_password"))
            self.object.save()
            
            return Response({"status": "senha alterada com sucesso"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ===================================================================
# VIEWSET PARA GERENCIAMENTO DE USUÁRIOS (Corrigido)
# ===================================================================

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserAndProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return self.queryset
        return self.queryset.none()

    @action(detail=True, methods=['post'], url_path='toggle-active')
    def toggle_active(self, request, pk=None):
        user_to_toggle = self.get_object()
        if user_to_toggle.is_superuser:
            return Response({'error': 'Não é possível desativar um superusuário.'}, status=status.HTTP_400_BAD_REQUEST)
        
        user_to_toggle.is_active = not user_to_toggle.is_active
        user_to_toggle.save()
        
        serializer = self.get_serializer(user_to_toggle)
        return Response(serializer.data)