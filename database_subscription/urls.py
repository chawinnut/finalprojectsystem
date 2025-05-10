from django.urls import path
from . import views

app_name = 'database_subscription'

urlpatterns = [
    path('', views.database_subscription_list, name='database_subscription_list'),
    path('create/', views.database_subscription_create, name='database_subscription_create'),
    path('update/<int:pk>/', views.database_subscription_update, name='database_subscription_update'),
    path('delete/<int:pk>/', views.database_subscription_delete, name='database_subscription_delete'),
    path('detail/<int:pk>/', views.database_subscription_detail, name='database_subscription_detail'),
    path('history/', views.database_subscription_history, name='database_subscription_history'),
    path('history/detail/<int:pk>/', views.database_subscription_history_detail, name='database_subscription_history_detail'),
    path('import/', views.import_subscriptions, name='import_subscriptions'),
    path('import/template/excel/', views.download_import_template_excel, name='download_import_template_excel'),
    path('import/template/csv/', views.download_import_template_csv, name='download_import_template_csv'),
]