from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django.contrib.auth.models import Group
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(label='อีเมล', required=True)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2')

class ForgetPasswordForm(forms.Form):
    email = forms.EmailField(label='อีเมล')

class UserEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('role', 'is_active', 'is_staff', 'is_superuser') # ฟิลด์ที่ต้องการให้แก้ไข
        labels = {
            'role': 'บทบาท',
            'is_active': 'สถานะใช้งาน',
            'is_staff': 'สถานะเจ้าหน้าที่',
            'is_superuser': 'สถานะผู้ดูแลระบบสูงสุด',
        }
        help_texts = {
            'role': 'เลือกบทบาทของผู้ใช้งานในระบบ',
            'is_active': 'กำหนดว่าผู้ใช้สามารถเข้าสู่ระบบได้หรือไม่ (ยกเลิกการเลือกเพื่อระงับบัญชี)',
            'is_staff': 'กำหนดว่าผู้ใช้สามารถเข้าสู่ Django Admin Site ได้หรือไม่ (สำหรับผู้ดูแลระบบ)',
            'is_superuser': 'กำหนดว่าผู้ใช้มีสิทธิ์ทั้งหมดโดยอัตโนมัติ (สำหรับผู้ดูแลระบบสูงสุดเท่านั้น)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].label = 'บทบาท'
        self.fields['role'].help_text = 'เลือกบทบาทที่เหมาะสมกับผู้ใช้งาน'
    

class GroupCreationForm(forms.Form):
    name = forms.CharField(max_length=150, label='ชื่อกลุ่ม') 

    def clean_name(self):
        name = self.cleaned_data['name']
        if Group.objects.filter(name=name).exists():
            raise forms.ValidationError("ชื่อกลุ่มนี้มีอยู่แล้ว")
        return name

    def save(self):
        return Group.objects.create(name=self.cleaned_data['name'])