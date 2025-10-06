# treks/views.py

from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator

from .models import CungDuongTrek
from .forms import TrekFilterForm, CungDuongTrekForm

# Hàm kiểm tra quyền Admin
def is_admin_check(user):
    return user.is_staff

# ==============================================================================
# === VIEW CHO NGƯỜI DÙNG / GUEST (ĐÃ CÓ TỪ TRƯỚC) ===
# ==============================================================================
# Giữ lại view này, không thay đổi
def danh_sach_cung_duong(request):
    # ... code cũ ...
    pass # Để ngắn gọn, không viết lại code ở đây


# ==============================================================================
# === CÁC VIEW MỚI CHO TRANG DASHBOARD ADMIN ===
# ==============================================================================

# Dùng decorator để bảo vệ tất cả các view dưới đây
@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin_check), name='dispatch')
class CungDuongListView(ListView):
    model = CungDuongTrek
    template_name = 'admin/treks/cung_duong_list.html' # Template mới
    context_object_name = 'cung_duong_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('tinh_thanh', 'do_kho').order_by('-ngay_tao')
        
        search_query = self.request.GET.get('q', '')
        if search_query:
            queryset = queryset.filter(
                Q(ten__icontains=search_query) | Q(tinh_thanh__ten__icontains=search_query)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        return context

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin_check), name='dispatch')
class CungDuongCreateView(CreateView):
    model = CungDuongTrek
    form_class = CungDuongTrekForm
    template_name = 'admin/treks/cung_duong_form.html' # Template mới
    success_url = reverse_lazy('treks_admin:cung_duong_list') # URL để quay về sau khi tạo thành công

    def form_valid(self, form):
        form.instance.nguoi_tao = self.request.user
        # Thêm thông báo thành công (tùy chọn)
        # messages.success(self.request, "Tạo cung đường mới thành công!")
        return super().form_valid(form)

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin_check), name='dispatch')
class CungDuongUpdateView(UpdateView):
    model = CungDuongTrek
    form_class = CungDuongTrekForm
    template_name = 'admin/treks/cung_duong_form.html' # Dùng chung template với Create
    success_url = reverse_lazy('treks_admin:cung_duong_list')

@method_decorator(login_required, name='dispatch')
@method_decorator(user_passes_test(is_admin_check), name='dispatch')
class CungDuongDeleteView(DeleteView):
    model = CungDuongTrek
    template_name = 'admin/treks/cung_duong_confirm_delete.html' # Template mới
    success_url = reverse_lazy('treks_admin:cung_duong_list')