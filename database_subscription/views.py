from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .forms import DatabaseSubscriptionForm, UploadUsageStatisticsForm, ImportFileForm, UsageStatisticsForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.utils import timezone
import pandas as pd
from .models import DatabaseSubscription, UsageStatistics, FinancialManagement, DatabaseSubscriptionArchive, UsageStatisticsArchive
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import DatabaseSubscriptionArchive

@login_required
def database_subscription_list(request):
    current_year = timezone.now().year
    subscriptions = DatabaseSubscription.objects.filter(
        subscription_start_date__year__lte=current_year,
        subscription_end_date__year__gte=current_year
    ).order_by('DB_Name')
    paginator = Paginator(subscriptions, 10)
    page = request.GET.get('page')
    try:
        subscriptions = paginator.page(page)
    except PageNotAnInteger:
        subscriptions = paginator.page(1)
    except EmptyPage:
        subscriptions = paginator.page(paginator.num_pages)
    return render(request, 'database_subscription/database_subscription_list.html', {'subscriptions': subscriptions})

@login_required
def database_subscription_create(request):
    if request.method == 'POST':
        form = DatabaseSubscriptionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มฐานข้อมูลที่บอกรับสำเร็จ!')
            return redirect('database_subscription:database_subscription_list')
    else:
        form = DatabaseSubscriptionForm()
    return render(request, 'database_subscription/database_subscription_form.html', {'form': form, 'title': 'เพิ่มฐานข้อมูลที่บอกรับ'})

@login_required
def database_subscription_update(request, pk):
    subscription = get_object_or_404(DatabaseSubscription, pk=pk)
    if request.method == 'POST':
        form = DatabaseSubscriptionForm(request.POST, instance=subscription)
        if form.is_valid():
            # สร้าง Archive ก่อน Save การเปลี่ยนแปลง
            DatabaseSubscriptionArchive.objects.create(
                database_subscription=subscription,
                DB_Name=subscription.DB_Name,
                DB_Collection=subscription.DB_Collection,
                DBJournal_List=subscription.DBJournal_List,
                DBEBook_List=subscription.DBEBook_List,
                subscription_start_date=subscription.subscription_start_date,
                subscription_end_date=subscription.subscription_end_date,
                renewal_date=subscription.renewal_date,
                FinMnm_ID=subscription.FinMnm_ID
            )
            form.save()
            messages.success(request, 'แก้ไขข้อมูลฐานข้อมูลที่บอกรับสำเร็จ!')
            return redirect('database_subscription:database_subscription_list')
    else:
        form = DatabaseSubscriptionForm(instance=subscription)
    return render(request, 'database_subscription/database_subscription_form.html', {'form': form, 'title': 'แก้ไขฐานข้อมูลที่บอกรับ'})

@login_required
def database_subscription_delete(request, pk):
    subscription = get_object_or_404(DatabaseSubscription, pk=pk)
    if request.method == 'POST':
        subscription.delete()
        messages.success(request, 'ลบฐานข้อมูลที่บอกรับสำเร็จ!')
        return redirect('database_subscription:database_subscription_list')
    return render(request, 'database_subscription/database_subscription_confirm_delete.html', {'subscription': subscription})

@login_required
def import_usage_statistics(request):
    if request.method == 'POST':
        form = UploadUsageStatisticsForm(request.POST, request.FILES)
        if form.is_valid():
            upload_file = request.FILES['upload_file']
            try:
                df = pd.read_excel(upload_file)  # รองรับไฟล์ Excel (.xlsx, .xls)
            except Exception as e:
                try:
                    df = pd.read_csv(upload_file)  # รองรับไฟล์ CSV
                except Exception as e:
                    messages.error(request, f'ไม่สามารถอ่านไฟล์ได้: {e}')
                    return render(request, 'database_subscription/import_usage_statistics_form.html', {'form': form, 'title': 'นำเข้าสถิติการใช้งาน'})

            imported_count = 0
            error_count = 0

            # คาดหวังว่าไฟล์จะมี Columns: database_name, usage_count, usage_type, usage_historydate, year
            for index, row in df.iterrows():
                try:
                    database_name = row['database_name']
                    usage_count = int(row['usage_count'])
                    usage_type = row['usage_type']
                    usage_historydate = pd.to_datetime(row['usage_historydate'])
                    year = int(row['year'])

                    try:
                        database = DatabaseSubscription.objects.get(DB_Name=database_name)
                        UsageStatistics.objects.create(
                            database_subscription=database,
                            Usage_Count=usage_count,
                            Usage_Type=usage_type,
                            Usage_HistoryDate=usage_historydate,
                            year=year
                        )
                        imported_count += 1
                    except DatabaseSubscription.DoesNotExist:
                        messages.error(request, f'ไม่พบฐานข้อมูล "{database_name}" ในระบบ')
                        error_count += 1
                    except Exception as e:
                        messages.error(request, f'เกิดข้อผิดพลาดในการบันทึกข้อมูลแถวที่ {index + 2}: {e}')
                        error_count += 1

                except KeyError as e:
                    messages.error(request, f'ไฟล์ไม่ถูกต้อง ขาด Column: {e}')
                    return render(request, 'database_subscription/import_usage_statistics_form.html', {'form': form, 'title': 'นำเข้าสถิติการใช้งาน'})
                except ValueError as e:
                    messages.error(request, f'ข้อมูลไม่ถูกต้องในแถวที่ {index + 2}: {e}')
                    error_count += 1

            messages.success(request, f'นำเข้าข้อมูลสถิติการใช้งานสำเร็จ {imported_count} รายการ พบข้อผิดพลาด {error_count} รายการ')
            return redirect('database_subscription:database_subscription_list')
        else:
            messages.error(request, 'เกิดข้อผิดพลาดในการอัปโหลดไฟล์')
    else:
        form = UploadUsageStatisticsForm()
    return render(request, 'database_subscription/import_usage_statistics_form.html', {'form': form, 'title': 'นำเข้าสถิติการใช้งาน'})

