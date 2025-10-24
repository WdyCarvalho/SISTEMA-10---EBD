# core/views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Turma # Importe o modelo Turma que criamos

@login_required 
def dashboard(request):
    """
    Esta é a view da página principal (Dashboard) do professor.
    Agora ela também busca e lista as turmas do professor logado.
    """
    
    # Esta é a lógica de permissão que você pediu!
    # Filtramos as Turmas buscando apenas aquelas onde o campo 'professor'
    # é exatamente o 'request.user' (o usuário que fez o login).
    turmas_do_professor = Turma.objects.filter(professor=request.user).order_by('nome')
    
    contexto = {
        'usuario': request.user,
        'turmas': turmas_do_professor, # Passamos a lista de turmas para o template
    }
    return render(request, 'dashboard.html', contexto)