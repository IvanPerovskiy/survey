from django.contrib.auth import get_user_model
from django.core.management.utils import get_random_secret_key

from main.models import User, UserRole


def create_auth_user(user_id):
    auth_user = get_user_model().objects.create_user(
        username=f'user_{user_id}',
        is_active=True
    )
    return auth_user


def create_admin_user(login, password):
    user = User.objects.create(
        login=login,
        role=UserRole.ADMIN,
        salt=get_random_secret_key()
    )
    auth_user = create_auth_user(
        user.id
    )
    auth_user.set_password(user.hash_password(password))
    auth_user.save()

    user.auth_user = auth_user
    user.save()

    return user
