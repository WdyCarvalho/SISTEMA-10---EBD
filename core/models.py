# core/models.py
from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum # Importamos o Sum para fazer somas

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
    def pontos_totais_turma(self):
        """Calcula o total de pontos de todos os alunos da turma."""
        # 'self.alunos' é o related_name que definimos no modelo Aluno
        total = self.alunos.aggregate(total_pontos=Sum('pontos_totais'))['total_pontos']
        return total or 0


class Aluno(models.Model):
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
    versiculo = models.BooleanField(default=False, verbose_name="Versículo")
    convidado = models.BooleanField(default=False, verbose_name="Convidado")
    oferta = models.BooleanField(default=False, verbose_name="Oferta")
    atividades = models.BooleanField(default=False, verbose_name="Atividades")
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
        
        self.pontos_ganhos = pontos

        # 2. Salva o registro atual no banco ANTES de atualizar o aluno
        # Usamos uma flag 'update_fields' para evitar um loop infinito
        super().save(*args, **kwargs)

        # 3. Atualizar o placar geral do aluno
        # Chamamos a função que recalcula o total a partir de todos os registros
        self.aluno.recalcular_pontos_totais()