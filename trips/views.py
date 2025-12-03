# trips/views.py
from django.db.models import Case, When # Thêm vào đầu file views.py
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
from treks.views import AdminRequiredMixin
from .models import ChuyenDi, ChuyenDiThanhVien, ChuyenDiMedia
from .forms import TripAdminFilterForm, TripFilterForm, ChuyenDiForm, TimelineFormSet, SelectTrekFilterForm
from django.db.models import Max, OuterRef, Subquery, Prefetch, Q
from django.db.models import Sum, Count, Q
from django.views.decorators.http import require_http_methods
from .models import ChuyenDiTinNhan, ChuyenDiTinNhanMedia
from django.contrib.auth.decorators import login_required, user_passes_test
import json
import csv
from django.http import HttpResponse
from django.template.loader import render_to_string
# trips/views.py

def get_base_template(request):
    """
    Hàm này giúp Django nhận biết:
    - Nếu link có chữ 'dashboard' hoặc 'admin' -> Trả về giao diện Admin (admin_base.html)
    - Nếu không -> Trả về giao diện User (base.html)
    """
    path = request.path
    if '/dashboard/' in path or '/admin-dashboard/' in path or '/admin/' in path:
        return 'admin_base.html'
    return 'base.html'
class TripHubView(ListView):
    model = ChuyenDi
    template_name = 'trips/trip_hub.html'
    context_object_name = 'trips'
    paginate_by = 12 

    def get_queryset(self):
        # 1. Base Query
        queryset = ChuyenDi.objects.select_related(
            'cung_duong', 
            'cung_duong__tinh_thanh', 
            'cung_duong__do_kho',
            'nguoi_to_chuc__taikhoanhoso', 
            'anh_bia'
        ).prefetch_related('tags')

        now = timezone.now()

        # 2. CHỈ LỌC: Sắp diễn ra & Không bị hủy
        # (BỎ hết đoạn lọc user.is_authenticated ở đây đi)
        queryset = queryset.filter(
            ngay_bat_dau__gt=now
        ).exclude(trang_thai='DA_HUY')

        # =========================================================
        # 3. ANNOTATE (Giữ nguyên để lấy trạng thái hiển thị Badge)
        # =========================================================
        if self.request.user.is_authenticated:
            status_subquery = ChuyenDiThanhVien.objects.filter(
                chuyen_di=OuterRef('pk'),
                user=self.request.user
            ).values('trang_thai_tham_gia')[:1]

            queryset = queryset.annotate(
                user_status=Subquery(status_subquery)
            )

        queryset = queryset.annotate(
            so_thanh_vien_tham_gia=Count('thanh_vien', filter=Q(thanh_vien__trang_thai_tham_gia='DA_THAM_GIA')),
            duration=ExpressionWrapper(F('ngay_ket_thuc') - F('ngay_bat_dau'), output_field=DurationField())
        )
        # =========================================================
        # 4. XỬ LÝ FORM LỌC (FILTER) TỪ SIDEBAR
        # =========================================================
        self.filter_form = TripFilterForm(self.request.GET)
        
        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            
            # --- Tìm kiếm từ khóa ---
            if q := data.get('q'):
                queryset = queryset.filter(Q(ten_chuyen_di__icontains=q) | Q(cung_duong__ten__icontains=q))
            
            # --- Địa điểm ---
            if tinh_thanh := data.get('tinh_thanh'):
                queryset = queryset.filter(cung_duong__tinh_thanh=tinh_thanh)
            
            # --- Ngày khởi hành (Lọc những chuyến đi sau ngày user chọn) ---
            if start_date := data.get('start_date'):
                queryset = queryset.filter(ngay_bat_dau__date__gte=start_date)

            # --- Tags (Hashtag) ---
            if tags := data.get('tags'):
                queryset = queryset.filter(tags__in=tags)

            # --- Độ khó ---
            if do_kho_list := data.get('do_kho'):
                queryset = queryset.filter(cung_duong__do_kho__in=do_kho_list)

            # --- Khoảng giá ---
            if data.get('price_min'):
                queryset = queryset.filter(chi_phi_uoc_tinh__gte=data.get('price_min'))
            if data.get('price_max'):
                queryset = queryset.filter(chi_phi_uoc_tinh__lte=data.get('price_max'))
            
            # --- Thời lượng (Số ngày) ---
            if data.get('duration_min'):
                # Trừ 1 ngày để cover trường hợp làm tròn (VD: đi sáng về chiều tính là 0 ngày nhưng user muốn tìm 1 ngày)
                min_delta = datetime.timedelta(days=data.get('duration_min') - 1) 
                queryset = queryset.filter(duration__gte=min_delta)
            
            if data.get('duration_max'):
                max_delta = datetime.timedelta(days=data.get('duration_max'))
                queryset = queryset.filter(duration__lte=max_delta)

            # --- LOGIC QUAN TRỌNG: Lọc 'Còn chỗ' ---
            # So sánh số người đã tham gia (annotate ở trên) với số lượng tối đa
            if data.get('con_cho'):
                queryset = queryset.filter(so_thanh_vien_tham_gia__lt=F('so_luong_toi_da'))

            # --- Sắp xếp ---
            sort_by = data.get('sort_by')
            if sort_by == 'price_asc':
                queryset = queryset.order_by('chi_phi_uoc_tinh')
            elif sort_by == 'price_desc':
                queryset = queryset.order_by('-chi_phi_uoc_tinh')
            elif sort_by == 'date_asc':
                queryset = queryset.order_by('ngay_bat_dau') # Ngày gần nhất lên trước
            else:
                queryset = queryset.order_by('ngay_bat_dau') # Mặc định: Sắp đi lên trước (thay vì mới tạo)

        else:
            # Mặc định nếu không lọc: Chuyến nào sắp đi nhất thì hiện lên đầu
            queryset = queryset.order_by('ngay_bat_dau')

        # Loại bỏ bản ghi trùng lặp (do join bảng Tags nhiều lần)
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
    
    # Logic kiểm tra Cung đường
    if not cung_duong_slug:
        # Nếu là Admin tạo từ dashboard mà chưa chọn cung đường -> Chuyển hướng về list trek admin
        if '/dashboard/' in request.path or '/admin-dashboard/' in request.path:
             return redirect('treks_admin:cung_duong_list') # Hoặc trang chọn của Admin nếu có
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
                chuyen_di.trang_thai = 'DANG_TUYEN'
                
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

                # --- ĐIỀU HƯỚNG SAU KHI LƯU ---
                # Nếu là Admin -> Về Dashboard
                if '/dashboard/' in request.path or '/admin-dashboard/' in request.path:
                    messages.success(request, "Đã tạo chuyến đi thành công.")
                    return redirect('trips_admin:trip_list')
                
                # Nếu là User -> Về trang thành công
                return redirect('trips:trip_create_success', pk=chuyen_di.pk)
        else:
            messages.error(request, "Có lỗi xảy ra, vui lòng kiểm tra lại thông tin bên dưới.")
    else:
        form = ChuyenDiForm()
        timeline_formset = TimelineFormSet()

    # Lấy base template
    base_template = get_base_template(request)

    context = {
        'form': form, 
        'timeline_formset': timeline_formset, 
        'cung_duong': cung_duong, 
        'page_title': 'Lên kế hoạch Chuyến đi',
        'is_edit': False,
        'base_template': base_template, # Gửi tên file base xuống
        'is_admin_view': 'admin_base.html' in base_template # Cờ đánh dấu để hiện/ẩn nút bấm
    }
    return render(request, 'trips/trip_form.html', context)

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
    
    # 1. QUYỀN TRUY CẬP: Cho phép nếu là Chủ bài viết HOẶC là Admin (Staff)
    def test_func(self):
        trip = self.get_object()
        return trip.nguoi_to_chuc == self.request.user or self.request.user.is_staff

    # 2. GỬI GIAO DIỆN XUỐNG TEMPLATE
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f"Chỉnh sửa: {self.object.ten_chuyen_di}"
        context['is_edit'] = True
        
        # Xác định giao diện
        context['base_template'] = get_base_template(self.request)
        context['is_admin_view'] = 'admin_base.html' in context['base_template']
        
        # Formset timeline
        if self.request.POST:
            context['timeline_formset'] = TimelineFormSet(self.request.POST, instance=self.object)
        else:
            context['timeline_formset'] = TimelineFormSet(instance=self.object)
        return context
        
    # 3. XỬ LÝ LƯU & CHUYỂN HƯỚNG
    def form_valid(self, form):
        context = self.get_context_data()
        timeline_formset = context['timeline_formset']
        
        if form.is_valid() and timeline_formset.is_valid():
            with transaction.atomic():
                self.object = form.save()
                timeline_formset.instance = self.object
                timeline_formset.save()
                
                # Lưu ảnh media (nếu có)
                if self.request.FILES.getlist('trip_media_files'):
                    for f in self.request.FILES.getlist('trip_media_files'):
                        ChuyenDiMedia.objects.create(chuyen_di=self.object, user=self.request.user, file=f)
            
            messages.success(self.request, "Đã cập nhật chuyến đi thành công.")
            
            # QUAN TRỌNG: Nếu đang ở Dashboard -> Quay về danh sách Dashboard
            path = self.request.path
            if '/dashboard/' in path or '/admin-dashboard/' in path:
                return redirect('trips_admin:trip_list')
                
            return super().form_valid(form)
        else:
            messages.error(self.request, "Vui lòng kiểm tra lại các lỗi bên dưới.")
            return self.render_to_response(context)

    def get_success_url(self):
        return self.object.get_absolute_url()

