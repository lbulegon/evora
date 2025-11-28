from django import forms
from django.contrib.auth.models import User
from .models import Evento, Cliente, PublicacaoAgora

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


class PpaBulkUpdateForm(forms.Form):
    """Formulário para atualização de PPA em lote"""
    evento = forms.ModelChoiceField(
        queryset=Evento.objects.all(),
        required=False,
        label='Evento/Campanha',
        help_text='Filtrar por evento específico (opcional)'
    )
    mesh_type = forms.ChoiceField(
        choices=[('', 'Todos')] + list(PublicacaoAgora.TipoMesh.choices),
        required=False,
        label='Tipo de Mesh',
        help_text='Filtrar por tipo de mesh (opcional)'
    )
    ppa_value = forms.DecimalField(
        max_digits=3,
        decimal_places=2,
        min_value=0.0,
        max_value=1.0,
        label='Valor PPA',
        help_text='Valor PPA (0.0 a 1.0)'
    )
    apply_mode = forms.ChoiceField(
        choices=[
            ('set', 'Definir (substituir valor)'),
            ('increment', 'Incrementar (+valor)'),
            ('decrement', 'Decrementar (-valor)'),
        ],
        label='Modo de Aplicação',
        help_text='Como aplicar o valor PPA'
    )
    only_zero = forms.BooleanField(
        required=False,
        label='Apenas PPA = 0',
        help_text='Aplicar apenas em publicações com PPA = 0.0'
    )