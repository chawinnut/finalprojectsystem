from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from .forms import DatabaseSubscriptionForm, CollectionDetailFormSet
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.utils import timezone
import pandas as pd
from .models import DatabaseSubscription, Collection, CollectionDetail, DatabaseSubscriptionChangeLog
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.forms.models import model_to_dict
from .forms import ImportFileForm
from django.contrib import messages
from datetime import datetime
import pandas as pd
import csv
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
import openpyxl
from .models import DatabaseSubscription, CollectionDetail
from .forms import DatabaseSubscriptionForm
from django.conf import settings
import os
from decimal import Decimal

@login_required
@permission_required('database_subscription.view_databasesubscription')
def database_subscription_list(request):
    current_year = str(timezone.now().year)
    selected_year_str = request.GET.get('year', current_year)  # กำหนดค่าเริ่มต้นเป็นปีปัจจุบัน

    subscriptions = DatabaseSubscription.objects.order_by('DB_Name')

    if selected_year_str and selected_year_str != '':
        try:
            selected_year = int(selected_year_str)
            subscriptions = subscriptions.filter(renewal_year=selected_year_str).order_by('DB_Name')
        except ValueError:
            messages.error(request, f"รูปแบบปีไม่ถูกต้อง: '{selected_year_str}'")

    available_years = DatabaseSubscription.objects.exclude(renewal_year__isnull=True).exclude(renewal_year='').values_list('renewal_year', flat=True).distinct().order_by('-renewal_year')
    available_years = [str(year) for year in available_years if year]

    paginator = Paginator(subscriptions, 20)
    page = request.GET.get('page')
    try:
        subscriptions = paginator.page(page)
    except PageNotAnInteger:
        subscriptions = paginator.page(1)
    except EmptyPage:
        subscriptions = paginator.page(paginator.num_pages)

    context = {
        'subscriptions': subscriptions,
        'available_years': available_years,
        'selected_year': selected_year_str,
        'current_year': current_year,
        'page_obj': subscriptions,
        'paginator': paginator,
    }
    return render(request, 'database_subscription/database_subscription_list.html', context)

