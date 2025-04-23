from django.urls import path
from . import views

app_name = 'financial_mnm'

urlpatterns = [
    path('vendors/', views.vendor_list, name='vendor_list'),
    path('vendors/create/', views.vendor_create, name='vendor_create'),
    path('vendors/<int:pk>/edit/', views.vendor_update, name='vendor_update'),
    path('vendors/<int:pk>/delete/', views.vendor_delete, name='vendor_delete'),
    path('funders/', views.funder_list, name='funder_list'),
    path('funders/create/', views.funder_create, name='funder_create'),
    path('funders/<int:pk>/edit/', views.funder_update, name='funder_update'),
    path('funders/<int:pk>/delete/', views.funder_delete, name='funder_delete'),
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/create/', views.payment_create, name='payment_create'),
    path('payments/<int:pk>/edit/', views.payment_update, name='payment_update'),
    path('payments/<int:pk>/delete/', views.payment_delete, name='payment_delete'),
    path('import/', views.import_data, name='import_data'),

    # URLs สำหรับ Dashboard และรายการจัดการการเงิน
    path('financial/dashboard/', views.dashboard, name='financial_dashboard'),
    path('financial/list/', views.financial_management_list, name='financial_management_list'),
    path('financial/details/<int:fin_mnm_id>/', views.financial_details, name='financial_details'),

    # URL สำหรับหน้า Dashboard หลัก (อาจใช้เป็นหน้าแรกของส่วน financial ก็ได้)
    path('financial/', views.dashboard, name='financial_management_root'),

    # URL สำหรับ Dashboard ที่ Root (ถ้าต้องการให้ dashboard เป็นหน้าแรก)
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.dashboard, name='financial_dashboard_default'),  # default - ใช้ชื่อนี้ใน home.html (เปลี่ยนชื่อให้สื่อถึง default)

    path('calendar/', views.calendar_view, name='calendar'),
    path('calendar/create/', views.calendar_create, name='calendar_create'),
    path('calendar/update/<int:pk>/', views.calendar_update, name='calendar_update'),
    path('calendar/delete/<int:pk>/', views.calendar_delete, name='calendar_delete'),
    path('calendar/events/', views.calendar_events_json, name='calendar_events_json'), # เพิ่ม URL นี้
]