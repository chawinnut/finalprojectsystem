from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('authentication.urls')),
    path('database_search/', include('database_search.urls')),
    path('subscriptions/', include('database_subscription.urls', namespace='database_subscription')),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('financial/', include('financial_mnm.urls', namespace='financial_mnm')),
]