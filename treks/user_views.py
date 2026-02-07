# treks/user_views.py

from django.http import JsonResponse
from django.urls import reverse
from django.views.generic import ListView, DetailView
from django.db.models import Q, Count, Avg
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models.functions import Coalesce
from trips.models import ChuyenDi
from .models import CungDuongTrek, CungDuongDanhGia, CungDuongAnhDanhGia
from .forms import CungDuongFilterForm, CungDuongDanhGiaForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.db.models import Subquery, OuterRef, Count, Q
# ==========================================================
# === CungDuongListView (Không đổi) ===
# ==========================================================
class CungDuongListView(ListView):
    model = CungDuongTrek
    template_name = 'treks/cung_duong_list.html'
    context_object_name = 'cung_duong_list'
    paginate_by = 9
    
    def get_queryset(self):
        # 1. Tạo Subquery đếm số chuyến đi SẮP DIỄN RA
        # [FIX LỖI]: Thay is_deleted bằng logic trang_thai và thời gian
        chuyen_di_subquery = ChuyenDi.objects.filter(
            cung_duong=OuterRef('pk'),
            trang_thai='DANG_TUYEN',       # Chỉ đếm chuyến đang tuyển
            ngay_bat_dau__gt=timezone.now() # Chỉ đếm chuyến trong tương lai
        ).values('cung_duong').annotate(cnt=Count('id')).values('cnt')

        # 2. Tạo Subquery đếm số bình luận (Giữ nguyên logic tốt của bạn)
        binh_luan_subquery = CungDuongDanhGia.objects.filter(
            cung_duong=OuterRef('pk')
        ).exclude(
            Q(binh_luan__isnull=True) | Q(binh_luan__exact='')
        ).values('cung_duong').annotate(cnt=Count('id')).values('cnt')

        # 3. Query chính: Áp dụng Subquery + Coalesce
        # Coalesce(..., 0) giúp chuyển None thành 0 nếu không tìm thấy dữ liệu
        queryset = CungDuongTrek.objects.filter(trang_thai='DA_DUYET').annotate(
            so_chuyen_di=Coalesce(Subquery(chuyen_di_subquery), 0),
            so_binh_luan=Coalesce(Subquery(binh_luan_subquery), 0)
        ).select_related('tinh_thanh', 'do_kho').order_by('-danh_gia_trung_binh', '-ngay_cap_nhat')

        # 4. Xử lý bộ lọc (Giữ nguyên logic của bạn)
        form = CungDuongFilterForm(self.request.GET)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            
            # Lọc theo từ khóa
            if q := cleaned_data.get('q'):
                queryset = queryset.filter(ten__icontains=q)
            
            # Lọc theo Dropdown (ForeignKey)
            if tinh_thanh := cleaned_data.get('tinh_thanh'):
                queryset = queryset.filter(tinh_thanh=tinh_thanh)

            if do_kho := cleaned_data.get('do_kho'):
                queryset = queryset.filter(do_kho=do_kho)

            # Lọc theo khoảng số (Range)
            if (min_do_dai := cleaned_data.get('min_do_dai')) is not None:
                queryset = queryset.filter(do_dai_km__gte=min_do_dai)
            
            if (max_do_dai := cleaned_data.get('max_do_dai')) is not None:
                queryset = queryset.filter(do_dai_km__lte=max_do_dai)

            if (min_danh_gia := cleaned_data.get('min_danh_gia')) is not None:
                queryset = queryset.filter(danh_gia_trung_binh__gte=min_danh_gia)

            if (min_do_cao := cleaned_data.get('min_do_cao')) is not None:
                queryset = queryset.filter(tong_do_cao_leo_m__gte=min_do_cao)
                
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Khám phá Cung đường"
        # Truyền form vào context để hiển thị lại lựa chọn cũ trên giao diện
        context['filter_form'] = CungDuongFilterForm(self.request.GET or None)
        return context

