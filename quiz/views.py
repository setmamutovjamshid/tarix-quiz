import json
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import transaction
from django.db.models import Q
from django.conf import settings
from django.core.paginator import Paginator

from .models import Question
from .auth_utils import (
    get_client_ip,
    check_rate_limit,
    record_failed_attempt,
    reset_attempts,
    create_admin_token,
    admin_api_required,
    is_admin_authenticated
)


# ==========================================
# SAHIFA KO'RINISHALARI (HTML Views)
# ==========================================

def index_view(request):
    """Bosh sahifa: Test topshirish interfeysi (foydalanuvchi qismi)"""
    return render(request, 'quiz/index.html')


def admin_view(request):
    """Admin sahifasi: kirish yoki boshqaruv paneli"""
    return render(request, 'quiz/admin.html')


# ==========================================
# FOYDALANUVCHI API (Ommaviy)
# ==========================================

@require_http_methods(["GET"])
def stats_api(request):
    """Bazadagi jami savollar sonini qaytaradi"""
    total = Question.objects.count()
    return JsonResponse({
        'success': True,
        'total': total
    })


@require_http_methods(["GET"])
def quiz_questions_api(request):
    """
    Tasodifiy savollarni qaytaradi.
    MUHIM: to'g'ri javob (correct) maydoni foydalanuvchiga YUBORILMAYDI!
    """
    import random

    try:
        count = int(request.GET.get('count', 20))
    except (ValueError, TypeError):
        count = 20

    if count < 1:
        count = 1

    all_ids = list(Question.objects.values_list('id', flat=True))
    total_in_db = len(all_ids)

    if not all_ids:
        return JsonResponse({
            'success': True,
            'count': 0,
            'questions': []
        })

    if count > total_in_db:
        count = total_in_db

    selected_ids = random.sample(all_ids, count)

    # Faqat kerakli maydonlarni tezkor olish (to'g'ri javobsiz)
    questions_qs = Question.objects.filter(id__in=selected_ids).only(
        'id', 'question', 'option_a', 'option_b', 'option_c', 'option_d'
    )
    questions_map = {q.id: q for q in questions_qs}
    questions_data = [
        questions_map[qid].to_public_dict()
        for qid in selected_ids
        if qid in questions_map
    ]

    return JsonResponse({
        'success': True,
        'count': len(questions_data),
        'questions': questions_data
    })


@csrf_exempt
@require_http_methods(["POST"])
def check_answer_api(request):
    """
    Foydalanuvchi tanlagan javobni tekshiradi.
    Kutiladi: { "questionId": 12, "choice": 0..3 }
    Qaytaradi: { "isCorrect": bool, "correct": int, "correctOption": str }
    """
    try:
        body = json.loads(request.body.decode('utf-8'))
        question_id = int(body.get('questionId'))
        choice = int(body.get('choice'))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({
            'success': False,
            'error': "Noto'g'ri so'rov ma'lumotlari kiritildi."
        }, status=400)

    if choice not in [0, 1, 2, 3]:
        return JsonResponse({
            'success': False,
            'error': "Variant 0 dan 3 gacha bo'lishi kerak."
        }, status=400)

    try:
        question = Question.objects.only(
            'correct', 'option_a', 'option_b', 'option_c', 'option_d'
        ).get(id=question_id)
    except Question.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': "Bunday ID'li savol topilmadi."
        }, status=404)

    is_correct = (question.correct == choice)
    options = [question.option_a, question.option_b, question.option_c, question.option_d]
    correct_text = options[question.correct]

    return JsonResponse({
        'success': True,
        'isCorrect': is_correct,
        'correct': question.correct,
        'correctOptionText': correct_text
    })


# ==========================================
# ADMIN AUTH API
# ==========================================

@csrf_exempt
@require_http_methods(["POST"])
def admin_login_api(request):
    """
    Admin tizimiga kirish.
    Rate limiting (brute-force himoyasi) va JWT cookie o'rnatish.
    """
    ip = get_client_ip(request)
    allowed, wait_seconds = check_rate_limit(ip)
    if not allowed:
        return JsonResponse({
            'success': False,
            'error': f"Login urinishlari me'yordan oshdi. Iltimos, {wait_seconds} soniyadan so'ng qayta urinib ko'ring."
        }, status=429)

    try:
        body = json.loads(request.body.decode('utf-8'))
        password = body.get('password', '')
    except Exception:
        password = ''

    admin_pass = getattr(settings, 'ADMIN_PASSWORD', 'admin123')

    if password == admin_pass:
        reset_attempts(ip)
        token = create_admin_token()
        response = JsonResponse({
            'success': True,
            'message': "Admin tizimiga muvaffaqiyatli kirildi."
        })
        # Imzolangan, httpOnly cookie o'rnatish
        response.set_cookie(
            key='admin_session',
            value=token,
            max_age=7 * 24 * 3600,
            httponly=True,
            samesite='Lax',
            secure=not settings.DEBUG
        )
        return response
    else:
        record_failed_attempt(ip)
        return JsonResponse({
            'success': False,
            'error': "Maxfiy parol noto'g'ri. Qayta urinib ko'ring."
        }, status=401)


