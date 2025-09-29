# treks/admin.py

from django.contrib import admin
from .models import CungDuongTrek, CungDuongDanhGia, CungDuongAnhDanhGia, CungDuongVatDungGoiY

# Tùy chỉnh giao diện hiển thị cho CungDuongTrek trong trang Admin
@admin.register(CungDuongTrek)
class CungDuongTrekAdmin(admin.ModelAdmin):
    # Các cột sẽ hiển thị trong danh sách
    list_display = ('ten', 'tinh_thanh', 'do_kho', 'do_dai_km', 'danh_gia_trung_binh', 'da_duyet')
    
    # Thêm bộ lọc ở sidebar bên phải
    list_filter = ('da_duyet', 'tinh_thanh', 'do_kho')
    
    # Thêm ô tìm kiếm
    # Dấu '__' cho phép tìm kiếm vào trường của model liên quan (Foreign Key)
    search_fields = ('ten', 'mo_ta', 'tinh_thanh__ten')
    
    # Tự động tạo slug từ trường 'ten'
    prepopulated_fields = {'slug': ('ten',)}
    
    # Sắp xếp mặc định
    ordering = ('-ngay_tao',)

# Đăng ký các model khác để có thể quản lý (tùy chọn)
admin.site.register(CungDuongDanhGia)
admin.site.register(CungDuongAnhDanhGia)
admin.site.register(CungDuongVatDungGoiY)