# ==========================================================
# === 3. CÁC VIEW CHI TIẾT & API (Giữ nguyên phần lớn) ===
# ==========================================================
def find_trip_by_code(request):
    """Tìm chuyến đi và cấp quyền truy cập ngay nếu mã đúng"""
    code = request.GET.get('code', '').strip()
    
    if not code:
        return JsonResponse({'status': 'error', 'message': 'Vui lòng nhập mã chuyến đi.'})

    # Tìm chuyến đi có mã bắt đầu bằng chuỗi nhập vào
    # Lưu ý: Chuyển UUID sang chuỗi để so sánh startswith
    trip = None
    all_trips = ChuyenDi.objects.all()
    
    # Cách so sánh thủ công để hỗ trợ startswith cho UUID field (hoặc dùng filter nếu DB hỗ trợ cast)
    for t in all_trips:
        if str(t.ma_moi).startswith(code):
            trip = t
            break

    if trip:
        # --- LOGIC MỚI: Cấp quyền ngay lập tức ---
        # Nếu mã đúng, lưu session luôn để vào trang chi tiết không bị hỏi lại
        request.session[f'access_granted_{trip.pk}'] = True
        
        return JsonResponse({
            'status': 'success',
            'url': trip.get_absolute_url()
        }) 
    else: 
        return JsonResponse({
            'status': 'error', 
            'message': 'Không tìm thấy chuyến đi nào với mã này.'
        })

