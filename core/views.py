# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory # Importamos o "criador de super-formulários"
from .models import Turma, Aluno, Chamada, RegistroChamada
from .forms import RegistroChamadaForm # Importamos nosso novo formulário
from datetime import date # Para pegar a data de hoje

# Mantenha a view 'dashboard' que já existe
@login_required
def dashboard(request):
    turmas_do_professor = Turma.objects.filter(professor=request.user).order_by('nome')
    contexto = {
        'usuario': request.user,
        'turmas': turmas_do_professor,
    }
    return render(request, 'dashboard.html', contexto)


# --- NOSSA NOVA VIEW ---
@login_required
def pagina_chamada(request, turma_id):
    """
    Esta view controla a página de "Fazer Chamada".
    Ela lida com o seletor de data e com o FormSet de alunos.
    """
    # 1. SEGURANÇA: Garante que a turma existe E pertence ao professor logado.
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)

    # 2. LÓGICA DA DATA: Pega a data da URL (ex: ?data=2025-10-17)
    #    Se nenhuma data for passada, usa a data de hoje (date.today())
    data_selecionada_str = request.GET.get('data', date.today().isoformat())
    data_selecionada = date.fromisoformat(data_selecionada_str)

    # 3. PEGAR OU CRIAR OBJETOS:
    #    Cria o "evento" da Chamada para esta turma/data (ou pega se já existir)
    chamada, _ = Chamada.objects.get_or_create(
        turma=turma, 
        data=data_selecionada,
        defaults={'criado_por': request.user}
    )

    # 4. GARANTIR REGISTROS:
    #    Para o FormSet funcionar, precisamos que os registros de chamada
    #    já existam no banco. Este loop garante isso.
    alunos_da_turma = turma.alunos.all().order_by('nome_completo')
    for aluno in alunos_da_turma:
        RegistroChamada.objects.get_or_create(
            chamada=chamada, 
            aluno=aluno
        )
    
    # 5. CRIAR O "SUPER-FORMULÁRIO" (FormSet):
    #    Diz ao Django para criar um conjunto de formulários
    #    para TODOS os registros daquela chamada.
    RegistroChamadaFormSet = modelformset_factory(
        RegistroChamada, 
        form=RegistroChamadaForm, 
        extra=0 # 'extra=0' diz para não criar formulários em branco
    )

    # 6. PROCESSAR O FORMULÁRIO (SALVAR):
    if request.method == 'POST':
        # Se o professor clicou em "Salvar", preenchemos o FormSet com os dados do POST
        queryset = RegistroChamada.objects.filter(chamada=chamada)
        formset = RegistroChamadaFormSet(request.POST, queryset=queryset)
        
        if formset.is_valid():
            formset.save() # Salva TODOS os registros de uma vez
            # (A nossa lógica de pontos no models.py será ativada aqui)
            return redirect('dashboard') # Volta para o painel
        # Se o formset não for válido (raro aqui), ele será reexibido com erros

    # 7. EXIBIR O FORMULÁRIO (CARREGAMENTO INICIAL):
    else:
        # Pega todos os registros da chamada e os ordena pelo nome do aluno
        queryset = RegistroChamada.objects.filter(chamada=chamada).select_related('aluno').order_by('aluno__nome_completo')
        formset = RegistroChamadaFormSet(queryset=queryset)

    # 8. ENVIAR TUDO PARA O TEMPLATE:
    contexto = {
        'turma': turma,
        'formset': formset,
        'data_selecionada_str': data_selecionada_str,
    }
    return render(request, 'chamada.html', contexto)