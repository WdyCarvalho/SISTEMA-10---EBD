# core/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum, Count

from django.db.models.signals import post_save
from django.dispatch import receiver

# -----------------------------------------------------------------------------
# MODELOS PRINCIPAIS (Turma, Aluno)
# -----------------------------------------------------------------------------

class Turma(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    professor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='turmas_lecionadas'
    )

    def __str__(self):
        return f"Turma: {self.nome}"

    @property
    def pontuacao_media_turma(self):
        """Calcula a pontuação MÉDIA da turma."""

        # Usamos aggregate para pegar a Soma e a Contagem
        dados = self.alunos.aggregate(
            total_pontos=Sum('pontos_totais'),
            num_alunos=Count('id')
        )

        total_pontos = dados['total_pontos'] or 0
        num_alunos = dados['num_alunos'] or 0

        # Evita erro de divisão por zero se a turma não tiver alunos
        if num_alunos == 0:
            return 0

        # Retorna a média
        return total_pontos / num_alunos


class Aluno(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='aluno', # Permite fazer request.user.aluno
        null=True, 
        blank=True
    )
    nome_completo = models.CharField(max_length=255)
    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name='alunos'
    )
    pontos_totais = models.IntegerField(default=0)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome_completo} ({self.turma.nome})"
    
    def recalcular_pontos_totais(self):
        """
        Função que recalcula o total de pontos do aluno 
        somando todos os 'pontos_ganhos' dos seus registros.
        """
        total = self.registros_de_chamada.aggregate(total=Sum('pontos_ganhos'))['total']
        self.pontos_totais = total or 0
        self.save(update_fields=['pontos_totais']) # Salva apenas este campo para evitar loops

# -----------------------------------------------------------------------------
# MODELOS DE CHAMADA (Chamada, RegistroChamada)
# -----------------------------------------------------------------------------

class Chamada(models.Model):
    turma = models.ForeignKey(Turma, on_delete=models.CASCADE, related_name='chamadas')
    data = models.DateField()
    criado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ('turma', 'data')

    def __str__(self):
        return f"Chamada de {self.turma.nome} - {self.data.strftime('%d/%m/%Y')}"

# core/models.py

class RegistroChamada(models.Model):
    chamada = models.ForeignKey(Chamada, on_delete=models.CASCADE, related_name='registros')
    aluno = models.ForeignKey(Aluno, on_delete=models.CASCADE, related_name='registros_de_chamada')

    presenca = models.BooleanField(default=False, verbose_name="Presença")
    biblia = models.BooleanField(default=False, verbose_name="Bíblia")
    versiculo = models.BooleanField(default=False, verbose_name="Texto Bíblico")
    convidado = models.BooleanField(default=False, verbose_name="Convidado")
    oferta = models.BooleanField(default=False, verbose_name="Oferta")
    atividades = models.BooleanField(default=False, verbose_name="Questionário")
    revista = models.BooleanField(default=False, verbose_name="Revista") # <-- ADICIONE ESTA LINHA

    pontos_ganhos = models.IntegerField(default=0)

    def __str__(self):
        return f"Registro: {self.aluno.nome_completo} ({self.chamada.data.strftime('%d/%m/%Y')})"

    # --- A MÁGICA ACONTECE AQUI! ---
    def save(self, *args, **kwargs):
        # 1. Calcular os pontos ganhos neste registro específico
        pontos = 0
        if self.presenca: pontos += 1
        if self.biblia: pontos += 1
        if self.versiculo: pontos += 1
        if self.convidado: pontos += 1
        if self.oferta: pontos += 1
        if self.atividades: pontos += 1
        if self.revista: pontos += 1  # <-- ESTA É A LINHA DA CORREÇÃO
        
        self.pontos_ganhos = pontos

        # 2. Salva o registro atual no banco ANTES de atualizar o aluno
        super().save(*args, **kwargs)

        # 3. Atualizar o placar geral do aluno
        # Chamamos a função que recalcula o total a partir de todos os registros
        self.aluno.recalcular_pontos_totais()


class PerfilProfessor(models.Model):
    """
    Armazena o placar total de pontos do professor.
    É ligado ao Usuário (login) do professor.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil_professor'
    )
    pontos_totais = models.IntegerField(default=0)

    class Meta:
        verbose_name = "Perfil de Professor"
        verbose_name_plural = "Perfis de Professor"

    def __str__(self):
        return f"Perfil de {self.user.username}"
    
    def recalcular_pontos_totais(self):
        """
        Recalcula o total de pontos somando todos os registros de chamada.
        """
        total = self.registros_de_chamada.aggregate(total=Sum('pontos_ganhos'))['total']
        self.pontos_totais = total or 0
        self.save(update_fields=['pontos_totais'])

# --- Função Bônus: Cria um Perfil automaticamente quando um User é salvo ---
# Isso facilita nossa vida, pois não precisamos criar no admin manualmente
@receiver(post_save, sender=User)
def criar_ou_atualizar_perfil_professor(sender, instance, created, **kwargs):
    """
    Se um novo Usuário for criado, cria um PerfilProfessor para ele.
    """
    if created:
        PerfilProfessor.objects.create(user=instance)
    else:
        # Se o usuário for salvo (mas não criado), apenas garante que o perfil exista
        PerfilProfessor.objects.get_or_create(user=instance)


# -----------------------------------------------------------------------------
# MODELO 2: O REGISTRO DIÁRIO DA CHAMADA DO PROFESSOR
# -----------------------------------------------------------------------------
class RegistroChamadaProfessor(models.Model):
    """
    Armazena os critérios da chamada do professor para um dia específico.
    """
    chamada = models.OneToOneField(
        Chamada,
        on_delete=models.CASCADE,
        related_name='registro_professor'
    )
    # O professor que fez a chamada (ligado ao perfil dele)
    professor = models.ForeignKey(
        PerfilProfessor,
        on_delete=models.CASCADE,
        related_name='registros_de_chamada'
    )
    
    # Critérios de pontuação
    presenca = models.BooleanField(default=False, verbose_name="Presença")
    biblia = models.BooleanField(default=False, verbose_name="Bíblia")
    revista = models.BooleanField(default=False, verbose_name="Revista")
    oferta = models.BooleanField(default=False, verbose_name="Oferta")
    convidado = models.BooleanField(default=False, verbose_name="Convidado")

    pontos_ganhos = models.IntegerField(default=0)

    def __str__(self):
        return f"Registro Prof. {self.professor.user.username} - {self.chamada.data}"

    def save(self, *args, **kwargs):
        # 1. Calcula os pontos ganhos neste dia
        pontos = 0
        if self.presenca: pontos += 1
        if self.biblia: pontos += 1
        if self.revista: pontos += 1
        if self.oferta: pontos += 1
        if self.convidado: pontos += 1
        
        self.pontos_ganhos = pontos
        
        # 2. Salva o registro atual
        super().save(*args, **kwargs)

        # 3. Atualiza o placar geral do professor
        self.professor.recalcular_pontos_totais()