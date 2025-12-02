from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.db.models import Count
from .models import GameHuyHieu, GameHuyHieuNguoiDung
from .forms import GameHuyHieuForm
from django.db.models import OuterRef, Subquery, Case, When, Value, IntegerField
# --- KIỂM TRA QUYỀN ADMIN/STAFF ---
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

# 1. READ: Danh sách tất cả huy hiệu (Ai cũng xem được)
class BadgeListView(ListView):
    model = GameHuyHieu
    template_name = 'gamification/badge_list.html'
    context_object_name = 'badges'
    ordering = ['-id']

    def get_queryset(self):
        # Nếu là staff thì xem hết, user thường chỉ xem huy hiệu đang active
        if self.request.user.is_staff:
            return GameHuyHieu.objects.all()
        return GameHuyHieu.objects.filter(is_active=True)

# 2. READ: Danh sách huy hiệu của TÔI (User đã đăng nhập)
class MyBadgeListView(LoginRequiredMixin, ListView):
    model = GameHuyHieu
    template_name = 'gamification/my_badges.html'
    context_object_name = 'badges_page' # Đổi tên vì bây giờ là 1 trang (page object)
    paginate_by = 12 # Số lượng huy hiệu trên mỗi trang

    def get_queryset(self):
        user = self.request.user
        
        # 1. Subquery để lấy ngày đạt được của từng huy hiệu (nếu có)
        earned_subquery = GameHuyHieuNguoiDung.objects.filter(
            user=user,
            huy_hieu=OuterRef('pk')
        ).values('ngay_dat_duoc')[:1]

        # 2. Query chính: Lấy tất cả huy hiệu active
        qs = GameHuyHieu.objects.filter(is_active=True).annotate(
            earned_at=Subquery(earned_subquery) # Gắn ngày nhận vào
        ).annotate(
            # Tạo trường giả 'status_order': 1 là đã sở hữu, 0 là chưa
            status_order=Case(
                When(earned_at__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )

        # 3. Sắp xếp:
        # - Ưu tiên status_order giảm dần (1 lên trước -> Đã sở hữu lên đầu)
        # - Sau đó đến earned_at tăng dần (Ngày bé -> Nhận trước -> Nằm bên trái/trước)
        return qs.order_by('-status_order', 'earned_at', 'id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Tính toán thống kê
        total_badges = GameHuyHieu.objects.filter(is_active=True).count()
        earned_count = GameHuyHieuNguoiDung.objects.filter(user=user).count()
        
        # Tính phần trăm để vẽ thanh tiến trình (Progress Bar)
        progress_percent = 0
        if total_badges > 0:
            progress_percent = int((earned_count / total_badges) * 100)

        context['total_badges'] = total_badges
        context['earned_count'] = earned_count
        context['progress_percent'] = progress_percent
        return context
# 3. CREATE: Tạo huy hiệu mới (Chỉ Staff)
class BadgeCreateView(StaffRequiredMixin, CreateView):
    model = GameHuyHieu
    form_class = GameHuyHieuForm
    template_name = 'gamification/badge_form.html'
    success_url = reverse_lazy('gamification:badge_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Tạo Huy Hiệu Mới'
        context['btn_text'] = 'Tạo mới'
        return context

# 4. UPDATE: Chỉnh sửa huy hiệu (Chỉ Staff)
class BadgeUpdateView(StaffRequiredMixin, UpdateView):
    model = GameHuyHieu
    form_class = GameHuyHieuForm
    template_name = 'gamification/badge_form.html'
    success_url = reverse_lazy('gamification:badge_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Cập nhật: {self.object.ten}'
        context['btn_text'] = 'Lưu thay đổi'
        return context

# 5. DELETE: Xóa huy hiệu (Chỉ Staff)
class BadgeDeleteView(StaffRequiredMixin, DeleteView):
    model = GameHuyHieu
    template_name = 'gamification/badge_confirm_delete.html'
    success_url = reverse_lazy('gamification:badge_list')