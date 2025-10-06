# cSpell:disable

from django.urls import path
from . import views

app_name = 'community'

urlpatterns = [
    # Danh sách bài viết
    path('', views.danh_sach_bai_viet, name='danh-sach-bai-viet'),
    
    # Chi tiết bài viết
    path('bai-viet/<int:bai_viet_id>/', views.chi_tiet_bai_viet, name='chi-tiet-bai-viet'),
    
    # Tạo, sửa, xóa bài viết
    path('tao-bai-viet/', views.tao_bai_viet, name='tao-bai-viet'),
    path('sua-bai-viet/<int:bai_viet_id>/', views.sua_bai_viet, name='sua-bai-viet'),
    path('xoa-bai-viet/<int:bai_viet_id>/', views.xoa_bai_viet, name='xoa-bai-viet'),
    
    # Bài viết của tôi
    path('bai-viet-cua-toi/', views.bai_viet_cua_toi, name='bai-viet-cua-toi'),
    
    # Upvote (AJAX)
    path('upvote/<int:bai_viet_id>/', views.toggle_upvote, name='toggle-upvote'),
    
    # Xóa media (AJAX)
    path('xoa-media/<int:media_id>/', views.xoa_media, name='xoa-media'),
    
    # Xóa bình luận
    path('xoa-binh-luan/<int:binh_luan_id>/', views.xoa_binh_luan, name='xoa-binh-luan'),
]