@csrf_exempt
@require_http_methods(["POST"])
def admin_logout_api(request):
    """Admin sessiyasini tugatish va cookie'ni o'chirish"""
    response = JsonResponse({
        'success': True,
        'message': "Tizimdan muvaffaqiyatli chiqildi."
    })
    response.delete_cookie('admin_session')
    return response


@require_http_methods(["GET"])
def admin_me_api(request):
    """Admin sessiyasi faolligini tekshirish"""
    authenticated = is_admin_authenticated(request)
    return JsonResponse({
        'authenticated': authenticated
    })


# ==========================================
# ADMIN CRUD & BOSHQARUV API (Himoyalangan)
# ==========================================

@require_http_methods(["GET"])
@admin_api_required
def admin_questions_list_api(request):
    """
    Savollar ro'yxatini sahifalab (50 tadan) va qidiruv bilan qaytarish.
    Parametrlar: page=1, limit=50, search=""
    """
    try:
        page_num = int(request.GET.get('page', 1))
    except (ValueError, TypeError):
        page_num = 1
    try:
        limit = min(max(int(request.GET.get('limit', 50)), 1), 100)
    except (ValueError, TypeError):
        limit = 50
    search = request.GET.get('search', '').strip()

    qs = Question.objects.all()

    if search:
        qs = qs.filter(
            Q(question__icontains=search) |
            Q(option_a__icontains=search) |
            Q(option_b__icontains=search) |
            Q(option_c__icontains=search) |
            Q(option_d__icontains=search)
        )

    qs = qs.order_by('id')
    paginator = Paginator(qs, limit)
    page_obj = paginator.get_page(page_num)

    start_number = (page_obj.number - 1) * limit
    questions_data = []
    for idx, q in enumerate(page_obj, start=start_number + 1):
        item = q.to_admin_dict()
        item['order_number'] = idx
        questions_data.append(item)

    return JsonResponse({
        'success': True,
        'questions': questions_data,
        'total': paginator.count,
        'page': page_obj.number,
        'totalPages': paginator.num_pages,
        'hasNext': page_obj.has_next(),
        'hasPrev': page_obj.has_previous()
    })


@csrf_exempt
@require_http_methods(["POST"])
@admin_api_required
def admin_question_create_api(request):
    """Yangi savol qo'shish"""
    try:
        data = json.loads(request.body.decode('utf-8'))
        question_text = data.get('question', '').strip()
        option_a = data.get('option_a', '').strip()
        option_b = data.get('option_b', '').strip()
        option_c = data.get('option_c', '').strip()
        option_d = data.get('option_d', '').strip()
        correct = int(data.get('correct', -1))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({
            'success': False,
            'error': "Noto'g'ri ma'lumot formati."
        }, status=400)

    if not (question_text and option_a and option_b and option_c and option_d):
        return JsonResponse({
            'success': False,
            'error': "Savol matni va barcha 4 ta variant to'ldirilishi shart."
        }, status=400)

    if correct not in [0, 1, 2, 3]:
        return JsonResponse({
            'success': False,
            'error': "To'g'ri javob indeksi 0 (A), 1 (B), 2 (C) yoki 3 (D) bo'lishi kerak."
        }, status=400)

    question = Question.objects.create(
        question=question_text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct=correct
    )

    return JsonResponse({
        'success': True,
        'message': "Savol muvaffaqiyatli qo'shildi.",
        'question': question.to_admin_dict()
    }, status=201)


@csrf_exempt
@require_http_methods(["PUT", "DELETE"])
@admin_api_required
def admin_question_detail_api(request, question_id):
    """Savolni tahrirlash (PUT) yoki o'chirish (DELETE)"""
    try:
        question = Question.objects.get(id=question_id)
    except Question.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': "Savol topilmadi."
        }, status=404)

    if request.method == "DELETE":
        question.delete()
        return JsonResponse({
            'success': True,
            'message': f"#{question_id} raqamli savol o'chirildi."
        })

    elif request.method == "PUT":
        try:
            data = json.loads(request.body.decode('utf-8'))
            question_text = data.get('question', '').strip()
            option_a = data.get('option_a', '').strip()
            option_b = data.get('option_b', '').strip()
            option_c = data.get('option_c', '').strip()
            option_d = data.get('option_d', '').strip()
            correct = int(data.get('correct', -1))
        except (ValueError, TypeError, json.JSONDecodeError):
            return JsonResponse({
                'success': False,
                'error': "Noto'g'ri ma'lumot formati."
            }, status=400)

        if not (question_text and option_a and option_b and option_c and option_d):
            return JsonResponse({
                'success': False,
                'error': "Barcha maydonlar to'ldirilishi shart."
            }, status=400)

        if correct not in [0, 1, 2, 3]:
            return JsonResponse({
                'success': False,
                'error': "To'g'ri javob indeksi 0 dan 3 gacha bo'lishi kerak."
            }, status=400)

        question.question = question_text
        question.option_a = option_a
        question.option_b = option_b
        question.option_c = option_c
        question.option_d = option_d
        question.correct = correct
        question.save()

        return JsonResponse({
            'success': True,
            'message': "Savol muvaffaqiyatli yangilandi.",
            'question': question.to_admin_dict()
        })


