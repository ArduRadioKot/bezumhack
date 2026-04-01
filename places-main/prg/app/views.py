from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from . import models
from .models import Profile, Service, Feedback, Transaction, Wallet, ServiceRequest, Chat, Message
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Profile, Service
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.core.mail import send_mail, BadHeaderError
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.http import HttpResponse
from .models import Profile
import os
from decimal import Decimal, InvalidOperation
from django.conf import settings


def is_executor(user):
    return user.profile.role == 'executor'


def register(request):
    if request.method == 'POST':
        try:
            username = request.POST['username'].strip()
            password = request.POST['password']
            password_confirm = request.POST['password_confirm']
            email = request.POST['email'].strip()
            first_name = request.POST['first_name'].strip()
            last_name = request.POST['last_name'].strip()
            middle_name = request.POST.get('middle_name', '').strip()
            phone = request.POST['phone'].strip()
            city = request.POST['city'].strip()
            birth_date = request.POST['birth_date']
            role = request.POST['role']
        except KeyError as e:
            messages.error(request, f'Отсутствует поле: {e}')
            return render(request, 'register.html')

        errors = []
        if User.objects.filter(username=username).exists():
            errors.append('Пользователь с таким логином уже существует')
        if User.objects.filter(email=email).exists():
            errors.append('Пользователь с таким email уже существует')
        if password != password_confirm:
            errors.append('Пароли не совпадают')
        try:
            validate_email(email)
        except ValidationError:
            errors.append('Введите корректный email')

        if errors:
            for err in errors:
                messages.error(request, err)
            return render(request, 'register.html', {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'middle_name': middle_name,
                'phone': phone,
                'city': city,
                'birth_date': birth_date,
                'role': role
            })

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                last_name=last_name
            )
            user.is_active = False
            user.save()

            Profile.objects.create(
                user=user,
                middle_name=middle_name,
                phone=phone,
                city=city,
                birth_date=birth_date,
                role=role
            )

            with transaction.atomic():
                wallet = Wallet.objects.create(user=user, balance=0)
                Transaction.objects.create(
                    user=user,
                    amount=0,
                    transaction_type='initial',
                    description="Активация кошелька"
                )

            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = request.build_absolute_uri(
                f"/activate/{uid}/{token}/"
            )

            subject = 'Подтвердите вашу почту'
            message = render_to_string('activation_email.html', {
                'user': user,
                'activation_link': activation_link,
            })
            send_mail(subject, message, None, [email], fail_silently=False)

            return redirect('check_mail')

        except Exception as e:
            #logger.exception("Ошибка при создании пользователя:")
            messages.error(request, f'Не удалось зарегистрировать: {e}')
            return render(request, 'register.html', {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'middle_name': middle_name,
                'phone': phone,
                'city': city,
                'birth_date': birth_date,
                'role': role
            })

    return render(request, 'register.html')


def check_mail(request):
    return render(request, 'check_your_gmail.html')
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Email подтверждён. Теперь можно войти.')
        return redirect('login')
    else:
        return HttpResponse('Ссылка недействительна или уже использована.', status=400)


def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Аккаунт не активирован. Проверьте почту.')
        else:
            messages.error(request, 'Неверный логин или пароль')
    return render(request, 'login.html')


def user_logout(request):
    logout(request)
    return redirect('home')


def index(request):
    return render(request, 'index.html')




def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль')
    
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('home')

def index(request):
    services = Service.objects.all().order_by('-created_at')
    return render(request, 'index.html', {'services': services})


