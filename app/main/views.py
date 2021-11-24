from datetime import datetime

from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, status
from rest_framework.mixins import RetrieveModelMixin, ListModelMixin
from rest_framework.decorators import action, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.settings import api_settings
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .models import Survey, Question, AnswerChoice, User, UserRole, Answer
from .serializers import SurveySerializer, SurveySerializerCreate, SurveySerializerUpdate, \
    LoginSerializer, CredentialsSerializer, QuestionSerializer, TakeSurveySerializer, AnswerSerializerList, \
    AnswerSerializerRequest
from main.decorators import admin_required
from main.responses import *


class UserViewSet(
        viewsets.GenericViewSet):
    REFRESHTOKEN_COOKIE = 'REFRESHTOKEN'

    queryset = User.objects.all()
    serializer_class = LoginSerializer

    login_response = openapi.Response(SUCCESS_RESPONSE, CredentialsSerializer)

    def __set_refreshtoken_cookie(self, response, refresh_token):
        response.set_cookie(
            self.REFRESHTOKEN_COOKIE,
            value=refresh_token,
            secure=True,
            httponly=True,
        )

    def __delete_refreshtoken_cookie(self, response):
        response.delete_cookie(self.REFRESHTOKEN_COOKIE)

    def __get_credentials_response(self, user, refresh_token=None):
        if refresh_token is None:
            refresh_token = RefreshToken.for_user(user.auth_user)

        serializer = CredentialsSerializer(data={
            'access_token': str(refresh_token.access_token),
            'expires': datetime.utcfromtimestamp(refresh_token['exp']),
            'user_id': user.pk
        })

        if not serializer.is_valid():
            raise RuntimeError(serializer.errors)

        response = Response(serializer.validated_data)
        self.__set_refreshtoken_cookie(response, str(refresh_token))

        return response

    @swagger_auto_schema(responses={
        200: login_response,
        400: BAD_REQUEST
    })
    @action(
        detail=False,
        methods=['post'],
        serializer_class=LoginSerializer,
        permission_classes=(AllowAny,),
    )
    @authentication_classes([])
    @permission_classes([])
    def login(self, request, **kwargs):
        """
        Авторизация в системе
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        current_user = User.objects.filter(
            login=serializer.validated_data['login']
        ).first()
        if not current_user:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        password = current_user.hash_password(
            serializer.validated_data['password'],
        )

        auth_user = authenticate(
            request=request,
            username=f'user_{current_user.id}',
            password=password
        )
        if auth_user is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        return self.__get_credentials_response(current_user)


class SurveyViewset(viewsets.GenericViewSet, ListModelMixin, RetrieveModelMixin):
    queryset = Survey.objects.prefetch_related(
        'questions').prefetch_related(
        'questions__answer_choices').all()
    serializer_class = SurveySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['id', 'start_date', 'end_date', 'is_deleted']
    ordering_fields = ['created', 'start_date', 'end_date']
    ordering = ['-created']

    answer_param = openapi.Parameter('user_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER)
    survey_response = openapi.Response(SUCCESS_RESPONSE, SurveySerializer)
    answer_response = openapi.Response(SUCCESS_RESPONSE, AnswerSerializerList)

    def get_serializer_class(self):
        if self.action == 'create':
            return SurveySerializerCreate
        elif self.action == 'update':
            return SurveySerializerUpdate
        return self.serializer_class

    @swagger_auto_schema(responses={
        201: survey_response,
        400: BAD_REQUEST,
        404: NOT_FOUND
    })
    @admin_required
    def create(self, request, *args, **kwargs):
        """
        Создание опроса
        Доступно только администратору
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(data=SurveySerializer(instance).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(responses={
        200: survey_response,
        400: BAD_REQUEST,
        404: NOT_FOUND

    })
    @admin_required
    def update(self, request, *args, **kwargs):
        """
        Изменение опроса
        Доступно только администратору
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(data=SurveySerializer(instance).data, status=status.HTTP_200_OK)

    @admin_required
    def destroy(self, request, pk=None):
        """
        Удаление опроса
        Доступно только администратору
        В реальности опрос не удаляется, просто ставится флаг
        """
        instance = get_object_or_404(self.queryset, pk=pk)
        instance.is_deleted = True
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(responses={
        201: SUCCESS_RESPONSE,
        400: BAD_REQUEST,
        404: NOT_FOUND
    })
    @action(
        detail=True,
        url_path='take',
        methods=['post'],
        serializer_class=TakeSurveySerializer,
        permission_classes=(AllowAny,)
    )
    @authentication_classes([])
    def take(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_201_CREATED)

    @swagger_auto_schema(manual_parameters=[answer_param], responses={
        200: answer_response,
        400: BAD_REQUEST
    })
    @action(
        detail=False,
        url_path='answers',
        methods=['get'],
        permission_classes=(AllowAny,),
        serializer_class=AnswerSerializerRequest
    )
    @authentication_classes([])
    def get_answers(self, request, *args, **kwargs):
        """
        Получение всех ответов по user_id
        """
        user = User.objects.filter(external_id=int(request.query_params.get('user_id', -1)))
        if not user:
            return Response(status=status.HTTP_404_NOT_FOUND)
        answers = Answer.objects.select_related(
            'question').select_related(
            'choice').select_related(
            'question__survey').filter(
            user_id=user.id
        ).order_by('-created').all()
        data = []
        for answer in answers:
            item = {
                'survey_id': answer.question.survey.id,
                'question_id': answer.question.id,
                'question': answer.question.body,
                'answer': answer.body if answer.body else answer.choice.body
            }
        data.append(item)
        return Response(
            data={'user_id': user.external_id, 'results': data},
            status=status.HTTP_200_OK
        )


class QuestionViewset(viewsets.GenericViewSet, ListModelMixin, RetrieveModelMixin):
    queryset = Question.objects.prefetch_related('answer_choices').filter(
        is_deleted=False
    ).all()
    serializer_class = QuestionSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['id', 'survey_id']
    ordering_fields = ['created', 'survey_id']
    ordering = ['created']

    @admin_required
    def create(self, request, *args, **kwargs):
        """
        Создание вопроса
        Доступно только администратору
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(data=QuestionSerializer(instance).data, status=status.HTTP_201_CREATED)

    @admin_required
    def update(self, request, *args, **kwargs):
        """
        Изменение вопроса
        Доступно только администратору
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response(data=QuestionSerializer(instance).data, status=status.HTTP_200_OK)

    @admin_required
    def destroy(self, request, pk=None):
        """
        Удаление вопроса
        Доступно только администратору
        В реальности опрос не удаляется, просто ставится флаг
        """
        instance = Question.objects.filter(pk=pk).first()
        if not instance:
            return Response(status=status.HTTP_404_NOT_FOUND)
        instance.is_deleted = True
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)



