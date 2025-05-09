# financial_mnm/urls.py
from django.urls import path
from . import views

app_name = 'financial_mnm'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('list/', views.financial_management_list, name='financial_management_list'),
    path('details/<int:fm_id>/', views.financial_details, name='financial_details'),
    path('add/', views.add_budget, name='add_budget'),
    path('budget/', views.budget_list, name='budget_list'),
    path('budget/edit/<int:budget_year>/', views.edit_budget, name='edit_budget'),
    path('budget/delete/<int:budget_year>/', views.delete_budget, name='delete_budget'),
    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/create/', views.calendar_create, name='calendar_create'),
    path('calendar/update/<int:pk>/', views.calendar_update, name='calendar_update'),
    path('calendar/delete/<int:pk>/', views.calendar_delete, name='calendar_delete'),
    path('calendar/events/', views.calendar_events_json, name='calendar_events_json'),
    path('', views.dashboard, name='financial_dashboard_root'),
    path('database/price-history/<str:db_name>/', views.database_price_history_detail_by_name, name='database_price_history_detail_by_name'),
]