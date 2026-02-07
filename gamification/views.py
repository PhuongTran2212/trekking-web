<<<<<<< HEAD
# gamification/views.py

from django.shortcuts import render
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import OuterRef, Subquery, Case, When, Value, IntegerField

# Import Models
from .models import GameHuyHieu, GameHuyHieuNguoiDung
from .forms import GameHuyHieuForm
from core.models import The, DoKho  # <--- CHỈ IMPORT 1 LẦN Ở ĐÂY LÀ ĐỦ

# --- MIXIN KIỂM TRA QUYỀN ADMIN/STAFF ---
class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

# 1. READ: Danh sách tất cả huy hiệu (Dành cho Admin)
class BadgeListView(ListView):
    model = GameHuyHieu
    template_name = 'gamification/badge_list.html'
    context_object_name = 'badges'
    ordering = ['-id']

    def get_queryset(self):
        if self.request.user.is_staff:
            return GameHuyHieu.objects.all()
        return GameHuyHieu.objects.filter(is_active=True)

# 2. READ: Bảng thành tựu CỦA TÔI (User View)
class MyBadgeListView(LoginRequiredMixin, ListView):
    model = GameHuyHieu
    template_name = 'gamification/my_badges.html'
    context_object_name = 'badges_page'
    paginate_by = 12

    def get_queryset(self):
        user = self.request.user
        
        # Subquery lấy ngày nhận
        earned_subquery = GameHuyHieuNguoiDung.objects.filter(
            user=user,
            huy_hieu=OuterRef('pk')
        ).values('ngay_dat_duoc')[:1]

        # Annotate & Sắp xếp
        qs = GameHuyHieu.objects.filter(is_active=True).annotate(
            earned_at=Subquery(earned_subquery)
        ).annotate(
            status_order=Case(
                When(earned_at__isnull=False, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        )
        return qs.order_by('-status_order', 'earned_at', 'id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        total_badges = GameHuyHieu.objects.filter(is_active=True).count()
        earned_count = GameHuyHieuNguoiDung.objects.filter(user=user).count()
        
        progress_percent = 0
        if total_badges > 0:
            progress_percent = int((earned_count / total_badges) * 100)

        context['total_badges'] = total_badges
        context['earned_count'] = earned_count
        context['progress_percent'] = progress_percent
        return context

# 3. CREATE: Tạo huy hiệu mới (CẦN DANH SÁCH TAG & ĐỘ KHÓ)
class BadgeCreateView(StaffRequiredMixin, CreateView):
    model = GameHuyHieu
    form_class = GameHuyHieuForm
    template_name = 'gamification/badge_form.html'
    success_url = reverse_lazy('gamification:badge_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Tạo Huy Hiệu Mới'
        context['btn_text'] = 'Tạo mới'
        
        # Gửi dữ liệu cho Dropdown
        context['list_tags'] = The.objects.all().order_by('ten') 
        context['list_dokho'] = DoKho.objects.all().order_by('id')
        return context

# 4. UPDATE: Chỉnh sửa huy hiệu (CẦN DANH SÁCH TAG & ĐỘ KHÓ)
class BadgeUpdateView(StaffRequiredMixin, UpdateView):
    model = GameHuyHieu
    form_class = GameHuyHieuForm
    template_name = 'gamification/badge_form.html'
    success_url = reverse_lazy('gamification:badge_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Cập nhật: {self.object.ten}'
        context['btn_text'] = 'Lưu thay đổi'
        
        # Gửi dữ liệu cho Dropdown
        context['list_tags'] = The.objects.all().order_by('ten')
        context['list_dokho'] = DoKho.objects.all().order_by('id')
        return context

# 5. DELETE
class BadgeDeleteView(StaffRequiredMixin, DeleteView):
    model = GameHuyHieu
    template_name = 'gamification/badge_confirm_delete.html'
    success_url = reverse_lazy('gamification:badge_list')
=======
from django.shortcuts import render

# Create your views here.
>>>>>>> 2a3c570e2a74a83ea4beae6f32f15af4df86cb43
