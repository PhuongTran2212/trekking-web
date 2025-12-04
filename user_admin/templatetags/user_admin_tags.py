from django import template

register = template.Library()

@register.filter
def has_profile(user):
    try:
        return hasattr(user, 'taikhoanhoso')
    except Exception:
        return False
