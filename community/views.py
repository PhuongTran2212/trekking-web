import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.contrib.contenttypes.models import ContentType

# IMPORT FORMS
from .forms import BaiVietForm, MediaBaiVietForm, BinhLuanForm, BaoCaoForm

# IMPORT MODELS
from .models import (
    CongDongBaiViet, 
    CongDongMediaBaiViet, 
    CongDongBinhChonBaiViet,
    CongDongBinhLuan
)
from core.models import HeThongBaoCao

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
    qs = CongDongBaiViet.objects.select_related('tac_gia', 'chuyen_di') \
                                .prefetch_related('media', 'binh_luan__user', 'binh_luan__cac_tra_loi__user')
    bai_viet = get_object_or_404(qs, id=bai_viet_id)

    is_approved = bai_viet.trang_thai == CongDongBaiViet.TrangThaiBaiViet.DA_DUYET
    if not is_approved and bai_viet.tac_gia != request.user:
        raise Http404("Bài viết chưa được duyệt hoặc không tồn tại.")
    
    if is_approved and request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'Bạn cần đăng nhập để bình luận.')
            return redirect('accounts:login')

        form = BinhLuanForm(request.POST)
        if form.is_valid():
            binh_luan = form.save(commit=False)
            binh_luan.bai_viet = bai_viet
            binh_luan.user = request.user
            
            tra_loi_id = request.POST.get('tra_loi_binh_luan_id')
            if tra_loi_id:
                try:
                    binh_luan_cha = CongDongBinhLuan.objects.get(id=tra_loi_id, bai_viet=bai_viet)
                    binh_luan.tra_loi_binh_luan = binh_luan_cha
                except CongDongBinhLuan.DoesNotExist:
                    messages.error(request, 'Bình luận gốc không tồn tại.')
                    return redirect('community:chi-tiet-bai-viet', bai_viet_id=bai_viet.id)
            
            binh_luan.save()
            messages.success(request, 'Đã thêm bình luận thành công.')
        else:
            messages.error(request, "Đã có lỗi xảy ra với bình luận.")
        
        return redirect('community:chi-tiet-bai-viet', bai_viet_id=bai_viet.id)

    binh_luan_goc = bai_viet.binh_luan.filter(tra_loi_binh_luan__isnull=True)
    da_upvote = False
    form = None

    if is_approved and request.user.is_authenticated:
        da_upvote = bai_viet.da_binh_chon(request.user)
        form = BinhLuanForm()

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
            bai_viet.save() # Lưu để có ID tạo folder media
            
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
    """Chỉnh sửa bài viết: Reset bình luận và bình chọn khi lưu"""
    bai_viet = get_object_or_404(CongDongBaiViet, id=bai_viet_id, tac_gia=request.user)

    if request.method == 'POST':
        form = BaiVietForm(request.POST, instance=bai_viet)
        files = request.FILES.getlist('media_files')

        if form.is_valid():
            bai_viet = form.save(commit=False)
            
            # --- LOGIC MỚI: RESET DỮ LIỆU ---
            # 1. Đưa trạng thái về chờ duyệt
            bai_viet.trang_thai = CongDongBaiViet.TrangThaiBaiViet.CHO_DUYET
            
            # 2. Reset số lượt bình chọn về 0
            bai_viet.luot_binh_chon = 0
            
            # 3. Xóa lịch sử ai đã bình chọn (để họ có thể vote lại từ đầu)
            # Lưu ý: 'binh_chon' là related_name trong models.py
            bai_viet.binh_chon.all().delete()
            
            # 4. Xóa toàn bộ bình luận cũ
            # Lưu ý: 'binh_luan' là related_name trong models.py
            bai_viet.binh_luan.all().delete()
            # --------------------------------

            bai_viet.save()
            
            # Lưu tags
            form.save_m2m()

            # Xử lý media mới (giữ nguyên code cũ của bạn)
            for file in files:
                loai_media = 'video' if file.content_type.startswith('video') else 'anh'
                CongDongMediaBaiViet.objects.create(
                    bai_viet=bai_viet,
                    loai_media=loai_media,
                    duong_dan_file=file
                )
                if hasattr(file, 'close'):
                    file.close()

            messages.success(request, 'Bài viết đã được chỉnh sửa.')
            return redirect('community:bai-viet-cua-toi')
    else:
        form = BaiVietForm(instance=bai_viet)

    return render(request, 'community/sua_bai_viet.html', {'form': form, 'bai_viet': bai_viet})


