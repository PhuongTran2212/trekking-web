# core/admin.py
from django.contrib import admin
from .models import TinhThanh, The, LoaiVatDung, VatDung, DoKho

admin.site.register(TinhThanh)
admin.site.register(The)
admin.site.register(LoaiVatDung)
admin.site.register(VatDung)
admin.site.register(DoKho)
