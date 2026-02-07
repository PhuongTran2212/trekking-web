from django.contrib import admin
from django.utils.html import format_html
from .models import (
    CongDongBaiViet,
    CongDongMediaBaiViet,
    CongDongBinhChonBaiViet,
    CongDongBinhLuan
)


class MediaBaiVietInline(admin.TabularInline):
    """Inline để hiển thị media trong admin bài viết"""
    model = CongDongMediaBaiViet
    extra = 0
    readonly_fields = ['preview_media', 'ngay_tai_len']
    fields = ['loai_media', 'duong_dan_file', 'preview_media', 'ngay_tai_len']
    
    def preview_media(self, obj):
        if obj.duong_dan_file:
            if obj.loai_media == 'anh':
                return format_html(
                    '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                    obj.duong_dan_file.url
                )
            else:
                return format_html(
                    '<video width="200" controls><source src="{}" type="video/mp4"></video>',
                    obj.duong_dan_file.url
                )
        return "Không có file"
    preview_media.short_description = 'Preview'


@admin.register(CongDongBaiViet)
class CongDongBaiVietAdmin(admin.ModelAdmin):
    list_display = [
        'tieu_de', 
        'tac_gia', 
        'trang_thai_badge',
        'luot_binh_chon', 
        'so_binh_luan',
        'ngay_dang'
    ]
    list_filter = ['trang_thai', 'ngay_dang', 'chuyen_di', 'tags']
    search_fields = ['tieu_de', 'noi_dung', 'tac_gia__username']
    readonly_fields = ['ngay_dang', 'ngay_cap_nhat', 'luot_binh_chon']
    inlines = [MediaBaiVietInline]
    filter_horizontal = ('tags',)
    
    fieldsets = (
        ('Thông tin bài viết', {
            'fields': ('tieu_de', 'noi_dung', 'tac_gia', 'chuyen_di', 'tags')
        }),
        ('Trạng thái', {
            'fields': ('trang_thai', 'luot_binh_chon')
        }),
        ('Thời gian', {
            'fields': ('ngay_dang', 'ngay_cap_nhat'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['duyet_bai_viet', 'tu_choi_bai_viet']
    
    def trang_thai_badge(self, obj):
        colors = {
            'cho_duyet': 'orange',
            'da_duyet': 'green',
            'tu_choi': 'red'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.trang_thai, 'gray'),
            obj.get_trang_thai_display()
        )
    trang_thai_badge.short_description = 'Trạng thái'
    
    def so_binh_luan(self, obj):
        return obj.so_luong_binh_luan()
    so_binh_luan.short_description = 'Số bình luận'
    
    def duyet_bai_viet(self, request, queryset):
        updated = queryset.update(trang_thai=CongDongBaiViet.TrangThaiBaiViet.DA_DUYET)
        self.message_user(request, f'Đã duyệt {updated} bài viết.')
    duyet_bai_viet.short_description = 'Duyệt bài viết đã chọn'
    
    def tu_choi_bai_viet(self, request, queryset):
        updated = queryset.update(trang_thai=CongDongBaiViet.TrangThaiBaiViet.TU_CHOI)
        self.message_user(request, f'Đã từ chối {updated} bài viết.')
    tu_choi_bai_viet.short_description = 'Từ chối bài viết đã chọn'

@admin.register(CongDongMediaBaiViet)
class CongDongMediaBaiVietAdmin(admin.ModelAdmin):
    list_display = ['bai_viet', 'loai_media', 'preview_thumbnail', 'ngay_tai_len']
    list_filter = ['loai_media', 'ngay_tai_len']
    search_fields = ['bai_viet__tieu_de']
    readonly_fields = ['ngay_tai_len', 'preview_media']
    
    def preview_thumbnail(self, obj):
        if obj.duong_dan_file:
            if obj.loai_media == 'anh':
                return format_html(
                    '<img src="{}" style="max-width: 50px; max-height: 50px;" />',
                    obj.duong_dan_file.url
                )
            return '🎥 Video'
        return "N/A"
    preview_thumbnail.short_description = 'Preview'
    
    def preview_media(self, obj):
        if obj.duong_dan_file:
            if obj.loai_media == 'anh':
                return format_html(
                    '<img src="{}" style="max-width: 400px;" />',
                    obj.duong_dan_file.url
                )
            else:
                return format_html(
                    '<video width="400" controls><source src="{}" type="video/mp4"></video>',
                    obj.duong_dan_file.url
                )
        return "Không có file"
    preview_media.short_description = 'Preview đầy đủ'


@admin.register(CongDongBinhChonBaiViet)
class CongDongBinhChonBaiVietAdmin(admin.ModelAdmin):
    list_display = ['bai_viet', 'user', 'ngay_binh_chon']
    list_filter = ['ngay_binh_chon']
    search_fields = ['bai_viet__tieu_de', 'user__username']
    readonly_fields = ['ngay_binh_chon']


@admin.register(CongDongBinhLuan)
class CongDongBinhLuanAdmin(admin.ModelAdmin):
    list_display = ['bai_viet', 'user', 'noi_dung_ngan', 'tra_loi_binh_luan', 'ngay_binh_luan']
    list_filter = ['ngay_binh_luan']
    search_fields = ['bai_viet__tieu_de', 'user__username', 'noi_dung']
    readonly_fields = ['ngay_binh_luan']
    
    def noi_dung_ngan(self, obj):
        return obj.noi_dung[:50] + '...' if len(obj.noi_dung) > 50 else obj.noi_dung
    noi_dung_ngan.short_description = 'Nội dung'
