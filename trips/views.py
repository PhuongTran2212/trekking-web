# trips/views.py

import datetime
from django.db import transaction
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.generic import ListView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Q, Count
from django.utils import timezone

from treks.models import CungDuongTrek
from core.models import TrangThaiChuyenDi
from .models import ChuyenDi, ChuyenDiThanhVien, ChuyenDiMedia
from .forms import TripFilterForm, ChuyenDiForm, TimelineFormSet, SelectTrekFilterForm
import json
# ==========================================================
# === 1. TRANG HUB "KHÁM PHÁ CHUYẾN ĐI" ===
# ==========================================================
class TripHubView(ListView):
    model = ChuyenDi
    template_name = 'trips/trip_hub.html'
    context_object_name = 'trips'
    paginate_by = 9

    def get_queryset(self):
        # Lấy tất cả chuyến đi công khai
        queryset = ChuyenDi.objects.filter(
            che_do_rieng_tu='CONG_KHAI',
            # Bỏ lọc theo trạng thái nếu bạn muốn hiện cả chuyến đã kết thúc/đã hủy
            # Hoặc giữ lại nếu chỉ muốn hiện chuyến đang hoạt động:
            # trang_thai__ten__in=['Đang tuyển thành viên', 'Sắp diễn ra', 'Đã đóng', 'Đang diễn ra'], 
        ).select_related(
            'cung_duong__tinh_thanh', 'cung_duong__do_kho', 'nguoi_to_chuc__taikhoanhoso', 'trang_thai', 'anh_bia'
        ).annotate(
            so_thanh_vien_tham_gia=Count('thanh_vien', filter=Q(thanh_vien__trang_thai_tham_gia='DA_THAM_GIA'))
        )
        
        # --- SẮP XẾP ---
        # 'ngay_tao': Tạo trước lên đầu (Cũ -> Mới)
        # '-ngay_tao': Tạo sau lên đầu (Mới -> Cũ)
        queryset = queryset.order_by('ngay_tao') 

        # --- BỘ LỌC ---
        self.filter_form = TripFilterForm(self.request.GET)
        if self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if q := cleaned_data.get('q'):
                queryset = queryset.filter(Q(ten_chuyen_di__icontains=q) | Q(cung_duong__ten__icontains=q))
            if cung_duong := cleaned_data.get('cung_duong'):
                queryset = queryset.filter(cung_duong=cung_duong)
            if tinh_thanh := cleaned_data.get('tinh_thanh'):
                queryset = queryset.filter(cung_duong__tinh_thanh=tinh_thanh)
            if start_date := cleaned_data.get('start_date'):
                queryset = queryset.filter(ngay_bat_dau__date__gte=start_date)
            if tags := cleaned_data.get('tags'):
                queryset = queryset.filter(tags__in=tags).distinct()
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Khám phá Chuyến đi"
        context['filter_form'] = self.filter_form
        return context


def trip_events_api(request):
    public_trips = Q(che_do_rieng_tu='CONG_KHAI')
    user_trips = Q()
    if request.user.is_authenticated:
        user_trips = Q(thanh_vien__user=request.user)
    all_trips = ChuyenDi.objects.filter(public_trips | user_trips).distinct()
    events = []
    for trip in all_trips:
        color, text_color = '#3b82f6', 'white'
        if request.user.is_authenticated and trip.thanh_vien.filter(user=request.user).exists():
            color, text_color = ('#6b7280', 'white') if trip.ngay_ket_thuc < timezone.now() else ('#22c55e', 'white')
        events.append({
            'id': trip.id, 'title': trip.ten_chuyen_di, 'start': trip.ngay_bat_dau.isoformat(),
            'end': (trip.ngay_ket_thuc + datetime.timedelta(days=1)).isoformat(),
            'color': color, 'textColor': text_color, 'url': trip.get_absolute_url(),
        })
    return JsonResponse(events, safe=False)

