# core/views.py

from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages # Importe o sistema de mensagens
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory # Importamos o "criador de super-formulários"
from django.db import transaction
from django.db.models import Sum, Avg, Count
from .models import Turma, Aluno, Chamada, RegistroChamada, User, PerfilProfessor, RegistroChamadaProfessor
from .forms import RegistroChamadaForm, RegistroChamadaProfessorForm, TurmaForm, ProfessorUserCreationForm, AlunoUserCreationForm, SupervisorUserCreationForm, AlunoUserUpdateForm, ProfessorUserUpdateForm
from datetime import date # Para pegar a data de hoje
from .context_processors import permissoes_context # Importe a função que criamos


from django.urls import reverse_lazy # Para redirects após deletar
from django.views.generic import UpdateView, DeleteView # Views genéricas
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin # Para segurança em Class-Based Views


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

# core/views.py
# ... (outras views) ...

@login_required
def relatorio_professor_individual(request, professor_user_id):
    """
    (NOVA ETAPA 14)
    Mostra o relatório de um professor específico (pelo ID do User).
    Acessível apenas por Supervisores.
    """
    permissores = permissoes_context(request)
    
    # SEGURANÇA: Só Supervisores
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem ver este relatório.</p>")

    # Busca o usuário do professor
    professor_user = get_object_or_404(User, id=professor_user_id)
    
    try:
        # Pega o perfil e os registros
        perfil = professor_user.perfil_professor
        registros = RegistroChamadaProfessor.objects.filter(professor=perfil).order_by('-chamada__data')
    except PerfilProfessor.DoesNotExist:
        return HttpResponseForbidden("<h1>Erro</h1><p>O perfil deste professor não foi encontrado.</p>")
    
    # Calcula estatísticas
    faltas = registros.filter(presenca=False).count()
    presencas = registros.filter(presenca=True).count()
    
    contexto = {
        'professor': professor_user, # Passa o User do professor
        'registros': registros,
        'faltas': faltas,
        'presencas': presencas,
        'pontos_totais': perfil.pontos_totais
    }
    
    # Reutiliza o template que já criamos!
    return render(request, 'meu_relatorio_professor.html', contexto)

# core/views.py
# ... (outras views) ...

@login_required
def gerenciamento_professores(request):
    """
    (NOVA ETAPA 14)
    Mostra a lista de todos os professores para o Supervisor.
    """
    permissores = permissoes_context(request)
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem ver este relatório.</p>")

    # Busca todos os Usuários que estão no grupo "Professores"
    # e já pega seus perfis (pontos) e turmas (prefetch)
    lista_professores = User.objects.filter(
        groups__name='Professores'
    ).select_related(
        'perfil_professor'
    ).prefetch_related(
        'turmas_lecionadas' # O related_name que demos no modelo Turma
    ).order_by('username')

    contexto = {'lista_professores': lista_professores}
    return render(request, 'gerenciamento_professores.html', contexto)

@login_required
def pagina_cadastros(request):
    """
    (NOVA ETAPA 17)
    Mostra o hub de opções de cadastro (Turma, Professor, Aluno).
    Acessível apenas por Supervisores.
    """
    permissores = permissoes_context(request)
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem ver esta página.</p>")

    return render(request, 'cadastros_hub.html')

@login_required
def cadastrar_turma(request):
    """
    (NOVA ETAPA 17)
    View para o Supervisor criar uma nova turma.
    """
    permissores = permissoes_context(request)
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem ver esta página.</p>")

    if request.method == 'POST':
        form = TurmaForm(request.POST)
        if form.is_valid():
            turma = form.save()
            # Adiciona uma mensagem de sucesso
            messages.success(request, f"A turma '{turma.nome}' foi criada com sucesso!")
            return redirect('gerenciamento_turmas') # Redireciona para a lista de turmas
    else:
        form = TurmaForm()

    contexto = {
        'form': form,
        'form_title': 'Cadastrar Nova Turma' # Título para o template genérico
    }
    return render(request, 'form_generico.html', contexto)

@login_required
def cadastrar_professor(request):
    """
    (NOVA ETAPA 17)
    View para o Supervisor criar um novo Professor (Usuário).
    """
    permissores = permissoes_context(request)
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem ver esta página.</p>")

    if request.method == 'POST':
        form = ProfessorUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # Salva o usuário e o adiciona ao grupo
            messages.success(request, f"O professor '{user.username}' foi criado com sucesso!")
            # Redireciona para a lista de gerenciamento de professores
            return redirect('gerenciamento_professores') 
    else:
        form = ProfessorUserCreationForm()

    contexto = {
        'form': form,
        'form_title': 'Cadastrar Novo Professor' 
    }
    return render(request, 'form_generico.html', contexto)

@login_required
def cadastrar_aluno(request):
    """
    (NOVA ETAPA 17)
    View para o Supervisor criar um novo Aluno (User + Aluno).
    """
    permissores = permissoes_context(request)
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem ver esta página.</p>")

    if request.method == 'POST':
        form = AlunoUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # Salva o User E cria o Aluno vinculado
            messages.success(request, f"O aluno '{user.username}' foi criado e vinculado com sucesso!")
            # Redireciona para a lista de gerenciamento de alunos
            return redirect('gerenciamento_alunos')
    else:
        form = AlunoUserCreationForm()

    contexto = {
        'form': form,
        'form_title': 'Cadastrar Novo Aluno'
    }
    return render(request, 'form_generico.html', contexto)

