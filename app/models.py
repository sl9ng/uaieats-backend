# app/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Profile(models.Model):
    USER_ROLE_CHOICES = (
        ('cliente', 'Cliente'),
        ('admin', 'Admin'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=10, choices=USER_ROLE_CHOICES, default='cliente')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    # Campos para verificação de e-mail
    is_verified = models.BooleanField(default=False)
    verification_code = models.CharField(max_length=6, null=True, blank=True)
    code_expiry = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.user.username} Profile'

class Restaurant(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    address = models.CharField(max_length=255, blank=True, null=True)
    delivery_time = models.IntegerField(default=30)
    image = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return self.name

class Dish(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='dishes')
    category = models.CharField(max_length=100, default='Outros')
    image = models.URLField(max_length=500, blank=True, null=True)
    
    def __str__(self):
        return f'{self.name} ({self.restaurant.name})'

class Order(models.Model):
    STATUS_CHOICES = [
        ('P', 'Pendente'),
        ('C', 'Completo'),
    ]
    PAYMENT_CHOICES = [
        ('cash', 'Dinheiro'),
        ('card', 'Cartão de Crédito'),
    ]
    
    # Campo de usuário
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True)
    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default='P')
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)

    # Campo de método de pagamento
    payment_method = models.CharField(max_length=50, choices=PAYMENT_CHOICES, default='card')

    def __str__(self):
        return f'Order #{self.id}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    def __str__(self):
        return f'{self.quantity}x {self.dish.name}'

class Card(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cards')
    card_number = models.CharField(max_length=19)
    card_holder_name = models.CharField(max_length=255)
    expiry_date = models.CharField(max_length=5)
    cvv = models.CharField(max_length=4)
    card_brand = models.CharField(max_length=50, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.card_brand or 'Cartão'} **** {self.card_number[-4:]} ({self.user.username})"

    class Meta:
        verbose_name = "Cartão de Crédito/Débito"
        verbose_name_plural = "Cartões de Crédito/Débito"