@login_required
@permission_required('database_subscription.add_databasesubscription')
def database_subscription_create(request):
    subscription_form = DatabaseSubscriptionForm()
    collection_detail_formset = CollectionDetailFormSet(prefix='collections')

    if request.method == 'POST':
        subscription_form = DatabaseSubscriptionForm(request.POST, request.FILES)
        collection_detail_formset = CollectionDetailFormSet(request.POST, prefix='collections')

        if subscription_form.is_valid() and collection_detail_formset.is_valid():
            database_subscription = subscription_form.save()
            collection_detail_formset.instance = database_subscription
            collection_detail_formset.save()

            if 'upload_file' in request.FILES:
                uploaded_file = request.FILES['upload_file']
                file_extension = uploaded_file.name.split('.')[-1].lower()

                try:
                    if file_extension == 'csv':
                        decoded_file = uploaded_file.read().decode('utf-8').splitlines()
                        reader = csv.DictReader(decoded_file)
                    elif file_extension in ['xlsx', 'xls']:
                        df = pd.read_excel(uploaded_file)
                        reader = df.to_dict('records')
                    else:
                        messages.error(request, "รองรับเฉพาะไฟล์ CSV และ Excel (.xlsx, .xls)")
                        return render(request, 'database_subscription/database_subscription_form.html', {
                            'subscription_form': subscription_form,
                            'collection_detail_formset': collection_detail_formset,
                            'title': 'เพิ่มฐานข้อมูลที่บอกรับ'
                        })

                    imported_count = 0
                    updated_collection_count = 0
                    created_collection_count = 0

                    for row in reader:
                        collection_name = row.get('Collection_Name')
                        journal_count_str = row.get('Journal_Count')
                        ebook_count_str = row.get('EBook_Count')
                        original_price_str = row.get('Original_Price')  # Get original price
                        original_currency = row.get('Original_Currency', 'THB') # Get original currency, default to THB

                        # Handle None or empty strings
                        journal_count = 0
                        if journal_count_str:
                            if isinstance(journal_count_str, str) and journal_count_str.isdigit():
                                journal_count = int(journal_count_str)
                            elif isinstance(journal_count_str, (int, float)):
                                journal_count = int(journal_count_str)
                            else:
                                messages.warning(request, f"Invalid journal count format for Collection: {collection_name}. Setting to 0.")

                        ebook_count = 0
                        if ebook_count_str:
                            if isinstance(ebook_count_str, str) and ebook_count_str.isdigit():
                                ebook_count = int(ebook_count_str)
                            elif isinstance(ebook_count_str, (int, float)):
                                ebook_count = int(ebook_count_str)
                            else:
                                messages.warning(request, f"Invalid ebook count format for Collection: {collection_name}. Setting to 0.")

                        original_price = 0
                        if original_price_str:
                            try:
                                original_price = float(original_price_str)  # Convert to float first
                            except ValueError:
                                messages.warning(request, f"Invalid original price format for Collection: {collection_name}. Setting to 0.")

                        existing_collection = CollectionDetail.objects.filter(
                            database_subscription=database_subscription,
                            collection_name=collection_name
                        ).first()

                        if existing_collection:
                            existing_collection.journal_count += journal_count
                            existing_collection.ebook_count += ebook_count
                            existing_collection.original_price = original_price # update original price
                            existing_collection.original_currency = original_currency # update original currency
                            existing_collection.save()
                            updated_collection_count += 1
                        else:
                            CollectionDetail.objects.create(
                                database_subscription=database_subscription,
                                collection_name=collection_name,
                                journal_count=journal_count,
                                ebook_count=ebook_count,
                                original_price=original_price, # set original price
                                original_currency=original_currency # set original currency
                            )
                            created_collection_count += 1
                            imported_count += 1

                    messages.success(request, f"เพิ่มฐานข้อมูลสำเร็จและนำเข้าข้อมูล: สร้าง Collections ใหม่ {created_collection_count}, อัปเดต Collections {updated_collection_count}")

                except FileNotFoundError:
                    messages.error(request, "ไม่พบไฟล์ที่อัปโหลด")
                except pd.errors.EmptyDataError:
                    messages.error(request, "ไฟล์ที่อัปโหลดไม่มีข้อมูล")
                except Exception as e:
                    messages.error(request, f"เกิดข้อผิดพลาดในการอ่านหรือประมวลผลไฟล์: {e}")

            else:
                messages.success(request, 'เพิ่มฐานข้อมูลที่บอกรับสำเร็จ!')

            return redirect('database_subscription:database_subscription_list')
        else:
            messages.error(request, 'เกิดข้อผิดพลาดในการบันทึกข้อมูล')

    return render(request, 'database_subscription/database_subscription_form.html', {
        'subscription_form': subscription_form,
        'collection_detail_formset': collection_detail_formset,
        'title': 'เพิ่มฐานข้อมูลที่บอกรับ'
    })


@login_required
@permission_required('database_subscription.change_databasesubscription')
def database_subscription_update(request, pk):
    from .forms import CollectionDetailFormSet
    subscription = get_object_or_404(DatabaseSubscription, pk=pk)
    subscription_form = DatabaseSubscriptionForm(instance=subscription)
    collection_detail_formset = CollectionDetailFormSet(instance=subscription, prefix='collections')

    if request.method == 'POST':
        subscription_form = DatabaseSubscriptionForm(request.POST, request.FILES, instance=subscription)
        collection_detail_formset = CollectionDetailFormSet(request.POST, prefix='collections', instance=subscription)  # ส่ง instance แค่ครั้งเดียว

        if subscription_form.is_valid() and collection_detail_formset.is_valid():
            old_data = model_to_dict(subscription)
            updated_subscription = subscription_form.save()
            new_data = model_to_dict(updated_subscription)
            changed_fields = {}
            for field, new_value in new_data.items():
                if old_data.get(field) != new_value:
                    changed_fields[field] = {'old': old_data.get(field), 'new': new_value}

            if changed_fields:
                DatabaseSubscriptionChangeLog.objects.create(
                    database_subscription=updated_subscription,
                    archived_at=timezone.now(),
                    change_details=changed_fields
                )
            collection_detail_formset.instance = updated_subscription 
            collection_detail_formset.save()
            messages.success(request, 'แก้ไขข้อมูลฐานข้อมูลที่บอกรับสำเร็จ!')
            return redirect('database_subscription:database_subscription_detail', pk=updated_subscription.pk)
        else:
            messages.error(request, 'เกิดข้อผิดพลาดในการบันทึกข้อมูล')

    return render(request, 'database_subscription/database_subscription_form.html', {
        'subscription_form': subscription_form,
        'collection_detail_formset': collection_detail_formset,
        'title': 'แก้ไขฐานข้อมูลที่บอกรับ'
    })

