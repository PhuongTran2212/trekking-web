# treks/user_views.py (ĐÃ SỬA LỖI)
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import CungDuongTrek, CungDuongDanhGia, CungDuongAnhDanhGia
# BỎ IMPORT FORM UPLOAD
from .forms import CungDuongFilterForm, CungDuongDanhGiaForm
from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.urls import reverse

# ... (CungDuongListView không đổi) ...
class CungDuongListView(ListView):
    model = CungDuongTrek
    template_name = 'treks/cung_duong_list.html'
    context_object_name = 'cung_duong_list'
    paginate_by = 9
    def get_queryset(self):
        queryset = CungDuongTrek.objects.filter(trang_thai='DA_DUYET').order_by('-danh_gia_trung_binh', '-ngay_cap_nhat')
        form = CungDuongFilterForm(self.request.GET)
        if form.is_valid():
            q, tinh_thanh, do_kho, min_do_dai, max_do_dai = (form.cleaned_data.get(k) for k in ['q', 'tinh_thanh', 'do_kho', 'min_do_dai', 'max_do_dai'])
            if q: queryset = queryset.filter(ten__icontains=q)
            if tinh_thanh: queryset = queryset.filter(tinh_thanh=tinh_thanh)
            if do_kho: queryset = queryset.filter(do_kho=do_kho)
            if min_do_dai: queryset = queryset.filter(do_dai_km__gte=min_do_dai)
            if max_do_dai: queryset = queryset.filter(do_dai_km__lte=max_do_dai)
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Khám phá Cung đường"
        context['filter_form'] = CungDuongFilterForm(self.request.GET or None)
        return context

# ==========================================================
# === THAY THẾ TOÀN BỘ CLASS NÀY ===
# ==========================================================
class CungDuongDetailView(DetailView):
    model = CungDuongTrek
    template_name = 'treks/cung_duong_detail.html'
    context_object_name = 'trek'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        # Chỉ hiển thị các cung đường đã được duyệt
        return CungDuongTrek.objects.filter(trang_thai='DA_DUYET')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trek = self.object
        
        # 1. Lấy tất cả đánh giá và tối ưu hóa truy vấn
        all_reviews = trek.danh_gia.select_related('user', 'user__taikhoanhoso').prefetch_related('anh_danh_gia').order_by('-ngay_danh_gia')
        
        total_reviews = all_reviews.count()
        # Lấy điểm trung bình đã được tính sẵn từ model (do signal cập nhật)
        average_rating = trek.danh_gia_trung_binh
        
        # 2. TÍNH TOÁN PHÂN BỐ ĐÁNH GIÁ (RATING BREAKDOWN)
        rating_breakdown = []
        if total_reviews > 0:
            star_counts = all_reviews.values('diem_danh_gia').annotate(count=Count('id'))
            counts_dict = {item['diem_danh_gia']: item['count'] for item in star_counts}
            for i in range(5, 0, -1):
                count = counts_dict.get(i, 0)
                # Tính toán tỷ lệ phần trăm
                percentage = (count / total_reviews) * 100
                rating_breakdown.append({
                    'stars': i,
                    'count': count,
                    'percentage': percentage
                })
        
        # 3. KIỂM TRA XEM USER HIỆN TẠI ĐÃ ĐÁNH GIÁ CHƯA
        user_has_reviewed = False
        if self.request.user.is_authenticated:
            user_has_reviewed = all_reviews.filter(user=self.request.user).exists()
        
        # 4. TRUYỀN TẤT CẢ DỮ LIỆU SANG TEMPLATE
        context['page_title'] = trek.ten
        context['reviews'] = all_reviews # Danh sách chi tiết các đánh giá
        context['total_reviews'] = total_reviews # Tổng số
        context['average_rating'] = average_rating # Điểm trung bình
        context['rating_breakdown'] = rating_breakdown # Dữ liệu cho biểu đồ
        context['user_has_reviewed'] = user_has_reviewed
        context['vat_dung_goi_y'] = trek.vat_dung_goi_y.all()
        
        # Chỉ truyền form nếu user chưa đánh giá và form chưa được thêm vào context (tránh ghi đè khi post lỗi)
        if 'review_form' not in context and self.request.user.is_authenticated and not user_has_reviewed:
            context['review_form'] = CungDuongDanhGiaForm()
            
        return context
    
    def post(self, request, *args, **kwargs):
        # Hàm post của bạn đã đúng, giữ nguyên
        if not request.user.is_authenticated:
            messages.error(request, "Bạn cần đăng nhập để đánh giá."); return redirect('accounts:dang-nhap')
        trek = self.get_object()
        if CungDuongDanhGia.objects.filter(cung_duong=trek, user=request.user).exists():
            messages.error(request, "Bạn đã đánh giá cung đường này rồi."); return redirect(trek.get_absolute_url() + '#reviews')
        
        review_form = CungDuongDanhGiaForm(request.POST, request.FILES)

        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.cung_duong, review.user = trek, request.user
            review.save()
            
            for f in request.FILES.getlist('hinh_anh'): 
                CungDuongAnhDanhGia.objects.create(danh_gia=review, hinh_anh=f)
            
            messages.success(request, "Cảm ơn bạn đã gửi đánh giá!"); 
            return redirect(trek.get_absolute_url() + '#reviews')
        else:
            context = self.get_context_data()
            context['review_form'] = review_form
            messages.error(request, "Đã có lỗi xảy ra, vui lòng kiểm tra lại thông tin."); 
            return self.render_to_response(context)
        # ==========================================================
# === VIEW MỚI ĐỂ XÓA ĐÁNH GIÁ ===
# ==========================================================
def delete_review(request, pk):
    review = get_object_or_404(CungDuongDanhGia, pk=pk)
    # Chỉ chủ sở hữu hoặc admin mới được xóa
    if review.user != request.user and not request.user.is_staff:
        messages.error(request, "Bạn không có quyền xóa đánh giá này.")
        return redirect(review.cung_duong.get_absolute_url())
    
    trek_slug = review.cung_duong.slug
    review.delete()
    messages.success(request, "Đã xóa đánh giá của bạn.")
    return redirect('treks:cung_duong_detail', slug=trek_slug)


# ==========================================================
# === VIEW MỚI ĐỂ SỬA ĐÁNH GIÁ ===
# ==========================================================
class UpdateReviewView(LoginRequiredMixin, UpdateView):
    model = CungDuongDanhGia
    form_class = CungDuongDanhGiaForm
    template_name = 'treks/review_update_form.html' # Sẽ tạo template này ở bước sau

    def get_object(self, queryset=None):
        obj = super().get_object()
        # Chỉ chủ sở hữu hoặc admin mới được sửa
        if obj.user != self.request.user and not self.request.user.is_staff:
            raise PermissionDenied
        return obj

    def get_success_url(self):
        messages.success(self.request, "Đã cập nhật đánh giá của bạn.")
        return reverse('treks:cung_duong_detail', slug=self.object.cung_duong.slug)