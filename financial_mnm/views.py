from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Vendor, Funder, Payment, CalendarEvent
from .forms import VendorForm, FunderForm, PaymentForm, UploadFileForm, CalendarEventForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.utils import timezone
from database_subscription.models import DatabaseSubscription, UsageStatistics
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from .models import FinancialManagement
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.core.serializers import serialize
from django.conf import settings


# Create your views here.
@login_required
def financial_management_list(request):
    current_year = timezone.now().year
    database_subscriptions = DatabaseSubscription.objects.filter(
        subscription_start_date__year__lte=current_year,
        subscription_end_date__year__gte=current_year
    ).select_related('FinMnm_ID__Vendor_ID') # เอา 'FinMnm_ID__Funder_ID' ออก

    financial_data = []
    for sub in database_subscriptions:
        latest_usage = UsageStatistics.objects.filter(
            database_subscription=sub,
            year=current_year
        ).aggregate(Sum('Usage_Count'))['Usage_Count__sum'] or 0

        latest_payment = Payment.objects.filter(
            database_subscription=sub
        ).order_by('-Payment_Date').first()
        payment_status = latest_payment.Payment_Status if latest_payment else "รอข้อมูล"

        vendor_name = sub.FinMnm_ID.Vendor_ID.Vendor_Name if sub.FinMnm_ID and sub.FinMnm_ID.Vendor_ID else '-'

        financial_data.append({
            'db_name': sub.DB_Name,
            'vendor': vendor_name,
            'subscription_period': f"{sub.subscription_start_date} - {sub.subscription_end_date}" if sub.subscription_start_date and sub.subscription_end_date else '-',
            'usage_last_year': latest_usage,
            'payment_status': payment_status,
            'negotiation_process': sub.FinMnm_ID.Negotiation_Details if sub.FinMnm_ID else '-',
            'perpetual_license': sub.FinMnm_ID.Perpetual_License if sub.FinMnm_ID else False,
            'usage_terms': sub.FinMnm_ID.Usage_Terms if sub.FinMnm_ID else '-',
            'details_link': f"/financial/details/{sub.FinMnm_ID}/",
        })

    context = {
        'financial_data': financial_data,
        'current_year': current_year,
    }
    return render(request, 'financial_mnm/financial_management_list.html', context)

@login_required
def financial_details(request, fin_mnm_id):
    subscription = get_object_or_404(DatabaseSubscription, FinMnm_ID=fin_mnm_id)
    context = {
        'subscription': subscription,
    }
    return render(request, 'financial_mnm/financial_details.html', context)

# --- Views สำหรับ Vendor ---
@login_required
def vendor_list(request):
    vendors = Vendor.objects.all().order_by('Vendor_Name')
    paginator = Paginator(vendors, 10)
    page = request.GET.get('page')
    try:
        vendors = paginator.page(page)
    except PageNotAnInteger:
        vendors = paginator.page(1)
    except EmptyPage:
        vendors = paginator.page(paginator.num_pages)
    return render(request, 'financial_mnm/vendor_list.html', {'vendors': vendors})

@login_required
def vendor_create(request):
    if request.method == 'POST':
        form = VendorForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มผู้ขายสำเร็จ!')
            return redirect('financial_mnm:vendor_list')
    else:
        form = VendorForm()
    return render(request, 'financial_mnm/vendor_form.html', {'form': form, 'title': 'เพิ่มผู้ขาย'})

