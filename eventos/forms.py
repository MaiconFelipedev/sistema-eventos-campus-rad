from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Atividade, Evento


class DateTimeLocalInput(forms.DateTimeInput):
    input_type = "datetime-local"


class CadastroForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class EventoForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = ["nome", "descricao", "data_inicio", "data_fim", "inscricoes_abertas"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 5}),
            "data_inicio": DateTimeLocalInput(format="%Y-%m-%dT%H:%M"),
            "data_fim": DateTimeLocalInput(format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["data_inicio"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["data_fim"].input_formats = ["%Y-%m-%dT%H:%M"]


class AtividadeForm(forms.ModelForm):
    class Meta:
        model = Atividade
        fields = ["titulo", "tipo", "descricao", "responsavel", "sala", "inicio", "fim"]
        widgets = {
            "descricao": forms.Textarea(attrs={"rows": 5}),
            "inicio": DateTimeLocalInput(format="%Y-%m-%dT%H:%M"),
            "fim": DateTimeLocalInput(format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, evento, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.evento = evento
        self.fields["inicio"].input_formats = ["%Y-%m-%dT%H:%M"]
        self.fields["fim"].input_formats = ["%Y-%m-%dT%H:%M"]
