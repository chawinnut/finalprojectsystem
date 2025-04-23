from django import forms
from .models import DatabaseSubscription, UsageStatistics

class DatabaseSubscriptionForm(forms.ModelForm):
    class Meta:
        model = DatabaseSubscription
        fields = '__all__'
        widgets = {
            'subscription_start_date': forms.DateInput(attrs={'type': 'date'}),
            'subscription_end_date': forms.DateInput(attrs={'type': 'date'}),
            'renewal_date': forms.DateInput(attrs={'type': 'date'}),
        }
        labels = {
            'DB_Name': 'ชื่อฐานข้อมูล',
            'DB_Collection': 'Collection',
            'DBJournal_List': 'จำนวนชื่อเรื่องแบบวารสาร',
            'DBEBook_List': 'จำนวนชื่อเรื่องแบบ E-Books',
            'subscription_start_date': 'วันที่เริ่มต้นการบอกรับ',
            'subscription_end_date': 'วันที่สิ้นสุดการบอกรับ',
            'renewal_date': 'กำหนดการต่ออายุการบอกรับ',
            'FinMnm_ID': 'รหัสการจัดการการเงิน',
        }

class UsageStatisticsForm(forms.ModelForm):
    class Meta:
        model = UsageStatistics
        fields = ['database_subscription', 'Usage_Count', 'Usage_Type', 'Usage_HistoryDate', 'year']
        widgets = {
            'Usage_HistoryDate': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'year': forms.NumberInput(attrs={'min': 2000}),
        }
        labels = {
            'database_subscription': 'ฐานข้อมูล',
            'Usage_Count': 'จำนวนการใช้งาน',
            'Usage_Type': 'ประเภทการใช้งาน',
            'Usage_HistoryDate': 'วันที่และเวลาใช้งาน',
            'year': 'ปี',
        }

class UploadUsageStatisticsForm(forms.Form):
    upload_file = forms.FileField(label='เลือกไฟล์ Excel/CSV สำหรับสถิติการใช้งาน')


class ImportFileForm(forms.Form):
    upload_file = forms.FileField(label='เลือกไฟล์ Excel/CSV')


class ImportHistoryForm(forms.Form):
    history_file = forms.FileField(label='เลือกไฟล์ CSV/Excel')