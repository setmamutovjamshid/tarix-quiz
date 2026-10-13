import time
import functools
import jwt
from django.conf import settings
from django.http import JsonResponse

# Login urinishlarini kuzatish uchun xotira kesh (In-memory Rate Limiter)
# { ip_address: [timestamp, timestamp, ...] }
_LOGIN_ATTEMPTS = {}
MAX_ATTEMPTS = 5
LOCKOUT_SECONDS = 600  # 10 daqiqa


def get_client_ip(request):
    """Mijozning haqiqiy IP manzilini aniqlash"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


def check_rate_limit(ip):
    """
    IP bo'yicha login urinishlarini tekshirish.
    Qaytaradi: (is_allowed: bool, wait_seconds: int)
    """
    now = time.time()
    attempts = _LOGIN_ATTEMPTS.get(ip, [])
    # 10 daqiqadan eski urinishlarni tozalash
    valid_attempts = [t for t in attempts if now - t < LOCKOUT_SECONDS]
    _LOGIN_ATTEMPTS[ip] = valid_attempts

    if len(valid_attempts) >= MAX_ATTEMPTS:
        oldest = valid_attempts[0]
        wait_seconds = int(LOCKOUT_SECONDS - (now - oldest))
        return False, max(1, wait_seconds)

    return True, 0


def record_failed_attempt(ip):
    """Muvaffaqiyatsiz login urinishini qayd etish"""
    now = time.time()
    attempts = _LOGIN_ATTEMPTS.get(ip, [])
    attempts.append(now)
    _LOGIN_ATTEMPTS[ip] = attempts


def reset_attempts(ip):
    """Muvaffaqiyatli kirgach urinishlar tarixini tozalash"""
    if ip in _LOGIN_ATTEMPTS:
        del _LOGIN_ATTEMPTS[ip]


def create_admin_token():
    """Admin uchun imzolangan JWT token yaratish (7 kun amal qiladi)"""
    payload = {
        'role': 'admin',
        'iat': int(time.time()),
        'exp': int(time.time()) + (7 * 24 * 3600)  # 7 kun
    }
    token = jwt.encode(payload, settings.SESSION_SECRET, algorithm='HS256')
    return token


def verify_admin_token(token):
    """JWT tokenni tekshirish"""
    if not token:
        return False
    try:
        payload = jwt.decode(token, settings.SESSION_SECRET, algorithms=['HS256'])
        return payload.get('role') == 'admin'
    except Exception:
        return False


def is_admin_authenticated(request):
    """So'rovda yaroqli admin cookie borligini tekshirish"""
    token = request.COOKIES.get('admin_session')
    return verify_admin_token(token)


def admin_api_required(view_func):
    """Admin API endpointlari uchun himoya dekoratori"""
    @functools.wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_admin_authenticated(request):
            return JsonResponse({
                'success': False,
                'error': "Ruxsat berilmagan. Iltimos, admin sifatida tizimga kiring."
            }, status=401)
        return view_func(request, *args, **kwargs)
    return _wrapped_view
