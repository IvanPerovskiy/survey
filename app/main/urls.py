from django.urls import path, include
from rest_framework import routers

from main import views


router = routers.SimpleRouter(trailing_slash=False)
router.register('surveys', views.SurveyViewset)
router.register('questions', views.QuestionViewset)
router.register('', views.UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