@login_required
def subscription_archive(request, pk):
    database_subscription = get_object_or_404(DatabaseSubscription, pk=pk)
    archives = DatabaseSubscriptionArchive.objects.filter(database_subscription=database_subscription).order_by('-archived_at')
    return render(request, 'database_subscription/subscription_archive.html', {'database_subscription': database_subscription, 'archives': archives})

@login_required
def import_subscriptions(request):
    if request.method == 'POST' and request.FILES['excel_file']:
        excel_file = request.FILES['excel_file']
        try:
            df = pd.read_excel(excel_file)
            imported_count = 0
            error_count = 0
            for index, row in df.iterrows():
                try:
                    fin_mnm = FinancialManagement.objects.get(FinMnm_ID=row['FinMnm_ID']) # สมมติว่ามี column นี้
                    DatabaseSubscription.objects.create(
                        DB_Name=row['DB_Name'],
                        DB_Collection=row.get('DB_Collection', None),
                        DBJournal_List=row.get('DBJournal_List', None),
                        DBEBook_List=row.get('DBEBook_List', None),
                        subscription_start_date=pd.to_datetime(row['subscription_start_date']).date() if pd.notnull(row['subscription_start_date']) else None,
                        subscription_end_date=pd.to_datetime(row['subscription_end_date']).date() if pd.notnull(row['subscription_end_date']) else None,
                        renewal_date=pd.to_datetime(row['renewal_date']).date() if pd.notnull(row['renewal_date']) else None,
                        FinMnm_ID=fin_mnm
                    )
                    imported_count += 1
                except FinancialManagement.DoesNotExist:
                    messages.error(request, f"ไม่พบ FinMnm_ID: {row['FinMnm_ID']} ในไฟล์ Excel บรรทัดที่ {index + 2}")
                    error_count += 1
                    continue
                except Exception as e:
                    messages.error(request, f"เกิดข้อผิดพลาดในการสร้างฐานข้อมูลจากแถวที่ {index + 2}: {e}")
                    error_count += 1
            messages.success(request, f'นำเข้าข้อมูลฐานข้อมูลจาก Excel สำเร็จ {imported_count} รายการ พบข้อผิดพลาด {error_count} รายการ')
            return redirect('database_subscription:database_subscription_list')
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาดในการอ่านไฟล์ Excel: {e}')
    return render(request, 'database_subscription/import_subscriptions.html')

@login_required
def usage_statistics_list(request):
    usage_statistics = UsageStatistics.objects.all()
    return render(request, 'database_subscription/usage_statistics_list.html', {'usage_statistics': usage_statistics})

@login_required
def usage_statistics_create(request):
    if request.method == 'POST':
        form = UsageStatisticsForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'เพิ่มสถิติการใช้งานสำเร็จ')
            return redirect('database_subscription:usage_statistics_list')
    else:
        form = UsageStatisticsForm()
    return render(request, 'database_subscription/usage_statistics_form.html', {'form': form, 'title': 'เพิ่มสถิติการใช้งาน'})

@login_required
def usage_statistics_edit(request, pk):
    usage = get_object_or_404(UsageStatistics, pk=pk)
    if request.method == 'POST':
        form = UsageStatisticsForm(request.POST, instance=usage)
        if form.is_valid():
            UsageStatisticsArchive.objects.create(
                usage_statistics=usage,
                Usage_Count=usage.Usage_Count,
                Usage_Type=usage.Usage_Type,
                Usage_HistoryDate=usage.Usage_HistoryDate,
                database_subscription=usage.database_subscription,
                year=usage.year
            )
            form.save()
            messages.success(request, 'แก้ไขสถิติการใช้งานสำเร็จ')
            return redirect('database_subscription:usage_statistics_list')
    else:
        form = UsageStatisticsForm(instance=usage)
    return render(request, 'database_subscription/usage_statistics_form.html', {'form': form, 'title': 'แก้ไขสถิติการใช้งาน'})

