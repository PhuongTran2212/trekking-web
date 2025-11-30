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
from django.db.models import F, ExpressionWrapper, DurationField
from treks.models import CungDuongTrek
from core.models import TrangThaiChuyenDi
from .models import ChuyenDi, ChuyenDiThanhVien, ChuyenDiMedia
from .forms import TripFilterForm, ChuyenDiForm, TimelineFormSet, SelectTrekFilterForm
from django.db.models import Max, OuterRef, Subquery, Prefetch, Q
from django.views.decorators.http import require_http_methods
from .models import ChuyenDiTinNhan, ChuyenDiTinNhanMedia

import json

# ... (Giữ nguyên TripHubView và trip_events_api) ...
class TripHubView(ListView):
    model = ChuyenDi
    template_name = 'trips/trip_hub.html'
    context_object_name = 'trips'
    paginate_by = 12 

    def get_queryset(self):
        # =========================================================
        # 1. QUERY CƠ BẢN & TỐI ƯU HÓA (Eager Loading)
        # =========================================================
        queryset = ChuyenDi.objects.filter(che_do_rieng_tu='CONG_KHAI').select_related(
            'cung_duong', 
            'cung_duong__tinh_thanh', 
            'cung_duong__do_kho',        # Để lọc độ khó nhanh hơn
            'nguoi_to_chuc__taikhoanhoso', 
            'trang_thai', 
            'anh_bia'
        ).prefetch_related(
            'tags'                       # [QUAN TRỌNG] Lấy Hashtag để hiển thị ở Card
        ).annotate(
            # Đếm số thành viên ĐÃ tham gia (để lọc full slot)
            so_thanh_vien_tham_gia=Count('thanh_vien', filter=Q(thanh_vien__trang_thai_tham_gia='DA_THAM_GIA')),
            
            # Tính thời lượng (Duration) = Ngày về - Ngày đi
            # Kết quả trả về dạng timedelta
            duration=ExpressionWrapper(
                F('ngay_ket_thuc') - F('ngay_bat_dau'),
               output_field=DurationField()
            )
        )

        # =========================================================
        # 2. XỬ LÝ FORM LỌC (FILTER)
        # =========================================================
        self.filter_form = TripFilterForm(self.request.GET)
        
        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            
            # --- TÌM KIẾM CƠ BẢN ---
            if q := data.get('q'):
                queryset = queryset.filter(Q(ten_chuyen_di__icontains=q) | Q(cung_duong__ten__icontains=q))
            
            # --- ĐỊA ĐIỂM & THỜI GIAN ---
            if tinh_thanh := data.get('tinh_thanh'):
                queryset = queryset.filter(cung_duong__tinh_thanh=tinh_thanh)
            
            if start_date := data.get('start_date'):
                queryset = queryset.filter(ngay_bat_dau__date__gte=start_date)

            # --- HASHTAG (CHỦ ĐỀ) ---
            if tags := data.get('tags'):
                # Lọc theo quan hệ nhiều-nhiều (M2M)
                queryset = queryset.filter(tags__in=tags)

            # --- ĐỘ KHÓ ---
            if do_kho_list := data.get('do_kho'):
                queryset = queryset.filter(cung_duong__do_kho__in=do_kho_list)

            # --- KHOẢNG GIÁ ---
            if data.get('price_min'):
                queryset = queryset.filter(chi_phi_uoc_tinh__gte=data.get('price_min'))
            if data.get('price_max'):
                queryset = queryset.filter(chi_phi_uoc_tinh__lte=data.get('price_max'))
            
            # --- THỜI LƯỢNG (SỐ NGÀY) ---
            # duration_min/max là số nguyên (ngày), cần đổi sang timedelta để so sánh
            if data.get('duration_min'):
                # Ví dụ: Nhập 2 ngày -> Lọc các chuyến >= 1 ngày (để cover trường hợp làm tròn)
                min_delta = datetime.timedelta(days=data.get('duration_min') - 1) 
                queryset = queryset.filter(duration__gte=min_delta)
            
            if data.get('duration_max'):
                max_delta = datetime.timedelta(days=data.get('duration_max'))
                queryset = queryset.filter(duration__lte=max_delta)

            # --- TRẠNG THÁI: CÒN CHỖ ---
            if data.get('con_cho'):
                # Lọc những chuyến mà số người tham gia < số lượng tối đa
                queryset = queryset.filter(so_thanh_vien_tham_gia__lt=F('so_luong_toi_da'))

            # =========================================================
            # 3. SẮP XẾP (SORTING)
            # =========================================================
            sort_by = data.get('sort_by')
            if sort_by == 'price_asc':
                queryset = queryset.order_by('chi_phi_uoc_tinh')
            elif sort_by == 'price_desc':
                queryset = queryset.order_by('-chi_phi_uoc_tinh')
            elif sort_by == 'date_asc':
                queryset = queryset.order_by('ngay_bat_dau')
            else:
                # Mặc định: Mới tạo nhất lên đầu
                queryset = queryset.order_by('-ngay_tao')

        else:
            # Nếu không lọc gì cả, mặc định sắp xếp mới nhất
            queryset = queryset.order_by('-ngay_tao')

        # Dùng distinct() để loại bỏ các bản ghi trùng lặp 
        # (quan trọng khi lọc theo Tags hoặc Độ khó nhiều lựa chọn)
        return queryset.distinct()

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
# === 2. LUỒNG TẠO & SỬA CHUYẾN ĐI (ĐÃ CẬP NHẬT) ===
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
        timeline_formset = TimelineFormSet(request.POST)

        if form.is_valid() and timeline_formset.is_valid():
            with transaction.atomic():
                chuyen_di = form.save(commit=False)
                chuyen_di.nguoi_to_chuc = request.user
                chuyen_di.cung_duong = cung_duong
                
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
                form.save_m2m()

                timeline_formset.instance = chuyen_di
                timeline_formset.save()

                ChuyenDiThanhVien.objects.create(
                    chuyen_di=chuyen_di, user=request.user, 
                    vai_tro='TRUONG_DOAN', trang_thai_tham_gia='DA_THAM_GIA'
                )

                if request.FILES.getlist('trip_media_files'):
                     for f in request.FILES.getlist('trip_media_files'):
                        ChuyenDiMedia.objects.create(chuyen_di=chuyen_di, user=request.user, file=f)

                # --- REDIRECT SANG TRANG SUCCESS ---
                return redirect('trips:trip_create_success', pk=chuyen_di.pk)
        else:
            messages.error(request, "Có lỗi xảy ra, vui lòng kiểm tra lại thông tin bên dưới.")
    else:
        form = ChuyenDiForm()
        timeline_formset = TimelineFormSet()

    context = {
        'form': form, 
        'timeline_formset': timeline_formset, 
        'cung_duong': cung_duong, 
        'page_title': 'Lên kế hoạch Chuyến đi',
        'is_edit': False
    }
    return render(request, 'trips/trip_form.html', context)

