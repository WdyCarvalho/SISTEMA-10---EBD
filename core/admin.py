# core/admin.py
from django.contrib import admin
from .models import Turma, Aluno, Chamada, RegistroChamada

# -----------------------------------------------------------------------------
# Classe para melhorar a exibição de ALUNO no Admin
# -----------------------------------------------------------------------------
@admin.register(Aluno)
class AlunoAdmin(admin.ModelAdmin):
    # Quais colunas mostrar na lista de alunos
    list_display = ('nome_completo', 'turma', 'pontos_totais') 
    
    # Adiciona um filtro lateral para filtrar por turma
    list_filter = ('turma',) 
    
    # Adiciona uma barra de busca
    search_fields = ('nome_completo',) 
    
    # Ordena por nome por padrão
    ordering = ('nome_completo',)

# -----------------------------------------------------------------------------
# Classe para melhorar a exibição de REGISTRO DE CHAMADA no Admin
# -----------------------------------------------------------------------------
@admin.register(RegistroChamada)
class RegistroChamadaAdmin(admin.ModelAdmin):
    # 1. Define os campos que aparecerão no formulário de "Adicionar"
    # Esta é a correção para o seu problema!
    fields = (
        'chamada', 
        'aluno', 
        'presenca',
        'revista',
        'biblia', 
        'versiculo', 
        'convidado', 
        'oferta', 
        'atividades',
        'pontos_ganhos' # Vamos mostrar, mas tornar readonly
    )
    
    # 2. Torna o campo 'pontos_ganhos' apenas leitura, 
    # pois ele é calculado automaticamente
    readonly_fields = ('pontos_ganhos',) 

    # 3. Melhora a lista principal de registros
    list_display = ('aluno', 'chamada', 'pontos_ganhos')
    list_filter = ('chamada__turma', 'chamada__data') # Permite filtrar por turma ou data
    
# -----------------------------------------------------------------------------
# Registros simples (sem customização por enquanto)
# -----------------------------------------------------------------------------
admin.site.register(Turma)
admin.site.register(Chamada)