@login_required
def usage_statistics_delete(request, pk):
    usage = get_object_or_404(UsageStatistics, pk=pk)
    if request.method == 'POST':
        usage.delete()
        messages.success(request, 'ลบสถิติการใช้งานสำเร็จ')
        return redirect('database_subscription:usage_statistics_list')
    return render(request, 'database_subscription/usage_statistics_confirm_delete.html', {'usage': usage})

@login_required
def usage_statistics_archive(request, pk):
    usage_statistics = get_object_or_404(UsageStatistics, pk=pk)
    archives = UsageStatisticsArchive.objects.filter(usage_statistics=usage_statistics).order_by('-archived_at')
    return render(request, 'database_subscription/usage_statistics_archive.html', {'usage_statistics': usage_statistics, 'archives': archives})

@login_required
def all_subscription_archives(request):
    archives = DatabaseSubscriptionArchive.objects.all().order_by('-archived_at')
    return render(request, 'database_subscription/all_subscription_archives.html', {'archives': archives})

from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import ImportHistoryForm
import pandas as pd
from .models import DatabaseSubscriptionArchive, DatabaseSubscription
from financial_mnm.models import FinancialManagement

@login_required
def import_subscription_history(request):
    if request.method == 'POST':
        form = ImportHistoryForm(request.POST, request.FILES)
        if form.is_valid():
            history_file = request.FILES['history_file']
            try:
                df = pd.read_excel(history_file)
            except Exception:
                try:
                    df = pd.read_csv(history_file)
                except Exception as e:
                    messages.error(request, f'ไม่สามารถอ่านไฟล์ได้: {e}')
                    return render(request, 'database_subscription/import_history_form.html', {'form': form, 'title': 'นำเข้าประวัติฐานข้อมูล'})

            imported_count = 0
            error_count = 0
            for index, row in df.iterrows():
                try:
                    db_name = row['DB_Name']
                    try:
                        database = DatabaseSubscription.objects.get(DB_Name=db_name)
                    except DatabaseSubscription.DoesNotExist:
                        messages.error(request, f'ไม่พบฐานข้อมูล "{db_name}" ในระบบ (แถวที่ {index + 2})')
                        error_count += 1
                        continue

                    fin_mnm_id = row.get('FinMnm_ID')
                    fin_mnm = None
                    if pd.notnull(fin_mnm_id):
                        try:
                            fin_mnm = FinancialManagement.objects.get(FinMnm_ID=fin_mnm_id)
                        except FinancialManagement.DoesNotExist:
                            messages.error(request, f'ไม่พบ FinMnm_ID "{fin_mnm_id}" ในระบบ (แถวที่ {index + 2})')
                            error_count += 1
                            continue

                    DatabaseSubscriptionArchive.objects.create(
                        database_subscription=database,
                        DB_Name=db_name,
                        DB_Collection=row.get('DB_Collection'),
                        DBJournal_List=row.get('DBJournal_List'),
                        DBEBook_List=row.get('DBEBook_List'),
                        subscription_start_date=pd.to_datetime(row.get('subscription_start_date')).date() if pd.notnull(row.get('subscription_start_date')) else None,
                        subscription_end_date=pd.to_datetime(row.get('subscription_end_date')).date() if pd.notnull(row.get('subscription_end_date')) else None,
                        renewal_date=pd.to_datetime(row.get('renewal_date')).date() if pd.notnull(row.get('renewal_date')) else None,
                        FinMnm_ID=fin_mnm,
                        year=int(row['year']) if pd.notnull(row['year']) else None,
                    )
                    imported_count += 1
                except KeyError as e:
                    messages.error(request, f'ไฟล์ไม่ถูกต้อง ขาด Column: {e} (แถวที่ {index + 2})')
                    return render(request, 'database_subscription/import_history_form.html', {'form': form, 'title': 'นำเข้าประวัติฐานข้อมูล'})
                except ValueError as e:
                    messages.error(request, f'ข้อมูลไม่ถูกต้องในแถวที่ {index + 2}: {e}')
                    error_count += 1

            messages.success(request, f'นำเข้าข้อมูลประวัติสำเร็จ {imported_count} รายการ พบข้อผิดพลาด {error_count} รายการ')
            return redirect('database_subscription:all_subscription_archives')
        else:
            messages.error(request, 'เกิดข้อผิดพลาดในการอัปโหลดไฟล์')
    else:
        form = ImportHistoryForm()
    return render(request, 'database_subscription/import_history_form.html', {'form': form, 'title': 'นำเข้าประวัติฐานข้อมูล'})