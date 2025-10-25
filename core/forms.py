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
        widgets = {
            'presenca': forms.CheckboxInput(attrs={'title': 'Presença'}),
            'biblia': forms.CheckboxInput(attrs={'title': 'Bíblia'}),
            'versiculo': forms.CheckboxInput(attrs={'title': 'Versículo'}),
            'convidado': forms.CheckboxInput(attrs={'title': 'Convidado'}),
            'oferta': forms.CheckboxInput(attrs={'title': 'Oferta'}),
            'atividades': forms.CheckboxInput(attrs={'title': 'Atividades'}),
            'revista': forms.CheckboxInput(attrs={'title': 'Revista'}),
        }


class RegistroChamadaProfessorForm(forms.ModelForm):
    """
    Este é o formulário para a chamada do professor.
    """
    class Meta:
        model = RegistroChamadaProfessor
        # Campos que o professor irá marcar
        fields = ['presenca', 'biblia', 'revista', 'oferta', 'convidado']