# core/context_processors.py

def permissoes_context(request):
    """
    Este processador injeta informações de permissão em todos os templates.
    """
    is_professor = False
    is_aluno = False
    
    if request.user.is_authenticated:
        # Verifica se está no grupo "Professores"
        is_professor = request.user.groups.filter(name='Professores').exists()
        
        # Verifica se o usuário está ligado a um 'Aluno'
        # (usando a relação 'aluno' que criamos no models.py)
        is_aluno = hasattr(request.user, 'aluno')

    return {
        'is_professor': is_professor,
        'is_aluno': is_aluno,
    }