# ==========================================================
# === 2. LUỒNG TẠO & SỬA CHUYẾN ĐI (ĐÃ FIX LOGIC) ===
# ==========================================================
@login_required
def create_trip_view(request):
    cung_duong_slug = request.GET.get('cung_duong')
    if not cung_duong_slug:
        messages.error(request, "Vui lòng chọn một cung đường để bắt đầu.")
        return redirect('treks:cung_duong_list')
    cung_duong = get_object_or_404(CungDuongTrek, slug=cung_duong_slug)

    if request.method == 'POST':
        form = ChuyenDiForm(request.POST)
        # [FIX] Lấy dữ liệu Timeline từ POST
        timeline_formset = TimelineFormSet(request.POST)

        # [FIX] Kiểm tra cả 2 form
        if form.is_valid() and timeline_formset.is_valid():
            with transaction.atomic():
                chuyen_di = form.save(commit=False)
                chuyen_di.nguoi_to_chuc = request.user
                chuyen_di.cung_duong = cung_duong
                
                # Set trạng thái mặc định
                try:
                    chuyen_di.trang_thai = TrangThaiChuyenDi.objects.get(ten='Đang tuyển thành viên')
                except TrangThaiChuyenDi.DoesNotExist:
                     chuyen_di.trang_thai = TrangThaiChuyenDi.objects.first()

                # Snapshot dữ liệu
                chuyen_di.cd_ten = cung_duong.ten
                chuyen_di.cd_mo_ta = cung_duong.mo_ta
                chuyen_di.cd_tinh_thanh_ten = cung_duong.tinh_thanh.ten
                chuyen_di.cd_do_kho_ten = cung_duong.do_kho.ten if cung_duong.do_kho else "Chưa xác định"
                chuyen_di.cd_do_dai_km = cung_duong.do_dai_km
                chuyen_di.cd_thoi_gian_uoc_tinh_gio = cung_duong.thoi_gian_uoc_tinh_gio
                chuyen_di.cd_tong_do_cao_leo_m = cung_duong.tong_do_cao_leo_m
                chuyen_di.cd_du_lieu_ban_do_geojson = cung_duong.du_lieu_ban_do_geojson
                
                chuyen_di.save()
                form.save_m2m() # Lưu tags

                # [FIX] Lưu Timeline Formset
                timeline_formset.instance = chuyen_di
                timeline_formset.save()

                # Tạo trưởng đoàn
                ChuyenDiThanhVien.objects.create(
                    chuyen_di=chuyen_di, user=request.user, 
                    vai_tro='TRUONG_DOAN', trang_thai_tham_gia='DA_THAM_GIA'
                )

                # Lưu ảnh upload lúc tạo
                if request.FILES.getlist('trip_media_files'):
                     for f in request.FILES.getlist('trip_media_files'):
                        ChuyenDiMedia.objects.create(chuyen_di=chuyen_di, user=request.user, file=f)

                messages.success(request, f"Đã tạo chuyến đi '{chuyen_di.ten_chuyen_di}' thành công!")
                return redirect('trips:update_trip', pk=chuyen_di.pk, slug=chuyen_di.slug)
        else:
            messages.error(request, "Có lỗi xảy ra, vui lòng kiểm tra lại thông tin bên dưới.")
    else:
        form = ChuyenDiForm()
        timeline_formset = TimelineFormSet() # Formset rỗng

    context = {
        'form': form, 
        'timeline_formset': timeline_formset, # Truyền xuống template
        'cung_duong': cung_duong, 
        'page_title': 'Lên kế hoạch Chuyến đi',
        'is_edit': False
     
    }
    return render(request, 'trips/trip_form.html', context)

class TripUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = ChuyenDi
    form_class = ChuyenDiForm
    template_name = 'trips/trip_form.html'
    
    def test_func(self):
        return self.get_object().nguoi_to_chuc == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Chỉnh sửa: {self.object.ten_chuyen_di}"
        context['is_edit'] = True
        if self.request.POST:
            context['timeline_formset'] = TimelineFormSet(self.request.POST, instance=self.object)
        else:
            context['timeline_formset'] = TimelineFormSet(instance=self.object)
        return context
        
    def form_valid(self, form):
        context = self.get_context_data()
        timeline_formset = context['timeline_formset']
        
        # [FIX] Kiểm tra cả timeline_formset
        if form.is_valid() and timeline_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                
                # Lưu Timeline
                timeline_formset.instance = self.object
                timeline_formset.save()
                
                # Lưu ảnh mới
                for f in self.request.FILES.getlist('trip_media_files'):
                    ChuyenDiMedia.objects.create(chuyen_di=self.object, user=self.request.user, file=f)
            
            messages.success(self.request, "Đã cập nhật chuyến đi thành công.")
            return super().form_valid(form)
        else:
            messages.error(self.request, "Vui lòng kiểm tra lại các lỗi.")
            return self.render_to_response(context)

    def get_success_url(self):
        return self.object.get_absolute_url()

# ==========================================================
# === 3. CÁC VIEW KHÁC (GIỮ NGUYÊN) ===
# ==========================================================
class TripDetailView(DetailView):
    model = ChuyenDi
    template_name = 'trips/trip_detail.html'
    context_object_name = 'trip'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.object
        user = self.request.user
        
        context['is_organizer'] = (user.is_authenticated and trip.nguoi_to_chuc == user)
        membership = None
        if user.is_authenticated:
            membership = trip.thanh_vien.filter(user=user).first()
        
        context['membership'] = membership
        context['is_member'] = (membership and membership.trang_thai_tham_gia == 'DA_THAM_GIA')
        
        if context['is_organizer']:
            context['pending_requests'] = trip.thanh_vien.filter(trang_thai_tham_gia='DA_GUI_YEU_CAU')
        
        return context

@login_required
@require_POST
def join_trip_request(request, pk):
    trip = get_object_or_404(ChuyenDi, pk=pk)
    if trip.thanh_vien.filter(user=request.user).exists():
        return JsonResponse({'status': 'error', 'message': 'Bạn đã gửi yêu cầu hoặc đã là thành viên.'}, status=400)
    if trip.thanh_vien.filter(trang_thai_tham_gia='DA_THAM_GIA').count() >= trip.so_luong_toi_da:
        return JsonResponse({'status': 'error', 'message': 'Chuyến đi đã đủ thành viên.'}, status=400)
    ChuyenDiThanhVien.objects.create(
        chuyen_di=trip, user=request.user,
        ly_do_tham_gia=request.POST.get('reason', ''),
        trang_thai_tham_gia='DA_GUI_YEU_CAU'
    )
    return JsonResponse({'status': 'success', 'message': 'Đã gửi yêu cầu tham gia.'})

@login_required
@require_POST
def cancel_join_request(request, pk):
    trip = get_object_or_404(ChuyenDi, pk=pk)
    membership = get_object_or_404(ChuyenDiThanhVien, chuyen_di=trip, user=request.user, trang_thai_tham_gia='DA_GUI_YEU_CAU')
    membership.delete()
    return JsonResponse({'status': 'success', 'message': 'Đã hủy yêu cầu tham gia.'})

@login_required
@require_POST
def leave_trip(request, pk):
    trip = get_object_or_404(ChuyenDi, pk=pk)
    if trip.ngay_bat_dau <= timezone.now():
        return JsonResponse({'status': 'error', 'message': 'Không thể rời khỏi chuyến đi đã bắt đầu.'}, status=400)
    membership = get_object_or_404(ChuyenDiThanhVien, chuyen_di=trip, user=request.user, trang_thai_tham_gia='DA_THAM_GIA')
    if membership.vai_tro == 'TRUONG_DOAN':
        return JsonResponse({'status': 'error', 'message': 'Trưởng đoàn không thể rời chuyến đi. Hãy hủy chuyến đi nếu cần.'}, status=400)
    membership.trang_thai_tham_gia = 'DA_ROI_DI'
    membership.save()
    return JsonResponse({'status': 'success', 'message': 'Bạn đã rời khỏi chuyến đi.'})

