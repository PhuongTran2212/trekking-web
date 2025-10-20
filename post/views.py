# post/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

# Import model CongDongBaiViet từ app 'community' và đổi tên thành 'Post' để tiện sử dụng
from community.models import CongDongBaiViet as Post

@staff_member_required
def post_list_view(request):
    """
    Hiển thị danh sách bài viết để admin quản lý, có chức năng lọc theo trạng thái.
    """
    status_filter = request.GET.get('status')
    
    # Lấy tất cả bài viết và thông tin tác giả liên quan
    post_list = Post.objects.select_related('tac_gia').all().order_by('-ngay_dang')

    # Lọc danh sách dựa trên query parameter 'status' từ URL
    if status_filter in ['cho_duyet', 'da_duyet', 'tu_choi']:
        post_list = post_list.filter(trang_thai=status_filter)

    context = {
        'posts': post_list,
        'status_filter': status_filter,
        'title': 'Quản lý Bài viết'
    }
    return render(request, 'post/admin_post_list.html', context)

@staff_member_required
def post_update_status_view(request, post_id, status):
    """
    View chung để cập nhật trạng thái của bài viết (Duyệt hoặc Từ chối).
    Chỉ chấp nhận phương thức POST để đảm bảo an toàn.
    """
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        
        # Lấy các lựa chọn trạng thái hợp lệ từ model
        valid_statuses = Post.TrangThaiBaiViet.values
        
        if status in valid_statuses:
            post.trang_thai = status
            post.save()
            
            # Hiển thị thông báo tương ứng
            if status == Post.TrangThaiBaiViet.DA_DUYET:
                messages.success(request, f'Đã duyệt thành công bài viết "{post.tieu_de}".')
            elif status == Post.TrangThaiBaiViet.TU_CHOI:
                messages.warning(request, f'Đã từ chối bài viết "{post.tieu_de}".')
        else:
            messages.error(request, 'Trạng thái cập nhật không hợp lệ.')
            
    # Sau khi xử lý, chuyển hướng về trang danh sách
    return redirect('post_admin:post_list')

@staff_member_required
def post_delete_view(request, post_id):
    """
    Xử lý hành động XÓA một bài viết.
    Chỉ chấp nhận phương thức POST.
    """
    if request.method == 'POST':
        post = get_object_or_404(Post, id=post_id)
        post_title = post.tieu_de # Lưu lại tiêu đề để hiển thị thông báo
        post.delete()
        messages.error(request, f'Đã xóa vĩnh viễn bài viết "{post_title}".')
    return redirect('post_admin:post_list')

@staff_member_required
def post_detail_view(request, post_id):
    """
    Hiển thị chi tiết một bài viết cho admin.
    """
    # Lấy bài viết và các dữ liệu liên quan một cách hiệu quả
    post = get_object_or_404(
        Post.objects.prefetch_related('media', 'tags', 'binh_luan__user'),
        id=post_id
    )
    
    context = {
        'post': post,
        'title': 'Chi tiết Bài viết'
    }
    return render(request, 'post/admin_post_detail.html', context)