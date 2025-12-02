# treks/views.py
from django.utils import timezone  # <--- BẮT BUỘC PHẢI LÀ DÒNG NÀY
from datetime import timedelta     # <--- Để dùng tính toán trừ lùi ngày
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.db import transaction
from django.db.models import Q, Count, Avg
import requests

from .models import CungDuongTrek, CungDuongMedia, TrangThaiDuyet, CungDuongDanhGia
from .forms import CungDuongTrekAdminForm, CungDuongTrekFilterForm, CungDuongMapForm # Thêm CungDuongMapForm

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

class CungDuongBaseView:
    """Mixin chứa toàn bộ logic xử lý upload media."""
    def handle_media_uploads(self, request, trek_instance):
        # 1. Xử lý các file từ thư viện (từ input name='files_to_upload')
        gallery_files = request.FILES.getlist('files_to_upload')
        if gallery_files:
            for f in gallery_files:
                loai = 'ANH' if f.content_type.startswith('image') else 'VIDEO'
                CungDuongMedia.objects.create(
                    cung_duong=trek_instance, 
                    file=f, 
                    loai_media=loai,
                    la_anh_bia=False
                )
            messages.info(request, f"Đã tải lên thành công {len(gallery_files)} file media mới.")


class CungDuongListView(AdminRequiredMixin, ListView):
    model = CungDuongTrek
    template_name = 'admin/treks/cungduong_list.html'
    context_object_name = 'cung_duong_list'
    paginate_by = 10

    # treks/views.py

    def get_queryset(self):
        # 1. Query gốc (như cũ)
        queryset = super().get_queryset()\
            .select_related('tinh_thanh', 'do_kho', 'nguoi_tao')\
            .annotate(media_count=Count('media'))
            # LƯU Ý: Tạm thời bỏ .order_by() ở đây để xử lý bên dưới
        
        self.filter_form = CungDuongTrekFilterForm(self.request.GET)
        
        # Mặc định sắp xếp nếu không chọn gì
        ordering = '-ngay_cap_nhat'

        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            
            # ... (Giữ nguyên logic lọc q, tinh_thanh, do_kho, trang_thai cũ) ...
            if data.get('q'):
                queryset = queryset.filter(Q(ten__icontains=data['q']) | Q(dia_diem_chi_tiet__icontains=data['q']))
            if data.get('tinh_thanh'):
                queryset = queryset.filter(tinh_thanh=data['tinh_thanh'])
            if data.get('do_kho'):
                queryset = queryset.filter(do_kho=data['do_kho'])
            if data.get('trang_thai'):
                queryset = queryset.filter(trang_thai=data['trang_thai'])

            # ... (Giữ nguyên logic lọc bo_loc_nhanh cũ) ...
            loc_nhanh = data.get('bo_loc_nhanh')
            if loc_nhanh == 'missing_map':
                queryset = queryset.filter(Q(du_lieu_ban_do_geojson__isnull=True) | Q(du_lieu_ban_do_geojson__exact={}) | Q(du_lieu_ban_do_geojson__exact=''))
            elif loc_nhanh == 'missing_image':
                queryset = queryset.filter(media_count=0)
            elif loc_nhanh == 'low_rating':
                queryset = queryset.filter(danh_gia_trung_binh__lt=3.0, so_luot_danh_gia__gt=0)
            elif loc_nhanh == 'no_reviews':
                queryset = queryset.filter(so_luot_danh_gia=0)
            elif loc_nhanh == 'outdated':
                sau_thang_truoc = timezone.now() - timedelta(days=180)
                queryset = queryset.filter(ngay_cap_nhat__lt=sau_thang_truoc)

            # === XỬ LÝ LOGIC MỚI ===
            
            # 1. Lọc theo Người tạo (Admin vs User)
            author_type = data.get('author_type')
            if author_type == 'admin':
                queryset = queryset.filter(nguoi_tao__is_staff=True)
            elif author_type == 'user':
                queryset = queryset.filter(nguoi_tao__is_staff=False)

            # 2. Xử lý Sắp xếp
            sort_by = data.get('sort_by')
            if sort_by == 'oldest':
                ordering = 'ngay_cap_nhat' # Cũ nhất lên đầu
            elif sort_by == 'rating_desc':
                ordering = '-danh_gia_trung_binh' # Điểm cao nhất
            elif sort_by == 'rating_asc':
                ordering = 'danh_gia_trung_binh' # Điểm thấp nhất
            elif sort_by == 'review_desc':
                ordering = '-so_luot_danh_gia' # Nhiều review nhất
            else:
                ordering = '-ngay_cap_nhat' # Mặc định: Mới nhất
            # === XỬ LÝ LỌC CHỈ SỐ (MỚI) ===
            # 1. Lọc Độ dài
            if data.get('min_len'):
                queryset = queryset.filter(do_dai_km__gte=data['min_len'])
            if data.get('max_len'):
                queryset = queryset.filter(do_dai_km__lte=data['max_len'])

            # 2. Lọc Thời gian
            if data.get('min_time'):
                queryset = queryset.filter(thoi_gian_uoc_tinh_gio__gte=data['min_time'])
            if data.get('max_time'):
                queryset = queryset.filter(thoi_gian_uoc_tinh_gio__lte=data['max_time'])

            # 3. Lọc Độ cao
            if data.get('min_high'):
                queryset = queryset.filter(tong_do_cao_leo_m__gte=data['min_high'])
            if data.get('max_high'):
                queryset = queryset.filter(tong_do_cao_leo_m__lte=data['max_high'])

        return queryset.order_by(ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # --- THÊM PHẦN THỐNG KÊ TỔNG QUAN (DASHBOARD MINI) ---
        
        # 1. Tổng số cung đường hiện có
        context['total_treks'] = CungDuongTrek.objects.count()
        
        # 2. Số lượng bài đang CHỜ DUYỆT (Quan trọng nhất với Admin)
        context['pending_count'] = CungDuongTrek.objects.filter(trang_thai=TrangThaiDuyet.CHO_DUYET).count()
        
        # 3. Tổng số lượt đánh giá trên toàn hệ thống
        context['total_reviews'] = CungDuongDanhGia.objects.count()
        
        # 4. Điểm đánh giá trung bình của toàn bộ các cung đường
        avg_rating = CungDuongTrek.objects.aggregate(Avg('danh_gia_trung_binh'))['danh_gia_trung_binh__avg']
        context['global_avg_rating'] = round(avg_rating, 1) if avg_rating else 0.0

        # ... (giữ nguyên phần context filter_form cũ) ...
        context['page_title'] = "Quản lý Cung đường"
        context['filter_form'] = getattr(self, 'filter_form', CungDuongTrekFilterForm(self.request.GET))
        
        # Giữ query params khi phân trang
        params = self.request.GET.copy()
        if 'page' in params: del params['page']
        context['query_params'] = params.urlencode()
        
        return context
        return context

class CungDuongCreateView(AdminRequiredMixin, CungDuongBaseView, CreateView):
    model = CungDuongTrek
    form_class = CungDuongTrekAdminForm
    template_name = 'admin/treks/cungduong_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Thêm Cung đường mới"
        return context

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.nguoi_tao = self.request.user
        if not form.cleaned_data.get('trang_thai'):
            self.object.trang_thai = TrangThaiDuyet.DA_DUYET
        try:
            with transaction.atomic():
                self.object.save()
                form.save_m2m() 
                self.handle_media_uploads(self.request, self.object)
            messages.success(self.request, f"Đã tạo thành công cung đường '{self.object.ten}'.")
            return redirect(self.get_success_url())
        except Exception as e:
            messages.error(self.request, f"Lỗi khi tạo cung đường: {e}")
            return self.form_invalid(form)

    def get_success_url(self):
        # SAU KHI TẠO XONG, CHUYỂN NGAY ĐẾN TRANG CHỈNH SỬA BẢN ĐỒ
        messages.info(self.request, "Tiếp theo: Hãy chọn vị trí trên bản đồ cho cung đường vừa tạo.")
        return reverse('treks_admin:cung_duong_edit_map', kwargs={'pk': self.object.pk})

# treks/views.py

# THAY THẾ TOÀN BỘ CLASS NÀY
class CungDuongUpdateView(AdminRequiredMixin, CungDuongBaseView, UpdateView):
    model = CungDuongTrek
    form_class = CungDuongTrekAdminForm
    template_name = 'admin/treks/cungduong_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Chỉnh sửa: {self.object.ten}"
        return context
        
    def form_valid(self, form):
        """
        Hàm này được gọi khi form chính hợp lệ.
        Nó sẽ lưu thông tin và gọi hàm xử lý upload.
        """
        try:
            with transaction.atomic():
                # Lưu thông tin chính từ form
                self.object = form.save()
                
                # Gọi hàm xử lý upload file media mới
                self.handle_media_uploads(self.request, self.object)

            messages.success(self.request, f"Đã cập nhật thành công thông tin cho '{self.object.ten}'.")
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            messages.error(self.request, f"Lỗi khi cập nhật: {e}")
            return self.form_invalid(form)
        
    def get_success_url(self):
        # Sau khi lưu, ở lại trang chỉnh sửa
        return reverse('treks_admin:cung_duong_update', kwargs={'pk': self.object.pk})

class CungDuongDetailView(AdminRequiredMixin, DetailView):
    model = CungDuongTrek
    template_name = 'admin/treks/cungduong_detail.html'
    context_object_name = 'trek'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Chi tiết: {self.object.ten}"
        reviews = CungDuongDanhGia.objects.filter(cung_duong=self.object).order_by('-ngay_danh_gia')
        context['reviews'] = reviews
        context['total_reviews'] = reviews.count()
        return context

class CungDuongDeleteView(AdminRequiredMixin, DeleteView):
    model = CungDuongTrek
    template_name = 'admin/treks/confirm_delete.html'
    success_url = reverse_lazy('treks_admin:cung_duong_list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Đã xóa vĩnh viễn cung đường '{self.object.ten}'.")
        return super().form_valid(form)

def delete_media_view(request, pk):
    if request.method != 'POST': return redirect('treks_admin:cung_duong_list')
    if not request.user.is_staff: return redirect('treks_admin:cung_duong_list')
    try:
        media = get_object_or_404(CungDuongMedia, pk=pk)
        cung_duong_pk = media.cung_duong.pk
        media.delete() 
        messages.success(request, "Đã xóa thành công media.")
        return redirect('treks_admin:cung_duong_update', pk=cung_duong_pk)
    except Exception as e:
        messages.error(request, f"Lỗi khi xóa media: {e}")
        return redirect('treks_admin:cung_duong_list')

class NominatimProxyView(AdminRequiredMixin, View):
    """
    API Proxy này giờ đây có 2 chức năng:
    1. Tìm kiếm xuôi (search): ?q=<tên địa điểm>
    2. Tìm kiếm ngược (reverse): ?lat=<vĩ độ>&lon=<kinh độ>
    """
    def get(self, request, *args, **kwargs):
        query = request.GET.get('q', '').strip()
        lat = request.GET.get('lat')
        lon = request.GET.get('lon')

        headers = { 'User-Agent': 'TrekkingApp/1.0 (YourAppContact@example.com)' }
        
        try:
            # === CHỨC NĂNG TÌM KIẾM NGƯỢC (REVERSE GEOCODING) ===
            if lat and lon:
                api_url = "https://nominatim.openstreetmap.org/reverse"
                params = {
                    'format': 'jsonv2', # SỬA LỖI: Dùng format jsonv2 để có cấu trúc ổn định
                    'lat': lat,
                    'lon': lon,
                    'zoom': 18,        # THÊM: Mức độ chi tiết, 18 là mức đường phố
                    'addressdetails': 1
                }
                response = requests.get(api_url, params=params, headers=headers, timeout=10)
                response.raise_for_status() # Ném lỗi nếu status code là 4xx hoặc 5xx
                
                data = response.json()
                # API reverse chỉ trả về 1 object, ta cho vào list để đồng bộ
                # và đảm bảo có display_name
                if 'display_name' not in data:
                    data['display_name'] = f"Tọa độ: {lat}, {lon}"

                return JsonResponse([data], safe=False)

            # === CHỨC NĂNG TÌM KIẾM XUÔI (SEARCH) ===
            elif query:
                api_url = "https://nominatim.openstreetmap.org/search"
                params = {
                    'q': query,
                    'format': 'json',
                    'addressdetails': 1,
                    'limit': 5
                }
                response = requests.get(api_url, params=params, headers=headers, timeout=10)
                response.raise_for_status()
                return JsonResponse(response.json(), safe=False)
            
            else:
                return JsonResponse({'error': 'Missing required parameters (q or lat/lon).'}, status=400)

        except requests.exceptions.RequestException as e:
            return JsonResponse({'error': f'Failed to connect to Nominatim API: {e}'}, status=502)
        except Exception as e:
            # Bắt các lỗi khác, ví dụ JSONDecodeError
            return JsonResponse({'error': f'An unexpected error occurred: {str(e)}'}, status=500)

# ==========================================================
# === VIEW MỚI CHO TRANG BẢN ĐỒ RIÊNG BIỆT ===
# ==========================================================
class CungDuongMapUpdateView(AdminRequiredMixin, UpdateView):
    model = CungDuongTrek
    form_class = CungDuongMapForm
    template_name = 'admin/treks/cungDuong_map_form.html'

    def form_valid(self, form):
        # Lưu dữ liệu GeoJSON từ form
        self.object = form.save(commit=False)
        
        # Lấy giá trị độ dài được tính toán từ request POST
        calculated_length = self.request.POST.get('do_dai_km_calculated')
        
        if calculated_length:
            try:
                # Cập nhật trường do_dai_km của object
                self.object.do_dai_km = float(calculated_length)
                messages.info(self.request, f"Độ dài cung đường được tự động cập nhật thành {calculated_length} km.")
            except (ValueError, TypeError):
                messages.warning(self.request, "Không thể cập nhật độ dài tự động.")
        
        self.object.save()
        messages.success(self.request, f"Đã cập nhật vị trí trên bản đồ cho '{self.object.ten}'.")
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self):
         return reverse('treks_admin:cung_duong_update', kwargs={'pk': self.object.pk})
def set_cover_media_view(request, pk):
    if request.method != 'POST': return redirect('treks_admin:cung_duong_list')
    if not request.user.is_staff: return redirect('treks_admin:cung_duong_list')
    try:
        media = get_object_or_404(CungDuongMedia, pk=pk)
        cung_duong = media.cung_duong
        # Xóa cờ ảnh bìa hiện tại
        cung_duong.media.filter(la_anh_bia=True).update(la_anh_bia=False)
        # Đặt ảnh mới làm ảnh bìa
        media.la_anh_bia = True
        media.save()
        messages.success(request, "Đã đặt ảnh này làm ảnh bìa thành công.")
        return redirect('treks_admin:cung_duong_update', pk=cung_duong.pk)
    except Exception as e:
        messages.error(request, f"Lỗi khi đặt ảnh bìa: {e}")
        return redirect('treks_admin:cung_duong_list')