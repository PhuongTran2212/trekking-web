# report_admin/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

# === SỬA DÒNG IMPORT NÀY ===
from core.models import HeThongBaoCao, HeThongThongBao
from community.models import CongDongBaiViet

@staff_member_required
def report_list_view(request):
    status_filter = request.GET.get('status')
    report_list = HeThongBaoCao.objects.select_related('nguoi_bao_cao').order_by('-ngay_bao_cao')

    if status_filter in ['Mới', 'Đang xử lý', 'Đã xử lý']:
        report_list = report_list.filter(trang_thai=status_filter)
        
    context = {
        'reports': report_list,
        'status_filter': status_filter,
        'title': 'Quản lý Báo cáo'
    }
    return render(request, 'report/admin_report_list.html', context)


@staff_member_required
def report_detail_view(request, report_id):
    report = get_object_or_404(HeThongBaoCao, id=report_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('ghi_chu_xu_ly', '')
        post = report.content_object 

        report.ghi_chu_xu_ly = notes
        report.nguoi_xu_ly = request.user
        report.trang_thai = HeThongBaoCao.TrangThaiBaoCao.DA_XU_LY

        if action == 'dismiss':
            report.save()
            messages.success(request, f"Đã xử lý báo cáo #{report.id}. Bài viết được xác định không vi phạm.")
        
        elif post:
            if action == 'hide_and_warn':
                post.trang_thai = CongDongBaiViet.TrangThaiBaiViet.TU_CHOI
                post.save()
                HeThongThongBao.objects.create(
                    nguoi_nhan=post.tac_gia,
                    tieu_de="Bài viết của bạn cần chỉnh sửa",
                    noi_dung=f"Bài viết '{post.tieu_de}' của bạn đã bị tạm ẩn do vi phạm nhẹ quy định. Vui lòng vào chỉnh sửa lại.",
                    lien_ket=post.get_edit_url()
                )
                report.save()
                messages.warning(request, f"Đã xử lý báo cáo #{report.id}. Bài viết đã được tạm ẩn và gửi yêu cầu chỉnh sửa.")

            elif action == 'delete_and_warn':
                post_author = post.tac_gia
                post_title = post.tieu_de
                post.delete()
                HeThongThongBao.objects.create(
                    nguoi_nhan=post_author,
                    tieu_de="Bài viết của bạn đã bị xóa",
                    noi_dung=f"Bài viết '{post_title}' của bạn đã bị xóa do vi phạm nghiêm trọng quy định cộng đồng."
                )
                report.save()
                messages.error(request, f"Đã xử lý báo cáo #{report.id}. Bài viết đã bị xóa vĩnh viễn.")
            else:
                 messages.error(request, "Hành động không hợp lệ. Vui lòng thử lại.")
                 context = {'report': report, 'title': 'Chi tiết Báo cáo'}
                 return render(request, 'report/admin_report_detail.html', context)
        else:
            report.save()
            messages.info(request, f"Đã xử lý báo cáo #{report.id}. Đối tượng bị báo cáo đã không còn tồn tại.")

        return redirect('report_admin:report_list')

    context = {
        'report': report,
        'title': 'Chi tiết Báo cáo'
    }
    return render(request, 'report/admin_report_detail.html', context)