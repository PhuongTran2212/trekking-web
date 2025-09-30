# treks/user_views.py (ĐÃ SỬA LỖI)
from django.views.generic import ListView, DetailView
from django.db.models import Q
from django.shortcuts import redirect
from django.contrib import messages
from .models import CungDuongTrek, CungDuongDanhGia, CungDuongAnhDanhGia
# BỎ IMPORT FORM UPLOAD
from .forms import CungDuongFilterForm, CungDuongDanhGiaForm

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

class CungDuongDetailView(DetailView):
    model = CungDuongTrek
    template_name = 'treks/cung_duong_detail.html'
    context_object_name = 'trek'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    def get_queryset(self): return CungDuongTrek.objects.filter(trang_thai='DA_DUYET')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trek = self.get_object()
        context['page_title'] = trek.ten
        context['vat_dung_goi_y'] = trek.vat_dung_goi_y.all()
        reviews = trek.danh_gia.all().order_by('-ngay_danh_gia')
        context['reviews'] = reviews
        user_has_reviewed = False
        if self.request.user.is_authenticated:
            if reviews.filter(user=self.request.user).exists(): user_has_reviewed = True
        context['user_has_reviewed'] = user_has_reviewed
        if not user_has_reviewed and self.request.user.is_authenticated:
            context['review_form'] = CungDuongDanhGiaForm()
        return context
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Bạn cần đăng nhập để đánh giá."); return redirect('accounts:dang-nhap')
        trek = self.get_object()
        if CungDuongDanhGia.objects.filter(cung_duong=trek, user=request.user).exists():
            messages.error(request, "Bạn đã đánh giá cung đường này rồi."); return redirect('treks:cung_duong_detail', slug=trek.slug)
        
        review_form = CungDuongDanhGiaForm(request.POST)

        if review_form.is_valid():
            review = review_form.save(commit=False)
            review.cung_duong, review.user = trek, request.user
            review.save()
            
            # VÒNG LẶP NÀY XỬ LÝ NHIỀU FILE TỪ <input name="hinh_anh" multiple>
            for f in request.FILES.getlist('hinh_anh'): 
                CungDuongAnhDanhGia.objects.create(danh_gia=review, hinh_anh=f)
            
            messages.success(request, "Cảm ơn bạn đã gửi đánh giá!"); 
            return redirect('treks:cung_duong_detail', slug=trek.slug)
        else:
            context = self.get_context_data()
            context['review_form'] = review_form # Trả về form với lỗi
            messages.error(request, "Đã có lỗi xảy ra, vui lòng kiểm tra lại thông tin."); 
            return self.render_to_response(context)