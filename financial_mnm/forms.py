from django import forms
#from database_subscription.models
from .models import CalendarEvent
from .models import FinancialManagement
import datetime

from django import forms
from .models import FinancialManagement
import datetime

class NumberInputWithCommas(forms.NumberInput):
    template_name = 'widgets/number_input_with_commas.html'

    class Media:
        js = ('js/jquery.inputmask.min.js', 'js/init_inputmask.js',)


class AddBudgetForm(forms.ModelForm):
    Budget_Year = forms.IntegerField(
        label="ปีงบประมาณ",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    Total_Budget = forms.DecimalField(
        label="งบประมาณทั้งหมด",
        max_digits=20,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control no-spinners'})
    )

    class Meta:
        model = FinancialManagement
        fields = ['Budget_Year', 'Total_Budget']

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