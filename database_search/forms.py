from django import forms

class DatabaseSearchForm(forms.Form):
    query = forms.CharField(
        label='คำค้นหา',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'ชื่อฐานข้อมูล, วารสาร...'})
    )
    collection = forms.CharField(
        label='Collection',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'ชื่อ Collection'})
    )
    publisher_conditions = forms.CharField(
        label='เงื่อนไขสำนักพิมพ์',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'เงื่อนไขของสำนักพิมพ์'})
    )
    subscription_duration = forms.CharField(
        label='ปีที่บอกรับ',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'ค.ศ.'})
    )
    # คุณสามารถเพิ่ม Fields อื่นๆ ที่ต้องการค้นหาได้ที่นี่