from django.urls import path, re_path
from . import views

urlpatterns = [
    # Sahifalar
    path('', views.index_view, name='index'),
    re_path(r'^admin/?$', views.admin_view, name='admin_panel'),

    # Ommaviy API
    re_path(r'^api/stats/?$', views.stats_api, name='api_stats'),
    re_path(r'^api/quiz/?$', views.quiz_questions_api, name='api_quiz'),
    re_path(r'^api/answer/?$', views.check_answer_api, name='api_answer'),

    # Admin Auth API
    re_path(r'^api/admin/login/?$', views.admin_login_api, name='api_admin_login'),
    re_path(r'^api/admin/logout/?$', views.admin_logout_api, name='api_admin_logout'),
    re_path(r'^api/admin/me/?$', views.admin_me_api, name='api_admin_me'),

    # Admin Boshqaruv API
    re_path(r'^api/admin/questions/?$', views.admin_questions_list_api, name='api_admin_questions_list'),
    re_path(r'^api/admin/questions/create/?$', views.admin_question_create_api, name='api_admin_questions_create'),
    re_path(r'^api/admin/questions/(?P<question_id>\d+)/?$', views.admin_question_detail_api, name='api_admin_question_detail'),
    re_path(r'^api/admin/questions/import/?$', views.admin_questions_import_api, name='api_admin_questions_import'),
    re_path(r'^api/admin/questions/export/?$', views.admin_questions_export_api, name='api_admin_questions_export'),
    re_path(r'^api/admin/questions/all/?$', views.admin_questions_delete_all_api, name='api_admin_questions_delete_all'),
]