def service_detail(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    return render(request, 'service_detail.html', {'service': service})


@login_required
def profile(request):
    user = request.user
    try:
        user_profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        user_profile = None
    
    context = {
        'user': user,
        'profile': user_profile,
        'date_joined': user.date_joined,
    }
    return render(request, 'profile.html', context)

@login_required
@user_passes_test(is_executor)
def create_service(request):
    if request.method == 'POST':
        service = Service(
            author=request.user,
            title=request.POST['title'],
            description=request.POST['description'],
            price=request.POST['price'],
            image=request.FILES['image']
        )
        service.save()
        return redirect('home')
    return render(request, 'create_service.html')


@login_required
def service_detail(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    user_profile = request.user.profile 
    is_customer = user_profile.role == 'customer'
    feedback_submitted = False  

    if request.method == 'POST':
        if is_customer:
            feedback_text = request.POST.get('feedback_text')
            if feedback_text:
                Feedback.objects.create(service=service, author=request.user, text=feedback_text)
                messages.success(request, 'Отзыв успешно отправлен!')
                feedback_submitted = True 
                return redirect('service_detail', service_id=service_id) 

    return render(request, 'service_detail.html', {
        'service': service,
        'is_customer': is_customer,
        'feedback_submitted': feedback_submitted 
    })


@login_required
def my_feedbacks(request):
    if request.user.profile.role == 'executor':
        feedbacks = Feedback.objects.filter(service__author=request.user)  
        return render(request, 'my_feedbacks.html', {'feedbacks': feedbacks})
    else:
        messages.error(request, "У вас нет прав для просмотра этой страницы.")
        return redirect('home')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Неверный логин или пароль')
    
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('home')

def index(request):
    services = Service.objects.all().order_by('-created_at')
    return render(request, 'index.html', {'services': services})

def service_detail(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    return render(request, 'service_detail.html', {'service': service})


@login_required
def profile(request):
    user = request.user
    try:
        user_profile = Profile.objects.get(user=user)
    except Profile.DoesNotExist:
        user_profile = None
    
    context = {
        'user': user,
        'profile': user_profile,
        'date_joined': user.date_joined,
    }
    return render(request, 'profile.html', context)

@login_required
@user_passes_test(is_executor)
def create_service(request):
    if request.method == 'POST':
        service = Service(
            author=request.user,
            title=request.POST['title'],
            description=request.POST['description'],
            price=request.POST['price'],
            image=request.FILES['image']
        )
        service.save()
        return redirect('home')
    return render(request, 'create_service.html')


@login_required
def service_detail(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    user_profile = request.user.profile  
    is_customer = user_profile.role == 'customer'
    feedback_submitted = False  

    if request.method == 'POST':
        if is_customer:
            feedback_text = request.POST.get('feedback_text')
            if feedback_text:
                Feedback.objects.create(service=service, author=request.user, text=feedback_text)
                messages.success(request, 'Отзыв успешно отправлен!')
                feedback_submitted = True 
                return redirect('service_detail', service_id=service_id) 

    return render(request, 'service_detail.html', {
        'service': service,
        'is_customer': is_customer,
        'feedback_submitted': feedback_submitted 
    })


@login_required
def my_feedbacks(request):
    if request.user.profile.role == 'executor':
        feedbacks = Feedback.objects.filter(service__author=request.user) 
        return render(request, 'my_feedbacks.html', {'feedbacks': feedbacks})
    else:
        messages.error(request, "У вас нет прав для просмотра этой страницы.")
        return redirect('home')


from decimal import Decimal
from django.db import transaction


@login_required
def add_balance(request):
    if request.method == 'POST':
        try:
            amount = Decimal(request.POST.get('amount'))
            if amount <= -2:
                raise ValueError("Сумма должна быть положительной")

            with transaction.atomic():
                wallet, created = Wallet.objects.get_or_create(user=request.user)
                wallet.balance += amount
                wallet.save()

                Transaction.objects.create(
                    user=request.user,
                    amount=amount,
                    transaction_type='deposit',
                    description=f"Пополнение баланса"
                )

            messages.success(request, f'Баланс пополнен на {amount} ₽')
            return redirect('profile')

        except (ValueError, InvalidOperation) as e:
            messages.error(request, f'Ошибка: {str(e)}')

    return render(request, 'add_balance.html')


@login_required
def process_payment(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    user_profile = request.user.profile

    if user_profile.role != 'customer':
        messages.error(request, "Только заказчики могут оплачивать услуги")
        return redirect('service_detail', service_id=service_id)

    # Получаем или создаем кошельки
    customer_wallet, c_created = Wallet.objects.get_or_create(
        user=request.user,
        defaults={'balance': 0}
    )
    executor_wallet, e_created = Wallet.objects.get_or_create(
        user=service.author,
        defaults={'balance': 0}
    )

    if c_created:
        Transaction.objects.create(
            user=request.user,
            amount=0,
            transaction_type='initial',
            description="Автоматическое создание кошелька"
        )
        messages.info(request, "Ваш кошелек был автоматически создан")

    if e_created:
        Transaction.objects.create(
            user=service.author,
            amount=0,
            transaction_type='initial',
            description="Автоматическое создание кошелька"
        )

    if customer_wallet.balance < service.price:
        messages.error(request, "Недостаточно средств на балансе")
        return redirect('service_detail', service_id=service_id)

    try:
        with transaction.atomic():
            # Списание у заказчика
            customer_wallet.balance -= service.price
            customer_wallet.save()

            Transaction.objects.create(
                user=request.user,
                amount=-service.price,
                transaction_type='payment',
                description=f"Оплата услуги '{service.title}'"
            )

            # Зачисление исполнителю
            executor_wallet.balance += service.price
            executor_wallet.save()

            Transaction.objects.create(
                user=service.author,
                amount=service.price,
                transaction_type='income',
                description=f"Получение оплаты за услугу '{service.title}'"
            )

            messages.success(request, "Оплата прошла успешно!")
            return redirect('service_detail', service_id=service_id)

    except Exception as e:
        messages.error(request, f"Ошибка при обработке платежа: {str(e)}")
        return redirect('service_detail', service_id=service_id)


# views.py
from decimal import Decimal
from django.db import transaction


# views.py
@login_required
def request_service(request, service_id):
    service = get_object_or_404(Service, pk=service_id)
    customer = request.user

    if customer.profile.role != 'customer':
        messages.error(request, "Только заказчики могут запрашивать услуги")
        return redirect('service_detail', service_id=service_id)

    # Получаем или создаем кошелек, если его нет
    wallet, created = Wallet.objects.get_or_create(
        user=customer,
        defaults={'balance': 0}
    )
    
    if created:
        messages.info(request, "Кошелек был автоматически создан с балансом 0 ₽")
        Transaction.objects.create(
            user=customer,
            amount=0,
            transaction_type='initial',
            description="Автоматическое создание кошелька"
        )

    if wallet.balance < service.price:
        messages.error(request, "Недостаточно средств на балансе")
        return redirect('service_detail', service_id=service_id)

    try:
        with transaction.atomic():
            # Резервируем средства
            wallet.balance -= service.price
            wallet.save()

            Transaction.objects.create(
                user=customer,
                amount=-service.price,
                transaction_type='reservation',
                description=f"Резервирование средств для услуги '{service.title}'"
            )

            # Создаем запрос
            ServiceRequest.objects.create(
                customer=customer,
                executor=service.author,
                service=service,
                price=service.price,
                status='pending'
            )

            messages.success(request, "Запрос на услугу успешно создан!")
            return redirect('order_submitted')

    except Exception as e:
        messages.error(request, f"Ошибка при создании запроса: {str(e)}")
        return redirect('service_detail', service_id=service_id)


@login_required
def update_request_status(request, request_id):
    service_request = get_object_or_404(
        ServiceRequest,
        pk=request_id,
        executor=request.user  # Проверка что запрос принадлежит исполнителю
    )

    if request.method == 'POST':
        new_status = request.POST.get('status')
        result_file = request.FILES.get('result_file')

        with transaction.atomic():
            if new_status == 'in_progress':
                service_request.status = 'in_progress'

            elif new_status == 'rejected':
                # Возврат средств заказчику
                service_request.customer.wallet.balance += service_request.price
                service_request.customer.wallet.save()
                service_request.status = 'rejected'

            elif new_status == 'completed':
                service_request.status = 'completed'
                if result_file:
                    service_request.result_file = result_file

            service_request.save()
            messages.success(request, "Статус успешно обновлен")
            return redirect('user_requests')

    context = {
        'request': service_request,
    }
    return render(request, 'update_request.html', context)

@login_required
def complete_payment(request, request_id):
    service_request = get_object_or_404(ServiceRequest, pk=request_id, customer=request.user)

    if service_request.status != 'completed' or service_request.is_paid:
        messages.error(request, "Невозможно выполнить оплату")
        return redirect('profile')

    with transaction.atomic():
        # Перевод средств исполнителю
        service_request.executor.wallet.balance += service_request.price
        service_request.executor.wallet.save()

        service_request.is_paid = True
        service_request.save()

    messages.success(request, "Оплата успешно проведена")
    return redirect('view_request', request_id=request_id)


@login_required
def user_requests(request):
    # Получаем все запросы где пользователь является заказчиком или исполнителем
    customer_requests = ServiceRequest.objects.filter(customer=request.user)
    executor_requests = ServiceRequest.objects.filter(executor=request.user)

    context = {
        'customer_requests': customer_requests,
        'executor_requests': executor_requests
    }

    return render(request, 'request_list.html', context)


def order_submitted(request):
    return render(request, 'order_submitted.html')


@login_required
def view_request(request, request_id):
    service_request = get_object_or_404(
        ServiceRequest,
        Q(customer=request.user) | Q(executor=request.user),  
        pk=request_id
    )
    return render(request, 'view_request.html', {'request': service_request})

@login_required
def create_chat(request, login1, login2):
    users_sorted = sorted([login1, login2])
    filename = f"chat_{users_sorted[0]}_{users_sorted[1]}.html"
    template_path = os.path.join('chats', filename)
    full_path = os.path.join(settings.BASE_DIR, 'app', 'templates', 'chats', filename)

    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    

    if not os.path.exists(full_path):
        with open(full_path, 'w') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Чат {login1} и {login2}</title>
</head>
<body>
    <h1>Чат между {login1} и {login2}</h1>
    <a href="/chats/">Назад к списку чатов</a>
</body>
</html>""")
    
    user1 = get_object_or_404(User, username=login1)
    user2 = get_object_or_404(User, username=login2)
    chat, created = Chat.objects.get_or_create()
    chat.participants.add(user1, user2)
    
    return redirect('chat_list')

@login_required
def chat_list(request):
    chats = Chat.objects.filter(participants=request.user)
    return render(request, 'chats/list.html', {'chats': chats})

def serve_chat_file(request, filename):
    try:
        user1, user2 = filename.replace('chat_', '').replace('.html', '').split('_')
        if request.user.username not in [user1, user2]:
            return redirect('chat_list')
    except:
        return redirect('chat_list')
    
    return render(request, f'chats/{filename}')