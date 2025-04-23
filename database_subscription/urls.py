from django.urls import path
from . import views

app_name = 'database_subscription'

urlpatterns = [
    path('list/', views.database_subscription_list, name='database_subscription_list'),
    path('create/', views.database_subscription_create, name='subscription_create'),
    path('update/<int:pk>/', views.database_subscription_update, name='subscription_update'),
    path('delete/<int:pk>/', views.database_subscription_delete, name='subscription_delete'),
    path('archive/<int:pk>/', views.subscription_archive, name='subscription_archive'),
    path('archives/all/', views.all_subscription_archives, name='all_subscription_archives'),
    path('import/excel/', views.import_subscriptions, name='import_subscription_excel'),
    path('usage/list/', views.usage_statistics_list, name='usage_statistics_list'),
    path('usage/create/', views.usage_statistics_create, name='usage_statistics_create'),
    path('usage/edit/<int:pk>/', views.usage_statistics_edit, name='usage_statistics_edit'),
    path('usage/delete/<int:pk>/', views.usage_statistics_delete, name='usage_statistics_delete'),
    path('usage/archive/<int:pk>/', views.usage_statistics_archive, name='usage_statistics_archive'),
    path('usage/import/', views.import_usage_statistics, name='import_usage_statistics'),
]