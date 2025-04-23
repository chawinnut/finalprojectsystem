from django.urls import path, reverse_lazy
from authentication import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('forgetpassword/', views.forgetpw, name='forget_password'),
    path(
        'accounts/login/',
        auth_views.LoginView.as_view(template_name='registration/login.html', success_url=reverse_lazy('home')),
        name='login'
    ),
    path('register/', views.register, name='register'),
    path(
        'password_reset/',
        auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
        name='password_reset'
    ),
    path(
        'password_reset/done/',
        auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
        name='password_reset_done'
    ),
    path(
        'password_reset/confirm/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
        name='password_reset_confirm'
    ),
    path(
        'password_reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
        name='password_reset_complete'
    ),
    path('verify_email/<str:token>/', views.verify_email, name='verify_email'),
    path('logout/', views.logout_view, name='logout'),
    path('set-renewal-reminder/', views.set_renewal_reminder, name='set_renewal_reminder'),
    path('hide-renewal-alert/', views.hide_renewal_alert, name='hide_renewal_alert'),
    path('logout/', views.logout_view, name='logout'),
]