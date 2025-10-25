# core/context_processors.py

def permissoes_context(request):
    """
    Este processador injeta informações de permissão em todos os templates.
    (Versão Etapa 11, com Supervisores)
    """
    is_professor = False
    is_aluno = False
    is_supervisor = False
    aluno = None 
    
    if request.user.is_authenticated:
        # 1. É Supervisor? (A verificação mais alta)
        is_supervisor = request.user.groups.filter(name='Supervisores').exists()

        # 2. É Professor?
        is_professor = request.user.groups.filter(name='Professores').exists()
        
        # 3. É Aluno?
        try:
            aluno = request.user.aluno 
            is_aluno = True
        except:
            is_aluno = False

    return {
        'is_supervisor': is_supervisor,
        'is_professor': is_professor,
        'is_aluno': is_aluno,
        'aluno_global': aluno,
    }