# ==========================================================
# === CungDuongDetailView (ĐÃ ĐƯỢC TỐI ƯU VÀ SỬA LỖI) ===
# ==========================================================
class CungDuongDetailView(DetailView):
    model = CungDuongTrek
    template_name = 'treks/cung_duong_detail.html'
    context_object_name = 'trek'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return CungDuongTrek.objects.filter(trang_thai='DA_DUYET')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trek = self.object
        all_reviews_qs = trek.danh_gia.select_related('user', 'user__taikhoanhoso').prefetch_related('anh_danh_gia').order_by('-ngay_danh_gia')

        paginator = Paginator(all_reviews_qs, 6)
        page_number = self.request.GET.get('page', 1)
        try:
            reviews_page = paginator.page(page_number)
        except (PageNotAnInteger, EmptyPage):
            reviews_page = paginator.page(1)
        
        context['reviews_page'] = reviews_page
        
        total_reviews = all_reviews_qs.count()
        average_rating = trek.danh_gia_trung_binh

        stats = {
            'total': total_reviews,
            'with_comment': all_reviews_qs.exclude(Q(binh_luan__isnull=True) | Q(binh_luan__exact='')).count(),
            'with_media': all_reviews_qs.filter(anh_danh_gia__isnull=False).distinct().count(),
            'stars': {}
        }
        if total_reviews > 0:
            star_counts = all_reviews_qs.values('diem_danh_gia').annotate(count=Count('id'))
            counts_dict = {item['diem_danh_gia']: item['count'] for item in star_counts}
            for i in range(5, 0, -1):
                stats['stars'][i] = counts_dict.get(i, 0)
        
        user_has_reviewed = False
        if self.request.user.is_authenticated:
            user_has_reviewed = all_reviews_qs.filter(user=self.request.user).exists()
        
        context['page_title'] = trek.ten
        context['total_reviews'] = total_reviews
        context['average_rating'] = average_rating
        context['review_stats'] = stats
        context['user_has_reviewed'] = user_has_reviewed
        
        if 'review_form' not in context and self.request.user.is_authenticated and not user_has_reviewed:
            context['review_form'] = CungDuongDanhGiaForm()
            
        return context
    
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Bạn cần đăng nhập để thực hiện hành động này.")
            return redirect('accounts:dang-nhap')

        self.object = self.get_object()
        review_id = request.POST.get('review_id')
        
       # --- TRƯỜNG HỢP CẬP NHẬT ĐÁNH GIÁ (TỪ MODAL) ---
        if review_id:
            review_to_update = get_object_or_404(CungDuongDanhGia, pk=review_id, user=request.user)
                
            update_form = CungDuongDanhGiaForm(request.POST, instance=review_to_update)
            if update_form.is_valid():
                with transaction.atomic():
                    # Lưu các thay đổi về rating và bình luận
                    updated_review = update_form.save(commit=False)
                    updated_review.ngay_danh_gia = timezone.now() # Cập nhật lại thời gian
                    updated_review.save()
                    
                    # Thêm ảnh mới nếu có
                    for f in request.FILES.getlist('hinh_anh_moi'): 
                        CungDuongAnhDanhGia.objects.create(danh_gia=updated_review, hinh_anh=f)

                    # === PHẦN MỚI: XỬ LÝ XÓA ẢNH ===
                    images_to_delete_str = request.POST.get('images_to_delete')
                    if images_to_delete_str:
                        # Chuyển chuỗi "42,45,48" thành một list các số nguyên
                        try:
                            image_ids_to_delete = [int(pk) for pk in images_to_delete_str.split(',') if pk.strip().isdigit()]
                        except (ValueError, TypeError):
                            image_ids_to_delete = []
                        
                        if image_ids_to_delete:
                            # Xóa các ảnh có pk nằm trong list và thuộc về đánh giá đang sửa
                            # (Thêm `danh_gia=updated_review` để tăng cường bảo mật)
                            CungDuongAnhDanhGia.objects.filter(
                                pk__in=image_ids_to_delete,
                                danh_gia=updated_review
                            ).delete()
                    # === KẾT THÚC PHẦN XÓA ẢNH ===
                messages.success(request, "Đã cập nhật đánh giá của bạn.")
            else:
                # Chuyển lỗi form thành message để hiển thị
                error_str = ". ".join([f"{field}: {', '.join(errors)}" for field, errors in update_form.errors.items()])
                messages.error(request, f"Lỗi khi cập nhật: {error_str}")
            return redirect(self.object.get_absolute_url() + '#reviews')

        # --- TRƯỜNG HỢP TẠO MỚI ĐÁNH GIÁ ---
        if CungDuongDanhGia.objects.filter(cung_duong=self.object, user=request.user).exists():
            messages.warning(request, "Bạn đã đánh giá cung đường này rồi.")
            return redirect(self.object.get_absolute_url() + '#reviews')
        
        review_form = CungDuongDanhGiaForm(request.POST, request.FILES)
        if review_form.is_valid():
            with transaction.atomic():
                new_review = review_form.save(commit=False)
                new_review.cung_duong = self.object
                new_review.user = request.user
                new_review.save()
                for f in request.FILES.getlist('hinh_anh'): 
                    CungDuongAnhDanhGia.objects.create(danh_gia=new_review, hinh_anh=f)
            messages.success(request, "Cảm ơn bạn đã gửi đánh giá!")
            return redirect(self.object.get_absolute_url() + '#reviews')
        else:
            messages.error(request, "Đã có lỗi xảy ra. Vui lòng kiểm tra lại thông tin.")
            context = self.get_context_data()
            context['review_form'] = review_form
            return self.render_to_response(context)

