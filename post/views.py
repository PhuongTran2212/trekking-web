# post/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Q  # <-- Cần import thêm để tính toán
from django.core.paginator import Paginator # <-- Import phân trang

# Import model
from community.models import CongDongBaiViet as Post

@staff_member_required
def post_list_view(request):
    """
    Hiển thị danh sách bài viết quản trị với thống kê và phân trang.
    """
    # 1. Lấy QuerySet cơ bản (chưa lọc)
    base_qs = Post.objects.select_related('tac_gia').all().order_by('-ngay_dang')

    # 2. TÍNH TOÁN THỐNG KÊ (Đây là phần bạn đang thiếu)
    # Dùng aggregate để đếm trực tiếp từ DB, nhanh hơn loop
    stats = base_qs.aggregate(
        total=Count('id'),
        pending=Count('id', filter=Q(trang_thai='cho_duyet')), # Kiểm tra lại value trong model nếu khác
        approved=Count('id', filter=Q(trang_thai='da_duyet')),
        rejected=Count('id', filter=Q(trang_thai='tu_choi'))
    )

    # 3. Xử lý Lọc & Tìm kiếm cho danh sách hiển thị
    status_filter = request.GET.get('status')
    search_query = request.GET.get('q', '')
    
    display_list = base_qs # Tạo biến mới để filter hiển thị

    # Lọc theo tab trạng thái
    if status_filter in ['cho_duyet', 'da_duyet', 'tu_choi']:
        display_list = display_list.filter(trang_thai=status_filter)

    # Lọc theo từ khóa tìm kiếm
    if search_query:
        display_list = display_list.filter(
            Q(tieu_de__icontains=search_query) | 
            Q(tac_gia__username__icontains=search_query)
        )

    # 4. Phân trang (20 bài/trang)
    paginator = Paginator(display_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'posts': page_obj,         # Danh sách đã phân trang
        'page_obj': page_obj,      # Đối tượng phân trang
        'status_filter': status_filter,
        'search_query': search_query,
        'title': 'Quản lý Bài viết Cộng đồng',
        
        # Truyền dữ liệu thống kê vào Template
        'total_posts': stats['total'],
        'pending_count': stats['pending'],
        'approved_count': stats['approved'],
        'rejected_count': stats['rejected'],
    }
    return render(request, 'post/admin_post_list.html', context)

@staff_member_required
def post_update_status_view(request, post_id, status):
    """Cập nhật trạng thái bài viết"""
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        # Lưu ý: Đảm bảo Post.TrangThaiBaiViet.values trả về đúng list string
        # Nếu model dùng TextChoices, cách này ổn.
        valid_statuses = Post.TrangThaiBaiViet.values 
        
        if status in valid_statuses:
            post.trang_thai = status
            post.save()
            
            if status == 'da_duyet': # Hoặc Post.TrangThaiBaiViet.DA_DUYET
                messages.success(request, f'Đã duyệt: "{post.tieu_de}"')
            elif status == 'tu_choi':
                messages.warning(request, f'Đã từ chối: "{post.tieu_de}"')
        else:
            messages.error(request, 'Trạng thái không hợp lệ.')
            
    return redirect('post_admin:post_list')

@staff_member_required
def post_delete_view(request, post_id):
    """Xóa bài viết"""
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        title = post.tieu_de
        post.delete()
        messages.error(request, f'Đã xóa vĩnh viễn: "{title}"')
    return redirect('post_admin:post_list')

@staff_member_required
def post_detail_view(request, post_id):
    """Xem chi tiết"""
    post = get_object_or_404(
        Post.objects.prefetch_related('media', 'binh_luan__user'),
        id=post_id
    )
    context = {
        'post': post,
        'title': f'Chi tiết: {post.tieu_de}'
    }
    return render(request, 'post/admin_post_detail.html', context)