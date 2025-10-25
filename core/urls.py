# core/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views 

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # --- NOSSA NOVA URL ---
    # ex: /turma/1/chamada/
    # O 'turma_id' será passado para a view
    path('turma/<int:turma_id>/chamada/', views.pagina_chamada, name='pagina_chamada'),

    path('relatorios/', views.pagina_relatorios, name='relatorios'),
    
    # --- URL PARA O RELATÓRIO DO ALUNO ---
    path('meu-relatorio/', views.meu_relatorio, name='meu_relatorio'),

    # --- URL DO ROTEADOR DE LOGIN ---
    path('roteador/', views.login_router, name='login_router'),

    path('turma/<int:turma_id>/detalhes/', views.detalhes_turma, name='detalhes_turma'),
]