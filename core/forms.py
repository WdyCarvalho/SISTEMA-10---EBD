# core/forms.py
from django import forms
from .models import Turma, RegistroChamada, RegistroChamadaProfessor, Aluno # Adicione Turma
from django.contrib.auth.models import User, Group # Adicione Group
from django.contrib.auth.forms import UserCreationForm # Importa o form base
from django.db import transaction # Para garantir a criação segura
from django.forms import ModelChoiceField # Para o dropdown de Turma




class RegistroChamadaForm(forms.ModelForm):

    """
    Este é o formulário para um ÚNICO registro de chamada.
    Vamos usá-lo para criar um 'FormSet' (um conjunto de formulários).
    """
    class Meta:
        model = RegistroChamada
        
        # Incluímos apenas os campos que o professor deve marcar
        fields = [
            'presenca', 
            'biblia', 
            'versiculo', 
            'convidado', 
            'oferta', 
            'atividades', 
            'revista'
        ]
        
        # Opcional: Remove os "labels" (nomes) de cada caixa
        # --- ATUALIZAÇÃO DOS WIDGETS (ETAPA 16) ---
        widgets = {
            'presenca': forms.CheckboxInput(attrs={'title': 'Presença', 'class': 'form-check-input'}),
            'biblia': forms.CheckboxInput(attrs={'title': 'Bíblia', 'class': 'form-check-input'}),
            'revista': forms.CheckboxInput(attrs={'title': 'Revista', 'class': 'form-check-input'}),
            'oferta': forms.CheckboxInput(attrs={'title': 'Oferta', 'class': 'form-check-input'}),
            'versiculo': forms.CheckboxInput(attrs={'title': 'Texto Bíblico', 'class': 'form-check-input'}),
            'atividades': forms.CheckboxInput(attrs={'title': 'Questionário', 'class': 'form-check-input'}),
            'convidado': forms.CheckboxInput(attrs={'title': 'Convidado', 'class': 'form-check-input'}),
        }


class RegistroChamadaProfessorForm(forms.ModelForm):
    """
    Este é o formulário para a chamada do professor.
    """
    class Meta:
        model = RegistroChamadaProfessor
        # Campos que o professor irá marcar
        fields = ['presenca', 'biblia', 'revista', 'oferta', 'convidado']
    

# =============================================
# === FORMULÁRIOS DE CADASTRO (ETAPA 17) ===
# =============================================
# core/forms.py

