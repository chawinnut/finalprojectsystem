from django import forms
from database_subscription.models import Collection, DatabaseSubscription

class DatabaseSearchForm(forms.Form):
    query = forms.CharField(
        label='คำค้นหา',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'ชื่อฐานข้อมูล'})
    )
    subscription_year = forms.CharField(
        label='ปีที่บอกรับ',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'ค.ศ.'})
    )
    collection = forms.CharField(  # Add this field
        label='Collection',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'ชื่อ Collection'})
    )