# --- VIEW THÀNH CÔNG MỚI ---
class TripCreateSuccessView(LoginRequiredMixin, DetailView):
    model = ChuyenDi
    template_name = 'trips/trip_success.html'
    context_object_name = 'trip'

    def get_queryset(self):
        # Chỉ cho phép người tạo xem trang success của mình
        return super().get_queryset().filter(nguoi_to_chuc=self.request.user)

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
        
        if form.is_valid() and timeline_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                timeline_formset.instance = self.object
                timeline_formset.save()
                
                # Lưu ảnh mới (nếu có)
                if self.request.FILES.getlist('trip_media_files'):
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
# === 3. CÁC VIEW CHI TIẾT & API (Giữ nguyên phần lớn) ===
# ==========================================================

class TripDetailView(DetailView):
    model = ChuyenDi
    template_name = 'trips/trip_detail.html'
    context_object_name = 'trip'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'nguoi_to_chuc__taikhoanhoso', 'cung_duong__tinh_thanh', 'cung_duong__do_kho', 'anh_bia'
        ).prefetch_related('timeline', 'media', 'thanh_vien__user__taikhoanhoso')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.object
        user = self.request.user
        trip.so_thanh_vien_tham_gia = trip.thanh_vien.filter(trang_thai_tham_gia='DA_THAM_GIA').count()
        
        context['is_organizer'] = (user.is_authenticated and trip.nguoi_to_chuc == user)
        membership = None
        if user.is_authenticated:
            membership = trip.thanh_vien.filter(user=user).first()
        
        context['membership'] = membership
        context['is_member'] = (membership and membership.trang_thai_tham_gia == 'DA_THAM_GIA')
        
        if context['is_organizer']:
            context['pending_requests'] = trip.thanh_vien.filter(trang_thai_tham_gia='DA_GUI_YEU_CAU')
        
        return context

