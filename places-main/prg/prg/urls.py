"""
URL configuration for prg project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function vie    path('', views.index, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from app import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.index, name='home'),
    path('register/', views.register, name='register'),
    path('check-mail/', views.check_mail, name='check_mail'),

    path('activate/<uidb64>/<token>/', views.activate, name='activate'),

    path('login/', views.user_login, name='login'),
    path('accounts/login/', views.user_login, name='login'),

    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('create-service/', views.create_service, name='create_service'),
    path('service/<int:service_id>/', views.service_detail, name='service_detail'),
    path('my_feedbacks/', views.my_feedbacks, name='my_feedbacks'),
    path('add-balance/', views.add_balance, name='add_balance'),
    path('service/<int:service_id>/pay/', views.process_payment, name='process_payment'),

    path('request-service/<int:service_id>/', views.request_service, name='request_service'),
    path('manage-request/<int:request_id>/', views.update_request_status, name='manage_request'),
    path('complete-payment/<int:request_id>/', views.complete_payment, name='complete_payment'),
    path('requests/', views.user_requests, name='user_requests'),
    path('order-submitted/', views.order_submitted, name='order_submitted'),
    path('request/<int:request_id>/', views.view_request, name='view_request'),
    path('create-chat/<str:login1>/<str:login2>/', views.create_chat, name='create_chat'),
    path('chats/', views.chat_list, name='chat_list'),
    path('chats/<str:filename>', views.serve_chat_file, name='chat_file'),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
