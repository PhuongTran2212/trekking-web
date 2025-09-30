# treks/views.py

from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db import transaction
from django.db.models import Q
from .models import CungDuongTrek, CungDuongMedia, TrangThaiDuyet, CungDuongDanhGia
from .forms import CungDuongTrekAdminForm

class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

# ==============================================================================
# VIEW DÙNG CHUNG ĐỂ XỬ LÝ MEDIA - ĐÂY LÀ TRÁI TIM CỦA VIỆC TÁI CẤU TRÚC
# ==============================================================================
class CungDuongBaseView:
    """
    Một view mixin chứa logic xử lý upload media dùng chung
    cho cả Create và Update.
    """
    def handle_media_uploads(self, request, trek_instance):
        """Hàm xử lý upload ảnh bìa và thư viện media."""
        # 1. Xử lý ảnh bìa mới (nếu có)
        cover_image_file = request.FILES.get('anh_bia')
        if cover_image_file:
            # Xóa tất cả ảnh bìa cũ để đảm bảo chỉ có một
            trek_instance.media.filter(la_anh_bia=True).delete()
            # Tạo ảnh bìa mới
            CungDuongMedia.objects.create(
                cung_duong=trek_instance, 
                file=cover_image_file, 
                loai_media='ANH', 
                la_anh_bia=True
            )
        
        # 2. Xử lý các file mới trong thư viện (nếu có)
        gallery_files = request.FILES.getlist('file')
        if gallery_files:
            for f in gallery_files:
                loai = 'ANH' if f.content_type.startswith('image') else 'VIDEO'
                CungDuongMedia.objects.create(
                    cung_duong=trek_instance, 
                    file=f, 
                    loai_media=loai,
                    la_anh_bia=False # Luôn đảm bảo ảnh từ thư viện không phải ảnh bìa
                )

# ==============================================================================
# CÁC VIEW CHÍNH
# ==============================================================================

class CungDuongListView(AdminRequiredMixin, ListView):
    model = CungDuongTrek
    template_name = 'admin/treks/cungduong_list.html'
    context_object_name = 'cung_duong_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().order_by('-ngay_cap_nhat')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(Q(ten__icontains=query) | Q(tinh_thanh__ten__icontains=query))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Quản lý Cung đường"
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
        self.object.trang_thai = TrangThaiDuyet.DA_DUYET
        
        try:
            with transaction.atomic():
                self.object.save()
                form.save_m2m() # Lưu quan hệ ManyToMany
                
                # GỌI HÀM DÙNG CHUNG để xử lý media
                self.handle_media_uploads(self.request, self.object)

            messages.success(self.request, f"Đã tạo thành công cung đường '{self.object.ten}'.")
            return redirect(self.get_success_url())
        except Exception as e:
            messages.error(self.request, f"Đã có lỗi xảy ra khi tạo cung đường: {e}")
            return self.form_invalid(form)

    def get_success_url(self):
        # Sau khi tạo thành công, chuyển đến trang chi tiết
        return reverse('treks_admin:cung_duong_detail', kwargs={'pk': self.object.pk})

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
                
                # GỌI HÀM DÙNG CHUNG để xử lý media (code đã gọn hơn rất nhiều)
                self.handle_media_uploads(self.request, self.object)

            messages.success(self.request, f"Đã cập nhật thành công cung đường '{self.object.ten}'.")
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            messages.error(self.request, f"Đã có lỗi xảy ra khi cập nhật: {e}")
            return self.form_invalid(form)
        
    def get_success_url(self):
        # Quay về chính trang chỉnh sửa để xem kết quả ngay lập tức
        return reverse('treks_admin:cung_duong_update', kwargs={'pk': self.object.pk})

class CungDuongDetailView(AdminRequiredMixin, DetailView):
    model = CungDuongTrek
    template_name = 'admin/treks/cungduong_detail.html'
    context_object_name = 'trek'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Chi tiết: {self.object.ten}"
        context['reviews'] = CungDuongDanhGia.objects.filter(cung_duong=self.object).order_by('-ngay_danh_gia')
        return context

class CungDuongDeleteView(AdminRequiredMixin, DeleteView):
    model = CungDuongTrek
    template_name = 'admin/treks/confirm_delete.html'
    success_url = reverse_lazy('treks_admin:cung_duong_list')
    
    def form_valid(self, form):
        messages.success(self.request, f"Đã xóa vĩnh viễn cung đường '{self.object.ten}'.")
        return super().form_valid(form)

# View xóa media vẫn giữ nguyên, nó đã được thiết kế tốt
def delete_media_view(request, pk):
    if request.method != 'POST':
        messages.error(request, "Phương thức không hợp lệ.")
        return redirect('treks_admin:cung_duong_list')

    if not request.user.is_staff:
        messages.error(request, "Bạn không có quyền thực hiện hành động này.")
        return redirect('treks_admin:cung_duong_list')
        
    try:
        media = get_object_or_404(CungDuongMedia, pk=pk)
        cung_duong_pk = media.cung_duong.pk
        file_name = media.file.name
        
        media.delete() 

        messages.success(request, f"Đã xóa thành công media: {file_name}")
        return redirect('treks_admin:cung_duong_update', pk=cung_duong_pk)
    except Exception as e:
        messages.error(request, f"Đã có lỗi xảy ra khi xóa media: {e}")
        return redirect('treks_admin:cung_duong_list')