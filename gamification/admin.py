# gamification/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.db import models
from django.forms import Textarea, TextInput
from .models import GameHuyHieu, GameHuyHieuNguoiDung

@admin.register(GameHuyHieu)
class GameHuyHieuAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'hien_thi_anh', 
        'ten', 
        'hien_thi_logic', 
        'is_active'
    )
    list_display_links = ('id', 'ten', 'hien_thi_anh')
    list_editable = ('is_active',) # Bật tắt nhanh ngay danh sách
    list_filter = ('is_active', 'loai_dieu_kien')
    search_fields = ('ten', 'mo_ta', 'bien_so_phu')
    
    # Phân nhóm giao diện nhập liệu
    fieldsets = (
        ('Thông tin chung', {
            'fields': ('ten', 'mo_ta', 'anh_huy_hieu', 'is_active')
        }),
        ('Cấu hình Logic (Rule Engine)', {
            'fields': ('loai_dieu_kien', 'gia_tri_muc_tieu', 'bien_so_phu'),
            'description': 'Hệ thống sẽ tự động trao huy hiệu nếu chỉ số người dùng >= mục tiêu.',
        }),
    )

    # Tùy chỉnh kích thước ô nhập liệu
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '80'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80})},
    }

    def hien_thi_anh(self, obj):
        """Hiển thị ảnh nhỏ trong trang admin"""
        if obj.anh_huy_hieu:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; object-fit: contain; border-radius: 4px; border: 1px solid #ddd;" />',
                obj.anh_huy_hieu.url
            )
        return "No Image"
    hien_thi_anh.short_description = "Ảnh"

    def hien_thi_logic(self, obj):
        """Hiển thị tóm tắt điều kiện"""
        # Mặc định luôn là >=
        logic_str = f"{obj.get_loai_dieu_kien_display()} >= {obj.gia_tri_muc_tieu}"
        
        if obj.bien_so_phu:
            logic_str += f" (Tag/Code: {obj.bien_so_phu})"
            
        return format_html('<code style="color: #d63384;">{}</code>', logic_str)
    hien_thi_logic.short_description = "Điều kiện đạt"


@admin.register(GameHuyHieuNguoiDung)
class GameHuyHieuNguoiDungAdmin(admin.ModelAdmin):
    list_display = ('user', 'huy_hieu_badge', 'ngay_dat_duoc')
    list_filter = ('ngay_dat_duoc', 'huy_hieu')
    search_fields = ('user__username', 'user__email', 'huy_hieu__ten')
    autocomplete_fields = ['user', 'huy_hieu'] # Yêu cầu UserAdmin có search_fields
    date_hierarchy = 'ngay_dat_duoc'
    
    def huy_hieu_badge(self, obj):
        """Hiển thị tên huy hiệu có màu nền"""
        return format_html(
            '<span style="background-color: #e0f2f1; color: #00695c; padding: 4px 8px; border-radius: 12px; font-weight: bold;">{}</span>',
            obj.huy_hieu.ten
        )
    huy_hieu_badge.short_description = "Huy hiệu"

    def get_queryset(self, request):
        # Tối ưu SQL (tránh N+1 query)
        return super().get_queryset(request).select_related('user', 'huy_hieu')