from django import forms
from django.contrib.auth.models import User
from .models import Evento

class CadastroClienteForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']



class EventoAdminForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = '__all__'