from django.shortcuts import render, redirect
from django.http import HttpRequest, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm
from django import forms
from django.core.mail import send_mail
from django.urls import reverse
import uuid
from django.contrib.sites.shortcuts import get_current_site
from .models import LoginHistory, CustomUser
from .forms import CustomUserCreationForm
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from database_subscription.models import DatabaseSubscription
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json

def home(request):
    name = "Admin"
    acc = "account"
    show_popup = request.session.pop('show_renewal_popup', False)
    warning_message_str = request.session.pop('renewal_warning', None)
    remind_until_str = request.session.get('renewal_remind_until')
    show_alert = False
    warning_messages_list = []

    if show_popup and warning_message_str:
        warning_messages_list = warning_message_str.split('\n')

        if remind_until_str and remind_until_str != 'never':
            try:
                remind_until = timezone.datetime.fromisoformat(remind_until_str).date()
                if timezone.now().date() >= remind_until:
                    show_alert = True
                else:
                    show_alert = False
            except ValueError:
                # กรณี Parse วันที่ผิดพลาด ให้แสดง Alert
                show_alert = True
        elif remind_until_str is None:
            show_alert = True

    return render(request, "home.html", {"name": name, "acc": acc, 'show_alert': show_alert, 'renewal_warning_list': warning_messages_list})

def createaccount(request):
    return render(request, "createacc.html")

def forgetpw(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=settings.DEFAULT_FROM_EMAIL,
                email_template_name='registration/password_reset_email.html',
                subject_template_name='registration/password_reset_subject.txt',
            )
            return render(request, 'registration/password_reset_done.html')
    else:
        form = PasswordResetForm()

    return render(request, 'registration/forgetpw.html', {'form': form})

from django.views.decorators.http import require_POST
import json

def user_login(request: HttpRequest):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = request.POST.get('rememberMe')  # ตรวจสอบว่า Checkbox ถูกเลือกหรือไม่
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    LoginHistory.objects.create(
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT')
                    )

                    if remember_me:
                        # ตั้งค่า Session ให้หมดอายุในระยะยาว (ตัวอย่าง: 1 สัปดาห์)
                        request.session.set_expiry(60 * 60 * 24 * 7)  # 7 วัน
                    else:
                        # ตั้งค่า Session ให้หมดอายุเมื่อ Browser ปิด (ค่าเริ่มต้น)
                        request.session.set_expiry(0)

                    request.session.pop('renewal_remind_until', None)

                    today = timezone.now().date()
                    three_months_ahead = today + timedelta(days=90)
                    one_month_ahead = today + timedelta(days=30)
                    expiring_subscriptions = DatabaseSubscription.objects.filter(
                        subscription_end_date__lte=three_months_ahead,
                        subscription_end_date__gte=today
                    ).order_by('subscription_end_date')

                    warning_messages = []
                    for sub in expiring_subscriptions:
                        if sub.subscription_end_date <= one_month_ahead:
                            warning_messages.append(f"สัญญา '{sub.DB_Name}' กำลังจะหมดอายุใน 1 เดือน ({sub.subscription_end_date.strftime('%d/%m/%Y')})")
                        elif sub.subscription_end_date <= three_months_ahead:
                            warning_messages.append(f"สัญญา '{sub.DB_Name}' กำลังจะหมดอายุใน 3 เดือน ({sub.subscription_end_date.strftime('%d/%m/%Y')})")

                    if warning_messages:
                        request.session['renewal_warning'] = "\n".join(warning_messages)
                        request.session['show_renewal_popup'] = True
                    else:
                        request.session.pop('renewal_warning', None)
                        request.session.pop('show_renewal_popup', None)

                    return redirect('home')
                else:
                    return render(request, 'registration/account_inactive.html')
            else:
                pass
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})
    
def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email_verification_token = uuid.uuid4().hex
            user.is_active = False  # ตั้งค่าเป็นไม่ Active จนกว่าจะยืนยันอีเมล
            user.save()

            current_site = get_current_site(request)
            mail_subject = 'ยืนยันอีเมลของคุณ'
            verify_url = reverse('verify_email', kwargs={'token': user.email_verification_token})
            message = f'คลิกที่ลิงก์นี้เพื่อยืนยันอีเมลของคุณ: http://{current_site.domain}{verify_url}'
            to_email = form.cleaned_data.get('email')
            send_mail(mail_subject, message, 'your_email@example.com', [to_email]) # แทนที่ด้วยอีเมลผู้ส่งจริง

            return render(request, 'registration/register_email_sent.html') # แสดงหน้าแจ้งว่าส่งอีเมลยืนยันแล้ว
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def verify_email(request, token):
    print(f"Token ที่ได้รับใน verify_email: {token}")
    try:
        user = CustomUser.objects.get(email_verification_token=token)
        print(f"พบผู้ใช้: {user.username}, Token ใน DB: {user.email_verification_token}")
        user.is_email_verified = True
        user.is_active = True
        user.email_verification_token = None
        user.save()
        return render(request, 'registration/email_verified.html')
    except CustomUser.DoesNotExist:
        print(f"ไม่พบ Token: {token} ในฐานข้อมูล")
        return render(request, 'registration/email_verification_failed.html')

def user_login(request: HttpRequest):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = request.POST.get('rememberMe')  #จดจำฉัน
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    LoginHistory.objects.create(
                        user=user,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT')
                    )

                    if remember_me:
                        request.session.set_expiry(60 * 60 * 24 * 7)
                    else:
                        request.session.set_expiry(0)

                    request.session.pop('renewal_remind_until', None)

                    today = timezone.now().date()
                    three_months_ahead = today + timedelta(days=90)
                    one_month_ahead = today + timedelta(days=30)
                    expiring_subscriptions = DatabaseSubscription.objects.filter(
                        subscription_end_date__lte=three_months_ahead,
                        subscription_end_date__gte=today
                    ).order_by('subscription_end_date')

                    warning_messages = []
                    for sub in expiring_subscriptions:
                        if sub.subscription_end_date <= one_month_ahead:
                            warning_messages.append(f"การบอกรับฐานข้อมูล '{sub.DB_Name}' กำลังจะหมดอายุใน 1 เดือน ({sub.subscription_end_date.strftime('%d/%m/%Y')})")
                        elif sub.subscription_end_date <= three_months_ahead:
                            warning_messages.append(f"การบอกรับฐานข้อมูล '{sub.DB_Name}' กำลังจะหมดอายุใน 3 เดือน ({sub.subscription_end_date.strftime('%d/%m/%Y')})")

                    if warning_messages:
                        request.session['renewal_warning'] = "\n".join(warning_messages)
                        request.session['show_renewal_popup'] = True
                    else:
                        request.session.pop('renewal_warning', None)
                        request.session.pop('show_renewal_popup', None)

                    return redirect('home')
                else:
                    return render(request, 'registration/account_inactive.html')
            else:
                pass
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

@login_required
@require_POST
def set_renewal_reminder(request):
    try:
        data = json.loads(request.body)
        delay = data.get('delay')
        if delay:
            if delay == '1 hour':
                remind_until = timezone.now() + timedelta(hours=1)
            elif delay == 'today':
                remind_until = timezone.now().replace(hour=23, minute=59, second=59)
            elif delay == 'never':
                request.session['renewal_remind_until'] = 'never'
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': 'Invalid delay'})

            request.session['renewal_remind_until'] = remind_until.isoformat()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Delay not provided'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})

def logout_view(request):
    logout(request)
    return render(request, 'registration/logged_out.html')

@login_required
@require_POST
def hide_renewal_alert(request):
    request.session['show_alert'] = False
    return redirect('home')