# ... (Giữ nguyên các hàm API: join_trip_request, leave_trip, approve_member...) ...
# ... COPY LẠI CÁC HÀM API TỪ FILE CŨ NẾU CẦN, HOẶC GIỮ NGUYÊN NẾU ĐÃ CÓ ...

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
    

 # ==========================================================
# === 4. CHỨC NĂNG CHAT ROOM (THÊM MỚI) ===
# ==========================================================

class TripChatRoomView(LoginRequiredMixin, DetailView):
    model = ChuyenDi
    template_name = 'trips/chat_room.html'
    context_object_name = 'trip'
    pk_url_kwarg = 'trip_id'

    def get_object(self):
        trip = get_object_or_404(ChuyenDi, pk=self.kwargs['trip_id'])
        is_organizer = (trip.nguoi_to_chuc == self.request.user)
        is_member = trip.thanh_vien.filter(user=self.request.user, trang_thai_tham_gia='DA_THAM_GIA').exists()
        if not (is_member or is_organizer):
            raise HttpResponseForbidden("Bạn không có quyền truy cập.")
        return trip

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.object
        user = self.request.user

        # 1. SIDEBAR THÔNG MINH (Giống Messenger)
        # Lấy danh sách chuyến đi, SẮP XẾP theo tin nhắn mới nhất
        # Subquery để lấy thời gian tin nhắn cuối cùng của mỗi chuyến đi
        last_msg_time = ChuyenDiTinNhan.objects.filter(
            chuyen_di=OuterRef('pk')
        ).order_by('-thoi_gian_gui').values('thoi_gian_gui')[:1]

        last_msg_content = ChuyenDiTinNhan.objects.filter(
            chuyen_di=OuterRef('pk')
        ).order_by('-thoi_gian_gui').values('noi_dung')[:1]

        my_trips = ChuyenDi.objects.filter(
            Q(thanh_vien__user=user, thanh_vien__trang_thai_tham_gia='DA_THAM_GIA') | 
            Q(nguoi_to_chuc=user)
        ).distinct().annotate(
            last_activity=Subquery(last_msg_time),
            preview_content=Subquery(last_msg_content)
        ).order_by('-last_activity', '-ngay_tao') # Trồi lên đầu nếu có tin nhắn mới
        
        context['my_trips'] = my_trips

        # 2. Thành viên & Media (Giữ nguyên)
        context['members'] = trip.thanh_vien.filter(
            trang_thai_tham_gia='DA_THAM_GIA'
        ).select_related('user__taikhoanhoso')

        context['chat_media_files'] = ChuyenDiTinNhanMedia.objects.filter(
            tin_nhan__chuyen_di=trip,
            tin_nhan__da_xoa=False # Không lấy ảnh của tin đã xóa
        ).select_related('tin_nhan__nguoi_gui').order_by('-tin_nhan__thoi_gian_gui')
        
        return context
