# database_search/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.database_search, name='database_search'),
]