@login_required
def xoa_bai_viet(request, bai_viet_id):
    bai_viet = get_object_or_404(CongDongBaiViet, id=bai_viet_id, tac_gia=request.user)
    if request.method == 'POST':
        bai_viet.delete()
        messages.success(request, 'Đã xóa bài viết.')
        return redirect('community:bai-viet-cua-toi')
    return render(request, 'community/xoa_bai_viet.html', {'bai_viet': bai_viet})


@login_required
def bai_viet_cua_toi(request):
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

# --- HÀM XÓA MEDIA ĐÃ ĐƯỢC FIX ---
@login_required
@require_POST
def xoa_media(request, media_id):
    """
    Xóa media (ảnh/video). 
    Fix lỗi: Ưu tiên xóa DB trước hoặc bất chấp lỗi file lock để đảm bảo UI cập nhật.
    """
    # 1. Lấy object hoặc 404
    media = get_object_or_404(CongDongMediaBaiViet, id=media_id)

    # 2. Kiểm tra quyền
    if media.bai_viet.tac_gia != request.user and not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Bạn không có quyền xóa media này.'}, status=403)

    try:
        # 3. Thử xóa file vật lý
        if media.duong_dan_file:
            try:
                path = media.duong_dan_file.path
                if os.path.isfile(path):
                    if hasattr(media.duong_dan_file, 'close'):
                        media.duong_dan_file.close() # Đóng file
                    os.remove(path)
            except Exception as e:
                # Nếu Windows lock file, in lỗi ra console nhưng VẪN TIẾP TỤC xóa DB
                print(f"Window Lock Warning: Không xóa được file vật lý {media_id}. Lỗi: {e}")

        # 4. XÓA DATABASE (BẮT BUỘC)
        media.delete()

        return JsonResponse({'success': True})

    except Exception as e:
        print(f"CRITICAL ERROR khi xóa media ID {media_id}: {e}")
        return JsonResponse({'success': False, 'error': 'Lỗi server khi xóa dữ liệu.'}, status=500)
# ---------------------------------

@login_required
@require_POST
def xoa_binh_luan(request, binh_luan_id):
    binh_luan = get_object_or_404(CongDongBinhLuan, id=binh_luan_id)
    if binh_luan.user != request.user and not request.user.is_staff:
        messages.error(request, 'Bạn không có quyền xóa bình luận này.')
        return redirect('community:chi-tiet-bai-viet', bai_viet_id=binh_luan.bai_viet.id)

    bai_viet_id = binh_luan.bai_viet.id
    binh_luan.delete()
    messages.success(request, 'Đã xóa bình luận.')
    return redirect('community:chi-tiet-bai-viet', bai_viet_id=bai_viet_id)

@login_required
def bao_cao_bai_viet(request, bai_viet_id):
    bai_viet = get_object_or_404(CongDongBaiViet, id=bai_viet_id)
    content_type = ContentType.objects.get_for_model(bai_viet)

    da_bao_cao = HeThongBaoCao.objects.filter(
        nguoi_bao_cao=request.user,
        content_type=content_type,
        object_id=bai_viet.id
    ).exists()

    if da_bao_cao:
        messages.warning(request, 'Bạn đã báo cáo bài viết này rồi.')
        return redirect('community:chi-tiet-bai-viet', bai_viet_id=bai_viet.id)

    if request.method == 'POST':
        form = BaoCaoForm(request.POST)
        if form.is_valid():
            bao_cao = form.save(commit=False)
            bao_cao.nguoi_bao_cao = request.user
            bao_cao.content_object = bai_viet
            bao_cao.save()
            messages.success(request, 'Cảm ơn bạn đã gửi báo cáo.')
            return redirect('community:chi-tiet-bai-viet', bai_viet_id=bai_viet.id)
    else:
        form = BaoCaoForm()

    return render(request, 'community/bao_cao_bai_viet.html', {
        'form': form,
        'bai_viet': bai_viet
    })
