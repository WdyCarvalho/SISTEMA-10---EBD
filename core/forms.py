# core/forms.py
from django import forms

from .models import RegistroChamada, RegistroChamadaProfessor

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