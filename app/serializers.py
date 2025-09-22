from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
import re
from datetime import datetime

from .models import Restaurant, Dish, Order, OrderItem, Profile, Card

class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para validar e processar a alteração de senha.
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_new_password = serializers.CharField(required=True, write_only=True)

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"new_password": "A nova senha e a confirmação não correspondem."})
        
        return data

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Sua senha antiga está incorreta.")
        return value

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user

# ===================================================================
# SERIALIZERS DE USUÁRIO E PERFIL
# ===================================================================

class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='first_name', required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'name')
        extra_kwargs = {
            'password': {'write_only': True, 'required': True}, 
            'username': {'required': False, 'allow_blank': True},
            'email': {'required': True},
        }

    def validate_email(self, value):
        try:
            validate_email(value)
        except ValidationError:
            raise serializers.ValidationError("Formato de e-mail inválido.")
            
        if self.instance and self.instance.email == value:
            return value
            
        if User.objects.filter(email=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise serializers.ValidationError("Este e-mail já está em uso por outra conta.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', '')
        )
        return user

    def update(self, instance, validated_data):
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.email = validated_data.get('email', instance.email)
        
        password = validated_data.get('password')
        if password:
            instance.set_password(password)
            
        instance.save()
        return instance

class ProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)
    name = serializers.CharField(source='user.first_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Profile
        fields = ['id', 'user', 'role', 'phone_number', 'address', 'email', 'name', 'username']
        read_only_fields = ['user', 'role']


# ===================================================================
# SERIALIZERS DE RESTAURANTE E PRATOS
# ===================================================================

class DishSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = ['id', 'name', 'description', 'price', 'restaurant', 'category', 'image']

class RestaurantSerializer(serializers.ModelSerializer):
    dishes = DishSerializer(many=True, read_only=True)
    class Meta:
        model = Restaurant
        fields = ['id', 'name', 'description', 'address', 'delivery_time', 'image', 'dishes']

# ===================================================================
# SERIALIZER DE CARTÃO (COM VALIDAÇÕES COMPLETAS)
# ===================================================================

class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'user', 'card_number', 'card_holder_name', 'expiry_date', 'cvv', 'card_brand', 'created_at']
        read_only_fields = ['id', 'user', 'created_at', 'card_brand']

    def validate_expiry_date(self, value):
        if not re.match(r'^(0[1-9]|1[0-2])\/\d{2}$', value):
            raise serializers.ValidationError("Formato de data inválido (MM/AA).")
        
        try:
            month_str, year_str = value.split('/')
            expiry_month = int(month_str)
            expiry_year = int(f"20{year_str}")

            today = datetime.now()
            if expiry_year < today.year or \
               (expiry_year == today.year and expiry_month < today.month):
                raise serializers.ValidationError("Cartão expirado.")
        except ValueError:
            raise serializers.ValidationError("Formato de data inválido (MM/AA).")
        return value

    def validate_card_number(self, value):
        if not re.match(r'^\d{13,19}$', value):
            raise serializers.ValidationError("Número de cartão inválido. Deve conter entre 13 e 19 dígitos.")
        return value

    def validate_card_holder_name(self, value):
        if not re.match(r'^[A-Za-z\s]+$', value):
            raise serializers.ValidationError("O nome deve conter apenas letras e espaços.")
        return value
    
    def validate_cvv(self, value):
        if not re.match(r'^\d{3,4}$', value):
            raise serializers.ValidationError("O CVV deve ter 3 ou 4 dígitos numéricos.")
        return value

# ===================================================================
# SERIALIZERS DE PEDIDOS (ORDERS)
# ===================================================================

class OrderItemSerializer(serializers.ModelSerializer):
    dish_name = serializers.CharField(source='dish.name', read_only=True)
    dish_price = serializers.DecimalField(source='dish.price', max_digits=6, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'dish', 'quantity', 'price', 'dish_name', 'dish_price']

class OrderItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['dish', 'quantity']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemCreateSerializer(many=True, write_only=True)
    order_items = OrderItemSerializer(source='items', many=True, read_only=True)
    payment_method = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Order
        fields = ['id', 'user', 'status', 'created_at', 'total', 'payment_method', 'items', 'order_items']
        read_only_fields = ['id', 'user', 'status', 'created_at', 'total', 'order_items']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])
        payment_method = validated_data.pop('payment_method', 'card')

        validated_data['user'] = self.context['request'].user
        order = Order.objects.create(**validated_data)
        
        total_price = 0
        for item_data in items_data:
            dish = item_data['dish']
            quantity = item_data['quantity']
            price = dish.price
            OrderItem.objects.create(order=order, dish=dish, quantity=quantity, price=price)
            total_price += price * quantity
        
        order.total = total_price
        order.payment_method = payment_method
        order.save()
        return order

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True)

    def validate_new_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("A nova senha deve ter pelo menos 8 caracteres.")
        return value

# ===================================================================
# SERIALIZERS DE USUÁRIO E PERFIL (ADICIONAR)
# ===================================================================

class UserAndProfileSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_active', 'date_joined', 'first_name', 'profile')

    def get_profile(self, obj):
        try:
            profile = obj.profile
            return {
                'role': profile.role,
                'phone_number': profile.phone_number,
                'address': profile.address,
            }
        except Profile.DoesNotExist:
            return None