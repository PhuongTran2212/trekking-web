# articles/views.py
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
# Quan trọng: Đảm bảo bạn đã import CreateView
from django.views.generic import ListView, UpdateView, DeleteView, CreateView

from .models import BaiHuongDan, ChuyenMuc # Import ChuyenMuc
from .forms import BaiHuongDanAdminForm, ChuyenMucForm # Import ChuyenMucForm

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

class AdminArticleListView(AdminRequiredMixin, ListView):
    model = BaiHuongDan
    template_name = 'articles/admin_article_list.html'
    context_object_name = 'articles'
    paginate_by = 10

class AdminArticleUpdateView(AdminRequiredMixin, UpdateView):
    model = BaiHuongDan
    form_class = BaiHuongDanAdminForm
    template_name = 'articles/admin_article_form.html'
    success_url = reverse_lazy('articles:admin-list')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Chỉnh sửa bài viết"
        return context

class AdminArticleDeleteView(AdminRequiredMixin, DeleteView):
    model = BaiHuongDan
    template_name = 'articles/admin_article_confirm_delete.html'
    success_url = reverse_lazy('articles:admin-list')

@require_POST
@user_passes_test(lambda u: u.is_staff)
def approve_article(request, pk):
    article = get_object_or_404(BaiHuongDan, pk=pk)
    if not article.da_duyet:
        article.da_duyet = True
        article.nguoi_duyet = request.user
        article.ngay_duyet = timezone.now()
        article.save()
        messages.success(request, f"Đã duyệt thành công bài viết '{article.tieu_de}'.")
    else:
        messages.warning(request, "Bài viết này đã được duyệt trước đó.")
    return redirect('articles:admin-list')

# ===================================================================
# === BỔ SUNG CLASS VIEW NÀY (ĐÂY LÀ PHẦN BỊ THIẾU GÂY LỖI) ===
# ===================================================================
class AdminArticleCreateView(AdminRequiredMixin, CreateView):
    """
    View dành riêng cho Admin tạo bài viết mới.
    Bài viết được tạo sẽ tự động được duyệt.
    """
    model = BaiHuongDan
    form_class = BaiHuongDanAdminForm
    template_name = 'articles/admin_article_form.html' # Dùng chung template form
    success_url = reverse_lazy('articles:admin-list')

    def form_valid(self, form):
        form.instance.tac_gia = self.request.user
        # Vì Admin tạo, bài viết sẽ được duyệt ngay lập tức
        form.instance.da_duyet = True
        form.instance.nguoi_duyet = self.request.user
        form.instance.ngay_duyet = timezone.now()
        messages.success(self.request, "Bài viết đã được tạo và đăng thành công!")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Tạo bài viết kiến thức mới"
        return context
    
class ChuyenMucListView(AdminRequiredMixin, ListView):
    """View hiển thị danh sách tất cả chuyên mục."""
    model = ChuyenMuc
    template_name = 'articles/admin_category_list.html'
    context_object_name = 'categories'
    paginate_by = 10

class ChuyenMucCreateView(AdminRequiredMixin, CreateView):
    """View cho Admin tạo chuyên mục mới."""
    model = ChuyenMuc
    form_class = ChuyenMucForm
    template_name = 'articles/admin_category_form.html'
    success_url = reverse_lazy('articles:admin-category-list')

    def form_valid(self, form):
        messages.success(self.request, f"Đã tạo thành công chuyên mục '{form.instance.ten}'.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Thêm chuyên mục mới"
        return context

class ChuyenMucUpdateView(AdminRequiredMixin, UpdateView):
    """View cho Admin chỉnh sửa chuyên mục."""
    model = ChuyenMuc
    form_class = ChuyenMucForm
    template_name = 'articles/admin_category_form.html'
    success_url = reverse_lazy('articles:admin-category-list')

    def form_valid(self, form):
        messages.success(self.request, f"Đã cập nhật thành công chuyên mục '{form.instance.ten}'.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Chỉnh sửa chuyên mục: {self.object.ten}"
        return context

class ChuyenMucDeleteView(AdminRequiredMixin, DeleteView):
    """View cho Admin xóa chuyên mục."""
    model = ChuyenMuc
    template_name = 'articles/admin_category_confirm_delete.html'
    success_url = reverse_lazy('articles:admin-category-list')

    def form_valid(self, form):
        messages.success(self.request, f"Đã xóa thành công chuyên mục '{self.object.ten}'.")
        return super().form_valid(form)