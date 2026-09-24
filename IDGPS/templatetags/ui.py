from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def nav_active(context, prefix):
    """Sidebar havolasi joriy bo'limga tegishli bo'lsa 'is-active' qaytaradi."""
    request = context.get('request')
    if request and request.path.startswith(prefix):
        return 'is-active'
    return ''


@register.filter
def display_name(user):
    """Foydalanuvchining to'liq ismi (CustomUser.firstname ishlatiladi), bo'lmasa username."""
    if not user:
        return ''
    first = getattr(user, 'firstname', '') or getattr(user, 'first_name', '')
    full = f"{first} {getattr(user, 'last_name', '')}".strip()
    return full or user.username


@register.filter
def initials(user):
    name = display_name(user)
    parts = [p for p in name.split() if p]
    if not parts:
        return '?'
    if len(parts) == 1:
        return parts[0][:2]
    return parts[0][0] + parts[1][0]


@register.filter
def som(value):
    """1234567 -> '1 234 567' (so'm uchun, probel bilan ajratilgan)."""
    try:
        number = int(round(float(value or 0)))
    except (TypeError, ValueError):
        return value
    sign = '-' if number < 0 else ''
    return sign + f'{abs(number):,}'.replace(',', ' ')


@register.filter
def percent(part, whole):
    try:
        whole = float(whole)
        return round(float(part) * 100 / whole) if whole else 0
    except (TypeError, ValueError):
        return 0


@register.filter
def get_field(form, name):
    """Shablonda formadagi maydonni nomi bo'yicha olish: form|get_field:'mijoz'."""
    return form[name]
