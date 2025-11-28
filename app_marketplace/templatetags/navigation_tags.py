"""
Template tags para navegação
Tags úteis para melhorar a navegabilidade
"""

from django import template

register = template.Library()


@register.simple_tag
def is_active_url(request, url_name):
    """
    Retorna 'active' se a URL atual corresponde ao url_name
    
    Uso no template:
    {% is_active_url request 'home' as active_class %}
    <a class="nav-link {{ active_class }}" href="{% url 'home' %}">Home</a>
    """
    try:
        if request.resolver_match.url_name == url_name:
            return 'active'
    except AttributeError:
        pass
    return ''


@register.simple_tag
def is_active_pattern(request, pattern):
    """
    Retorna 'active' se a URL atual contém o padrão
    
    Uso no template:
    {% is_active_pattern request 'shopper_' as active_class %}
    """
    try:
        if pattern in request.resolver_match.url_name:
            return 'active'
    except AttributeError:
        pass
    return ''


@register.inclusion_tag('app_marketplace/navigation/breadcrumbs.html', takes_context=True)
def show_breadcrumbs(context, *items):
    """
    Renderiza breadcrumbs customizados
    
    Uso no template:
    {% show_breadcrumbs 'Home' 'Dashboard' 'Detalhes' %}
    """
    return {
        'items': items,
        'request': context.get('request')
    }

