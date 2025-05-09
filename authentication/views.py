from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
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
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import Group, Permission
from django.views.decorators.http import require_POST
import json
from .forms import UserEditForm
from django.contrib import messages

def user_login(request: HttpRequest):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    LoginHistory.objects.create(user=user, ip_address=request.META.get('REMOTE_ADDR'), user_agent=request.META.get('HTTP_USER_AGENT'))

                    request.session.pop('renewal_remind_until', None)

                    today = timezone.now().date()
                    one_month_ago = today - timedelta(days=30)
                    three_months_ago = today - timedelta(days=90)
                    one_month_ahead = today + timedelta(days=30)
                    three_months_ahead = today + timedelta(days=90)

                    expiring_renewals = DatabaseSubscription.objects.filter(
                        renewal_date__gte=one_month_ago,
                        renewal_date__lte=three_months_ahead
                    ).order_by('renewal_date')

                    warning_messages = []
                    for sub in expiring_renewals:
                        if sub.renewal_date:
                            time_difference = sub.renewal_date - today
                            if 0 <= time_difference.days <= 30:
                                message = f"กำหนดต่ออายุ '{sub.DB_Name}' ในอีก {time_difference.days} วัน ({sub.renewal_date.strftime('%d/%m/%Y')})"
                                warning_messages.append(message)
                            elif -30 <= time_difference.days < 0:
                                message = f"กำหนดต่ออายุ '{sub.DB_Name}' เมื่อ {-time_difference.days} วันที่ผ่านมา ({sub.renewal_date.strftime('%d/%m/%Y')})"
                                warning_messages.append(message)
                            elif 30 < time_difference.days <= 90:
                                message = f"กำหนดต่ออายุ '{sub.DB_Name}' ในอีกประมาณ 3 เดือน ({sub.renewal_date.strftime('%d/%m/%Y')})"
                                warning_messages.append(message)
                            elif -90 <= time_difference.days < -30:
                                message = f"กำหนดต่ออายุ '{sub.DB_Name}' เมื่อประมาณ {-time_difference.days // 30} เดือนที่ผ่านมา ({sub.renewal_date.strftime('%d/%m/%Y')})"
                                warning_messages.append(message)

                    if warning_messages:
                        request.session['renewal_warning'] = "\n".join(warning_messages)
                        request.session['renewal_acknowledged'] = False
                    else:
                        request.session.pop('renewal_warning', None)
                        request.session.pop('renewal_acknowledged', None)

                    return redirect('home')
                else:
                    return render(request, 'registration/account_inactive.html')
            else:
                form.add_error(None, 'ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง')
        else:
            pass
    else:
        form = AuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

@login_required
def home(request):
    name = request.user.username
    acc = request.user.groups.first().name if request.user.groups.exists() else "User"
    databases = DatabaseSubscription.objects.all().values('DB_Name', 'subscription_end_date', 'renewal_date')

    show_renewal_alert = False
    renewal_warning_list = []

    warning_message_str = request.session.get('renewal_warning')
    has_acknowledged = request.session.get('renewal_acknowledged', False)
    remind_until_str = request.session.get('renewal_remind_until')

    if warning_message_str:
        if remind_until_str == 'never':
            pass
        elif remind_until_str:
            try:
                remind_until = timezone.datetime.fromisoformat(remind_until_str)
                if timezone.now() >= remind_until:
                    renewal_warning_list = warning_message_str.split('\n')
                    show_renewal_alert = True
                else:
                    pass
            except ValueError:
                renewal_warning_list = warning_message_str.split('\n')
                show_renewal_alert = True
        elif not has_acknowledged:
            renewal_warning_list = warning_message_str.split('\n')
            show_renewal_alert = True
        else:
            pass
    else:
        pass

    print("home - show_renewal_alert:", show_renewal_alert)
    print("home - renewal_warning_list:", renewal_warning_list)
    print("home - renewal_remind_until:", remind_until_str)

    return render(request, "home.html", {
        "name": name,
        "acc": acc,
        "databases": databases,
        'show_renewal_alert': show_renewal_alert,
        'renewal_warning_list': renewal_warning_list,
    })
    

