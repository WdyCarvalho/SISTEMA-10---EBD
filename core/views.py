# core/views.py
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory # Importamos o "criador de super-formulários"
from django.db.models import Sum
from .models import Turma, Aluno, Chamada, RegistroChamada, User, PerfilProfessor, RegistroChamadaProfessor
from .forms import RegistroChamadaForm, RegistroChamadaProfessorForm
from datetime import date # Para pegar a data de hoje
from .context_processors import permissoes_context # Importe a função que criamos

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
    Esta view controla a página "Fazer Chamada" (Etapa 7 Revisada).
    Agora ela lida com DOIS formulários:
    1. O FormSet de Alunos
    2. O Form normal do Professor
    """
    # 1. SEGURANÇA E LÓGICA DE DATA (Igual antes)
    turma = get_object_or_404(Turma, id=turma_id, professor=request.user)
    data_selecionada_str = request.GET.get('data', date.today().isoformat())
    data_selecionada = date.fromisoformat(data_selecionada_str)

    # 2. PEGAR/CRIAR OBJETOS (Igual antes)
    chamada, _ = Chamada.objects.get_or_create(
        turma=turma, 
        data=data_selecionada,
        defaults={'criado_por': request.user}
    )

    # 3. GARANTIR REGISTROS DE ALUNOS (Igual antes)
    alunos_da_turma = turma.alunos.all().order_by('nome_completo')
    for aluno in alunos_da_turma:
        RegistroChamada.objects.get_or_create(
            chamada=chamada, 
            aluno=aluno
        )
    
    # --- 4. NOVO: GARANTIR REGISTRO DO PROFESSOR ---
    # Precisamos do Perfil do professor (que foi criado automaticamente)
    perfil_professor = request.user.perfil_professor
    registro_professor, _ = RegistroChamadaProfessor.objects.get_or_create(
        chamada=chamada,
        professor=perfil_professor
    )

    # 5. CRIAR O FORMSET DE ALUNOS (Igual antes)
    RegistroChamadaFormSet = modelformset_factory(
        RegistroChamada, 
        form=RegistroChamadaForm, 
        extra=0
    )

    # 6. PROCESSAR OS FORMULÁRIOS (SALVAR)
    if request.method == 'POST':
        # Instancia o FormSet de Alunos com os dados do POST
        queryset_alunos = RegistroChamada.objects.filter(chamada=chamada)
        formset_alunos = RegistroChamadaFormSet(request.POST, queryset=queryset_alunos, prefix='alunos') # Adicionamos um prefixo

        # --- NOVO: Instancia o Form do Professor com os dados do POST ---
        form_professor = RegistroChamadaProfessorForm(request.POST, instance=registro_professor, prefix='professor') # Adicionamos um prefixo
        
        # Valida AMBOS
        if formset_alunos.is_valid() and form_professor.is_valid():
            formset_alunos.save() # Salva todos os registros de alunos
            form_professor.save() # Salva o registro do professor
            
            # (Nossa lógica de pontos nos models.py será ativada aqui)
            return redirect('dashboard') 
    
    # 7. EXIBIR OS FORMULÁRIOS (CARREGAMENTO INICIAL)
    else:
        # FormSet de Alunos (Igual antes)
        queryset_alunos = RegistroChamada.objects.filter(chamada=chamada).select_related('aluno').order_by('aluno__nome_completo')
        formset_alunos = RegistroChamadaFormSet(queryset=queryset_alunos, prefix='alunos')

        # --- NOVO: Form do Professor ---
        form_professor = RegistroChamadaProfessorForm(instance=registro_professor, prefix='professor')

    # 8. ENVIAR TUDO PARA O TEMPLATE
    contexto = {
        'turma': turma,
        'formset_alunos': formset_alunos, # Mudamos o nome da variável
        'form_professor': form_professor, # Nova variável
        'data_selecionada_str': data_selecionada_str,
    }
    return render(request, 'chamada.html', contexto)

@login_required
def pagina_relatorios(request):
    """
    Esta view gera os dados para os 3 rankings gerais.
    AGORA, TODOS OS USUÁRIOS LOGADOS PODEM VER TODOS OS RANKINGS.
    """

    # 1. Ranking Geral de Alunos (Limitado aos 20 primeiros)
    ranking_alunos_geral = Aluno.objects.all().order_by('-pontos_totais')[:20]

    # 2. Ranking Geral de Turmas
    ranking_turmas_geral = Turma.objects.annotate(
        pontos_da_turma=Sum('alunos__pontos_totais')
    ).filter(
        pontos_da_turma__gt=0
    ).order_by('-pontos_da_turma')

    # 3. Ranking Geral de Professores
    ranking_professores = PerfilProfessor.objects.select_related('user').filter(
        pontos_totais__gt=0
    ).order_by(
        '-pontos_totais'
    )

    contexto = {
        'ranking_alunos_geral': ranking_alunos_geral,
        'ranking_turmas_geral': ranking_turmas_geral,
        'ranking_professores': ranking_professores,
        # Não precisamos mais passar 'is_professor' daqui, 
        # pois o context_processor já faz isso globalmente.
    }
    
    return render(request, 'relatorios.html', contexto)


@login_required
def meu_relatorio(request):
    """
    Esta view mostra o relatório pessoal do aluno logado.
    """
    # Se o usuário não for um aluno (ex: é professor),
    # redirecionamos para o dashboard de professor.
    if not hasattr(request.user, 'aluno'):
        return redirect('dashboard')

    aluno = request.user.aluno
    
    # Busca todos os registros do aluno, ordenados por data
    registros = RegistroChamada.objects.filter(aluno=aluno).order_by('-chamada__data')
    
    # Calcula as estatísticas
    faltas = registros.filter(presenca=False).count()
    presencas = registros.filter(presenca=True).count()
    
    contexto = {
        'aluno': aluno,
        'registros': registros,
        'faltas': faltas,
        'presencas': presencas,
        'pontos_totais': aluno.pontos_totais # Pega o total já calculado
    }
    return render(request, 'meu_relatorio.html', contexto)


@login_required
def login_router(request):
    """
    Redireciona o usuário para o dashboard correto (Professor ou Aluno)
    após o login.
    """
    permissoes = permissoes_context(request) # Pega o dict de permissões

    if permissoes['is_professor']:
        return redirect('dashboard') # Redireciona Professor
    elif permissoes['is_aluno']:
        return redirect('meu_relatorio') # Redireciona Aluno
    else:
        # Se for um superusuário sem grupo (ou outro tipo)
        return redirect('relatorios')

@login_required
def detalhes_turma(request, turma_id):
    """
    Mostra o ranking de alunos para uma turma específica.
    Controla a permissão de Professores e Alunos.
    """
    turma = get_object_or_404(Turma, id=turma_id)
    permissoes = permissoes_context(request)
    
    acesso_permitido = False
    
    if permissoes['is_professor'] and turma.professor == request.user:
        acesso_permitido = True
        
    if permissoes['is_aluno'] and request.user.aluno.turma == turma:
        acesso_permitido = True

    if not acesso_permitido:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Você não tem permissão para ver esta turma.</p>") 

    ranking_alunos_turma = Aluno.objects.filter(turma=turma).order_by('-pontos_totais')
    
    contexto = {
        'turma': turma,
        'ranking_alunos_turma': ranking_alunos_turma,
    }
    
    return render(request, 'detalhes_turma.html', contexto)