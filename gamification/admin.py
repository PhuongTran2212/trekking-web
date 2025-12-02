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
    list_editable = ('is_active',) # Cho phép bật/tắt nhanh ngay ở danh sách
    list_filter = ('is_active', 'loai_dieu_kien', 'toan_tu')
    search_fields = ('ten', 'mo_ta', 'bien_so_phu')
    
    # Phân nhóm các trường trong trang chi tiết để dễ nhìn hơn
    fieldsets = (
        ('Thông tin chung', {
            'fields': ('ten', 'mo_ta', 'anh_huy_hieu', 'is_active')
        }),
        ('Cấu hình Logic (Rule Engine)', {
            'fields': ('loai_dieu_kien', 'toan_tu', 'gia_tri_muc_tieu', 'bien_so_phu'),
            'description': 'Hệ thống sẽ dựa vào các thông số này để tự động trao huy hiệu.',
        }),
    )

    # Tùy chỉnh giao diện form nhập liệu
    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '80'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 80})},
    }

    def hien_thi_anh(self, obj):
        """Hiển thị ảnh nhỏ hoặc icon trong trang admin"""
        if obj.anh_huy_hieu:
            # Giả sử anh_huy_hieu là đường dẫn (URL hoặc path static)
            # Nếu là đường dẫn file tĩnh, bạn có thể cần thêm /static/ hoặc cấu hình media url
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; object-fit: contain;" />',
                obj.anh_huy_hieu
            )
        return "No Image"
    hien_thi_anh.short_description = "Ảnh"

    def hien_thi_logic(self, obj):
        """Hiển thị logic dưới dạng dễ đọc: LOẠI >= MỤC TIÊU"""
        operator_map = {'GTE': '>=', 'EQ': '=='}
        op_symbol = operator_map.get(obj.toan_tu, obj.toan_tu)
        
        logic_str = f"{obj.loai_dieu_kien} {op_symbol} {obj.gia_tri_muc_tieu}"
        
        if obj.bien_so_phu:
            logic_str += f" (Tag/Slug: {obj.bien_so_phu})"
            
        return format_html('<code>{}</code>', logic_str)
    hien_thi_logic.short_description = "Điều kiện đạt"


@admin.register(GameHuyHieuNguoiDung)
class GameHuyHieuNguoiDungAdmin(admin.ModelAdmin):
    list_display = ('user', 'huy_hieu_badge', 'ngay_dat_duoc')
    list_filter = ('ngay_dat_duoc', 'huy_hieu')
    search_fields = ('user__username', 'user__email', 'huy_hieu__ten')
    autocomplete_fields = ['user', 'huy_hieu'] # Yêu cầu UserAdmin và GameHuyHieuAdmin phải có search_fields
    date_hierarchy = 'ngay_dat_duoc'
    
    def huy_hieu_badge(self, obj):
        """Hiển thị tên huy hiệu kèm màu sắc cho đẹp"""
        return format_html(
            '<span style="background-color: #e3f2fd; color: #0d47a1; padding: 3px 8px; border-radius: 4px;">{}</span>',
            obj.huy_hieu.ten
        )
    huy_hieu_badge.short_description = "Huy hiệu"

    def get_queryset(self, request):
        # Tối ưu query (select_related) để tránh n+1 query
        return super().get_queryset(request).select_related('user', 'huy_hieu')