# START CHANGE: Substituir TurmaForm
class TurmaForm(forms.ModelForm):
    """
    Formulário para o Supervisor criar ou editar uma Turma.
    Atualizado para suportar múltiplos professores.
    """
    class Meta:
        model = Turma
        fields = ['nome', 'professores'] # Mude 'professor' para 'professores'

        # Usamos um SelectMultiple (caixa de seleção múltipla)
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex: Jovens, Casais...'}),
            'professores': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
        }
        labels = {
            'nome': 'Nome da Turma',
            'professores': 'Professores da Turma',
        }
        help_texts = {
            'professores': 'Segure Ctrl (ou Cmd) para selecionar mais de um professor.'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # A lógica de filtro agora se aplica a 'professores'
        try:
            professores_group = Group.objects.get(name='Professores')
            self.fields['professores'].queryset = User.objects.filter(groups=professores_group)
        except (Group.DoesNotExist, Exception):
            self.fields['professores'].queryset = User.objects.none()

        # Adiciona a classe 'form-control'
        for field_name, field in self.fields.items():
            if not isinstance(field.widget, forms.SelectMultiple):
                 field.widget.attrs.update({'class': 'form-control'})
# END CHANGE


class ProfessorUserCreationForm(UserCreationForm):
    """
    Formulário customizado para criar um Usuário e
    automaticamente adicioná-lo ao grupo 'Professores'.
    """
    # Adicionamos campos extras que não vêm no UserCreationForm padrão
    first_name = forms.CharField(max_length=150, required=False, label="Primeiro Nome")
    last_name = forms.CharField(max_length=150, required=False, label="Sobrenome")
    
    class Meta(UserCreationForm.Meta):
        # Usamos o modelo User padrão
        model = User
        # Definimos os campos que queremos no formulário
        fields = ("username", "first_name", "last_name")

    # Esta função é a mágica: ela é chamada DEPOIS que o User é salvo
    @transaction.atomic # Garante que ou tudo funciona ou nada é salvo
    def save(self, commit=True):
        user = super().save(commit=False) # Cria o User, mas não salva ainda
        
        # Salva os campos extras (first_name, last_name)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        
        if commit:
            user.save() # Agora salva o User no banco
            
            # Adiciona o usuário ao grupo 'Professores'
            try:
                professores_group = Group.objects.get(name='Professores')
                user.groups.add(professores_group)
            except Group.DoesNotExist:
                # Se o grupo não existir, podemos lançar um erro ou ignorar
                # (Aqui estamos ignorando, mas o ideal é garantir que o grupo exista)
                pass 
                
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona a classe 'form-control' a todos os campos
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

class AlunoUserCreationForm(UserCreationForm):
    """
    Formulário para criar um Usuário (login) E um Aluno (perfil)
    ao mesmo tempo, vinculando-os e associando a uma Turma.
    """
    # Campos do modelo Aluno
    nome_completo = forms.CharField(max_length=255, required=True, label="Nome Completo do Aluno")
    turma = ModelChoiceField(queryset=Turma.objects.all(), required=True, label="Turma")
    
    # Adicionamos first_name e last_name (opcional)
    first_name = forms.CharField(max_length=150, required=False, label="Primeiro Nome (Opcional)")
    last_name = forms.CharField(max_length=150, required=False, label="Sobrenome (Opcional)")

    class Meta(UserCreationForm.Meta):
        model = User
        # Campos do User + nossos campos extras
        fields = ("username", "first_name", "last_name", "nome_completo", "turma")
        field_order = ["username", "nome_completo", "turma", "first_name", "last_name"] # Ordem no form

        help_texts = {
            'username': 'Obrigatório. 150 caracteres ou menos. Letras, dígitos e @/./+/-/_ apenas.',
        }
        error_messages = {
            'password2': {
                'password_mismatch': ("As duas senhas não coincidem."),
            },
        }

    @transaction.atomic
    def save(self, commit=True):
        # 1. Cria o User (login)
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        
        if commit:
            user.save() # Salva o User
        
        # 2. Cria o Aluno (perfil) e o vincula
        aluno = Aluno.objects.create(
            user=user, # Vincula ao User que acabamos de criar
            nome_completo=self.cleaned_data["nome_completo"],
            turma=self.cleaned_data["turma"]
        )
        
        # Como o Aluno foi criado, o User não precisa ser salvo novamente
        return user # Retornamos o User, mas o Aluno também foi criado

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Adiciona classes CSS e ajusta dropdown
        self.fields['turma'].widget.attrs.update({'class': 'form-select'})
        for field_name, field in self.fields.items():
            if field_name != 'turma': # Evita sobrescrever o estilo do select
                 field.widget.attrs.update({'class': 'form-control'})

# core/forms.py
# ... (importações e outros forms) ...

class SupervisorUserCreationForm(UserCreationForm):
    """
    Formulário customizado para criar um Usuário e
    automaticamente adicioná-lo ao grupo 'Supervisores'.
    """
    first_name = forms.CharField(max_length=150, required=False, label="Primeiro Nome")
    last_name = forms.CharField(max_length=150, required=False, label="Sobrenome")
    
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name")

        help_texts = {
            'username': 'Obrigatório. 150 caracteres ou menos. Letras, dígitos e @/./+/-/_ apenas.',
        }
        error_messages = {
            'password2': {
                'password_mismatch': ("As duas senhas não coincidem."),
            },
        }

        help_texts = {
            'username': 'Obrigatório. 150 caracteres ou menos. Letras, dígitos e @/./+/-/_ apenas.',
            # Os textos de ajuda da senha vêm do Django, não precisam ser definidos aqui
            # a menos que você queira sobrescrever COMPLETAMENTE.
        }
        error_messages = {
            'password2': {
                'password_mismatch': ("As duas senhas não coincidem."),
            },
        }

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        
        if commit:
            user.save()
            
            # --- DIFERENÇA AQUI: Adiciona ao grupo 'Supervisores' ---
            try:
                supervisores_group = Group.objects.get(name='Supervisores')
                user.groups.add(supervisores_group)
            except Group.DoesNotExist:
                pass # Ignora se o grupo não existir
                
        return user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

# core/forms.py
# ...

class AlunoUserUpdateForm(forms.ModelForm):
    """
    Formulário para o Supervisor editar os dados de um Aluno (User + Aluno).
    NÃO inclui senha.
    """
    # Campos do modelo Aluno (pegamos do AlunoUserCreationForm)
    nome_completo = forms.CharField(max_length=255, required=True, label="Nome Completo do Aluno")
    turma = ModelChoiceField(queryset=Turma.objects.all(), required=True, label="Turma")

    # Campos do modelo User (sem senha)
    first_name = forms.CharField(max_length=150, required=False, label="Primeiro Nome")
    last_name = forms.CharField(max_length=150, required=False, label="Sobrenome")
    username = forms.CharField(max_length=150, required=True, label="Nome de usuário (Login)")

    class Meta:
        model = Aluno # O modelo principal é Aluno
        fields = ['nome_completo', 'turma'] # Campos diretos do Aluno

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se estamos editando (tem 'instance'), preenchemos os campos do User
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            # Torna o username não editável (geralmente boa prática)
            self.fields['username'].disabled = True 

        # Adiciona classes CSS
        self.fields['turma'].widget.attrs.update({'class': 'form-select'})
        for field_name, field in self.fields.items():
            if field_name != 'turma':
                 field.widget.attrs.update({'class': 'form-control'})

    @transaction.atomic
    def save(self, commit=True):
        aluno = super().save(commit=commit) # Salva o Aluno (nome_completo, turma)
        
        # Atualiza os dados do User associado
        user = aluno.user
        # O username não muda (está disabled)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            
        return aluno

class AlunoUserUpdateForm(forms.ModelForm):
    nome_completo = forms.CharField(max_length=255, required=True, label="Nome Completo do Aluno")
    turma = ModelChoiceField(queryset=Turma.objects.all(), required=True, label="Turma")
    first_name = forms.CharField(max_length=150, required=False, label="Primeiro Nome")
    last_name = forms.CharField(max_length=150, required=False, label="Sobrenome")
    username = forms.CharField(max_length=150, required=True, label="Nome de usuário (Login)")

    class Meta:
        model = Aluno
        fields = ['nome_completo', 'turma']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['username'].disabled = True

        self.fields['turma'].widget.attrs.update({'class': 'form-select'})
        for field_name, field in self.fields.items():
            # Aplica form-control a todos, exceto turma e username (que já tem estilo ou está disabled)
            if field_name not in ['turma', 'username']:
                 field.widget.attrs.update({'class': 'form-control'})
            # Garante que campos obrigatórios tenham o atributo
            if field.required:
                field.widget.attrs['required'] = 'required'

    @transaction.atomic
    def save(self, commit=True):
        aluno = super().save(commit=commit)
        user = aluno.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return aluno

class ProfessorUserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']
        labels = {
            'username': 'Nome de usuário (Login)',
            'first_name': 'Primeiro Nome',
            'last_name': 'Sobrenome',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].disabled = True
        for field_name, field in self.fields.items():
             # Aplica form-control a todos, exceto username (que está disabled)
            if field_name != 'username':
                field.widget.attrs.update({'class': 'form-control'})
            # Garante que campos obrigatórios tenham o atributo
            if field.required:
                field.widget.attrs['required'] = 'required'

