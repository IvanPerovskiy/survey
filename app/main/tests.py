from django.conf import settings as django_settings
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from main.models import *
from main.management.commands.start_server import start_server


class TestDataMixin(TestCase):
    def setUp(self):
        start_server()
        self.admin = APIClient()
        self.user = APIClient()
        response = self.admin.post('/api/login', {
            'login': django_settings.ADMIN_LOGIN,
            'password': django_settings.ADMIN_PASSWORD
        }, format='json')
        self.assertEqual(response.status_code, 200)
        access_token = response.data['access_token']
        self.admin.credentials(HTTP_AUTHORIZATION='Bearer %s' % access_token)

    def test_admin(self):
        response = self.admin.post('/api/surveys')
        self.assertEqual(response.status_code, 400)
        response = self.admin.post('/api/surveys', {
            'name': 'Тестовый опрос',
            'start_date': '2021-12-01',
            'end_date': '2022-01-01',
            'questions': [
                {
                    'body': 'Укажите ваш пол.',
                    'question_type': QuestionType.CHOICE,
                    'choices': ['Муж', 'Жен']
                },
                {
                    'body': 'Как вас зовут?',
                    'question_type': QuestionType.TEXT
                }
            ],
        }, format='json')
        question = Question.objects.filter(body='Укажите ваш пол.').first()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(question.question_type, QuestionType.CHOICE)
        self.assertEqual(len(question.answer_choices.all()), 2)
        response = self.admin.get('/api/surveys')
        self.assertEqual(response.status_code, 200)
        survey_id = response.data[0]['id']
        survey = Survey.objects.get(id=survey_id)

        self.assertEqual(survey.name, 'Тестовый опрос')
        response = self.admin.put(f'/api/surveys/{survey_id}', {
            'name': 'Тестовый опрос2'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        survey.refresh_from_db()
        self.assertEqual(survey.name, 'Тестовый опрос2')
        response = self.admin.get('/api/questions?survey_id=1')
        self.assertEqual(len(response.data), 2)
        response = self.admin.delete(f'/api/questions/{question.id}')
        self.assertEqual(response.status_code, 204)
        response = self.admin.get('/api/questions?survey_id=1')
        self.assertEqual(len(response.data), 1)
        question.refresh_from_db()
        self.assertEqual(question.is_deleted, True)

    def test_user(self):
        response = self.admin.post('/api/surveys', {
            'name': 'Тестовый опрос3',
            'start_date': '2021-11-01',
            'end_date': '2022-01-01',
            'questions': [
                {
                    'body': 'Укажите ваш пол.',
                    'question_type': QuestionType.CHOICE,
                    'choices': ['Муж', 'Жен']
                },
                {
                    'body': 'Как вас зовут?',
                    'question_type': QuestionType.TEXT
                }
            ],
        }, format='json')
        response = self.admin.get('/api/surveys')
        self.assertEqual(response.status_code, 200)
        survey_id = response.data[0]['id']
        survey = Survey.objects.get(id=survey_id)
        first_question = Question.objects.filter(body='Укажите ваш пол.').first()
        second_question = Question.objects.filter(body='Как вас зовут?').first()
        response = self.user.post(f'/api/surveys/{survey_id}/take', {
            'user_id': 123,
            'answers': [
                {
                    'question_id': first_question.id,
                    'choices_id': first_question.answer_choices.first().id
                },
                {
                    'body': 'Петя Иванов',
                    'question_id': second_question.id,
                }
            ],
        }, format='json')
        self.assertEqual(response.status_code, 201)

