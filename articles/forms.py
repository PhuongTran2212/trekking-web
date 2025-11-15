# articles/forms.py
from django import forms
from .models import BaiHuongDan

class BaiHuongDanAdminForm(forms.ModelForm):
    class Meta:
        model = BaiHuongDan
        fields = ['tieu_de', 'chuyen_muc', 'noi_dung']