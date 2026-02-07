from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def check_trip_access(context, trip):
    request = context.get('request')
    user = request.user if request else None

    # 1. Công khai -> Luôn cho phép
    if trip.che_do_rieng_tu == 'CONG_KHAI':
        return True

    # 2. Chưa đăng nhập -> Chặn (nếu là riêng tư)
    if not user or not user.is_authenticated:
        return False

    # 3. Là người tổ chức -> Cho phép
    if trip.nguoi_to_chuc == user:
        return True

    # 4. Đã tham gia (Dựa vào annotate user_status từ view)
    # Lưu ý: user_status được thêm vào từ annotate trong TripHubView
    if getattr(trip, 'user_status', '') == 'DA_THAM_GIA':
        return True
        
    # 5. Kiểm tra Session (Nếu vừa nhập mã đúng)
    if request.session.get(f'access_granted_{trip.pk}', False):
        return True

    return False