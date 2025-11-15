from django.contrib import admin
from .models import BaiHuongDan, ChuyenMuc # Import ChuyenMuc

# Đăng ký ChuyenMuc để admin có thể quản lý
@admin.register(ChuyenMuc)
class ChuyenMucAdmin(admin.ModelAdmin):
    list_display = ('ten', 'slug')
    # Tự động tạo slug từ tên
    prepopulated_fields = {'slug': ('ten',)}

# Giữ nguyên phần đăng ký BaiHuongDan nếu có
@admin.register(BaiHuongDan)
class BaiHuongDanAdmin(admin.ModelAdmin):
    list_display = ('tieu_de', 'chuyen_muc', 'tac_gia', 'da_duyet', 'ngay_dang')
    list_filter = ('da_duyet', 'chuyen_muc')
    search_fields = ('tieu_de', 'noi_dung')