@csrf_exempt
@require_http_methods(["POST"])
@admin_api_required
def admin_questions_import_api(request):
    """
    JSON formatidagi savollarni ommaviy import qilish.
    Format: [{"q":"Savol matni","o":["A","B","C","D"],"a":1}]
    """
    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return JsonResponse({
            'success': False,
            'error': "Yaroqsiz JSON fayl yoki ma'lumot formati."
        }, status=400)

    if not isinstance(data, list):
        return JsonResponse({
            'success': False,
            'error': "JSON ro'yxat (array) ko'rinishida bo'lishi kerak."
        }, status=400)

    if len(data) == 0:
        return JsonResponse({
            'success': False,
            'error': "Import uchun hech qanday savol berilmadi."
        }, status=400)

    new_questions = []
    errors = []

    for idx, item in enumerate(data, start=1):
        if not isinstance(item, dict):
            errors.append(f"{idx}-savol: Obyekt bo'lishi kerak.")
            continue

        q_text = str(item.get('q', '')).strip()
        options = item.get('o', [])
        correct = item.get('a')

        if not q_text:
            errors.append(f"{idx}-savol: 'q' (savol matni) bo'sh bo'lmasligi kerak.")
            continue

        if not isinstance(options, list) or len(options) != 4:
            errors.append(f"{idx}-savol: 'o' ro'yxatida aniq 4 ta variant bo'lishi kerak.")
            continue

        if not all(str(opt).strip() for opt in options):
            errors.append(f"{idx}-savol: Variantlardan biri bo'sh.")
            continue

        try:
            correct_int = int(correct)
            if correct_int not in [0, 1, 2, 3]:
                errors.append(f"{idx}-savol: 'a' 0 va 3 orasida bo'lishi kerak.")
                continue
        except (ValueError, TypeError):
            errors.append(f"{idx}-savol: 'a' butun son bo'lishi kerak (0 dan 3 gacha).")
            continue

        new_questions.append(Question(
            question=q_text,
            option_a=str(options[0]).strip(),
            option_b=str(options[1]).strip(),
            option_c=str(options[2]).strip(),
            option_d=str(options[3]).strip(),
            correct=correct_int
        ))

    if errors:
        return JsonResponse({
            'success': False,
            'error': "Ma'lumotlarda xatoliklar aniqlandi (import qilinmadi):",
            'details': errors[:10]  # Birinchi 10 ta xatolikni ko'rsatish
        }, status=400)

    # Tezkor ommaviy qo'shish (bulk_create) tranzaksiya bilan
    with transaction.atomic():
        Question.objects.bulk_create(new_questions, batch_size=500)

    return JsonResponse({
        'success': True,
        'message': f"{len(new_questions)} ta savol muvaffaqiyatli bazaga qo'shildi.",
        'importedCount': len(new_questions)
    })


@require_http_methods(["GET"])
@admin_api_required
def admin_questions_export_api(request):
    """
    Barcha savollarni belgilangan formatda eksport qilish:
    [{"q":"Savol","o":["A","B","C","D"],"a":1}]
    """
    questions = Question.objects.all().order_by('id')
    export_data = [q.to_export_dict() for q in questions]

    json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
    response = HttpResponse(json_str, content_type='application/json; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="savollar_export.json"'
    return response


@csrf_exempt
@require_http_methods(["DELETE"])
@admin_api_required
def admin_questions_delete_all_api(request):
    """
    Barcha savollarni tozalash (Tasdiqlash bilan).
    Kutiladi: { "confirm": "HA_OCHIRISH" }
    """
    try:
        body = json.loads(request.body.decode('utf-8'))
        confirm = body.get('confirm')
    except Exception:
        confirm = ''

    if confirm != "HA_OCHIRISH":
        return JsonResponse({
            'success': False,
            'error': "Barcha savollarni o'chirish uchun 'HA_OCHIRISH' tasdig'ini yuborishingiz kerak."
        }, status=400)

    count = Question.objects.count()
    Question.objects.all().delete()

    return JsonResponse({
        'success': True,
        'message': f"Barcha {count} ta savol muvaffaqiyatli o'chirildi.",
        'deletedCount': count
    })
