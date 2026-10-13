import json
from django.test import TestCase, Client
from django.conf import settings
from quiz.models import Question
from quiz.auth_utils import create_admin_token, _LOGIN_ATTEMPTS


class QuizAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Test savollarini yaratish
        self.q1 = Question.objects.create(
            question="Oʻzbekiston Respublikasi mustaqillikka qachon erishgan?",
            option_a="1990-yil 1-sentyabr",
            option_b="1991-yil 1-sentyabr",
            option_c="1992-yil 8-dekabr",
            option_d="1993-yil 2-iyul",
            correct=1
        )
        self.q2 = Question.objects.create(
            question="Python dasturlash tilining asoschisi kim?",
            option_a="Gvido van Rossum",
            option_b="Brendan Eich",
            option_c="Jeyms Gosling",
            option_d="Bjarne Stroustrup",
            correct=0
        )
        _LOGIN_ATTEMPTS.clear()

    def test_pages_render(self):
        """Bosh sahifa va Admin sahifasi 200 qaytarishi kerak"""
        res_index = self.client.get('/')
        self.assertEqual(res_index.status_code, 200)

        res_admin = self.client.get('/admin/')
        self.assertEqual(res_admin.status_code, 200)

    def test_stats_api(self):
        """Stats API bazadagi jami savollar sonini to'g'ri qaytarishi kerak"""
        res = self.client.get('/api/stats/')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['total'], 2)

    def test_quiz_api_hides_correct_answers(self):
        """MUHIM: /api/quiz javobida 'correct' maydoni BO'LMASLIGI kerak"""
        res = self.client.get('/api/quiz/?count=2')
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['questions']), 2)
        
        for q in data['questions']:
            self.assertIn('id', q)
            self.assertIn('question', q)
            self.assertIn('options', q)
            self.assertEqual(len(q['options']), 4)
            # Brauzerda to'g'ri javobni ko'rib bo'lmasligi kerak!
            self.assertNotIn('correct', q)
            self.assertNotIn('correct_answer', q)

    def test_check_answer_api(self):
        """Javobni serverda tekshirish"""
        # To'g'ri javob tekshiruvi (q1 uchun 1 = B)
        res_correct = self.client.post(
            '/api/answer/',
            data=json.dumps({'questionId': self.q1.id, 'choice': 1}),
            content_type='application/json'
        )
        self.assertEqual(res_correct.status_code, 200)
        data_correct = res_correct.json()
        self.assertTrue(data_correct['isCorrect'])
        self.assertEqual(data_correct['correct'], 1)

        # Noto'g'ri javob tekshiruvi (q1 uchun 0 = A)
        res_wrong = self.client.post(
            '/api/answer/',
            data=json.dumps({'questionId': self.q1.id, 'choice': 0}),
            content_type='application/json'
        )
        self.assertEqual(res_wrong.status_code, 200)
        data_wrong = res_wrong.json()
        self.assertFalse(data_wrong['isCorrect'])
        self.assertEqual(data_wrong['correct'], 1)
        self.assertEqual(data_wrong['correctOptionText'], "1991-yil 1-sentyabr")

    def test_admin_auth_and_rate_limiting(self):
        """Admin login, rate limiting va JWT tekshiruvi"""
        admin_pass = getattr(settings, 'ADMIN_PASSWORD', 'admin123')

        # Noto'g'ri parol
        res_fail = self.client.post(
            '/api/admin/login/',
            data=json.dumps({'password': 'notogri_parol'}),
            content_type='application/json'
        )
        self.assertEqual(res_fail.status_code, 401)
        self.assertFalse(res_fail.json()['success'])

        # 4 marta yana noto'g'ri kiritish (jami 5 ta muvaffaqiyatsiz urinish)
        for _ in range(4):
            self.client.post(
                '/api/admin/login/',
                data=json.dumps({'password': 'notogri_parol'}),
                content_type='application/json'
            )

        # 6-urinishda Rate Limit (429) bo'lishi kerak
        res_limited = self.client.post(
            '/api/admin/login/',
            data=json.dumps({'password': admin_pass}),
            content_type='application/json'
        )
        self.assertEqual(res_limited.status_code, 429)
        self.assertIn("me'yordan oshdi", res_limited.json()['error'])

        # Keshni tozalab, to'g'ri parol bilan kirish
        _LOGIN_ATTEMPTS.clear()
        res_ok = self.client.post(
            '/api/admin/login/',
            data=json.dumps({'password': admin_pass}),
            content_type='application/json'
        )
        self.assertEqual(res_ok.status_code, 200)
        self.assertIn('admin_session', res_ok.cookies)

    def test_admin_crud_operations(self):
        """Admin CRUD amallari himoyalangan va to'g'ri ishlashi kerak"""
        # Sessiyasiz murojaat qilsa 401 qaytishi kerak
        res_unauth = self.client.get('/api/admin/questions/')
        self.assertEqual(res_unauth.status_code, 401)

        # Sessiya o'rnatish
        token = create_admin_token()
        self.client.cookies['admin_session'] = token

        # Savollar ro'yxatini olish
        res_list = self.client.get('/api/admin/questions/')
        self.assertEqual(res_list.status_code, 200)
        self.assertEqual(res_list.json()['total'], 2)

        # Yangi savol qo'shish
        new_q_data = {
            'question': 'Dunyodagi eng katta okean qaysi?',
            'option_a': 'Atlantika',
            'option_b': 'Hind',
            'option_c': 'Shimoliy',
            'option_d': 'Tinch',
            'correct': 3
        }
        res_create = self.client.post(
            '/api/admin/questions/create/',
            data=json.dumps(new_q_data),
            content_type='application/json'
        )
        self.assertEqual(res_create.status_code, 201)
        created_id = res_create.json()['question']['id']

        # Savolni tahrirlash (PUT)
        update_data = {
            'question': 'Dunyodagi eng katta va chuqur okean qaysi?',
            'option_a': 'Atlantika',
            'option_b': 'Hind',
            'option_c': 'Shimoliy Muz',
            'option_d': 'Tinch okeani',
            'correct': 3
        }
        res_update = self.client.put(
            f'/api/admin/questions/{created_id}/',
            data=json.dumps(update_data),
            content_type='application/json'
        )
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.json()['question']['question'], 'Dunyodagi eng katta va chuqur okean qaysi?')

        # Savolni o'chirish (DELETE)
        res_delete = self.client.delete(f'/api/admin/questions/{created_id}/')
        self.assertEqual(res_delete.status_code, 200)
        self.assertFalse(Question.objects.filter(id=created_id).exists())

    def test_admin_import_export_delete_all(self):
        """JSON import, eksport va barchasini tozalash amallari"""
        token = create_admin_token()
        self.client.cookies['admin_session'] = token

        # Eksport tekshiruvi
        res_export = self.client.get('/api/admin/questions/export/')
        self.assertEqual(res_export.status_code, 200)
        exported = res_export.json()
        self.assertEqual(len(exported), 2)
        self.assertIn('q', exported[0])
        self.assertIn('o', exported[0])
        self.assertIn('a', exported[0])

        # Import tekshiruvi
        import_data = [
            {"q": "Yangi test savoli 1", "o": ["A1", "B1", "C1", "D1"], "a": 0},
            {"q": "Yangi test savoli 2", "o": ["A2", "B2", "C2", "D2"], "a": 2}
        ]
        res_import = self.client.post(
            '/api/admin/questions/import/',
            data=json.dumps(import_data),
            content_type='application/json'
        )
        self.assertEqual(res_import.status_code, 200)
        self.assertEqual(res_import.json()['importedCount'], 2)
        self.assertEqual(Question.objects.count(), 4)

        # Hammasini o'chirish tekshiruvi
        res_del_all = self.client.delete(
            '/api/admin/questions/all/',
            data=json.dumps({'confirm': 'HA_OCHIRISH'}),
            content_type='application/json'
        )
        self.assertEqual(res_del_all.status_code, 200)
        self.assertEqual(Question.objects.count(), 0)
