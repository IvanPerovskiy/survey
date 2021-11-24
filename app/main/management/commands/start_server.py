"""
Created on 24.08.2021

:author: Ivan Perovsky
Скрипт заполнения БД при разворачивании проекта
"""
import csv

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from django.conf import settings

from main.actions import create_admin_user


def start_server():
    """
    Функция разворачивания проекта после применения миграций
    :return:
    """
    create_admin_user(settings.ADMIN_LOGIN, settings.ADMIN_PASSWORD)

    get_user_model().objects.create_superuser(
        username=settings.SUPERUSER_LOGIN,
        email=settings.SUPERUSER_EMAIL,
        password=settings.SUPERUSER_PASSWORD
    )


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        with transaction.atomic():
            start_server()
