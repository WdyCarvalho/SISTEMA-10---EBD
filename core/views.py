
from django.shortcuts import render
from django.contrib.auth.decorators import login_required # Importamos o "protetor" de páginas

@login_required # Este "decorador" protege a view
def dashboard(request):
    """
    Esta é a view da página principal (Dashboard) do professor.
    Somente usuários logados podem acessá-la.
    """
    contexto = {
        'usuario': request.user
    }
    return render(request, 'dashboard.html', contexto)