# ==========================================================
# === VIEW ĐỂ LẤY DỮ LIỆU JSON CHO MODAL SỬA ĐÁNH GIÁ ===
# ==========================================================
# === VIEW ĐỂ LẤY DỮ LIỆU JSON (CẬP NHẬT) ===
@login_required
def get_review_data(request, pk):
    review = get_object_or_404(CungDuongDanhGia, pk=pk)
    
    if review.user != request.user and not request.user.is_staff:
        return JsonResponse({'error': 'Không có quyền truy cập.'}, status=403)
        
    images = []
    for img in review.anh_danh_gia.all():
        images.append({
            'id': img.id,
            'url': img.hinh_anh.url
        })

    data = {
        'id': review.id,
        'rating': review.diem_danh_gia,
        'comment': review.binh_luan,
        'images': images, # <--- Trả về danh sách ảnh
    }
    return JsonResponse(data)
# === VIEW MỚI ĐỂ XÓA ẢNH REVIEW ===
@login_required

@login_required
def delete_review_image(request, pk):
    image = get_object_or_404(CungDuongAnhDanhGia, pk=pk)
    
    # Kiểm tra quyền sở hữu
    if image.danh_gia.user != request.user and not request.user.is_staff:
        return JsonResponse({'status': 'error', 'message': 'Không có quyền xóa ảnh này.'}, status=403)
    
    image.delete()
    return JsonResponse({'status': 'success', 'message': 'Đã xóa ảnh.'})

# ==========================================================
# === VIEW ĐỂ XÓA ĐÁNH GIÁ ===
# ==========================================================
@login_required
def delete_review(request, pk):
    review = get_object_or_404(CungDuongDanhGia, pk=pk)
    if review.user != request.user and not request.user.is_staff:
        messages.error(request, "Bạn không có quyền xóa đánh giá này.")
        return redirect(review.cung_duong.get_absolute_url())
    
    trek_slug = review.cung_duong.slug
    review.delete()
    messages.success(request, "Đã xóa đánh giá của bạn.")
    return redirect('treks:cung_duong_detail', slug=trek_slug)