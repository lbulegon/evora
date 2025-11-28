from django import forms
from django.contrib.auth.models import User
from .models import Evento, Cliente

class CadastroClienteForm(forms.ModelForm):
    """
    Formulário de cadastro APENAS para Clientes.
    Shoppers e Keepers são cadastrados via admin ou tokens.
    """
    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Senha',
        help_text='Mínimo de 8 caracteres'
    )
    telefone = forms.CharField(
        max_length=20,
        required=False,
        label='Telefone',
        help_text='Telefone de contato (opcional)'
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email', 'password']
        labels = {
            'first_name': 'Nome',
            'last_name': 'Sobrenome',
            'username': 'Nome de usuário',
            'email': 'Email',
        }
        help_texts = {
            'username': '150 caracteres ou menos. Letras, dígitos e @/./+/-/_ apenas.',
        }



class EventoAdminForm(forms.ModelForm):
    class Meta:
        model = Evento
        fields = '__all__'