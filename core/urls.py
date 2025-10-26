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

    path('meu-relatorio/professor/', views.meu_relatorio_professor, name='meu_relatorio_professor'),

    path('aluno/<int:aluno_id>/relatorio/', views.relatorio_aluno_individual, name='relatorio_aluno_individual'),

    path('relatorios/ranking-alunos/', views.relatorio_ranking_alunos, name='relatorio_ranking_alunos'),
    path('relatorios/ranking-turmas/', views.relatorio_ranking_turmas, name='relatorio_ranking_turmas'),
    path('relatorios/ranking-professores/', views.relatorio_ranking_professores, name='relatorio_ranking_professores'),
    path('relatorios/gerenciamento-turmas/', views.gerenciamento_turmas, name='gerenciamento_turmas'),
    path('relatorios/gerenciamento-alunos/', views.gerenciamento_alunos, name='gerenciamento_alunos'),

    path('professor/<int:professor_user_id>/relatorio/', views.relatorio_professor_individual, name='relatorio_professor_individual'),
    path('relatorios/gerenciamento-professores/', views.gerenciamento_professores, name='gerenciamento_professores'),
]