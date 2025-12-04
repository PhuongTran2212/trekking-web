# articles/views.py
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.decorators import user_passes_test
from django.views.decorators.http import require_POST
from django.views.generic import ListView, UpdateView, DeleteView, CreateView
from django.views.generic import DetailView
from django.http import Http404
from .models import BaiHuongDan, ChuyenMuc
from .forms import BaiHuongDanAdminForm, ChuyenMucForm

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

class AdminArticleListView(AdminRequiredMixin, ListView):
    model = BaiHuongDan
    template_name = 'articles/admin_article_list.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('tac_gia', 'chuyen_muc').order_by('-ngay_dang')
        
        # Lấy tham số từ URL
        search_query = self.request.GET.get('q', '')
        category_id = self.request.GET.get('category', '')
        status = self.request.GET.get('status', '') # <-- MỚI

        # Lọc theo query tìm kiếm
        if search_query:
            queryset = queryset.filter(tieu_de__icontains=search_query)
        
        # Lọc theo chuyên mục
        if category_id:
            queryset = queryset.filter(chuyen_muc_id=category_id)
            
        # Lọc theo trạng thái <-- MỚI
        if status == 'approved':
            queryset = queryset.filter(da_duyet=True)
        elif status == 'pending':
            queryset = queryset.filter(da_duyet=False)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Gửi danh sách chuyên mục và các giá trị filter hiện tại ra template
        context['categories'] = ChuyenMuc.objects.all()
        context['current_q'] = self.request.GET.get('q', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_status'] = self.request.GET.get('status', '') # <-- MỚI

        # Tạo query string để giữ bộ lọc khi chuyển trang <-- MỚI
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['filter_query_string'] = query_params.urlencode()
        
        return context

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

class AdminArticleCreateView(AdminRequiredMixin, CreateView):
    model = BaiHuongDan
    form_class = BaiHuongDanAdminForm
    template_name = 'articles/admin_article_form.html'
    success_url = reverse_lazy('articles:admin-list')

    def form_valid(self, form):
        form.instance.tac_gia = self.request.user
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
    model = ChuyenMuc
    template_name = 'articles/admin_category_list.html'
    context_object_name = 'categories'
    paginate_by = 10

class ChuyenMucCreateView(AdminRequiredMixin, CreateView):
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
    model = ChuyenMuc
    template_name = 'articles/admin_category_confirm_delete.html'
    success_url = reverse_lazy('articles:admin-category-list')

    def form_valid(self, form):
        messages.success(self.request, f"Đã xóa thành công chuyên mục '{self.object.ten}'.")
        return super().form_valid(form)

class ArticleDetailView(DetailView):
    model = BaiHuongDan
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        # Nếu bài viết chưa duyệt và người xem KHÔNG phải là Admin/Staff -> Báo lỗi 404
        if not obj.da_duyet and not self.request.user.is_staff:
            raise Http404("Bài viết này không tồn tại hoặc chưa được duyệt.")
        return obj