@login_required
def cadastrar_supervisor(request):
    """
    (NOVA ETAPA 17)
    View para o Supervisor criar um novo Supervisor (Usuário).
    """
    permissores = permissoes_context(request)
    if not permissores['is_supervisor']:
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem ver esta página.</p>")

    if request.method == 'POST':
        form = SupervisorUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save() # Salva o usuário e o adiciona ao grupo
            messages.success(request, f"O supervisor '{user.username}' foi criado com sucesso!")
            # Podemos redirecionar para o Hub de Cadastros ou Gerenciamento de Supervisores (se criarmos)
            return redirect('pagina_cadastros') 
    else:
        form = SupervisorUserCreationForm()

    contexto = {
        'form': form,
        'form_title': 'Cadastrar Novo Supervisor' 
    }
    return render(request, 'form_generico.html', contexto)

# core/views.py
# ... (outras views) ...

# --- NOVAS VIEWS (ETAPA 17 - COMPLEMENTO) ---

# Mixin de Segurança para Supervisores em Class-Based Views
class SupervisorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        # Reutiliza nossa função de permissão
        return permissoes_context(self.request)['is_supervisor']

    def handle_no_permission(self):
        return HttpResponseForbidden("<h1>Acesso Negado</h1><p>Apenas supervisores podem acessar esta página.</p>")

# View para Editar Turma
class TurmaUpdateView(SupervisorRequiredMixin, UpdateView):
    model = Turma
    form_class = TurmaForm # Reutiliza o formulário que já temos
    template_name = 'form_generico.html' # Reutiliza o template genérico
    success_url = reverse_lazy('gerenciamento_turmas') # Para onde ir após salvar

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Editar Turma: {self.object.nome}' # Título dinâmico
        return context

    def form_valid(self, form):
        messages.success(self.request, f"A turma '{form.instance.nome}' foi atualizada com sucesso!")
        return super().form_valid(form)

# View para Apagar Turma
class TurmaDeleteView(SupervisorRequiredMixin, DeleteView):
    model = Turma
    template_name = 'confirmar_apagamento.html' # Template de confirmação (vamos criar)
    success_url = reverse_lazy('gerenciamento_turmas')

    def form_valid(self, form):
        turma_nome = self.object.nome
        messages.success(self.request, f"A turma '{turma_nome}' foi apagada com sucesso!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_nome'] = self.object.nome
        context['tipo_item'] = 'turma'
        return context

# core/views.py
# ...

# View para Editar Aluno
class AlunoUpdateView(SupervisorRequiredMixin, UpdateView):
    model = Aluno
    form_class = AlunoUserUpdateForm # Usa o novo formulário de edição
    template_name = 'form_generico.html'
    success_url = reverse_lazy('gerenciamento_alunos')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Editar Aluno: {self.object.nome_completo}'
        return context
        
    def form_valid(self, form):
        messages.success(self.request, f"Os dados do aluno '{form.instance.nome_completo}' foram atualizados com sucesso!")
        return super().form_valid(form)

# View para Apagar Aluno (Apaga o Aluno E o User associado)
class AlunoDeleteView(SupervisorRequiredMixin, DeleteView):
    model = Aluno
    template_name = 'confirmar_apagamento.html'
    success_url = reverse_lazy('gerenciamento_alunos')

    @transaction.atomic
    def form_valid(self, form):
        aluno_nome = self.object.nome_completo
        user_associado = self.object.user # Pega o User antes de apagar o Aluno
        
        # Primeiro, apaga o Aluno (que apaga o RegistroChamada via CASCADE)
        response = super().form_valid(form) 
        
        # Depois, apaga o User associado (se existir)
        if user_associado:
            user_associado.delete()
            
        messages.success(self.request, f"O aluno '{aluno_nome}' e seu usuário foram apagados com sucesso!")
        return response
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_nome'] = self.object.nome_completo
        context['tipo_item'] = 'aluno (e seu usuário associado)'
        return context

class ProfessorUpdateView(SupervisorRequiredMixin, UpdateView):
    model = User
    form_class = ProfessorUserUpdateForm # Usa o novo form de edição
    template_name = 'form_generico.html'
    success_url = reverse_lazy('gerenciamento_professores')

    def get_queryset(self):
        # Garante que só podemos editar usuários do grupo Professores
        professores_group = Group.objects.get(name='Professores')
        return User.objects.filter(groups=professores_group)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_title'] = f'Editar Professor: {self.object.username}'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Os dados do professor '{form.instance.username}' foram atualizados com sucesso!")
        return super().form_valid(form)
    
class ProfessorDeleteView(SupervisorRequiredMixin, DeleteView):
    model = User
    template_name = 'confirmar_apagamento.html'
    success_url = reverse_lazy('gerenciamento_professores')

    def get_queryset(self):
        # Garante que só podemos apagar usuários do grupo Professores
        professores_group = Group.objects.get(name='Professores')
        return User.objects.filter(groups=professores_group)

    @transaction.atomic # Garanta que 'transaction' está importado no topo
    def form_valid(self, form):
        professor_username = self.object.username
        # O on_delete=SET_NULL em Turma e CASCADE em PerfilProfessor cuidam das relações
        response = super().form_valid(form) # Apaga o User
        messages.success(self.request, f"O professor '{professor_username}' foi apagado com sucesso!")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['item_nome'] = self.object.username
        context['tipo_item'] = 'professor (o usuário de login)'
        context['aviso_extra'] = 'As turmas que este professor lecionava ficarão sem professor titular.'
        return context