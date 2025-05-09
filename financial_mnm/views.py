from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from .models import  CalendarEvent, FinancialManagement
from .forms import UploadFileForm, CalendarEventForm, AddBudgetForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.utils import timezone
from database_subscription.models import DatabaseSubscription
from django.db.models import Sum
from django.db.models import Q
from django.http import JsonResponse
from django.core.serializers import serialize
from django.conf import settings
from datetime import timedelta
from authentication.models import CustomUser

#from database_subscription.models import Vendor, Payment
#from database_subscription.forms import VendorForm, PaymentForm
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse

from collections import defaultdict

@login_required
def financial_report(request, budget_year):
    pass
    financial_data = FinancialManagement.objects.get(Budget_Year=budget_year)
    #total_spent = Payment.objects.filter(
       ###Payment_Date__year=budget_year, # กรองตามปีที่ชำระเงิน
        #payment_status='paid'
    #).aggregate(total=Sum('billing_amount'))['total'] or 0

    #remaining_budget = financial_data.Total_Budget - total_spent

    #context = {
    #    'financial_data': financial_data,
      ##  'remaining_budget': remaining_budget,
    #}
    #return render(request, 'financial_mnm/financial_report.html', context)

@login_required
def financial_management_list(request):
    current_year = timezone.now().year
    financial_records = FinancialManagement.objects.filter(Budget_Year=current_year).select_related('funder')

    financial_data = []
    for record in financial_records:
        # หา DatabaseSubscription ที่อาจเกี่ยวข้อง
        subscriptions = DatabaseSubscription.objects.filter(
            Q(subscription_start_date__year__lte=current_year) & Q(subscription_end_date__year__gte=current_year),
            Vendor_ID=record.vendor
        )
        db_names = [sub.DB_Name for sub in subscriptions]
        db_name_str = ", ".join(db_names) if db_names else "-"

        pass
    return render(request, 'financial_mnm/financial_management_list.html')

@login_required
def financial_details(request, fm_id):
    financial_record = get_object_or_404(FinancialManagement, pk=fm_id)
    current_year = timezone.now().year
    subscriptions = DatabaseSubscription.objects.filter(
        Q(subscription_start_date__year__lte=current_year) & Q(subscription_end_date__year__gte=current_year),
        funder=financial_record.funder,
        Vendor_ID=financial_record.vendor
    )
    #payments = Payment.objects.filter(
       #####'payments': payments,
    #return render(request, 'financial_mnm/financial_details.html', context)




