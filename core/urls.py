# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views # Views de autenticação prontas do Django
from . import views # Importa nossas views (a do dashboard)

urlpatterns = [
    # URL 1: A página principal (Dashboard)
    path('', views.dashboard, name='dashboard'),

    # URL 2: A tela de Login
    # Usamos a view pronta 'LoginView' do Django.
    # Ela automaticamente procura por 'registration/login.html'
    path('login/', auth_views.LoginView.as_view(), name='login'),

    # URL 3: A ação de Sair (Logout)
    # Usamos a view pronta 'LogoutView'.
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]