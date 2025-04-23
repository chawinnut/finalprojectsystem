from django import forms
from .models import Vendor, Funder, Payment
from .models import CalendarEvent

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = '__all__'

class FunderForm(forms.ModelForm):
    class Meta:
        model = Funder
        fields = '__all__'

from django import forms
from .models import Payment

CURRENCY_CHOICES = [
    ('THB', 'Thai Baht (THB)'),
    ('USD', 'United States Dollar (USD)'),
    ('EUR', 'Euro (EUR)'),
]

class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['database_subscription', 'Payment_Date', 'Payment_Amount', 'Payment_Method', 'Vendor_ID', 'payment_document', 'currency']
        widgets = {
            'Payment_Date': forms.DateInput(attrs={'type': 'date'}),
        }
    currency = forms.ChoiceField(
        choices=CURRENCY_CHOICES,
        label='สกุลเงิน',
        initial='THB'
    )
class UploadFileForm(forms.Form):
    upload_file = forms.FileField(label='เลือกไฟล์ Excel/CSV')


from django import forms
from .models import CalendarEvent

class CalendarEventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = ['title', 'date', 'time', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control calendar-input', 'type': 'date'}),
            'time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }