# knowledge/views.py
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView

# Quan trọng: Import model và form từ các app khác
from articles.models import BaiHuongDan
from .forms import ContributionForm

class KnowledgeListView(ListView):
    """Hiển thị TẤT CẢ các bài viết ĐÃ ĐƯỢC DUYỆT."""
    model = BaiHuongDan
    template_name = 'knowledge/knowledge_list.html'
    context_object_name = 'articles'
    paginate_by = 9
    
    # Chỉ lấy các bài đã duyệt
    queryset = BaiHuongDan.objects.filter(da_duyet=True).order_by('-ngay_duyet')

class KnowledgeDetailView(DetailView):
    """Hiển thị chi tiết một bài viết ĐÃ ĐƯỢC DUYỆT."""
    model = BaiHuongDan
    template_name = 'knowledge/knowledge_detail.html'
    context_object_name = 'article'

    # Để bảo mật, chỉ cho phép xem các bài đã duyệt
    def get_queryset(self):
        return super().get_queryset().filter(da_duyet=True)

class ContributionCreateView(LoginRequiredMixin, CreateView):
    """Form cho người dùng đóng góp bài viết."""
    model = BaiHuongDan
    form_class = ContributionForm
    template_name = 'knowledge/contribution_form.html'
    success_url = reverse_lazy('knowledge:list') # Sau khi gửi, quay về trang danh sách

    def form_valid(self, form):
        # Tự động gán tác giả là user đang đăng nhập
        form.instance.tac_gia = self.request.user
        # Trạng thái da_duyet mặc định là False, không cần gán
        messages.success(self.request, "Cảm ơn bạn đã đóng góp! Bài viết của bạn đã được gửi đi và đang chờ quản trị viên phê duyệt.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Đóng góp kiến thức"
        return context