@login_required
@permission_required('database_subscription.delete_databasesubscription')
def database_subscription_delete(request, pk):
    subscription = get_object_or_404(DatabaseSubscription, pk=pk)
    if request.method == 'POST':
        subscription.delete()
        messages.success(request, 'ลบฐานข้อมูลที่บอกรับสำเร็จ!')
        return redirect('database_subscription:database_subscription_list')
    return render(request, 'database_subscription/database_subscription_confirm_delete.html', {'subscription': subscription})



def parse_date(date_string):
    date_formats = ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y', '%d/%m/%Y']
    if date_string and isinstance(date_string, str):
        date_string = date_string.strip()
        for fmt in date_formats:
            try:
                return datetime.strptime(date_string, fmt).date()
            except ValueError:
                continue
    return None

def parse_decimal(decimal_string):
    """พยายามแปลง string เป็น Decimal หรือ None หากเป็น 'None' หรือว่าง"""
    if decimal_string and isinstance(decimal_string, str):
        cleaned_string = decimal_string.replace(',', '').strip()
        if cleaned_string.lower() == 'none' or not cleaned_string:
            return None
        try:
            return Decimal(cleaned_string)
        except ValueError:
            return None
    return None

@login_required
@permission_required('database_subscription.add_databasesubscription')
def import_subscriptions(request):
    if request.method == 'POST' and request.FILES.get('upload_file'):
        uploaded_file = request.FILES['upload_file']
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        uploaded_file_path = fs.path(filename)

        try:
            if uploaded_file.name.endswith('.xlsx'):
                workbook = openpyxl.load_workbook(uploaded_file_path)
                sheet = workbook.active
                data = list(sheet.rows)
                header = [str(cell.value).strip() for cell in data[0]]
                data = data[1:]
            elif uploaded_file.name.endswith('.csv'):
                with open(uploaded_file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    data = list(reader)
                header = [str(cell).strip() for cell in data[0]]
                data = data[1:]
            else:
                messages.error(request, "รูปแบบไฟล์ไม่ถูกต้อง กรุณาอัปโหลดไฟล์ .xlsx หรือ .csv เท่านั้น")
                return redirect('database_subscription:database_subscription_list')

            imported_db_count = 0
            updated_db_count = 0
            created_collection_count = {}
            updated_collection_count = {}

            for row in data:
                row_values = [str(cell.value).strip() if hasattr(cell, 'value') else '' for cell in row]
                row_data = dict(zip(header, row_values))
                renewal_year = row_data.get('renewal_year')  # Get renewal_year directly

                # If renewal_year is empty, try to get it from subscription_end_date
                if not renewal_year:
                    end_date = parse_date(row_data.get('subscription_end_date'))
                    if end_date:
                        renewal_year = str(end_date.year)
                    # No else, leave it as None if no end_date

                db_subscription_data = {
                    'DB_Name': row_data.get('DB_Name', ''),
                    'subscription_start_date': parse_date(row_data.get('subscription_start_date')),
                    'subscription_end_date': parse_date(row_data.get('subscription_end_date')),
                    'renewal_date': parse_date(row_data.get('renewal_date')),
                    'renewal_year': renewal_year,  # Use the determined renewal_year
                    'subscription_status': row_data.get('subscription_status', '').lower(),
                    'has_perpetual_license': row_data.get('has_perpetual_license', '').lower() in ['true', '1', 'yes'],
                    'perpetual_license_terms': row_data.get('perpetual_license_terms', ''),
                    'concurrent_users': concurrent_users_from_row(row_data.get('concurrent_users')),
                    'remote_access_allowed': row_data.get('remote_access_allowed', '').lower() in ['true', '1', 'yes'],
                    'download_allowed': row_data.get('download_allowed', '').lower() in ['true', '1', 'yes'],
                    'print_allowed': row_data.get('print_allowed', '').lower() in ['true', '1', 'yes'],
                    'copy_allowed': row_data.get('copy_allowed', '').lower() in ['true', '1', 'yes'],
                    'interlibrary_loan_allowed': row_data.get('interlibrary_loan_allowed', '').lower() in ['true', '1', 'yes'],
                    'usage_conditions_text': row_data.get('usage_conditions_text', ''),
                    'payment_date': parse_date(row_data.get('payment_date')),
                    'amount_paid_thb': parse_decimal(row_data.get('amount_paid_thb')),
                    'amount_original_currency': parse_decimal(row_data.get('amount_original_currency')),
                    'original_currency': row_data.get('original_currency', '')[:3],
                    'budget_allocated': parse_decimal(row_data.get('budget_allocated')),
                    'notes': row_data.get('notes', ''),
                }

                try:
                    db_subscription, created = DatabaseSubscription.objects.get_or_create(
                        DB_Name=db_subscription_data['DB_Name'],
                        defaults=db_subscription_data
                    )
                    if created:
                        imported_db_count += 1
                        created_collection_count[db_subscription.DB_Name] = 0
                        updated_collection_count[db_subscription.DB_Name] = 0
                    else:
                        updated_db_count += 1
                        created_collection_count.setdefault(db_subscription.DB_Name, 0)
                        updated_collection_count.setdefault(db_subscription.DB_Name, 0)
                        for key, value in db_subscription_data.items():
                            if value is not None and getattr(db_subscription, key, None) != value:
                                setattr(db_subscription, key, value)
                        db_subscription.save()

                    collection_names = row_data.get('Collection_Name', '').split(';')
                    journal_counts = row_data.get('Journal_Count', '').split(';')
                    ebook_counts = row_data.get('EBook_Count', '').split(';')

                    for i, collection_name in enumerate(collection_names):
                        collection_name = collection_name.strip()
                        journal_count = parse_int_or_none(journal_counts[i].strip() if i < len(journal_counts) else None)
                        ebook_count = parse_int_or_none(ebook_counts[i].strip() if i < len(ebook_counts) else None)

                        if collection_name and db_subscription:
                            collection, collection_created = Collection.objects.get_or_create(name=collection_name)
                            collection_detail, created = CollectionDetail.objects.get_or_create(
                                database_subscription=db_subscription,
                                collection_name=collection.name,
                                defaults={'journal_count': journal_count, 'ebook_count': ebook_count}
                            )
                            if created:
                                created_collection_count[db_subscription.DB_Name] += 1
                            else:
                                updated_collection_count[db_subscription.DB_Name] += 1

                except Exception as e:
                    messages.error(request, f"เกิดข้อผิดพลาดในการสร้าง/อัปเดตฐานข้อมูล '{row_data.get('DB_Name', 'ไม่ระบุ')}': {e}")
                    continue

            import_summary = f"นำเข้าข้อมูลสำเร็จ: สร้างฐานข้อมูลใหม่ {imported_db_count} ฐานข้อมูล, อัปเดต {updated_db_count} ฐานข้อมูล. "
            collection_summary = ""
            for db_name, created_count in created_collection_count.items():
                collection_summary += f"สร้าง {created_count} collections ใหม่สำหรับ '{db_name}', "
            for db_name, updated_count in updated_collection_count.items():
                collection_summary += f"อัปเดต {updated_count} collections สำหรับ '{db_name}', "

            messages.success(request, import_summary + collection_summary.rstrip(', '))
            return redirect('database_subscription:database_subscription_list')

        except Exception as e:
            messages.error(request, f"เกิดข้อผิดพลาดในการนำเข้าข้อมูล: {e}")
            return redirect('database_subscription:database_subscription_list')

    else:
        form = ImportFileForm()
    return render(request, 'database_subscription/import_form.html', {'form': form})


def concurrent_users_from_row(concurrent_users_str):
    concurrent_users_str = str(concurrent_users_str).strip().lower()
    if concurrent_users_str == 'unlimited':
        return 'unlimited'
    elif concurrent_users_str.isdigit():
        return concurrent_users_str
    elif concurrent_users_str in ['yes', 'true']:
        return '-1'
    elif concurrent_users_str in ['no', 'false']:
        return '1'
    elif not concurrent_users_str:
        return None
    else:
        return None

def parse_int_or_none(value):
    if value is not None and str(value).strip().isdigit():
        return int(value)
    return None

@login_required
@permission_required('database_subscription.view_databasesubscription')
def database_subscription_detail(request, pk):
    subscription = get_object_or_404(
        DatabaseSubscription.objects.prefetch_related('collection_details'),
        pk=pk
    )
    collection_details = subscription.collection_details.all()
    total_journals = sum(cd.journal_count for cd in collection_details if cd.journal_count is not None)
    total_ebooks = sum(cd.ebook_count for cd in collection_details if cd.ebook_count is not None)
    return render(request, 'database_subscription/database_subscription_detail.html', {
        'subscription': subscription,
        'collection_details': collection_details,
        'total_journals': total_journals,
        'total_ebooks': total_ebooks,
    })

@login_required
@permission_required('database_subscription.view_databasesubscriptionhistory')
def database_subscription_history(request):
    archives = DatabaseSubscriptionChangeLog.objects.all().order_by('-archived_at')
    return render(request, 'database_subscription/database_subscription_history.html', {
        'archives': archives,
    })



@login_required
@permission_required('database_subscription.view_databasesubscriptionhistory')
def database_subscription_history_detail(request, pk):
    history_entries = DatabaseSubscriptionChangeLog.objects.filter(database_subscription_id=pk).order_by('-archived_at')
    subscription = get_object_or_404(DatabaseSubscription, pk=pk)
    context = {
        'history_entries': history_entries,
        'subscription': subscription,
    }
    return render(request, 'database_subscription/database_subscription_history_detail.html', context)

@login_required
@permission_required('database_subscription.delete_databasesubscription')
def move_to_archive(request, pk):
    """ย้ายข้อมูลฐานข้อมูลที่บอกรับปัจจุบันเข้าแฟ้มประวัติ"""
    subscription = get_object_or_404(DatabaseSubscription, pk=pk)
    if request.method == 'POST':
        try:
            messages.success(request, f'ย้ายข้อมูล "{subscription.DB_Name}" เข้าแฟ้มประวัติแล้ว')
            return redirect('database_subscription:database_subscription_list') 
        except Exception as e:
            messages.error(request, f'เกิดข้อผิดพลาดในการย้ายข้อมูล "{subscription.DB_Name}" เข้าแฟ้มประวัติ: {e}')
            return redirect('database_subscription:database_subscription_detail', pk=pk)
    else:
        return render(request, 'database_subscription/confirm_move_to_archive.html', {'subscription': subscription})

def database_subscription_history(request):
    history = DatabaseSubscription.objects.exclude(renewal_year__isnull=True).exclude(renewal_year='').order_by('-renewal_year', 'DB_Name')
    years = history.values_list('renewal_year', flat=True).distinct()
    return render(request, 'database_subscription/database_history.html', {'history': history, 'years': years})

def database_subscription_history_by_year(request, year):
    subscriptions = DatabaseSubscription.objects.filter(renewal_year=year).order_by('DB_Name')
    return render(request, 'database_subscription/database_history_by_year.html', {'subscriptions': subscriptions, 'year': year})


from django.http import HttpResponse
from django.urls import reverse

@login_required
def download_import_template_excel(request):
    column_names = [
        'DB_Name', 'subscription_start_date', 'subscription_end_date', 'renewal_date', 'renewal_year',
        'subscription_status', 'has_perpetual_license', 'perpetual_license_terms', 'concurrent_users',
        'remote_access_allowed', 'download_allowed', 'print_allowed', 'copy_allowed', 'interlibrary_loan_allowed',
        'usage_conditions_text', 'payment_date', 'amount_paid_thb', 'amount_original_currency',
        'original_currency', 'budget_allocated', 'notes', 'Collection_Name', 'Journal_Count', 'EBook_Count'
    ]
    df = pd.DataFrame(columns=column_names)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="import_template.xlsx"'
    df.to_excel(response, index=False)
    return response

@login_required
def download_import_template_csv(request):
    column_names = [
        'DB_Name', 'subscription_start_date', 'subscription_end_date', 'renewal_date', 'renewal_year',
        'subscription_status', 'has_perpetual_license', 'perpetual_license_terms', 'concurrent_users',
        'remote_access_allowed', 'download_allowed', 'print_allowed', 'copy_allowed', 'interlibrary_loan_allowed',
        'usage_conditions_text', 'payment_date', 'amount_paid_thb', 'amount_original_currency',
        'original_currency', 'budget_allocated', 'notes', 'Collection_Name', 'Journal_Count', 'EBook_Count'
    ]
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="import_template.csv"'
    writer = csv.writer(response)
    writer.writerow(column_names)
    return response