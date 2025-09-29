# accounts/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db import transaction
from .models import TaiKhoanHoSo

class DangKyForm(UserCreationForm):
    # Định nghĩa lại thứ tự các trường sẽ hiển thị trên form
    email = forms.EmailField(
        required=True,
        help_text='Bắt buộc. Dùng để xác thực và khôi phục tài khoản.'
    )
    # <-- Di chuyển trường sdt lên đây, ngay sau email
    sdt = forms.CharField(
        label='Số điện thoại',
        max_length=15,
        required=True
    )
    first_name = forms.CharField(
        label='Tên',
        max_length=150,
        required=False
    )
    last_name = forms.CharField(
        label='Họ',
        max_length=150,
        required=False
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')

    def clean_sdt(self):
        sdt_data = self.cleaned_data.get('sdt')
        if TaiKhoanHoSo.objects.filter(sdt=sdt_data).exists():
            raise forms.ValidationError("Số điện thoại này đã được sử dụng bởi một tài khoản khác.")
        return sdt_data

    def clean_email(self):
        email_data = self.cleaned_data.get('email')
        if User.objects.filter(email=email_data).exists():
            raise forms.ValidationError("Địa chỉ email này đã được sử dụng bởi một tài khoản khác.")
        return email_data

    @transaction.atomic
    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        
        if commit:
            user.save()

        sdt = self.cleaned_data.get('sdt')
        if sdt:
            user.taikhoanhoso.sdt = sdt
            user.taikhoanhoso.save()

        return user
  