@login_required
@require_POST
def send_chat_message(request, trip_id):
    """API gửi tin nhắn (AJAX) - Có hỗ trợ Reply & File"""
    trip = get_object_or_404(ChuyenDi, pk=trip_id)
    
    # 1. KIỂM TRA QUYỀN (BẮT BUỘC)
    # User phải là người tổ chức HOẶC thành viên đã tham gia (DA_THAM_GIA)
    is_organizer = (trip.nguoi_to_chuc == request.user)
    is_member = trip.thanh_vien.filter(user=request.user, trang_thai_tham_gia='DA_THAM_GIA').exists()
    
    if not (is_organizer or is_member):
        return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền gửi tin nhắn trong nhóm này.'}, status=403)

    # 2. LẤY DỮ LIỆU TỪ FORM
    noi_dung = request.POST.get('message', '').strip()
    files = request.FILES.getlist('files')
    reply_to_id = request.POST.get('reply_to_id')

    # Nếu không có nội dung và không có file -> Báo lỗi
    if not noi_dung and not files:
        return JsonResponse({'status': 'error', 'message': 'Tin nhắn không được để trống.'}, status=400)

    # 3. XỬ LÝ REPLY (TRẢ LỜI TIN NHẮN)
    reply_obj = None
    if reply_to_id:
        try:
            # Chỉ cho phép reply tin nhắn thuộc cùng chuyến đi này
            reply_obj = ChuyenDiTinNhan.objects.get(pk=reply_to_id, chuyen_di=trip)
        except (ChuyenDiTinNhan.DoesNotExist, ValueError):
            pass # Nếu ID không hợp lệ hoặc không tìm thấy thì bỏ qua (gửi tin thường)

    # 4. TẠO TIN NHẮN MỚI
    try:
        tin_nhan = ChuyenDiTinNhan.objects.create(
            chuyen_di=trip,
            nguoi_gui=request.user,
            tra_loi_tin_nhan=reply_obj,
            noi_dung=noi_dung
        )

        # 5. XỬ LÝ FILE ĐÍNH KÈM (MEDIA)
        for f in files:
            # Xác định loại file dựa trên MIME type
            if f.content_type.startswith('image'):
                loai = 'ANH'
            elif f.content_type.startswith('video'):
                loai = 'VIDEO'
            else:
                loai = 'FILE'
            
            # Tính kích thước (KB)
            size_kb = round(f.size / 1024, 2)

            ChuyenDiTinNhanMedia.objects.create(
                tin_nhan=tin_nhan,
                duong_dan_file=f,
                loai_media=loai,
                ten_file_goc=f.name,
                kich_thuoc_file_kb=size_kb
            )

        return JsonResponse({'status': 'success', 'msg_id': tin_nhan.id})

    except Exception as e:
        # Log lỗi nếu cần thiết
        print(f"Lỗi gửi tin nhắn: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Có lỗi xảy ra phía server.'}, status=500)
    
# @login_required
# def get_chat_messages(request, trip_id):
#     """API lấy tin nhắn mới (AJAX Polling)"""
#     trip = get_object_or_404(ChuyenDi, pk=trip_id)
    
#     # Kiểm tra quyền truy cập (Quan trọng)
#     is_organizer = (trip.nguoi_to_chuc == request.user)
#     is_member = trip.thanh_vien.filter(user=request.user, trang_thai_tham_gia='DA_THAM_GIA').exists()
    
#     if not (is_organizer or is_member):
#         return JsonResponse({'status': 'error', 'message': 'Không có quyền truy cập'}, status=403)

#     # Lấy tin nhắn
#     messages_qs = ChuyenDiTinNhan.objects.filter(chuyen_di=trip)\
#         .select_related('nguoi_gui__taikhoanhoso')\
#         .prefetch_related('media')\
#         .order_by('thoi_gian_gui')
        
#     # Logic: Lấy tin mới hơn last_id
#     last_id = request.GET.get('last_id')
#     if last_id and last_id != '0':
#         try:
#             last_id = int(last_id)
#             messages_qs = messages_qs.filter(id__gt=last_id)
#         except ValueError:
#             pass # Nếu last_id không phải số thì bỏ qua
    
#     data = []
#     for msg in messages_qs:
#         # 1. Xử lý Media
#         media_list = []
#         for m in msg.media.all():
#             if m.duong_dan_file: # Kiểm tra file tồn tại
#                 media_list.append({
#                     'url': m.duong_dan_file.url,
#                     'type': m.loai_media,
#                     'name': m.ten_file_goc
#                 })
            
#         # 2. Xử lý Avatar an toàn (Fix lỗi AttributeError)
#         avatar_url = '/static/images/default-avatar.png'
#         if hasattr(msg.nguoi_gui, 'taikhoanhoso'):
#             hoso = msg.nguoi_gui.taikhoanhoso
#             # Thử lấy các tên trường phổ biến: 'avatar' hoặc 'anh_dai_dien'
#             user_avatar = getattr(hoso, 'avatar', None) or getattr(hoso, 'anh_dai_dien', None)
            
#             if user_avatar:
#                 try:
#                     avatar_url = user_avatar.url
#                 except ValueError:
#                     pass
       
#         # 3. Format dữ liệu trả về
#         data.append({
#             'id': msg.id,
#             'user_id': msg.nguoi_gui.id,
#             'username': msg.nguoi_gui.get_full_name() or msg.nguoi_gui.username,
#             'avatar': avatar_url,
#             'content': msg.noi_dung,
#             'timestamp': msg.thoi_gian_gui.strftime("%H:%M"),
#             'is_me': msg.nguoi_gui == request.user,
#             'media': media_list
#         })
        
#     return JsonResponse({'messages': data})
@login_required
def get_chat_messages(request, trip_id):
    """API lấy tin nhắn (Realtime: New messages + Updates for old messages)"""
    trip = get_object_or_404(ChuyenDi, pk=trip_id)
    
    # 1. Check quyền
    is_organizer = (trip.nguoi_to_chuc == request.user)
    is_member = trip.thanh_vien.filter(user=request.user, trang_thai_tham_gia='DA_THAM_GIA').exists()
    if not (is_organizer or is_member):
        return JsonResponse({'status': 'error'}, status=403)

    # Base QuerySet
    messages_qs = ChuyenDiTinNhan.objects.filter(chuyen_di=trip)\
        .select_related('nguoi_gui__taikhoanhoso', 'tra_loi_tin_nhan__nguoi_gui')\
        .prefetch_related('media', 'likes', 'dislikes')\
        .order_by('thoi_gian_gui')
        
    last_id = request.GET.get('last_id', 0)
    try: last_id = int(last_id)
    except: last_id = 0
    
    # A. Lấy tin nhắn MỚI (ID > last_id)
    new_msgs = messages_qs.filter(id__gt=last_id)

    # B. Lấy tin nhắn CŨ cần cập nhật (ID <= last_id)
    # Để đơn giản và hiệu quả, ta lấy 20 tin nhắn cuối cùng để check update realtime (Like/Delete)
    # Trong thực tế production có thể dùng Redis/Websocket để tối ưu hơn
    old_msgs_to_check = messages_qs.filter(id__lte=last_id).order_by('-id')[:20]

    # Hàm Helper Format dữ liệu (Dùng chung cho cả mới và cũ)
    def format_msg_data(msg):
        # 1. Media
        media_list = []
        if not msg.da_xoa:
            for m in msg.media.all():
                if m.duong_dan_file:
                    media_list.append({
                        'url': m.duong_dan_file.url,
                        'type': m.loai_media,
                        'name': m.ten_file_goc
                    })
        
        # 2. Avatar
        avatar_url = '/static/images/default-avatar.png'
        if hasattr(msg.nguoi_gui, 'taikhoanhoso'):
            hoso = msg.nguoi_gui.taikhoanhoso
            user_avatar = getattr(hoso, 'avatar', None) or getattr(hoso, 'anh_dai_dien', None)
            if user_avatar:
                try: avatar_url = user_avatar.url
                except ValueError: pass

        # 3. Reply
        reply_data = None
        if msg.tra_loi_tin_nhan:
            if msg.tra_loi_tin_nhan.da_xoa:
                reply_data = {'id': 0, 'username': 'Hệ thống', 'content': 'Tin nhắn đã bị thu hồi'}
            else:
                reply_content = msg.tra_loi_tin_nhan.noi_dung or "[File phương tiện]"
                reply_data = {
                    'id': msg.tra_loi_tin_nhan.id,
                    'username': msg.tra_loi_tin_nhan.nguoi_gui.username,
                    'content': reply_content
                }

        # 4. Reactions & Content
        is_liked = request.user in msg.likes.all()
        is_disliked = request.user in msg.dislikes.all()
        
        final_content = msg.noi_dung
        if msg.da_xoa:
            final_content = "Tin nhắn đã bị thu hồi."

        return {
            'id': msg.id,
            'user_id': msg.nguoi_gui.id,
            'username': msg.nguoi_gui.get_full_name() or msg.nguoi_gui.username,
            'avatar': avatar_url,
            'content': final_content,
            'timestamp': msg.thoi_gian_gui.strftime("%H:%M"),
            'full_date': msg.thoi_gian_gui.isoformat(),
            'is_me': msg.nguoi_gui == request.user,
            'media': media_list,
            'reply': reply_data,
            'is_deleted': msg.da_xoa,
            'reactions': {
                'likes_count': msg.likes.count(),
                'dislikes_count': msg.dislikes.count(),
                'user_liked': is_liked,
                'user_disliked': is_disliked
            }
        }

    # Gom dữ liệu
    data_messages = [format_msg_data(m) for m in new_msgs]
    data_updates = [format_msg_data(m) for m in old_msgs_to_check]
        
    return JsonResponse({
        'messages': data_messages, # Tin mới -> Append
        'updates': data_updates    # Tin cũ -> Update UI (Like/Delete)
    })

@login_required
@require_POST
def delete_chat_message(request, msg_id):
    """API Xóa tin nhắn (Soft Delete)"""
    msg = get_object_or_404(ChuyenDiTinNhan, pk=msg_id)
    
    # Chỉ người gửi mới được xóa
    if msg.nguoi_gui != request.user:
        return JsonResponse({'status': 'error', 'message': 'Không có quyền xóa.'}, status=403)
    
    msg.da_xoa = True
    msg.save()
    return JsonResponse({'status': 'success', 'message': 'Đã thu hồi tin nhắn.'})

@login_required
@require_POST
def react_chat_message(request, msg_id):
    """API Like/Dislike (Hỗ trợ toggle và tự like)"""
    # Lấy tin nhắn (có thể thêm check quyền xem tin nhắn nếu cần bảo mật cao hơn)
    msg = get_object_or_404(ChuyenDiTinNhan, pk=msg_id)
    
    # Kiểm tra quyền truy cập nhóm chat (Optional nhưng nên có)
    trip = msg.chuyen_di
    is_member = trip.thanh_vien.filter(user=request.user, trang_thai_tham_gia='DA_THAM_GIA').exists()
    is_organizer = (trip.nguoi_to_chuc == request.user)
    
    if not (is_member or is_organizer):
        return JsonResponse({'status': 'error', 'message': 'Không có quyền'}, status=403)

    action = request.POST.get('action') # 'like' hoặc 'dislike'
    user = request.user

    if action == 'like':
        if user in msg.likes.all():
            msg.likes.remove(user) # Unlike (Bỏ like)
        else:
            msg.likes.add(user)
            msg.dislikes.remove(user) # Bỏ dislike nếu đang like
            
    elif action == 'dislike':
        if user in msg.dislikes.all():
            msg.dislikes.remove(user) # Undislike (Bỏ dislike)
        else:
            msg.dislikes.add(user)
            msg.likes.remove(user) # Bỏ like nếu đang dislike
            
    # Trả về số lượng mới và trạng thái hiện tại của user
    return JsonResponse({
        'status': 'success', 
        'likes': msg.likes.count(), 
        'dislikes': msg.dislikes.count(),
        'user_liked': user in msg.likes.all(),       # True nếu đang like
        'user_disliked': user in msg.dislikes.all()  # True nếu đang dislike
    })