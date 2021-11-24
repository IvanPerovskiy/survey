import hashlib

from django.db import models
from django.conf import settings


class UserRole:
    ADMIN = 0
    ANONYMOUS = 1
    AUTH_USER = 2

    choices = (
        (ADMIN, 'Администратор'),
        (ANONYMOUS, 'Анонимный пользователь'),
        (AUTH_USER, 'Авторизованный пользователь')
    )


class UserStatus:
    NEW = 0
    ACTIVE = 1
    BLOCKED = 2
    DELETED = 3

    choices = (
        (NEW, 'Новый'),
        (ACTIVE, 'Активный'),
        (BLOCKED, 'Заблокированный'),
        (DELETED, 'Удаленный'),
    )


class QuestionType:
    TEXT = 0
    CHOICE = 1
    MULTICHOICE = 2

    choices = (
        (TEXT, 'Ответ текстом'),
        (CHOICE, 'Выбор одного варианта'),
        (MULTICHOICE, 'Выбор нескольких вариантов')
    )


class User(models.Model):
    external_id = models.BigIntegerField(null=True, blank=True)
    login = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=40, null=True, blank=True)

    auth_user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    salt = models.CharField(max_length=200, null=True, blank=True)
    status = models.IntegerField(choices=UserStatus.choices, default=UserStatus.ACTIVE)
    role = models.IntegerField(choices=UserRole.choices, default=UserRole.ANONYMOUS)

    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def hash_password(self, password):
        h = hashlib.sha256()
        h.update(password.encode('utf-8'))
        h.update(self.salt.encode('utf-8'))
        return h.hexdigest()


class Survey(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    start_date = models.DateField(verbose_name="Дата старта опроса")
    end_date = models.DateField(verbose_name="Дата окончания опроса")
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)


class Question(models.Model):
    survey = models.ForeignKey(Survey, on_delete=models.PROTECT, related_name='questions')
    question_type = models.IntegerField(choices=QuestionType.choices)
    body = models.CharField(max_length=1500)
    is_deleted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")


class AnswerChoice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name='answer_choices')
    body = models.CharField(max_length=500)
    is_deleted = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.PROTECT, related_name='all_answers')
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='answers')
    choice = models.ForeignKey(AnswerChoice, on_delete=models.PROTECT, blank=True, null=True)
    body = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")


