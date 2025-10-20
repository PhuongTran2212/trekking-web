from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from .models import CongDongMediaBaiViet
from .models import (
    CongDongBaiViet, 
    CongDongMediaBaiViet, 
    CongDongBinhChonBaiViet,
    CongDongBinhLuan
)
from .forms import BaiVietForm, MediaBaiVietForm, BinhLuanForm


def danh_sach_bai_viet(request):
    """Hiển thị danh sách bài viết đã được duyệt"""
    bai_viet_list = CongDongBaiViet.objects.filter(
        trang_thai=CongDongBaiViet.TrangThaiBaiViet.DA_DUYET
    ).select_related('tac_gia', 'chuyen_di').prefetch_related('media')

    # Tìm kiếm
    search_query = request.GET.get('search', '')
    if search_query:
        bai_viet_list = bai_viet_list.filter(
            Q(tieu_de__icontains=search_query) | 
            Q(noi_dung__icontains=search_query)
        )

    # Phân trang
    paginator = Paginator(bai_viet_list, 10)
    page_number = request.GET.get('page')
    bai_viet = paginator.get_page(page_number)

    return render(request, 'community/danh_sach_bai_viet.html', {
        'bai_viet': bai_viet,
        'search_query': search_query,
    })


def chi_tiet_bai_viet(request, bai_viet_id):
    """
    Hiển thị chi tiết bài viết, bình luận và xử lý việc đăng bình luận
    theo mẫu Post/Redirect/Get.
    """
    qs = CongDongBaiViet.objects.select_related('tac_gia', 'chuyen_di') \
                                .prefetch_related('media', 'binh_luan__user', 'binh_luan__cac_tra_loi__user')
    bai_viet = get_object_or_404(qs, id=bai_viet_id)

    # Kiểm tra quyền truy cập: bài viết phải được duyệt HOẶC người xem là tác giả
    is_approved = bai_viet.trang_thai == CongDongBaiViet.TrangThaiBaiViet.DA_DUYET
    if not is_approved and bai_viet.tac_gia != request.user:
        raise Http404("Bài viết chưa được duyệt hoặc không tồn tại.")
    
    # --- XỬ LÝ YÊU CẦU POST ---
    # Chỉ xử lý POST nếu bài viết đã được duyệt
    if is_approved and request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Bạn cần đăng nhập để bình luận.')
            # Chuyển hướng đến trang đăng nhập thay vì trả về lỗi 403
            return redirect('accounts:login')

        form = BinhLuanForm(request.POST)
        if form.is_valid():
            binh_luan = form.save(commit=False)
            binh_luan.bai_viet = bai_viet
            binh_luan.user = request.user
            tra_loi_id = request.POST.get('tra_loi_binh_luan_id')
            if tra_loi_id:
                binh_luan.tra_loi_binh_luan_id = tra_loi_id
            binh_luan.save()
            messages.success(request, 'Đã thêm bình luận thành công.')
        else:
            # Nếu form không hợp lệ, tạo một thông báo lỗi duy nhất để hiển thị
            error_message = "Đã có lỗi xảy ra. Vui lòng kiểm tra lại nội dung bình luận."
            # Lấy lỗi cụ thể hơn nếu có
            if form.errors:
                first_error_field = list(form.errors.keys())[0]
                first_error_message = form.errors[first_error_field][0]
                error_message = f"Lỗi: {first_error_message}"

            messages.error(request, error_message)
        
        # Luôn luôn redirect về chính trang này sau khi xử lý POST
        return redirect('community:chi-tiet-bai-viet', bai_viet_id=bai_viet.id)

    # --- CHUẨN BỊ DỮ LIỆU CHO YÊU CẦU GET ---
    
    binh_luan_goc = bai_viet.binh_luan.filter(tra_loi_binh_luan__isnull=True)
    da_upvote = False
    form = None # Form sẽ là None nếu người dùng chưa đăng nhập hoặc bài viết chưa duyệt

    if is_approved and request.user.is_authenticated:
        da_upvote = bai_viet.da_binh_chon(request.user)
        form = BinhLuanForm() # Tạo một form trống cho người dùng nhập liệu

    context = {
        'bai_viet': bai_viet,
        'binh_luan_goc': binh_luan_goc,
        'form': form,
        'da_upvote': da_upvote,
        'is_approved': is_approved,
    }
    return render(request, 'community/chi_tiet_bai_viet.html', context)


@login_required
def tao_bai_viet(request):
    """Tạo bài viết mới"""
    if request.method == 'POST':
        form = BaiVietForm(request.POST)
        files = request.FILES.getlist('media_files')

        if form.is_valid():
            bai_viet = form.save(commit=False)
            bai_viet.tac_gia = request.user
            bai_viet.trang_thai = CongDongBaiViet.TrangThaiBaiViet.CHO_DUYET
            bai_viet.save()
            
            form.save_m2m()

            for file in files:
                loai_media = 'video' if file.content_type.startswith('video') else 'anh'
                CongDongMediaBaiViet.objects.create(
                    bai_viet=bai_viet,
                    loai_media=loai_media,
                    duong_dan_file=file
                )
                if hasattr(file, 'close'):
                    file.close()

            messages.success(request, 'Bài viết của bạn đã được gửi và đang chờ duyệt.')
            return redirect('community:bai-viet-cua-toi')
    else:
        form = BaiVietForm()

    return render(request, 'community/tao_bai_viet.html', {'form': form})


