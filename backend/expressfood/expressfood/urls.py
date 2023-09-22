"""expressfood URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("admin/", admin.site.urls),

    #Gestion des utilisateurs
    path("login/", views.login, name="login"),
    path("register/", views.register, name="register"),
    path("users/", views.users, name="users"),

    #Gestion de la carte
    path("create_meal/", views.create_meal, name="create_meal"),
    path("daily_meals/", views.daily_meals, name="daily_meals"),
    path("daily_special/", views.daily_special, name="daily_special"),

    #Gestion des commandes
    path("all_order/", views.all_order, name="all_order"),
    path("order/", views.order, name="order"),
    path("pending_orders/", views.pending_orders, name="pending_orders"),
    path("prendre_en_charge/", views.prendre_en_charge, name="prendre_en_charge"),
    path("livraison_terminee/", views.livraison_terminee, name="livraison_terminee"),
    
]