@login_required
def vendor_update(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        form = VendorForm(request.POST, instance=vendor)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขข้อมูลผู้ขายสำเร็จ!')
            return redirect('financial_mnm:vendor_list')
    else:
        form = VendorForm(instance=vendor)
    return render(request, 'financial_mnm/vendor_form.html', {'form': form, 'title': 'แก้ไขผู้ขาย'})

@login_required
def vendor_delete(request, pk):
    vendor = get_object_or_404(Vendor, pk=pk)
    if request.method == 'POST':
        vendor.delete()
        messages.success(request, 'ลบผู้ขายสำเร็จ!')
        return redirect('financial_mnm:vendor_list')
    return render(request, 'financial_mnm/vendor_confirm_delete.html', {'vendor': vendor})

# --- Views สำหรับ Funder ---
@login_required
def funder_list(request):
    funders = Funder.objects.all().order_by('Funder_Name')
    paginator = Paginator(funders, 10)
    page = request.GET.get('page')
    try:
        funders = paginator.page(page)
    except PageNotAnInteger:
        funders = paginator.page(1)
    except EmptyPage:
        funders = paginator.page(paginator.num_pages)
    return render(request, 'financial_mnm/funder_list.html', {'funders': funders})

@login_required
def funder_create(request):
    if request.method == 'POST':
        form = FunderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มผู้ให้ทุนสำเร็จ!')
            return redirect('financial_mnm:funder_list')
    else:
        form = FunderForm()
    return render(request, 'financial_mnm/funder_form.html', {'form': form, 'title': 'เพิ่มผู้ให้ทุน'})

@login_required
def funder_update(request, pk):
    funder = get_object_or_404(Funder, pk=pk)
    if request.method == 'POST':
        form = FunderForm(request.POST, instance=funder)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขข้อมูลผู้ให้ทุนสำเร็จ!')
            return redirect('financial_mnm:funder_list')
    else:
        form = FunderForm(instance=funder)
    return render(request, 'financial_mnm/funder_form.html', {'form': form, 'title': 'แก้ไขผู้ให้ทุน'})

@login_required
def funder_delete(request, pk):
    funder = get_object_or_404(Funder, pk=pk)
    if request.method == 'POST':
        funder.delete()
        messages.success(request, 'ลบผู้ให้ทุนสำเร็จ!')
        return redirect('financial_mnm:funder_list')
    return render(request, 'financial_mnm/funder_confirm_delete.html', {'funder': funder})

# --- Views สำหรับ Payment ---
@login_required
def payment_list(request):
    payments = Payment.objects.all().order_by('-Payment_Date')
    paginator = Paginator(payments, 10)
    page = request.GET.get('page')
    try:
        payments = paginator.page(page)
    except PageNotAnInteger:
        payments = paginator.page(1)
    except EmptyPage:
        payments = paginator.page(paginator.num_pages)
    return render(request, 'financial_mnm/payment_list.html', {'payments': payments})

@login_required
def payment_create(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มรายการชำระเงินสำเร็จ!')
            return redirect('financial_mnm:payment_list')
    else:
        form = PaymentForm()
    return render(request, 'financial_mnm/payment_form.html', {'form': form, 'title': 'เพิ่มรายการชำระเงิน'})

@login_required
def payment_update(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        form = PaymentForm(request.POST, request.FILES, instance=payment)
        if form.is_valid():
            form.save()
            messages.success(request, 'แก้ไขรายการชำระเงินสำเร็จ!')
            return redirect('financial_mnm:payment_list')
    else:
        form = PaymentForm(instance=payment)
    return render(request, 'financial_mnm/payment_form.html', {'form': form, 'title': 'แก้ไขรายการชำระเงิน'})

@login_required
def payment_delete(request, pk):
    payment = get_object_or_404(Payment, pk=pk)
    if request.method == 'POST':
        payment.delete()
        messages.success(request, 'ลบรายการชำระเงินสำเร็จ!')
        return redirect('financial_mnm:payment_list')
    return render(request, 'financial_mnm/payment_confirm_delete.html', {'payment': payment})

# --- View สำหรับนำเข้าข้อมูล (อาจรวม Vendor, Funder, Payment ใน View เดียว หรือแยก) ---
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

# --- View สำหรับหน้าภาพรวม (Dashboard) ---
@login_required
def dashboard(request):
    current_year = timezone.now().year
    database_subscriptions = DatabaseSubscription.objects.filter(
        subscription_start_date__year__lte=current_year,
        subscription_end_date__year__gte=current_year
    ).select_related('FinMnm_ID')  # ดึงข้อมูล FinancialManagement ที่เกี่ยวข้อง

    dashboard_data = []
    for sub in database_subscriptions:
        financial_record = sub.FinMnm_ID
        vendor = financial_record.vendor.Vendor_Name if financial_record and hasattr(financial_record, 'vendor') and financial_record.vendor else '-'
        funder = financial_record.funder.Funder_Name if financial_record and hasattr(financial_record, 'funder') and financial_record.funder else '-'
        subscription_period = f"{sub.subscription_start_date} - {sub.subscription_end_date}" if sub.subscription_start_date and sub.subscription_end_date else '-'

        total_usage = UsageStatistics.objects.filter(
            database_subscription=sub,
            year=current_year
        ).aggregate(Sum('Usage_Count'))['Usage_Count__sum'] or 0

        latest_payment_status = "รอชำระ"  # ปรับตาม Logic การชำระเงินจริงของคุณ

        dashboard_data.append({
            'database_name': sub.DB_Name,
            'funder': funder,
            'vendor': vendor,
            'subscription_period': subscription_period,
            'usage_last_year': total_usage,
            'payment_status': latest_payment_status,
            'fin_mnm_id': sub.FinMnm_ID.FinMnm_ID if sub.FinMnm_ID else None,
        })

    # สรุปงบประมาณ (ตัวอย่าง - ปรับตาม Model Funder และ Logic การใช้จ่ายจริง)
    total_budget = Funder.objects.aggregate(Sum('Funder_Budget'))['Funder_Budget__sum'] or 0.00
    total_spent = 0.00  # คุณจะต้องดึงข้อมูลการใช้จ่ายจริงจาก Model Payment หรือ FinancialManagement
    remaining_budget = total_budget - total_spent

    # การแจ้งเตือนต่ออายุสัญญา (ตัวอย่าง - กำหนดเกณฑ์การแจ้งเตือน)
    renewal_alerts = DatabaseSubscription.objects.filter(
        subscription_end_date__lte=timezone.now() + timezone.timedelta(days=30)  # แจ้งเตือนเมื่อสัญญาใกล้หมดใน 30 วัน
    ).values('DB_Name', 'subscription_end_date')

    context = {
        'dashboard_data': dashboard_data,
        'current_year': current_year,
        'total_budget': total_budget,
        'total_spent': total_spent,
        'remaining_budget': remaining_budget,
        'renewal_alerts': renewal_alerts,
    }
    return render(request, 'financial_mnm/dashboard.html', context)

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
def calendar_view(request):
    events = CalendarEvent.objects.filter(created_by=request.user).order_by('date', 'time')
    return render(request, 'financial_mnm/calendar.html', {'events': events})

@login_required
def calendar_create(request):
    if request.method == 'POST':
        form = CalendarEventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.created_by = request.user
            event.save()
            return redirect('financial_mnm:calendar')
    else:
        form = CalendarEventForm()
    return render(request, 'financial_mnm/calendar_form.html', {'form': form, 'title': 'เพิ่มกำหนดการ'})

@login_required
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