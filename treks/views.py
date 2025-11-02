# treks/views.py

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
    def handle_media_uploads(self, request, trek_instance):
        cover_image_file = request.FILES.get('anh_bia')
        if cover_image_file:
            trek_instance.media.filter(la_anh_bia=True).delete()
            CungDuongMedia.objects.create(
                cung_duong=trek_instance, file=cover_image_file, loai_media='ANH', la_anh_bia=True
            )
        gallery_files = request.FILES.getlist('file')
        for f in gallery_files:
            loai = 'ANH' if f.content_type.startswith('image') else 'VIDEO'
            CungDuongMedia.objects.create(
                cung_duong=trek_instance, file=f, loai_media=loai, la_anh_bia=False
            )

class CungDuongListView(AdminRequiredMixin, ListView):
    model = CungDuongTrek
    template_name = 'admin/treks/cungduong_list.html'
    context_object_name = 'cung_duong_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('tinh_thanh', 'do_kho').order_by('-ngay_cap_nhat')
        self.filter_form = CungDuongTrekFilterForm(self.request.GET)
        if self.filter_form.is_valid():
            q = self.filter_form.cleaned_data.get('q')
            trang_thai = self.filter_form.cleaned_data.get('trang_thai')
            do_kho = self.filter_form.cleaned_data.get('do_kho')
            if q:
                queryset = queryset.filter(Q(ten__icontains=q) | Q(tinh_thanh__ten__icontains=q))
            if trang_thai:
                queryset = queryset.filter(trang_thai=trang_thai)
            if do_kho:
                queryset = queryset.filter(do_kho=do_kho)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Quản lý Cung đường"
        context['filter_form'] = self.filter_form
        params = self.request.GET.copy()
        if 'page' in params:
            del params['page']
        context['query_params'] = params.urlencode()
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

class CungDuongUpdateView(AdminRequiredMixin, CungDuongBaseView, UpdateView):
    model = CungDuongTrek
    form_class = CungDuongTrekAdminForm
    template_name = 'admin/treks/cungduong_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Chỉnh sửa: {self.object.ten}"
        return context
        
    def form_valid(self, form):
        try:
            with transaction.atomic():
                self.object = form.save()
                self.handle_media_uploads(self.request, self.object)
            messages.success(self.request, f"Đã cập nhật thành công cung đường '{self.object.ten}'.")
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            messages.error(self.request, f"Lỗi khi cập nhật: {e}")
            return self.form_invalid(form)
        
    def get_success_url(self):
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