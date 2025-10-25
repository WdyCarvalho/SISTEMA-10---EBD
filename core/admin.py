# core/admin.py
from django.contrib import admin
from .models import Turma, Aluno, Chamada, RegistroChamada

from .models import PerfilProfessor, RegistroChamadaProfessor

# -----------------------------------------------------------------------------
# Classe para melhorar a exibição de ALUNO no Admin
# (Esta é a versão mais recente que corrige o problema do campo "User")
# -----------------------------------------------------------------------------
@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    # O que mostrar na LISTA de alunos
    list_display = ('nome_completo', 'turma', 'pontos_totais', 'user')
    
    # O que mostrar no FORMULÁRIO de edição
    # O campo 'user' está aqui
    fields = ('user', 'nome_completo', 'turma', 'pontos_totais')
    
    # 'pontos_totais' é "apenas leitura"
    readonly_fields = ('pontos_totais',)
    
    list_filter = ('turma',)
    search_fields = ('nome_completo', 'user__username') 
    ordering = ('nome_completo',)

# -----------------------------------------------------------------------------
# Classe para melhorar a exibição de REGISTRO DE CHAMADA no Admin
# (Esta é a versão que fizemos na Etapa 4 e 5)
# -----------------------------------------------------------------------------
@admin.register(RegistroChamada)
class RegistroChamadaAdmin(admin.ModelAdmin):
    # 1. Define os campos que aparecerão no formulário
    fields = (
        'chamada', 
        'aluno', 
        'presenca', 
        'biblia', 
        'versiculo', 
        'convidado', 
        'oferta', 
        'atividades',
        'revista', # Adicionado na Etapa 5
        'pontos_ganhos'
    )
    
    # 2. 'pontos_ganhos' é "apenas leitura"
    readonly_fields = ('pontos_ganhos',) 

    # 3. Melhora a lista principal de registros
    list_display = ('aluno', 'chamada', 'pontos_ganhos')
    list_filter = ('chamada__turma', 'chamada__data')

# -----------------------------------------------------------------------------
# Registros simples (modelos que não precisam de customização)
# -----------------------------------------------------------------------------
admin.site.register(Turma)
admin.site.register(Chamada)

admin.site.register(PerfilProfessor)
admin.site.register(RegistroChamadaProfessor)