@login_required
@require_POST
def hide_renewal_alert(request):
    request.session['renewal_acknowledged'] = True
    return redirect('home')

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
            send_mail(mail_subject, message, settings.DEFAULT_FROM_EMAIL, [to_email]) # แทนที่ด้วยอีเมลผู้ส่งจริง

            return render(request, 'registration/register_email_sent.html') # แสดงหน้าแจ้งว่าส่งอีเมลยืนยันแล้ว
    else:
        form = CustomUserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

def verify_email(request, token):
    try:
        user = CustomUser.objects.get(email_verification_token=token)
        user.is_email_verified = True
        user.is_active = True
        user.email_verification_token = None
        user.save()
        return render(request, 'registration/email_verified.html')
    except CustomUser.DoesNotExist:
        return render(request, 'registration/email_verification_failed.html')

@login_required
@require_POST
def set_renewal_reminder(request):
    try:
        data = json.loads(request.body)
        delay_str = data.get('delay')
        if delay_str:
            if delay_str == 'never':
                request.session['renewal_remind_until'] = 'never'
                return JsonResponse({'success': True})
            else:
                try:
                    delay = float(delay_str)
                    remind_until = timezone.now() + timedelta(hours=delay)
                    request.session['renewal_remind_until'] = remind_until.isoformat()
                    return JsonResponse({'success': True})
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid delay value'})
        else:
            return JsonResponse({'success': False, 'error': 'Delay not provided'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})

def logout_view(request):
    logout(request)
    return render(request, 'registration/logged_out.html')


# ส่วนที่ให้ head lib จัดการ role และ access ของคนอื่น ๆ

@login_required
def user_management_list(request):
    if request.user.groups.filter(name='super_librarian').exists():
        users = CustomUser.objects.all().order_by('username')
        return render(request, 'authentication/user_management_list.html', {'users': users})
    else:
        return render(request, 'permission_denied.html')

@login_required
def user_management_edit(request, user_id):
    user_to_edit = get_object_or_404(CustomUser, id=user_id)
    if request.user.groups.filter(name='super_librarian').exists():
        if request.method == 'POST':
            form = UserEditForm(request.POST, instance=user_to_edit)
            if form.is_valid():
                user = form.save()
                selected_groups = request.POST.getlist('groups')
                user.groups.set(selected_groups)
                return redirect('user_management_list')
        else:
            form = UserEditForm(instance=user_to_edit)
            groups = Group.objects.all()
            return render(request, 'authentication/user_management_edit.html', {'form': form, 'user': user_to_edit, 'groups': groups})
    else:
        return render(request, 'permission_denied.html')

@login_required
def group_management_list(request):
    if request.user.groups.filter(name='super_librarian').exists():
        groups = Group.objects.all().order_by('name')
        return render(request, 'authentication/group_management_list.html', {'groups': groups})
    else:
        return render(request, 'permission_denied.html')

@login_required
def group_management_edit(request, group_id):
    group_to_edit = get_object_or_404(Group, id=group_id)
    if request.user.groups.filter(name='super_librarian').exists():
        if request.method == 'POST':
            group_name = request.POST.get('name')
            selected_permissions = request.POST.getlist('permissions')
            group_to_edit.name = group_name
            group_to_edit.permissions.set(selected_permissions)
            group_to_edit.save()
            return redirect('group_management_list')
        else:
            permissions = Permission.objects.all().order_by('name')
            return render(request, 'authentication/group_management_edit.html', {'group': group_to_edit, 'permissions': permissions})
    else:
        return render(request, 'permission_denied.html')
    
from .forms import GroupCreationForm

@login_required
@permission_required('auth.add_group', raise_exception=True)
def group_management_create(request):
    if request.method == 'POST':
        form = GroupCreationForm(request.POST)
        if form.is_valid():
            group_name = form.cleaned_data['name']
            new_group = Group.objects.create(name=group_name)
            # ถ้าใช้ ModelForm โดยตรง การบันทึกจะง่ายกว่า:
            # new_group = form.save()
            return redirect('group_management_list')
    else:
        form = GroupCreationForm()
    return render(request, 'authentication/group_management_create.html', {'form': form})

@login_required
@permission_required('auth.delete_group', raise_exception=True)
def group_management_delete(request, group_id):
    group_to_delete = get_object_or_404(Group, id=group_id)
    if request.method == 'POST':
        group_to_delete.delete()
        messages.success(request, f'กลุ่ม "{group_to_delete.name}" ถูกลบแล้ว')
        return redirect('group_management_list')
    return render(request, 'authentication/group_management_delete.html', {'group': group_to_delete})