@login_required
@require_POST
def approve_member(request, pk, member_id):
    trip = get_object_or_404(ChuyenDi, pk=pk, nguoi_to_chuc=request.user)
    membership = get_object_or_404(ChuyenDiThanhVien, pk=member_id, chuyen_di=trip, trang_thai_tham_gia='DA_GUI_YEU_CAU')
    if trip.thanh_vien.filter(trang_thai_tham_gia='DA_THAM_GIA').count() >= trip.so_luong_toi_da:
        return JsonResponse({'status': 'error', 'message': 'Chuyến đi đã đủ thành viên, không thể duyệt thêm.'}, status=400)
    membership.trang_thai_tham_gia = 'DA_THAM_GIA'
    membership.save()
    return JsonResponse({'status': 'success', 'message': f'Đã duyệt thành viên {membership.user.username}.'})

@login_required
@require_POST
def reject_member(request, pk, member_id):
    trip = get_object_or_404(ChuyenDi, pk=pk, nguoi_to_chuc=request.user)
    membership = get_object_or_404(ChuyenDiThanhVien, pk=member_id, chuyen_di=trip)
    membership.trang_thai_tham_gia = 'BI_TU_CHOI'
    membership.save()
    return JsonResponse({'status': 'success', 'message': f'Đã từ chối thành viên {membership.user.username}.'})
    
@login_required
@require_POST
def upload_trip_media(request, pk):
    trip = get_object_or_404(ChuyenDi, pk=pk)
    is_member = trip.thanh_vien.filter(user=request.user, trang_thai_tham_gia='DA_THAM_GIA').exists()
    if not is_member:
        return HttpResponseForbidden("Chỉ thành viên của chuyến đi mới có thể tải lên media.")
    uploaded_files = []
    for f in request.FILES.getlist('files'):
        media = ChuyenDiMedia.objects.create(chuyen_di=trip, user=request.user, file=f)
        uploaded_files.append({'id': media.id, 'url': media.file.url})
    return JsonResponse({'status': 'success', 'message': f'Đã tải lên {len(uploaded_files)} file.', 'files': uploaded_files})

@login_required
@require_POST
def set_trip_cover(request, pk, media_id):
    trip = get_object_or_404(ChuyenDi, pk=pk, nguoi_to_chuc=request.user)
    media = get_object_or_404(ChuyenDiMedia, pk=media_id, chuyen_di=trip)
    trip.anh_bia = media
    trip.save()
    return JsonResponse({'status': 'success', 'message': 'Đã đặt ảnh bìa thành công.'})

@login_required
@require_POST
def delete_trip_media(request, media_id):
    media = get_object_or_404(ChuyenDiMedia, pk=media_id)
    if not (media.chuyen_di.nguoi_to_chuc == request.user or media.user == request.user):
        return HttpResponseForbidden("Bạn không có quyền xóa media này.")
    if media.chuyen_di.anh_bia_id == media.id:
        media.chuyen_di.anh_bia = None
        media.chuyen_di.save()
    media.delete()
    return JsonResponse({'status': 'success', 'message': 'Đã xóa media.'})

class SelectTrekForTripView(LoginRequiredMixin, ListView):
    model = CungDuongTrek
    template_name = 'trips/select_trek.html'
    context_object_name = 'treks'
    paginate_by = 9
    def get_queryset(self):
        queryset = CungDuongTrek.objects.filter(trang_thai='DA_DUYET').annotate(
            so_chuyen_di=Count('chuyendi')
        ).select_related('tinh_thanh', 'do_kho').order_by('-so_chuyen_di', '-danh_gia_trung_binh')
        self.filter_form = SelectTrekFilterForm(self.request.GET)
        if self.filter_form.is_valid():
            cleaned_data = self.filter_form.cleaned_data
            if q := cleaned_data.get('q'):
                queryset = queryset.filter(ten__icontains=q)
            if tinh_thanh := cleaned_data.get('tinh_thanh'):
                queryset = queryset.filter(tinh_thanh=tinh_thanh)
            if do_kho := cleaned_data.get('do_kho'):
                queryset = queryset.filter(do_kho=do_kho)
        return queryset
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = "Bước 1: Chọn Cung đường"
        context['filter_form'] = self.filter_form
        return context