@login_required
def import_data(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            upload_file = request.FILES['upload_file']
            # --- Logic สำหรับอ่านและบันทึกข้อมูลจากไฟล์ (Excel/CSV) ---
            # --- คุณจะต้องระบุรูปแบบไฟล์และ Fields ที่ต้องการนำเข้า ---
            messages.success(request, 'นำเข้าข้อมูลสำเร็จ!')
            return redirect('financial_mnm:some_list_view') # เปลี่ยน 'some_list_view'
        else:
            messages.error(request, 'เกิดข้อผิดพลาดในการอัปโหลดไฟล์')
    else:
        form = UploadFileForm()
    return render(request, 'financial_mnm/import_form.html', {'form': form, 'title': 'นำเข้าข้อมูล'})

import logging
logger = logging.getLogger(__name__)

@login_required
@permission_required('financial_mnm.view_dashboard')
def dashboard(request):
     try:
         current_year = timezone.now().year

         financial_year = FinancialManagement.objects.filter(Budget_Year=current_year).first()
         total_budget = financial_year.Total_Budget if financial_year else 0

         total_spent_current_year = DatabaseSubscription.objects.filter(renewal_year=current_year).aggregate(total_spent=Sum('amount_paid_thb'))['total_spent'] or 0

         remaining_budget = total_budget - total_spent_current_year

         renewal_alerts = []
         today = timezone.now().date()
         email_sent = set()

         database_subscriptions = DatabaseSubscription.objects.all() # ดึงข้อมูลฐานข้อมูลทั้งหมด
         database_subscriptions_grouped = defaultdict(list)
         for sub in database_subscriptions:
             sub.percentage_price_increase_thb_display = sub.percentage_price_increase_thb
             sub.percentage_price_increase_original_currency_display = sub.percentage_price_increase_original_currency
             database_subscriptions_grouped[sub.DB_Name].append(sub)

             if sub.renewal_date:
                 one_month_before = sub.renewal_date - timedelta(days=30)
                 three_months_before = sub.renewal_date - timedelta(days=90)
                 seven_days_before = sub.renewal_date - timedelta(days=7)

                 alert_data = {
                     'db_name': sub.DB_Name,
                     'end_date': sub.renewal_date,
                     'detail_url': reverse('database_subscription:database_subscription_detail', kwargs={'pk': sub.DS_ID}),
                     'alert_level': '',
                     'days_remaining': (sub.renewal_date - today).days,
                 }

                 recipient_emails = CustomUser.objects.filter(role__in=['admin', 'librarian']).values_list('email', flat=True)
                 recipient_list = list(recipient_emails)

                 if one_month_before <= today <= sub.renewal_date:
                     alert_data['alert_level'] = 'warning'
                     if one_month_before <= today < one_month_before + timedelta(days=1) and sub.DS_ID not in email_sent and recipient_list:
                         send_renewal_email_func(request, sub.DB_Name, sub.renewal_date, alert_data['days_remaining'], recipient_list)
                         email_sent.add(sub.DS_ID)
                 elif three_months_before <= today < one_month_before:
                     alert_data['alert_level'] = 'info'
                     if three_months_before <= today < three_months_before + timedelta(days=1) and sub.DS_ID not in email_sent and recipient_list:
                         send_renewal_email_func(request, sub.DB_Name, sub.renewal_date, alert_data['days_remaining'], recipient_list)
                         email_sent.add(sub.DS_ID)
                 elif seven_days_before <= today < one_month_before:
                     alert_data['alert_level'] = 'danger'
                     if seven_days_before <= today < seven_days_before + timedelta(days=1) and sub.DS_ID not in email_sent and recipient_list:
                         send_renewal_email_func(request, sub.DB_Name, sub.renewal_date, alert_data['days_remaining'], recipient_list)
                         email_sent.add(sub.DS_ID)

                 if alert_data['alert_level']:
                     renewal_alerts.append(alert_data)

         financial_records = FinancialManagement.objects.order_by('-Budget_Year')

         context = {
             'current_year': current_year,
             'total_budget': total_budget,
             'total_spent_current_year': total_spent_current_year,
             'remaining_budget': remaining_budget,
             'renewal_alerts': renewal_alerts,
             'financial_records': financial_records,
             'database_subscriptions_grouped': database_subscriptions_grouped,
         }
         return render(request, 'financial_mnm/dashboard.html', context)
     except Exception as e:
         import logging
         logger = logging.getLogger(__name__)
         logger.error(f"Error in dashboard view: {e}")
         return render(request, 'financial_mnm/error.html', {'error_message': 'เกิดข้อผิดพลาดในการแสดง Dashboard'})
     
@login_required
def database_price_history_detail_by_name(request, db_name):
    database_subscriptions = DatabaseSubscription.objects.filter(DB_Name=db_name).order_by('-renewal_year', '-subscription_start_date')
    context = {'database_subscriptions': database_subscriptions, 'db_name': db_name}
    return render(request, 'financial_mnm/database_price_history_detail.html', context)

@login_required
def database_price_history_detail(request, ds_id):
    database_subscription = get_object_or_404(DatabaseSubscription, pk=ds_id)
    price_history = []
    current_year = int(database_subscription.renewal_year) if database_subscription.renewal_year else timezone.now().year

    for year_offset in range(5):
        year = current_year - year_offset
        try:
            subscription_year = DatabaseSubscription.objects.get(DB_Name=database_subscription.DB_Name, renewal_year=str(year))
            price_history.append({
                'budget_year': subscription_year.renewal_year,
                'price': subscription_year.amount_original_currency,
                'currency': subscription_year.original_currency,
                'actual_cost_thb': subscription_year.amount_paid_thb,
            })
        except DatabaseSubscription.DoesNotExist:
            price_history.append({
                'budget_year': str(year),
                'price': None,
                'currency': database_subscription.original_currency,
                'actual_cost_thb': None,
            })
        except ValueError:
            pass

    for i in range(len(price_history) - 1, 0, -1):
        current_price = price_history[i]['price']
        previous_price = price_history[i - 1]['price']
        if current_price is not None and previous_price is not None and previous_price > 0 and price_history[i]['currency'] == price_history[i-1]['currency']:
            price_history[i]['percentage_increase'] = ((current_price - previous_price) / previous_price) * 100
        else:
            price_history[i]['percentage_increase'] = None

    price_history.reverse() # เรียงจากเก่าไปใหม่

    context = {
        'database_subscription': database_subscription,
        'price_history': price_history,
    }
    return render(request, 'financial_mnm/database_price_history_detail.html', context)

@login_required
@permission_required('financial_mnm.add_financialmanagement')
def add_budget(request):
    if request.method == 'POST':
        form = AddBudgetForm(request.POST)
        if form.is_valid():
            try:
                budget = form.save(commit=False)
                budget.Remaining_Budget = budget.Total_Budget
                budget.save()
                return redirect('financial_mnm:budget_list')
            except Exception as e:
                form.add_error(None, f"เกิดข้อผิดพลาดในการบันทึกงบประมาณ: {e}")
    else:
        form = AddBudgetForm()
    return render(request, 'financial_mnm/add_budget.html', {'form': form})

@login_required
def budget_list(request):
    financial_records = FinancialManagement.objects.order_by('-Budget_Year')
    budget_data = []

    for record in financial_records:
        total_spent = DatabaseSubscription.objects.filter(renewal_year=record.Budget_Year).aggregate(total_spent=Sum('amount_paid_thb'))['total_spent'] or 0
        remaining_budget = record.Total_Budget - total_spent
        budget_data.append({
            'year': record.Budget_Year,
            'total_budget': record.Total_Budget,
            'used_budget': total_spent,
            'remaining_budget': remaining_budget,
        })

    context = {
        'budget_data': budget_data,
    }
    return render(request, 'financial_mnm/budget_list.html', context)

@login_required
@permission_required('financial_mnm.change_financialmanagement')
def edit_budget(request, budget_year):
    financial_record = get_object_or_404(FinancialManagement, Budget_Year=budget_year)
    if request.method == 'POST':
        form = AddBudgetForm(request.POST, instance=financial_record)
        if form.is_valid():
            form.save()
            return redirect('financial_mnm:budget_list')
    else:
        form = AddBudgetForm(instance=financial_record)
    context = {'form': form, 'budget_year': budget_year}
    return render(request, 'financial_mnm/edit_budget.html', context)

@login_required
@permission_required('financial_mnm.delete_financialmanagement')
def delete_budget(request, budget_year):
    financial_record = get_object_or_404(FinancialManagement, Budget_Year=budget_year)
    if request.method == 'POST':
        financial_record.delete()
        return redirect('financial_mnm:budget_list')
    return render(request, 'financial_mnm/confirm_delete_budget.html', {'budget_year': budget_year})

def send_renewal_email_func(request, db_name, renewal_date, days_remaining, recipient_emails):
    subject = f"การแจ้งเตือนการต่ออายุสัญญาฐานข้อมูล: {db_name}"
    message = render_to_string('financial_mnm/renewal_email.html', {
        'db_name': db_name,
        'renewal_date': renewal_date.strftime('%d/%m/%Y'),
        'days_remaining': days_remaining,
    })
    from_email = settings.EMAIL_HOST_USER
    recipient_list = recipient_emails

    send_mail(subject, message, from_email, recipient_list, fail_silently=True, html_message=message)

@login_required
def calendar_create(request):
    if request.method == 'POST':
        form = CalendarEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user  # กำหนดผู้สร้างเป็นผู้ใช้ที่กำลังล็อกอิน
            event.save()
            return redirect('financial_mnm:calendar')
    else:
        form = CalendarEventForm()
    return render(request, 'financial_mnm/calendar_form.html', {'form': form, 'title': 'เพิ่มกำหนดการ'})

@login_required
def calendar_view(request):
    events = CalendarEvent.objects.filter(created_by=request.user).order_by('date', 'time') # หรือ Logic อื่นๆ
    return render(request, 'financial_mnm/calendar.html', {'events': events})

def calendar_update(request, pk):
    event = get_object_or_404(CalendarEvent, pk=pk)
    if request.method == 'POST':
        form = CalendarEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('financial_mnm:calendar')
    else:
        form = CalendarEventForm(instance=event)
    return render(request, 'financial_mnm/calendar_form.html', {'form': form, 'title': 'แก้ไขกำหนดการ'})

@login_required
def calendar_delete(request, pk):
    event = get_object_or_404(CalendarEvent, pk=pk)
    if request.method == 'POST':
        event.delete()
        return redirect('financial_mnm:calendar')
    return render(request, 'financial_mnm/calendar_confirm_delete.html', {'event': event})

@login_required
def calendar_events_json(request):
    events = CalendarEvent.objects.filter(created_by=request.user).values('title', 'date', 'time', 'id')
    event_list = []
    for event in events:
        event_list.append({
            'title': event['title'],
            'start': f"{event['date']}T{event['time'] if event['time'] else '00:00:00'}",
            'url': f"/financial/calendar/update/{event['id']}/" # URL สำหรับแก้ไข (สมมติว่ามี)
        })
    return JsonResponse(event_list, safe=False)



def send_renewal_email(request, db_name, renewal_date, days_remaining, recipient_email):
    subject = f"การแจ้งเตือนการต่ออายุสัญญาฐานข้อมูล: {db_name}"
    message = render_to_string('financial_mnm/renewal_email.html', {
        'db_name': db_name,
        'renewal_date': renewal_date,
        'days_remaining': days_remaining,
    })
    from_email = settings.EMAIL_HOST_USER
    recipient_list = [recipient_email]

    send_mail(subject, message, from_email, recipient_list, fail_silently=True, html_message=message)

@login_required
def calendar_create(request):
    if request.method == 'POST':
        form = CalendarEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user  # กำหนดผู้สร้างเป็นผู้ใช้ที่กำลังล็อกอิน
            event.save()
            return redirect('financial_mnm:calendar')
    else:
        form = CalendarEventForm()
    return render(request, 'financial_mnm/calendar_form.html', {'form': form, 'title': 'เพิ่มกำหนดการ'})

@login_required
def calendar_view(request):
    events = CalendarEvent.objects.filter(created_by=request.user).order_by('date', 'time') # หรือ Logic อื่นๆ
    return render(request, 'financial_mnm/calendar.html', {'events': events})

def calendar_update(request, pk):
    event = get_object_or_404(CalendarEvent, pk=pk)
    if request.method == 'POST':
        form = CalendarEventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            return redirect('financial_mnm:calendar')
    else:
        form = CalendarEventForm(instance=event)
    return render(request, 'financial_mnm/calendar_form.html', {'form': form, 'title': 'แก้ไขกำหนดการ'})

@login_required
def calendar_delete(request, pk):
    event = get_object_or_404(CalendarEvent, pk=pk)
    if request.method == 'POST':
        event.delete()
        return redirect('financial_mnm:calendar')
    return render(request, 'financial_mnm/calendar_confirm_delete.html', {'event': event})

@login_required
def calendar_events_json(request):
    events = CalendarEvent.objects.filter(created_by=request.user).values('title', 'date', 'time', 'id')
    event_list = []
    for event in events:
        event_list.append({
            'title': event['title'],
            'start': f"{event['date']}T{event['time'] if event['time'] else '00:00:00'}",
            'url': f"/financial/calendar/update/{event['id']}/" # URL สำหรับแก้ไข (สมมติว่ามี)
        })
    return JsonResponse(event_list, safe=False)

    
@login_required
@permission_required('financial_mnm.can_delete_all_financial_data') 
def delete_all_financial_data(request):
    if request.method == 'POST':
        FinancialManagement.objects.all().delete()
        return redirect('financial_mnm:financial_management_list') 
    else:
        return render(request, 'financial_mnm/confirm_delete_all_financial.html')
    
def send_renewal_email_func(request, db_name, renewal_date, days_remaining, recipient_emails):
    subject = f"การแจ้งเตือนการต่ออายุสัญญาฐานข้อมูล: {db_name}"
    message = render_to_string('financial_mnm/renewal_email.html', {
        'db_name': db_name,
        'renewal_date': renewal_date.strftime('%d/%m/%Y'),
        'days_remaining': days_remaining,
    })
    from_email = settings.EMAIL_HOST_USER
    recipient_list = recipient_emails

    send_mail(subject, message, from_email, recipient_list, fail_silently=True, html_message=message)