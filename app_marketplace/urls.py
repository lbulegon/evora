from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('cadastro/', views.cadastro, name='cadastro'),
    path('login/', views.login_view, name='login'),  # nova rota
    path('home/', views.home_view, name='home'),
    path('logout/', views.logout_view, name='logout'),

    
    path('clientes/', views.clientes, name='clientes'),
    path('personal_shoppers/', views.personal_shoppers, name='personal_shoppers'),
    path('pedidos/', views.pedidos, name='pedidos'),
  
]