# 2. API XÁC THỰC MÃ TRUY CẬP (Dùng cho trang Detail Riêng tư)
@require_POST
def verify_trip_access_code(request, pk):
    trip = get_object_or_404(ChuyenDi, pk=pk)
    code = request.POST.get('access_code', '').strip()

    # So sánh mã (Cho phép nhập 8 ký tự đầu hoặc full)
    if str(trip.ma_moi).startswith(code):
        # QUAN TRỌNG: Lưu vào Session để lần sau không hỏi lại (trong phiên làm việc này)
        request.session[f'access_granted_{trip.pk}'] = True
        return JsonResponse({'status': 'success', 'message': 'Mã chính xác. Đang truy cập...'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Mã chuyến đi không đúng.'})
    

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
        
        # --- LOGIC QUYỀN TRUY CẬP RIÊNG TƯ ---
        is_organizer = (user.is_authenticated and trip.nguoi_to_chuc == user)
        membership = None
        if user.is_authenticated:
            membership = trip.thanh_vien.filter(user=user).first()
        
        is_member = (membership and membership.trang_thai_tham_gia == 'DA_THAM_GIA')
        
        # Kiểm tra Session xem đã nhập mã đúng lần nào chưa
        has_session_access = self.request.session.get(f'access_granted_{trip.pk}', False)

        # Flag: Cho phép xem nội dung hay không?
        # Xem được nếu: Công khai HOẶC Là chủ HOẶC Là thành viên HOẶC Đã nhập mã đúng
        can_view_details = (
            trip.che_do_rieng_tu == 'CONG_KHAI' or 
            is_organizer or 
            is_member or 
            has_session_access
        )

        context['can_view_details'] = can_view_details
        # --------------------------------------

        # Các context cũ giữ nguyên
        trip.so_thanh_vien_tham_gia = trip.thanh_vien.filter(trang_thai_tham_gia='DA_THAM_GIA').count()
        context['is_organizer'] = is_organizer
        context['membership'] = membership
        context['is_member'] = is_member
        
        if context['is_organizer']:
            context['pending_requests'] = trip.thanh_vien.filter(trang_thai_tham_gia='DA_GUI_YEU_CAU')
        
        return context

# ... (Giữ nguyên các hàm API: join_trip_request, leave_trip, approve_member...) ...
# ... COPY LẠI CÁC HÀM API TỪ FILE CŨ NẾU CẦN, HOẶC GIỮ NGUYÊN NẾU ĐÃ CÓ ...

# trips/views.py

@login_required
@require_POST
def join_trip_request(request, pk):
    trip = get_object_or_404(ChuyenDi, pk=pk)
    ly_do = request.POST.get('reason', '').strip()

    # 1. Kiểm tra Slot (Quan trọng)
    # Lấy số lượng thực tế đã tham gia
    current_members = trip.thanh_vien.filter(trang_thai_tham_gia='DA_THAM_GIA').count()
    if current_members >= trip.so_luong_toi_da:
        return JsonResponse({'status': 'error', 'message': 'Rất tiếc, chuyến đi đã đủ thành viên.'}, status=400)

    # 2. Tìm xem User này đã có trong danh sách chưa
    membership = trip.thanh_vien.filter(user=request.user).first()

    if membership:
        # --- TRƯỜNG HỢP A: Đã có record ---
        
        # Nếu đang tham gia hoặc đang chờ -> Báo lỗi
        if membership.trang_thai_tham_gia in ['DA_THAM_GIA', 'DA_GUI_YEU_CAU']:
            return JsonResponse({'status': 'error', 'message': 'Bạn đã gửi yêu cầu hoặc đang là thành viên.'}, status=400)
        
        # Nếu bị từ chối -> Có thể chặn hoặc cho gửi lại (Tùy bạn, ở đây tôi cho chặn để tránh spam)
        if membership.trang_thai_tham_gia == 'BI_TU_CHOI':
             return JsonResponse({'status': 'error', 'message': 'Yêu cầu của bạn trước đó đã bị từ chối.'}, status=400)

        # Nếu ĐÃ RỜI ĐI -> KÍCH HOẠT LẠI (UPDATE)
        if membership.trang_thai_tham_gia == 'DA_ROI_DI':
            membership.trang_thai_tham_gia = 'DA_GUI_YEU_CAU' # Đưa về trạng thái chờ duyệt
            membership.ly_do_tham_gia = ly_do # Cập nhật lý do mới
            membership.ngay_tham_gia = timezone.now() # Cập nhật lại thời gian
            membership.save()
            return JsonResponse({'status': 'success', 'message': 'Chào mừng quay lại! Yêu cầu đã được gửi.'})

    else:
        # --- TRƯỜNG HỢP B: Chưa từng tham gia -> TẠO MỚI (CREATE) ---
        ChuyenDiThanhVien.objects.create(
            chuyen_di=trip, 
            user=request.user,
            ly_do_tham_gia=ly_do,
            trang_thai_tham_gia='DA_GUI_YEU_CAU'
        )
        return JsonResponse({'status': 'success', 'message': 'Đã gửi yêu cầu tham gia.'})
    
    # Fallback cho các trường hợp lạ
    return JsonResponse({'status': 'error', 'message': 'Không thể thực hiện yêu cầu.'}, status=400)
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
    
    # Logic phân quyền:
    # 1. Là thành viên ĐÃ THAM GIA
    is_member = trip.thanh_vien.filter(user=request.user, trang_thai_tham_gia='DA_THAM_GIA').exists()
    # 2. Là người tổ chức (Owner)
    is_owner = trip.nguoi_to_chuc == request.user
    # 3. Là Admin (Staff) - MỚI THÊM
    is_admin = request.user.is_staff 

    if not (is_member or is_owner or is_admin):
        return HttpResponseForbidden("Bạn không có quyền tải lên media cho chuyến đi này.")
        
    uploaded_files = []
    for f in request.FILES.getlist('files'):
        # Tạo media
        media = ChuyenDiMedia.objects.create(chuyen_di=trip, user=request.user, file=f)
        uploaded_files.append({'id': media.id, 'url': media.file.url})
        
    return JsonResponse({
        'status': 'success', 
        'message': f'Đã tải lên {len(uploaded_files)} file.', 
        'files': uploaded_files
    })

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
    
    # Logic phân quyền xóa:
    # 1. Người tải lên ảnh đó (Owner của Media)
    is_media_owner = media.user == request.user
    # 2. Chủ chuyến đi (Owner của Trip)
    is_trip_owner = media.chuyen_di.nguoi_to_chuc == request.user
    # 3. Admin (Staff) - MỚI THÊM
    is_admin = request.user.is_staff

    if not (is_media_owner or is_trip_owner or is_admin):
        return HttpResponseForbidden("Bạn không có quyền xóa media này.")
        
    # Xử lý nếu ảnh bị xóa là ảnh bìa -> Reset ảnh bìa
    if media.chuyen_di.anh_bia_id == media.id:
        media.chuyen_di.anh_bia = None
        media.chuyen_di.save()
        
    media.delete()
    return JsonResponse({'status': 'success', 'message': 'Đã xóa media.'})

# trips/views.py

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
        
        # --- LOGIC GIAO DIỆN ĐỘNG ---
        context['base_template'] = get_base_template(self.request)
        context['is_admin_view'] = 'admin_base.html' in context['base_template']
        # ----------------------------
        
        return context
    

 # ==========================================================
# === 4. CHỨC NĂNG CHAT ROOM (THÊM MỚI) ===
# ==========================================================

# ==========================================================
# === 4. CHỨC NĂNG CHAT ROOM ===
# ==========================================================

class TripChatRoomView(LoginRequiredMixin, DetailView):
    model = ChuyenDi
    template_name = 'trips/chat_room.html'
    context_object_name = 'trip'
    pk_url_kwarg = 'trip_id'

    def get_object(self):
        trip = get_object_or_404(ChuyenDi, pk=self.kwargs['trip_id'])
        # Kiểm tra quyền truy cập (Chủ phòng hoặc Thành viên đã tham gia)
        is_organizer = (trip.nguoi_to_chuc == self.request.user)
        is_member = trip.thanh_vien.filter(user=self.request.user, trang_thai_tham_gia='DA_THAM_GIA').exists()
        
        if not (is_member or is_organizer):
            raise HttpResponseForbidden("Bạn không có quyền truy cập vào nhóm chat này.")
        return trip

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        trip = self.object
        user = self.request.user

        # --- 1. SIDEBAR: DANH SÁCH NHÓM CHAT ---
        # Subquery: Lấy thời gian và nội dung tin nhắn cuối cùng
        last_msg_qs = ChuyenDiTinNhan.objects.filter(chuyen_di=OuterRef('pk')).order_by('-thoi_gian_gui')
        
        my_trips = ChuyenDi.objects.filter(
            Q(thanh_vien__user=user, thanh_vien__trang_thai_tham_gia='DA_THAM_GIA') | 
            Q(nguoi_to_chuc=user)
        ).distinct().annotate(
            last_activity=Subquery(last_msg_qs.values('thoi_gian_gui')[:1]),
            preview_content=Subquery(last_msg_qs.values('noi_dung')[:1])
        ).order_by(F('last_activity').desc(nulls_last=True), '-ngay_tao')
        
        context['my_trips'] = my_trips

# B1: Lấy list các tuple (id, tên)
        route_tuples = my_trips.values_list('cung_duong__id', 'cung_duong__ten')
        
        # B2: Dùng set để loại bỏ dòng trùng lặp
        unique_routes = set(route_tuples)
        
        # B3: Chuyển lại thành list dictionary và sắp xếp A-Z
        context['available_routes'] = sorted(
            [
                {'cung_duong__id': r[0], 'cung_duong__ten': r[1]} 
                for r in unique_routes 
                if r[0] is not None  # Loại bỏ None nếu có
            ],
            key=lambda x: x['cung_duong__ten'] # Sắp xếp theo tên
        )
        # ========================================================================

        # --- 2. THÔNG TIN THÀNH VIÊN ---
        context['members'] = trip.thanh_vien.filter(
            trang_thai_tham_gia='DA_THAM_GIA'
        ).select_related('user__taikhoanhoso')

        # --- 3. MEDIA (ẢNH/VIDEO) ---
        context['chat_media_files'] = ChuyenDiTinNhanMedia.objects.filter(
            tin_nhan__chuyen_di=trip,
            tin_nhan__da_xoa=False 
        ).select_related('tin_nhan__nguoi_gui').order_by('-tin_nhan__thoi_gian_gui')
        
        return context

# --- API: LẤY DANH SÁCH NHÓM (Dùng cho AJAX Search/Filter nếu cần) ---
@login_required
def get_my_chat_groups(request):
    user = request.user
    query = request.GET.get('q', '').strip()
    route_id = request.GET.get('route_id', '')

    # 1. Subquery lấy tin nhắn cuối cùng
    last_msg_qs = ChuyenDiTinNhan.objects.filter(chuyen_di=OuterRef('pk')).order_by('-thoi_gian_gui')

    # 2. Filter cơ bản (User tham gia)
    my_trips = ChuyenDi.objects.filter(
        Q(thanh_vien__user=user, thanh_vien__trang_thai_tham_gia='DA_THAM_GIA') | 
        Q(nguoi_to_chuc=user)
    ).distinct()

    # 3. Tìm kiếm theo tên
    if query:
        my_trips = my_trips.filter(ten_chuyen_di__icontains=query)

    # 4. Lọc theo cung đường (Route)
    if route_id and route_id != 'all':
        my_trips = my_trips.filter(cung_duong_id=route_id)

    # 5. Annotate & Order
    my_trips = my_trips.annotate(
        last_activity=Subquery(last_msg_qs.values('thoi_gian_gui')[:1]),
        preview_content=Subquery(last_msg_qs.values('noi_dung')[:1])
    ).order_by(F('last_activity').desc(nulls_last=True), '-ngay_tao')

    data = []
    for trip in my_trips:
        # Format thời gian: Nếu là hôm nay thì hiện giờ, khác thì hiện ngày/tháng
        time_str = ""
        if trip.last_activity:
            now = timezone.now().date()
            msg_date = trip.last_activity.date()
            time_str = trip.last_activity.strftime("%H:%M") if msg_date == now else trip.last_activity.strftime("%d/%m")

        # Xử lý cover url an toàn (tránh lỗi nếu ko có method cover_url)
        cover = trip.cover_url if hasattr(trip, 'cover_url') else (trip.anh_bia.file.url if trip.anh_bia else '/static/images/default-trip.jpg')
        
        # Xử lý lấy tên người tổ chức
        organizer_name = trip.nguoi_to_chuc.get_full_name() or trip.nguoi_to_chuc.username

        data.append({
            'id': trip.id,
            'name': trip.ten_chuyen_di,
            'cover': cover,
            'url': trip.get_chat_url() if hasattr(trip, 'get_chat_url') else f"/chuyen-di/chat/{trip.pk}/", # Fallback URL
            'status_name': trip.trang_thai.ten if trip.trang_thai else "",
            'last_msg': trip.preview_content or "Chưa có tin nhắn",
            'last_time': time_str,
            'organizer': organizer_name
        })
    
    return JsonResponse({'groups': data})
@login_required # Bắt buộc phải đăng nhập
@require_POST   # Chỉ chấp nhận method POST (chặn GET truy cập trực tiếp)
def send_chat_message(request, trip_id):
    """API gửi tin nhắn (AJAX) - Có hỗ trợ Reply & File"""
    
    # 1. KIỂM TRA DỮ LIỆU CƠ BẢN
    trip = get_object_or_404(ChuyenDi, pk=trip_id)
    
    # 2. KIỂM TRA QUYỀN (BẮT BUỘC)
    is_organizer = (trip.nguoi_to_chuc == request.user)
    is_member = trip.thanh_vien.filter(user=request.user, trang_thai_tham_gia='DA_THAM_GIA').exists()
    
    if not (is_organizer or is_member):
        return JsonResponse({'status': 'error', 'message': 'Bạn không có quyền gửi tin nhắn.'}, status=403)

    # 3. LẤY DỮ LIỆU FORM
    noi_dung = request.POST.get('message', '').strip()
    files = request.FILES.getlist('files')
    reply_to_id = request.POST.get('reply_to_id')

    if not noi_dung and not files:
        return JsonResponse({'status': 'error', 'message': 'Tin nhắn rỗng.'}, status=400)

    # 4. XỬ LÝ REPLY
    reply_obj = None
    if reply_to_id:
        try:
            reply_obj = ChuyenDiTinNhan.objects.get(pk=reply_to_id, chuyen_di=trip)
        except (ChuyenDiTinNhan.DoesNotExist, ValueError):
            pass 

    # 5. LƯU DỮ LIỆU (Dùng transaction.atomic để đảm bảo toàn vẹn)
    try:
        with transaction.atomic(): # <--- Bắt đầu giao dịch an toàn
            # A. Tạo tin nhắn
            tin_nhan = ChuyenDiTinNhan.objects.create(
                chuyen_di=trip,
                nguoi_gui=request.user,
                tra_loi_tin_nhan=reply_obj,
                noi_dung=noi_dung
            )

            # B. Xử lý File (Nếu tin nhắn lỗi thì file cũng không được lưu và ngược lại)
            if files:
                media_bulk_list = [] # (Tối ưu: gom lại lưu 1 lần nếu muốn, nhưng create từng cái cũng ok)
                for f in files:
                    mime = getattr(f, 'content_type', '')
                    if mime.startswith('image'): loai = 'ANH'
                    elif mime.startswith('video'): loai = 'VIDEO'
                    else: loai = 'FILE'
                    
                    size_kb = round(f.size / 1024, 2)

                    ChuyenDiTinNhanMedia.objects.create(
                        tin_nhan=tin_nhan,
                        duong_dan_file=f,
                        loai_media=loai,
                        ten_file_goc=f.name,
                        kich_thuoc_file_kb=size_kb
                    )
        
        # Nếu chạy đến đây tức là không có lỗi -> Trả về Success
        return JsonResponse({'status': 'success', 'msg_id': tin_nhan.id})

    except Exception as e:
        # Nếu có lỗi trong khối atomic, mọi thứ sẽ được rollback (hoàn tác)
        print(f"Lỗi gửi tin nhắn: {str(e)}")
        return JsonResponse({'status': 'error', 'message': 'Lỗi Server: ' + str(e)}, status=500)
    
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
    """API lấy tin nhắn tối ưu (Chỉ lấy 50 tin gần nhất khi mới vào)"""
    try:
        trip = get_object_or_404(ChuyenDi, pk=trip_id)
        
        # 1. Check quyền
        is_organizer = (trip.nguoi_to_chuc == request.user)
        is_member = trip.thanh_vien.filter(user=request.user, trang_thai_tham_gia='DA_THAM_GIA').exists()
        if not (is_organizer or is_member):
            return JsonResponse({'status': 'error', 'message': 'Forbidden'}, status=403)

        # 2. Base QuerySet (Tối ưu query DB)
        messages_qs = ChuyenDiTinNhan.objects.filter(chuyen_di=trip)\
            .select_related('nguoi_gui__taikhoanhoso', 'tra_loi_tin_nhan__nguoi_gui')\
            .prefetch_related('media', 'likes', 'dislikes')
            
        last_id = request.GET.get('last_id', 0)
        try: 
            last_id = int(last_id)
        except (ValueError, TypeError): 
            last_id = 0
        
        # 3. LOGIC LẤY TIN NHẮN (QUAN TRỌNG)
        if last_id == 0:
            # === MỚI VÀO PHÒNG: CHỈ LẤY 50 TIN CUỐI CÙNG ===
            # Lấy 50 tin mới nhất (sắp xếp giảm dần để slice)
            last_50_msgs = messages_qs.order_by('-thoi_gian_gui')[:50]
            # Đảo ngược lại để hiển thị đúng thứ tự thời gian (Cũ -> Mới)
            new_msgs = reversed(last_50_msgs) 
        else:
            # === REALTIME: LẤY CÁC TIN MỚI HƠN LAST_ID ===
            new_msgs = messages_qs.filter(id__gt=last_id).order_by('thoi_gian_gui')

        # Lấy tin cũ để check update (Like/Xóa)
        old_msgs_to_check = messages_qs.filter(id__lte=last_id).order_by('-id')[:20]

        # 4. Hàm Format Data (Giữ nguyên logic chuẩn)
        def format_msg_data(msg):
            # Media
            media_list = []
            if not msg.da_xoa:
                for m in msg.media.all():
                    if m.duong_dan_file:
                        media_list.append({
                            'url': m.duong_dan_file.url,
                            'type': m.loai_media,
                            'name': m.ten_file_goc
                        })
            
            # Avatar
            avatar_url = '/static/images/default-avatar.png'
            if hasattr(msg.nguoi_gui, 'taikhoanhoso'):
                hoso = msg.nguoi_gui.taikhoanhoso
                user_avatar = getattr(hoso, 'avatar', None) or getattr(hoso, 'anh_dai_dien', None)
                if user_avatar:
                    try: avatar_url = user_avatar.url
                    except ValueError: pass

            # Reply
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

            # Reactions & Content
            is_liked = request.user in msg.likes.all()
            is_disliked = request.user in msg.dislikes.all()
            final_content = msg.noi_dung
            if msg.da_xoa: final_content = "Tin nhắn đã bị thu hồi."

            # Timezone Safe
            try:
                local_time = timezone.localtime(msg.thoi_gian_gui)
                now = timezone.localtime(timezone.now())
                if local_time.date() == now.date():
                    time_str = local_time.strftime("%H:%M")
                else:
                    time_str = local_time.strftime("%d/%m %H:%M")
                iso_date = local_time.isoformat()
            except:
                time_str = msg.thoi_gian_gui.strftime("%H:%M")
                iso_date = str(msg.thoi_gian_gui)

            return {
                'id': msg.id,
                'user_id': msg.nguoi_gui.id,
                'username': msg.nguoi_gui.get_full_name() or msg.nguoi_gui.username,
                'avatar': avatar_url,
                'content': final_content,
                'timestamp': time_str,
                'full_date': iso_date,
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

        data_messages = [format_msg_data(m) for m in new_msgs]
        data_updates = [format_msg_data(m) for m in old_msgs_to_check]
            
        return JsonResponse({
            'messages': data_messages,
            'updates': data_updates
        })
    except Exception as e:
        print(f"CHAT ERROR: {e}") # In lỗi ra terminal để debug
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
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
# trips/views.py

# trips/views.py

class MyTripsView(LoginRequiredMixin, ListView):
    model = ChuyenDi
    template_name = 'trips/my_trips.html'
    context_object_name = 'trips'
    paginate_by = 9

    def get_queryset(self):
        user = self.request.user
        
        # 1. Base Query
        # --- SỬA LỖI Ở ĐÂY: Đã xóa 'trang_thai' khỏi select_related ---
        queryset = ChuyenDi.objects.filter(
            Q(thanh_vien__user=user) | Q(nguoi_to_chuc=user)
        ).distinct().select_related(
            'cung_duong', 
            'nguoi_to_chuc__taikhoanhoso', 
            'anh_bia'  # Chỉ giữ lại các trường là ForeignKey thật sự
        ).annotate(
            my_status=Subquery(
                ChuyenDiThanhVien.objects.filter(
                    chuyen_di=OuterRef('pk'),
                    user=user
                ).values('trang_thai_tham_gia')[:1]
            )
        )

        # 2. XỬ LÝ BỘ LỌC (Giữ nguyên)
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(ten_chuyen_di__icontains=q)

        status_filter = self.request.GET.get('status')
        now = timezone.now()
        if status_filter == 'upcoming':
            queryset = queryset.filter(ngay_ket_thuc__gte=now)
        elif status_filter == 'past':
            queryset = queryset.filter(ngay_ket_thuc__lt=now)

        role_filter = self.request.GET.get('role')
        if role_filter == 'host':
            queryset = queryset.filter(nguoi_to_chuc=user)
        elif role_filter == 'member':
            queryset = queryset.filter(thanh_vien__user=user).exclude(nguoi_to_chuc=user)

        return queryset.order_by('-ngay_bat_dau')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        now = timezone.now()

        # Stats Query
        base_qs = ChuyenDi.objects.filter(
            Q(thanh_vien__user=user, thanh_vien__trang_thai_tham_gia='DA_THAM_GIA') | 
            Q(nguoi_to_chuc=user)
        ).distinct()

        completed_qs = base_qs.filter(ngay_ket_thuc__lt=now)
        
        total_km_agg = completed_qs.aggregate(total=Sum('cd_do_dai_km'))['total']
        total_spent_agg = completed_qs.aggregate(total=Sum('chi_phi_uoc_tinh'))['total']

        context['stats'] = {
            'total_trips': completed_qs.count(),
            'total_km': total_km_agg if total_km_agg is not None else 0,
            'total_spent': total_spent_agg if total_spent_agg is not None else 0,
            'hosted': base_qs.filter(nguoi_to_chuc=user).count(),
        }
        
        context['page_title'] = "Quản lý Chuyến đi"
        return context
@require_POST
def delete_or_leave_trip(request, pk):
    trip = get_object_or_404(ChuyenDi, pk=pk)

    # 1. Nếu là Host -> Xóa chuyến đi
    if trip.nguoi_to_chuc == request.user:
        # (Tùy chọn) Kiểm tra nếu có thành viên khác thì không cho xóa, hoặc thông báo
        trip.delete()
        messages.success(request, f"Đã hủy chuyến đi: {trip.ten_chuyen_di}")
    
    # 2. Nếu là Member -> Rời nhóm
    else:
        member = ChuyenDiThanhVien.objects.filter(chuyen_di=trip, user=request.user).first()
        if member:
            member.delete()
            messages.success(request, f"Đã rời khỏi chuyến đi: {trip.ten_chuyen_di}")
        else:
            messages.error(request, "Bạn không phải là thành viên của chuyến đi này.")

    # return phải thụt đúng
    return redirect('trips:my_trips')
# ==========================================================
# === CÁC VIEW QUẢN TRỊ (ADMIN DASHBOARD) ===
# ==========================================================

class TripAdminListView(AdminRequiredMixin, ListView):
    model = ChuyenDi
    template_name = 'admin/trips/trip_list.html'
    context_object_name = 'trips'
    paginate_by = 15

    def get_queryset(self):
        # 1. Base Query: Lấy dữ liệu + Annotate
        queryset = ChuyenDi.objects.select_related(
            'nguoi_to_chuc__taikhoanhoso', 
            'cung_duong__tinh_thanh'
        ).annotate(
            # Đếm số người đã tham gia (Trạng thái = DA_THAM_GIA)
            total_members=Count('thanh_vien', 
                                filter=Q(thanh_vien__trang_thai_tham_gia='DA_THAM_GIA'), 
                                distinct=True),
            
            # Đếm tương tác
            total_msgs=Count('tin_nhan', distinct=True),
            total_media=Count('media', distinct=True)
        ).order_by('-ngay_bat_dau')

        # 2. Xử lý Bộ lọc
        self.filter_form = TripAdminFilterForm(self.request.GET)
        
        if self.filter_form.is_valid():
            data = self.filter_form.cleaned_data
            today = timezone.now()

            # --- Lọc Từ khóa ---
            if data.get('q'):
                queryset = queryset.filter(
                    Q(ten_chuyen_di__icontains=data['q']) | 
                    Q(nguoi_to_chuc__username__icontains=data['q'])
                )
            
            # --- Lọc Cung đường (MỚI) ---
            if data.get('cung_duong'):
                queryset = queryset.filter(cung_duong=data['cung_duong'])

            # --- Lọc Tỉnh thành ---
            if data.get('tinh_thanh'):
                queryset = queryset.filter(cung_duong__tinh_thanh=data['tinh_thanh'])

            # --- LỌC RỦI RO / TRẠNG THÁI ---
            risk_type = data.get('admin_status')
            
            if risk_type == 'upcoming_urgent':
                # Sắp đi trong 3 ngày tới
                limit = today + datetime.timedelta(days=3)
                queryset = queryset.filter(ngay_bat_dau__range=(today, limit), trang_thai='DANG_TUYEN')

            elif risk_type == 'ghost':
                # "Ma": Sắp đi (trong 7 ngày tới) NHƯNG < 2 người tham gia
                # Đã mở rộng range lên 7 ngày để dễ bắt lỗi hơn
                limit = today + datetime.timedelta(days=7)
                queryset = queryset.filter(
                    ngay_bat_dau__range=(today, limit),
                    total_members__lt=2,
                    trang_thai='DANG_TUYEN'
                )

            elif risk_type == 'crowded':
                # Đã full slot
                queryset = queryset.filter(total_members__gte=F('so_luong_toi_da'))

            elif risk_type == 'high_risk':
                # Thu tiền nhiều (> 5tr)
                queryset = queryset.filter(chi_phi_uoc_tinh__gte=5000000)

            elif risk_type == 'ongoing':
                # Đang diễn ra
                queryset = queryset.filter(ngay_bat_dau__lte=today, ngay_ket_thuc__gte=today)

            elif risk_type == 'canceled':
                # Đã hủy
                queryset = queryset.filter(trang_thai__in=['DA_HUY', 'TAM_HOAN'])

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Thống kê nhanh
        today = timezone.now()
        base_qs = ChuyenDi.objects.all()
        
        context['stats'] = {
            'total_active': base_qs.filter(trang_thai='DANG_TUYEN').count(),
            'ongoing_count': base_qs.filter(ngay_bat_dau__lte=today, ngay_ket_thuc__gte=today).count(),
            'urgent_24h': base_qs.filter(ngay_bat_dau__range=(today, today + datetime.timedelta(days=1))).count(),
            'canceled': base_qs.filter(trang_thai='DA_HUY').count()
        }
        
        context['page_title'] = "Giám sát & Quản lý Chuyến đi"
        context['filter_form'] = getattr(self, 'filter_form', TripAdminFilterForm(self.request.GET))
        
        # Giữ param khi phân trang
        params = self.request.GET.copy()
        if 'page' in params: del params['page']
        context['query_params'] = params.urlencode()
        context['now'] = today
        
        return context

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Thống kê nhanh cho Dashboard Mini (Trên đầu trang danh sách)
        today = timezone.now()
        
        # Queryset cơ sở để đếm thống kê (Tránh lặp lại code)
        base_qs = ChuyenDi.objects.all()
        
        context['stats'] = {
            'total_active': base_qs.filter(trang_thai='DANG_TUYEN').count(),
            # Đếm số đoàn đang trên núi (Đang diễn ra)
            'ongoing_count': base_qs.filter(ngay_bat_dau__lte=today, ngay_ket_thuc__gte=today).count(),
            # Đếm số đoàn sắp đi trong 24h tới
            'urgent_24h': base_qs.filter(ngay_bat_dau__range=(today, today + datetime.timedelta(days=1))).count(),
            'canceled': base_qs.filter(trang_thai='DA_HUY').count()
        }
        
        context['page_title'] = "Giám sát & Quản lý Chuyến đi"
        # Khởi tạo form nếu chưa có (để tránh lỗi template khi không filter)
        context['filter_form'] = getattr(self, 'filter_form', TripAdminFilterForm(self.request.GET))
        
        # Giữ param khi phân trang
        params = self.request.GET.copy()
        if 'page' in params: del params['page']
        context['query_params'] = params.urlencode()
        
        # Truyền biến 'now' xuống template để so sánh ngày tháng (hiện badge 'Hôm nay')
        context['now'] = today
        
        return context

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def force_cancel_trip(request, pk):
    trip = get_object_or_404(ChuyenDi, pk=pk)
    trip.trang_thai = 'DA_HUY'
    trip.save()
    messages.success(request, f"Đã hủy khẩn cấp chuyến đi: {trip.ten_chuyen_di}")
    return redirect('trips_admin:trip_list')
@login_required
@user_passes_test(lambda u: u.is_staff)
def export_trips_csv(request):
    # Tạo response object với content type là CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="danh_sach_chuyen_di.csv"'
    
    # Cho phép viết tiếng Việt (UTF-8 BOM)
    response.write(u'\ufeff'.encode('utf8')) 

    writer = csv.writer(response)
    
    # 1. Viết tiêu đề cột
    writer.writerow(['ID', 'Tên chuyến đi', 'Host (Leader)', 'Ngày đi', 'Ngày về', 'Số lượng', 'Chi phí', 'Trạng thái', 'Ngày tạo'])

    # 2. Lấy dữ liệu (Có thể tái sử dụng logic lọc nếu muốn, ở đây ta lấy all cho đơn giản)
    trips = ChuyenDi.objects.all().select_related('nguoi_to_chuc').order_by('-ngay_bat_dau')

    # 3. Viết dữ liệu từng dòng
    for trip in trips:
        # Tính số thành viên
        total_mem = trip.thanh_vien.filter(trang_thai_tham_gia='DA_THAM_GIA').count()
        
        writer.writerow([
            trip.id,
            trip.ten_chuyen_di,
            trip.nguoi_to_chuc.username,
            trip.ngay_bat_dau.strftime("%d/%m/%Y %H:%M"),
            trip.ngay_ket_thuc.strftime("%d/%m/%Y %H:%M"),
            f"{total_mem}/{trip.so_luong_toi_da}",
            trip.chi_phi_uoc_tinh,
            trip.get_trang_thai_display(),
            trip.ngay_tao.strftime("%d/%m/%Y")
        ])

    return response
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_peek_chat(request, pk):
    trip = get_object_or_404(ChuyenDi, pk=pk)
    
    # Lấy 100 tin nhắn gần nhất (tăng lên vì xem trang riêng rộng hơn)
    messages_qs = ChuyenDiTinNhan.objects.filter(chuyen_di=trip)\
        .select_related('nguoi_gui__taikhoanhoso')\
        .prefetch_related('media')\
        .order_by('-thoi_gian_gui')[:100]
    
    context = {
        'trip': trip,
        'messages': reversed(messages_qs), # Đảo ngược để tin cũ ở trên, tin mới ở dưới
        'page_title': f'Log Chat: {trip.ten_chuyen_di}'
    }
    
    # Thay đổi template trỏ đến file mới
    return render(request, 'admin/trips/trip_chat_log_full.html', context)
# ==========================================================
# === CÁC VIEW QUẢN TRỊ VIÊN MỚI (MEMBER MANAGEMENT) ===
# ==========================================================

@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_trip_members_manage(request, pk):
    trip = get_object_or_404(ChuyenDi, pk=pk)
    
    # Lấy danh sách thành viên (Leader lên đầu)
    members = trip.thanh_vien.select_related('user__taikhoanhoso').order_by(
        Case(When(vai_tro='TRUONG_DOAN', then=0), default=1),
        'ngay_tham_gia'
    )

    # Render file HTML con (Partial View)
    # Đảm bảo bạn đã tạo file templates/admin/trips/partial_member_list.html
    html_content = render_to_string('admin/trips/partial_member_list.html', {
        'members': members,
        'trip': trip
    }, request=request)

    return JsonResponse({'status': 'success', 'html': html_content})

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def admin_kick_member(request, member_id):
    """
    Admin chặn thành viên (Chuyển trạng thái sang BI_TU_CHOI)
    """
    membership = get_object_or_404(ChuyenDiThanhVien, pk=member_id)
    
    # Không cho phép chặn Trưởng đoàn (tránh lỗi logic)
    if membership.vai_tro == 'TRUONG_DOAN':
        return JsonResponse({'status': 'error', 'message': 'Không thể chặn Trưởng đoàn. Hãy đổi Leader trước.'}, status=400)

    try:
        membership.trang_thai_tham_gia = 'BI_TU_CHOI'
        membership.save()
        return JsonResponse({
            'status': 'success', 
            'message': f'Đã chặn thành viên: {membership.user.username}'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_POST
def admin_restore_member(request, member_id):
    """
    Admin khôi phục thành viên (Chuyển trạng thái về DA_THAM_GIA)
    """
    membership = get_object_or_404(ChuyenDiThanhVien, pk=member_id)
    trip = membership.chuyen_di

    # Kiểm tra slot (Admin có thể override, nhưng nên cảnh báo nếu cần thiết)
    # Ở đây ta cho phép Admin override luôn (quyền lực tối cao)
    
    try:
        membership.trang_thai_tham_gia = 'DA_THAM_GIA'
        membership.save()
        return JsonResponse({
            'status': 'success', 
            'message': f'Đã khôi phục thành viên: {membership.user.username}'
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
