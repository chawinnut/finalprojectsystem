# database_search/urls.py
from django.urls import path
from . import views

app_name = 'database_search'

urlpatterns = [
    path('', views.database_search, name='database_search'),
]