@login_required
def sua_bai_viet(request, bai_viet_id):
    """Chỉnh sửa bài viết"""
    bai_viet = get_object_or_404(CongDongBaiViet, id=bai_viet_id, tac_gia=request.user)

    if request.method == 'POST':
        form = BaiVietForm(request.POST, instance=bai_viet)
        files = request.FILES.getlist('media_files')

        if form.is_valid():
            bai_viet = form.save(commit=False)
            bai_viet.trang_thai = CongDongBaiViet.TrangThaiBaiViet.CHO_DUYET
            bai_viet.save()
            
            form.save_m2m()

            for file in files:
                loai_media = 'video' if file.content_type.startswith('video') else 'anh'
                CongDongMediaBaiViet.objects.create(
                    bai_viet=bai_viet,
                    loai_media=loai_media,
                    duong_dan_file=file
                )
                if hasattr(file, 'close'):
                    file.close()

            messages.success(request, 'Bài viết đã được cập nhật và đang chờ duyệt lại.')
            return redirect('community:bai-viet-cua-toi')
    else:
        form = BaiVietForm(instance=bai_viet)

    return render(request, 'community/sua_bai_viet.html', {'form': form, 'bai_viet': bai_viet})


@login_required
def xoa_bai_viet(request, bai_viet_id):
    """Xóa bài viết"""
    bai_viet = get_object_or_404(CongDongBaiViet, id=bai_viet_id, tac_gia=request.user)

    if request.method == 'POST':
        bai_viet.delete()
        messages.success(request, 'Đã xóa bài viết.')
        return redirect('community:bai-viet-cua-toi')

    return render(request, 'community/xoa_bai_viet.html', {'bai_viet': bai_viet})


@login_required
def bai_viet_cua_toi(request):
    """Hiển thị danh sách bài viết của người dùng hiện tại"""
    bai_viet_list = (
        CongDongBaiViet.objects
        .filter(tac_gia=request.user)
        .annotate(so_luong_binh_luan=Count('binh_luan'))
        .prefetch_related('media')
        .order_by('-ngay_dang')
    )

    paginator = Paginator(bai_viet_list, 10)
    page_number = request.GET.get('page')
    bai_viet = paginator.get_page(page_number)

    return render(request, 'community/bai_viet_cua_toi.html', {'bai_viet': bai_viet})


@login_required
@require_POST
def toggle_upvote(request, bai_viet_id):
    """Toggle upvote cho bài viết (AJAX)"""
    bai_viet = get_object_or_404(CongDongBaiViet, id=bai_viet_id)
    
    if bai_viet.trang_thai != CongDongBaiViet.TrangThaiBaiViet.DA_DUYET:
        return JsonResponse({
            'success': False,
            'error': 'Bài viết chưa được duyệt, không thể bình chọn.',
            'is_approved': False
        }, status=403)

    binh_chon = CongDongBinhChonBaiViet.objects.filter(
        bai_viet=bai_viet, user=request.user
    ).first()

    if binh_chon:
        binh_chon.delete()
        bai_viet.luot_binh_chon -= 1
        bai_viet.save()
        da_upvote = False
    else:
        CongDongBinhChonBaiViet.objects.create(bai_viet=bai_viet, user=request.user)
        bai_viet.luot_binh_chon += 1
        bai_viet.save()
        da_upvote = True

    return JsonResponse({
        'success': True,
        'da_upvote': da_upvote,
        'luot_binh_chon': bai_viet.luot_binh_chon,
        'is_approved': True
    })



@login_required
@require_POST
def xoa_media(request, media_id):
    """Xóa media của bài viết một cách an toàn và ghi lại lỗi (AJAX)"""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if not is_ajax:
        return JsonResponse({'success': False, 'error': 'Yêu cầu không hợp lệ.'}, status=400)

    try:
        media = get_object_or_404(CongDongMediaBaiViet, id=media_id)

        if media.bai_viet.tac_gia != request.user:
            return JsonResponse({'success': False, 'error': 'Bạn không có quyền thực hiện hành động này.'}, status=403)

        media.duong_dan_file.delete(save=False)
        media.delete()

        return JsonResponse({'success': True})

    except Exception as e:
        print(f"LỖI KHI XÓA MEDIA (ID: {media_id}): {e}")
        return JsonResponse({'success': False, 'error': 'Đã có lỗi xảy ra từ phía máy chủ.'}, status=500)


@login_required
@require_POST
def xoa_binh_luan(request, binh_luan_id):
    """Xóa bình luận"""
    binh_luan = get_object_or_404(CongDongBinhLuan, id=binh_luan_id)

    if binh_luan.user != request.user and not request.user.is_staff:
        messages.error(request, 'Bạn không có quyền xóa bình luận này.')
        return redirect('community:chi-tiet-bai-viet', bai_viet_id=binh_luan.bai_viet.id)

    bai_viet_id = binh_luan.bai_viet.id
    binh_luan.delete()
    messages.success(request, 'Đã xóa bình luận.')

    return redirect('community:chi-tiet-bai-viet', bai_viet_id=bai_viet_id)