# core/forms.py
from django import forms
from django.utils.text import slugify
from .models import TinhThanh, LoaiVatDung, VatDung, The

class TinhThanhForm(forms.ModelForm):
    class Meta:
        model = TinhThanh
        fields = ['ten', 'slug']

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            slug = slugify(self.cleaned_data.get('ten'))
        return slug

class LoaiVatDungForm(forms.ModelForm):
    class Meta:
        model = LoaiVatDung
        fields = ['ten']

class VatDungForm(forms.ModelForm):
    class Meta:
        model = VatDung
        fields = ['ten', 'loai_vat_dung', 'mo_ta']

class TheForm(forms.ModelForm):
    class Meta:
        model = The
        fields = ['ten', 'slug']
    
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            slug = slugify(self.cleaned_data.get('ten'))
        return slug