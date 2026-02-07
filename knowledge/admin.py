# knowledge/admin.py
from django.contrib import admin
from .models import KienThucBaiHuongDan

@admin.register(KienThucBaiHuongDan)
class KienThucAdmin(admin.ModelAdmin):
    """
    Tùy chỉnh giao diện quản lý cho model KienThucBaiHuongDan.
    """
    # 1. Các cột hiển thị trong danh sách
    list_display = ('tieu_de', 'chuyen_muc', 'tac_gia', 'ngay_dang')

    # 2. Bộ lọc (filter) ở thanh bên phải
    list_filter = ('chuyen_muc', 'tac_gia')

    # 3. Thanh tìm kiếm
    search_fields = ('tieu_de', 'noi_dung')

    # 4. Phân cấp theo ngày tháng
    date_hierarchy = 'ngay_dang'

    # 5. Tự động điền slug từ tiêu đề (nếu bạn có trường slug)
    # prepopulated_fields = {'slug': ('tieu_de',)} 

    # 6. Sắp xếp mặc định
    ordering = ('-ngay_dang',)

    def save_model(self, request, obj, form, change):
        """
        Tự động gán tác giả là người dùng admin hiện tại khi tạo bài viết mới.
        """
        if not obj.tac_gia:
            obj.tac_gia = request.user
        super().save_model(request, obj, form, change)
