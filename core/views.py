# core/views.py

from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory # Importamos o "criador de super-formulários"
from django.db.models import Sum, Avg, Count
from .models import Turma, Aluno, Chamada, RegistroChamada, User, PerfilProfessor, RegistroChamadaProfessor
from .forms import RegistroChamadaForm, RegistroChamadaProfessorForm
from datetime import date # Para pegar a data de hoje
from .context_processors import permissoes_context # Importe a função que criamos


@login_required 
def dashboard(request):
    permissores = permissoes_context(request)
    # SEGURANÇA: Só Professores
    if not permissores['is_professor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Esta página é apenas para professores.</p>")

    turmas_do_professor = Turma.objects.filter(professor=request.user).order_by('nome')
    contexto = {
        'usuario': request.user,
        'turmas': turmas_do_professor,
    }
    return render(request, 'dashboard.html', contexto)


# --- NOSSA NOVA VIEW ---
# core/views.py

@login_required
def pagina_chamada(request, turma_id):
    """
    (ETAPA 12 - ATUALIZADA)
    Controla a página "Fazer Chamada".
    Acesso: Supervisor (qualquer turma) ou Professor (apenas sua turma).
    Permite ao Supervisor pontuar o professor titular da turma.
    """
    permissores = permissoes_context(request)
    
    # 1. Busca a Turma
    turma = get_object_or_404(Turma, id=turma_id)

    # --- INÍCIO DA ATUALIZAÇÃO DE SEGURANÇA ---
    acesso_permitido = False
    
    if permissores['is_supervisor']:
        acesso_permitido = True
    elif permissores['is_professor'] and turma.professor == request.user:
        acesso_permitido = True
        
    if not acesso_permitido:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Você não tem permissão para fazer a chamada desta turma.</p>")
    # --- FIM DA ATUALIZAÇÃO DE SEGURANÇA ---

    # 2. LÓGICA DE DATA (Igual antes)
    data_selecionada_str = request.GET.get('data', date.today().isoformat())
    data_selecionada = date.fromisoformat(data_selecionada_str)

    # 3. PEGAR/CRIAR CHAMADA (Igual antes)
    chamada, _ = Chamada.objects.get_or_create(
        turma=turma, 
        data=data_selecionada,
        defaults={'criado_por': request.user} # Registra quem criou (o supervisor ou o prof)
    )

    # 4. GARANTIR REGISTROS DE ALUNOS (Igual antes)
    alunos_da_turma = turma.alunos.all().order_by('nome_completo')
    for aluno in alunos_da_turma:
        RegistroChamada.objects.get_or_create(chamada=chamada, aluno=aluno)
    
    # --- 5. ATUALIZAÇÃO: GARANTIR REGISTRO DO PROFESSOR TITULAR ---
    registro_professor = None
    form_professor = None
    professor_titular = turma.professor # Pega o professor associado à turma
    
    if professor_titular: # Só faz a chamada do prof se a turma tiver um
        try:
            # Pega o perfil do professor titular (NÃO do request.user)
            perfil_professor = professor_titular.perfil_professor 
            registro_professor, criado = RegistroChamadaProfessor.objects.update_or_create(
            chamada=chamada,  # Procura o registro pela 'chamada' (que é UNIQUE)
            defaults={'professor': perfil_professor} # Atualiza o professor se for diferente
        )
        except PerfilProfessor.DoesNotExist:
            professor_titular = None # Zera se o perfil não existir
    
    # 6. CRIAR O FORMSET DE ALUNOS (Igual antes)
    RegistroChamadaFormSet = modelformset_factory(RegistroChamada, form=RegistroChamadaForm, extra=0)

    # 7. PROCESSAR OS FORMULÁRIOS (SALVAR)
    if request.method == 'POST':
        queryset_alunos = RegistroChamada.objects.filter(chamada=chamada)
        formset_alunos = RegistroChamadaFormSet(request.POST, queryset=queryset_alunos, prefix='alunos')
        
        # Processa o form do professor apenas se ele existir
        if professor_titular:
            form_professor = RegistroChamadaProfessorForm(request.POST, instance=registro_professor, prefix='professor')
            
            if formset_alunos.is_valid() and form_professor.is_valid():
                formset_alunos.save()
                form_professor.save()
                return redirect('dashboard' if permissores['is_professor'] else 'relatorios')
        else:
            # Se não houver professor, só valida os alunos
            if formset_alunos.is_valid():
                formset_alunos.save()
                return redirect('dashboard' if permissores['is_professor'] else 'relatorios')
    
    # 8. EXIBIR OS FORMULÁRIOS (CARREGAMENTO INICIAL)
    else:
        queryset_alunos = RegistroChamada.objects.filter(chamada=chamada).select_related('aluno').order_by('aluno__nome_completo')
        formset_alunos = RegistroChamadaFormSet(queryset=queryset_alunos, prefix='alunos')
        
        # Cria o form do professor apenas se ele existir
        if professor_titular:
            form_professor = RegistroChamadaProfessorForm(instance=registro_professor, prefix='professor')

    # 8. ENVIAR TUDO PARA O TEMPLATE
    contexto = {
        'turma': turma,
        'professor_titular': professor_titular, # Envia o prof. da turma para o template
        'formset_alunos': formset_alunos,
        'form_professor': form_professor, # Pode ser None
        'data_selecionada_str': data_selecionada_str,
    }
    return render(request, 'chamada.html', contexto)

# core/views.py

@login_required
def pagina_relatorios(request):
    """
    (ETAPA 13 - ATUALIZADA)
    Esta é a view "Hub" do Supervisor.
    Ela NÃO busca dados, apenas renderiza o template dos CARDS.
    """
    permissores = permissoes_context(request)
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Esta página é apenas para supervisores.</p>")

    # Não precisa mais de contexto, só renderiza o HTML com os links
    return render(request, 'relatorios_hub.html')


@login_required
def meu_relatorio(request):
    """
    (ETAPA 11.4 - PONTO 5 - VERSÃO COMPLETA)
    Esta view mostra o relatório pessoal do aluno logado.
    Agora é trancada apenas para Alunos.
    """
    
    # --- INÍCIO DA ATUALIZAÇÃO (SEGURANÇA) ---
    permissores = permissoes_context(request)
    
    # SEGURANÇA: Só Alunos podem acessar
    if not permissores['is_aluno']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Esta página é apenas para alunos.</p>")
    
    # Tenta pegar o perfil do aluno logado
    try:
        aluno = request.user.aluno
    except Aluno.DoesNotExist:
        # Se o usuário não estiver linkado a um perfil 'Aluno', nega o acesso.
        return HttpResponseForbidden("<h1>Erro</h1><p>Seu usuário não está vinculado a um perfil de aluno.</p>")
    # --- FIM DA ATUALIZAÇÃO (SEGURANÇA) ---
    
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
    (ETAPA 11)
    Redireciona o usuário para o dashboard correto (Supervisor, Professor ou Aluno).
    """
    permissoes = permissoes_context(request) 

    # 1. Supervisor é enviado para os relatórios gerais
    if permissoes['is_supervisor']:
        return redirect('relatorios')
    
    # 2. Professor é enviado para suas turmas
    elif permissoes['is_professor']:
        return redirect('dashboard')
    
    # 3. Aluno é enviado para seu relatório pessoal
    elif permissoes['is_aluno']:
        return redirect('meu_relatorio')
    
    else:
        # Se não for nada, desloga (ou manda para o login)
        return redirect('login')

# core/views.py

@login_required
def detalhes_turma(request, turma_id):
    """
    (ETAPA 12 - ATUALIZADA)
    Mostra o ranking de alunos para uma turma.
    Acesso: Supervisor (qualquer turma) ou Professor (apenas sua turma).
    """
    permissores = permissoes_context(request)
    turma = get_object_or_404(Turma, id=turma_id)
    
    # --- INÍCIO DA ATUALIZAÇÃO DE SEGURANÇA ---
    acesso_permitido = False
    
    # Supervisores podem ver qualquer turma
    if permissores['is_supervisor']:
        acesso_permitido = True
    
    # Professores podem ver (apenas) suas próprias turmas
    elif permissores['is_professor'] and turma.professor == request.user:
        acesso_permitido = True
        
    if not acesso_permitido:
        return HttpResponseForbidden("<h1>Acesso Negado</h1>Você não tem permissão para ver esta turma.")
    # --- FIM DA ATUALIZAÇÃO DE SEGURANÇA ---

    # Se o acesso for permitido, busca os alunos
    ranking_alunos_turma = Aluno.objects.filter(turma=turma).order_by('-pontos_totais')
    
    contexto = {
        'turma': turma,
        'ranking_alunos_turma': ranking_alunos_turma,
    }
    
    return render(request, 'detalhes_turma.html', contexto)



@login_required
def meu_relatorio_professor(request):
    """
    (NOVA ETAPA 11)
    Esta view mostra o relatório pessoal do PROFESSOR logado.
    """
    permissoes = permissoes_context(request)
    
    # 1. SEGURANÇA: Só pode ser acessado por professores
    if not permissoes['is_professor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Esta página é apenas para professores.</p>")

    # 2. Busca o perfil e os registros
    try:
        perfil = request.user.perfil_professor
        registros = RegistroChamadaProfessor.objects.filter(professor=perfil).order_by('-chamada__data')
    except PerfilProfessor.DoesNotExist:
        return HttpResponseForbidden("<h1>Erro</h1><p>Seu perfil de professor não foi encontrado.</p>")
    
    # 3. Calcula estatísticas
    faltas = registros.filter(presenca=False).count()
    presencas = registros.filter(presenca=True).count()
    
    contexto = {
        'professor': request.user,
        'registros': registros,
        'faltas': faltas,
        'presencas': presencas,
        'pontos_totais': perfil.pontos_totais
    }
    return render(request, 'meu_relatorio_professor.html', contexto)

@login_required
def relatorio_aluno_individual(request, aluno_id):
    """
    (NOVA ETAPA 12)
    Mostra o relatório de um aluno específico.
    Acessível apenas por Supervisores.
    """
    permissores = permissoes_context(request)
    
    # SEGURANÇA: Só Supervisores
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem ver este relatório.</p>")

    # Busca o aluno pelo ID da URL
    aluno = get_object_or_404(Aluno, id=aluno_id)
    
    # O resto da lógica é igual ao 'meu_relatorio'
    registros = RegistroChamada.objects.filter(aluno=aluno).order_by('-chamada__data')
    faltas = registros.filter(presenca=False).count()
    presencas = registros.filter(presenca=True).count()
    
    contexto = {
        'aluno': aluno,
        'registros': registros,
        'faltas': faltas,
        'presencas': presencas,
        'pontos_totais': aluno.pontos_totais
    }
    # Reutiliza o template do aluno
    return render(request, 'meu_relatorio.html', contexto)

# core/views.py
# ... (outras views) ...

# -----------------------------------------------------------------
# ETAPA 13: NOVAS VIEWS DOS CARDS DO SUPERVISOR
# -----------------------------------------------------------------

@login_required
def relatorio_ranking_alunos(request):
    """Página 1: Mostra o Ranking Geral de Alunos."""
    permissores = permissoes_context(request)
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem ver este relatório.</p>")

    ranking_alunos_geral = Aluno.objects.all().order_by('-pontos_totais')[:20]
    contexto = {'ranking_alunos_geral': ranking_alunos_geral}
    return render(request, 'relatorios_ranking_alunos.html', contexto)

@login_required
def relatorio_ranking_turmas(request):
    """Página 2: Mostra o Ranking Geral de Turmas."""
    permissores = permissoes_context(request)
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem ver este relatório.</p>")

    ranking_turmas_geral = Turma.objects.annotate(
        pontuacao_media=Avg('alunos__pontos_totais')
    ).filter(pontuacao_media__gt=0).order_by('-pontuacao_media')
    contexto = {'ranking_turmas_geral': ranking_turmas_geral}
    return render(request, 'relatorios_ranking_turmas.html', contexto)

@login_required
def relatorio_ranking_professores(request):
    """Página 3: Mostra o Ranking Geral de Professores."""
    permissores = permissoes_context(request)
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem ver este relatório.</p>")

    ranking_professores = PerfilProfessor.objects.select_related('user').filter(
        pontos_totais__gt=0
    ).order_by('-pontos_totais')
    contexto = {'ranking_professores': ranking_professores}
    return render(request, 'relatorios_ranking_professores.html', contexto)

@login_required
def gerenciamento_turmas(request):
    """Página 4: Mostra a tabela de Gerenciamento de Turmas."""
    permissores = permissoes_context(request)
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem ver este relatório.</p>")

    lista_todas_turmas = Turma.objects.select_related('professor').all().order_by('nome')
    contexto = {'lista_todas_turmas': lista_todas_turmas}
    return render(request, 'gerenciamento_turmas.html', contexto)

@login_required
def gerenciamento_alunos(request):
    """Página 5: Mostra a tabela de Gerenciamento de Alunos."""
    permissores = permissoes_context(request)
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem ver este relatório.</p>")
        
    lista_todos_alunos = Aluno.objects.select_related('turma').all().order_by('nome_completo')
    contexto = {'lista_todos_alunos': lista_todos_alunos}
    return render(request, 'gerenciamento_alunos.html', contexto)