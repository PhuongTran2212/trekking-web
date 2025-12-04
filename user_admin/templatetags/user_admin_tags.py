from django import template

register = template.Library()

@register.filter
def has_profile(user):
    try:
        return hasattr(user, 'taikhoanhoso')
    except Exception:
        return False

from django.utils import timezone
import datetime

@register.filter
def time_ago_vi(value):
    """
    Chuyển đổi thời gian sang định dạng tiếng Việt "cách đây..."
    """
    if not value:
        return ""
        
    now = timezone.now()
    try:
        diff = now - value
    except:
        return value

    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "Vừa xong"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} phút trước"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} giờ trước"
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f"{days} ngày trước"
    else:
        return value.strftime("%d/%m/%Y")
