from django import forms
from .models import DatabaseSubscription, Collection, CollectionDetail
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory

class DatabaseSubscriptionForm(forms.ModelForm):
    notes = forms.CharField(
        required=False,
        label='หมายเหตุ',
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
    )

    amount_paid_thb = forms.CharField(
        label='จำนวนเงินที่ชำระ (บาท)',
        widget=forms.TextInput(attrs={'class': 'form-control amount-input'})
    )
    amount_original_currency = forms.CharField(
        label='จำนวนเงิน (สกุลเงินต้นทาง)',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control amount-input'})
    )
    budget_allocated = forms.CharField(
        label='งบประมาณที่ตั้งเบิก',
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control amount-input'})
    )

    original_currency = forms.ChoiceField(
        label='สกุลเงินต้นทาง',
        choices=[('', 'สกุลเงิน'), ('USD', 'USD'), ('GBP', 'GBP'), ('EUR', 'EUR'), ('THB', ('THB'))],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select currency-select'})
    )
    upload_file = forms.FileField(
        label='อัปโหลดไฟล์ข้อมูล (.xlsx, .xls, .csv)',
        required=False, 
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    class Meta:
        model = DatabaseSubscription
        fields = [
            'DB_Name',
            'subscription_start_date',
            'subscription_end_date',
            'renewal_date',
            'renewal_year',
            'subscription_status',
            'has_perpetual_license',
            'perpetual_license_terms',
            'concurrent_users',
            'remote_access_allowed',
            'download_allowed',
            'print_allowed',
            'copy_allowed',
            'interlibrary_loan_allowed',
            'usage_conditions_text',
            'license_agreement_file',
            'payment_date',
            'amount_paid_thb',
            'amount_original_currency',
            'original_currency',
            'budget_allocated',
            'notes'
        ]
        widgets = {
            'subscription_start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'subscription_end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'renewal_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'payment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            # Use Textarea with specific rows and CSS for scrolling
            'perpetual_license_terms': forms.Textarea(attrs={'rows': 1, 'class': 'form-control', 'style': 'resize: vertical; overflow-y: auto;'}),
            'usage_conditions_text': forms.Textarea(attrs={'rows': 1, 'class': 'form-control', 'style': 'resize: vertical; overflow-y: auto;'}),
            'DB_Name': forms.TextInput(attrs={'class': 'form-control'}),
            'subscription_status': forms.Select(attrs={'class': 'form-select'}),
            'has_perpetual_license': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'concurrent_users': forms.NumberInput(attrs={'class': 'form-control'}),
            'remote_access_allowed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'download_allowed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'print_allowed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'copy_allowed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'interlibrary_loan_allowed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'license_agreement_file': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'DB_Name': 'ชื่อฐานข้อมูล',
            'subscription_start_date': 'วันที่เริ่มต้นการบอกรับ',
            'subscription_end_date': 'วันที่สิ้นสุดการบอกรับ',
            'renewal_date': 'กำหนดการต่ออายุการบอกรับ',
            'renewal_year': 'ปีที่บอกรับ',
            'subscription_status': 'สถานะการบอกรับ',
            'has_perpetual_license': 'มีสิทธิ์ perpetual license',
            'perpetual_license_terms': 'เงื่อนไข perpetual license',
            'concurrent_users': 'จำนวนผู้ใช้งานพร้อมกัน',
            'remote_access_allowed': 'อนุญาตการเข้าถึงจากภายนอก',
            'download_allowed': 'อนุญาตการดาวน์โหลด',
            'print_allowed': 'อนุญาตการพิมพ์',
            'copy_allowed': 'อนุญาตการทำสำเนา',
            'interlibrary_loan_allowed': 'บริการยืมทรัพยากรระหว่างห้องสมุด (ILL)',
            'usage_conditions_text': 'เงื่อนไขการใช้งานอื่น ๆ ',
            'license_agreement_file': 'ไฟล์ข้อตกลงสิทธิ์การใช้งาน',
            'payment_date': 'วันที่ชำระเงิน',
            'amount_paid_thb': 'จำนวนเงินที่ชำระ (บาท)',
            'amount_original_currency': 'จำนวนเงิน (สกุลเงินต้นทาง)',
            'original_currency': 'สกุลเงินต้นทาง',
            'budget_allocated': 'งบประมาณที่ตั้งเบิก',
            'notes': 'หมายเหตุ',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['amount_paid_thb'].initial = self.instance.amount_paid_thb if self.instance and self.instance.amount_paid_thb is not None else ''
        self.fields['amount_original_currency'].initial = self.instance.amount_original_currency if self.instance and self.instance.amount_original_currency is not None else ''
        self.fields['budget_allocated'].initial = self.instance.budget_allocated if self.instance and self.instance.budget_allocated is not None else ''
        self.fields['original_currency'].initial = self.instance.original_currency

    upload_file = forms.FileField(required=False, label=("อัปโหลดไฟล์ Excel/CSV"))

    def clean(self):
        cleaned_data = super().clean()
        upload_file = cleaned_data.get('upload_file')

        if not upload_file:
            if not cleaned_data.get('DB_Name'):
                self.add_error('DB_Name', ("โปรดระบุชื่อฐานข้อมูล"))
        else:
            cleaned_data['DB_Name'] = None
            if 'collections' in self.data:
                for i in range(int(self.data['collections-TOTAL_FORMS'])):
                    cleaned_data[f'collections-{i}-collection_name'] = None
                    cleaned_data[f'collections-{i}-journal_count'] = None
                    cleaned_data[f'collections-{i}-ebook_count'] = None
            cleaned_data['subscription_start_date'] = None
            cleaned_data['subscription_end_date'] = None
            cleaned_data['renewal_date'] = None
            cleaned_data['renewal_year'] = None
            cleaned_data['subscription_status'] = None
            cleaned_data['has_perpetual_license'] = None
            cleaned_data['perpetual_license_terms'] = None
            cleaned_data['concurrent_users'] = None
            cleaned_data['remote_access_allowed'] = None
            cleaned_data['download_allowed'] = None
            cleaned_data['print_allowed'] = None
            cleaned_data['copy_allowed'] = None
            cleaned_data['interlibrary_loan_allowed'] = None
            cleaned_data['usage_conditions_text'] = None
            cleaned_data['license_agreement_file'] = None
            cleaned_data['payment_date'] = None
            cleaned_data['amount_paid_thb'] = None
            cleaned_data['amount_original_currency'] = None
            cleaned_data['original_currency'] = None
            cleaned_data['budget_allocated'] = None
            cleaned_data['notes'] = None
        return cleaned_data

    def clean_amount_paid_thb(self):
        value = self.cleaned_data['amount_paid_thb']
        try:
            return float(value.replace(',', '')) if value else None
        except ValueError:
            raise ValidationError("กรุณากรอกจำนวนเงินที่ถูกต้อง")

    def clean_amount_original_currency(self):
        value = self.cleaned_data['amount_original_currency']
        try:
            return float(value.replace(',', '')) if value else None
        except ValueError:
            raise ValidationError("กรุณากรอกจำนวนเงินที่ถูกต้อง")

    def clean_budget_allocated(self):
        value = self.cleaned_data['budget_allocated']
        try:
            return float(value.replace(',', '')) if value else None
        except ValueError:
            raise ValidationError("กรุณากรอกงบประมาณที่ถูกต้อง")

    def is_valid(self):
        return super().is_valid()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.amount_paid_thb = self.cleaned_data['amount_paid_thb']
        instance.amount_original_currency = self.cleaned_data['amount_original_currency']
        instance.original_currency = self.cleaned_data['original_currency']
        instance.budget_allocated = self.cleaned_data['budget_allocated']

        if commit:
            instance.save()
        else:
            self.save_m2m = self._save_m2m
        return instance

class ImportFileForm(forms.Form):
    upload_file = forms.FileField(label='โปรดเลือกไฟล์ Excel (.xlsx, .xls) หรือ CSV (.csv) เพื่อนำเข้าข้อมูล')

class ImportHistoryForm(forms.Form):
    history_file = forms.FileField(label='โปรดเลือกไฟล์ Excel (.xlsx, .xls) หรือ CSV (.csv) สำหรับนำเข้าประวัติข้อมูล')

class ImportHistoricalDataForm(forms.Form):
    upload_file = forms.FileField(label='โปรดเลือกไฟล์ Excel (.xlsx, .xls) หรือ CSV (.csv) สำหรับนำเข้าข้อมูลประวัติ')
    year = forms.IntegerField(label='ระบุปีของข้อมูลประวัติ (ค.ศ.)', min_value=1900)

CollectionDetailFormSet = inlineformset_factory(
    DatabaseSubscription,
    CollectionDetail,
    fields=('collection_name', 'journal_count', 'ebook_count'),
    extra=1,
    can_delete=True,
    widgets={
        'collection_name': forms.TextInput(attrs={'class': 'form-control'}),
        'journal_count': forms.NumberInput(attrs={'class': 'form-control', 'style': 'max-width: 150px;', 'placeholder': 'จำนวนชื่อเรื่องแบบ E-Journals'}),
        'ebook_count': forms.NumberInput(attrs={'class': 'form-control', 'style': 'max-width: 150px;', 'placeholder': 'จำนวน E-Books'}),
    },
    labels={
        'collection_name': 'ชื่อ Collection',
        'journal_count': 'จำนวนชื่อเรื่องแบบ E-Journals',
        'ebook_count': 'จำนวนชื่อเรื่องแบบ E-Books',
    },
)