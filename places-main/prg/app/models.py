from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    middle_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20)
    city = models.CharField(max_length=100)
    birth_date = models.DateField()
    role = models.CharField(max_length=20, choices=[
        ('customer', 'Заказчик'),
        ('executor', 'Исполнитель'),
    ])

    def __str__(self):
        return f"{self.user.username}'s Profile"
    

class Service(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=100, decimal_places=2)
    image = models.ImageField(upload_to='services/')
    created_at = models.DateTimeField(auto_now_add=True)

class Feedback(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='feedbacks')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback on {self.service.title} by {self.author.username}"


# models.py
class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=100, decimal_places=2, default=0)


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'Пополнение'),
        ('payment', 'Оплата услуги'),
        ('income', 'Получение средств'),
        ('initial', 'Начальный баланс')  # Добавьте это
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(  # Исправлено mount → amount
        max_digits=30,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)


# models.py
class ServiceRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('in_progress', 'В работе'),
        ('rejected', 'Отказано'),
        ('completed', 'Сделано'),
    ]

    customer = models.ForeignKey(User, related_name='customer_requests', on_delete=models.CASCADE)
    executor = models.ForeignKey(User, related_name='executor_requests', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    result_file = models.FileField(upload_to='service_results/', null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def clean(self):
        if self.customer.profile.role != 'customer':
            raise ValidationError("Заказчик должен иметь роль customer")

        if self.executor.profile.role != 'executor':
            raise ValidationError("Исполнитель должен иметь роль executor")

        if self.price <= 0:
            raise ValidationError("Цена должна быть положительной")


class Chat(models.Model):
    participants = models.ManyToManyField(User, related_name='chats')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.participants.count() != 2:
            raise ValidationError("Чат должен иметь ровно 2 участника")

class Message(models.Model):
    chat = models.ForeignKey(Chat, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)