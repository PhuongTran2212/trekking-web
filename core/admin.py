# core/admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import (
    TinhThanh, The, LoaiVatDung, VatDung, DoKho, TrangThaiChuyenDi,
    HeThongBaoCao, HeThongThongBao  # Thêm import
)

# Các model đã đăng ký giữ nguyên
admin.site.register(TinhThanh)
admin.site.register(The)
admin.site.register(LoaiVatDung)
admin.site.register(VatDung)
admin.site.register(DoKho)
admin.site.register(TrangThaiChuyenDi)

# === THÊM MỚI: TÙY CHỈNH ADMIN CHO HỆ THỐNG BÁO CÁO ===
@admin.register(HeThongBaoCao)
class HeThongBaoCaoAdmin(admin.ModelAdmin):
    list_display = ('content_object_link', 'nguoi_bao_cao', 'trang_thai_badge', 'ngay_bao_cao')
    list_filter = ('trang_thai', 'content_type', 'ngay_bao_cao')
    search_fields = ('object_id', 'nguoi_bao_cao__username', 'ly_do_bao_cao')
    readonly_fields = ('ngay_bao_cao', 'nguoi_bao_cao', 'content_object_link')
    list_per_page = 25
    
    fieldsets = (
        ('Thông tin Báo cáo', {
            'fields': ('content_object_link', 'nguoi_bao_cao', 'ly_do_bao_cao', 'ngay_bao_cao')
        }),
        ('Xử lý của Admin', {
            'fields': ('trang_thai', 'nguoi_xu_ly', 'ghi_chu_xu_ly')
        }),
    )

    def save_model(self, request, obj, form, change):
        # Tự động gán admin hiện tại là người xử lý khi trạng thái được thay đổi
        if 'trang_thai' in form.changed_data and obj.trang_thai != obj.TrangThaiBaoCao.MOI:
            if not obj.nguoi_xu_ly:
                obj.nguoi_xu_ly = request.user
        super().save_model(request, obj, form, change)

    def content_object_link(self, obj):
        """Tạo một link có thể click để đi đến trang admin của đối tượng bị báo cáo."""
        if obj.content_object:
            app_label = obj.content_type.app_label
            model_name = obj.content_type.model
            url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.object_id])
            return format_html('<a href="{}">{} #{}</a>', url, obj.content_type.name.title(), obj.object_id)
        return "Đối tượng đã bị xóa"
    content_object_link.short_description = 'Đối tượng bị báo cáo'

    def trang_thai_badge(self, obj):
        colors = {
            'Mới': 'blue',
            'Đang xử lý': 'orange',
            'Đã xử lý': 'green',
        }
        status = obj.get_trang_thai_display()
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(status, 'gray'),
            status
        )
    trang_thai_badge.short_description = 'Trạng thái'

# Tùy chọn: Đăng ký cả model Thông báo để tiện xem
@admin.register(HeThongThongBao)
class HeThongThongBaoAdmin(admin.ModelAdmin):
    list_display = ('nguoi_nhan', 'tieu_de', 'da_doc', 'ngay_tao')
    list_filter = ('da_doc', 'ngay_tao')
    search_fields = ('nguoi_nhan__username', 'tieu_de', 'noi_dung')