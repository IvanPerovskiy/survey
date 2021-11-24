import logging

from rest_framework import serializers, exceptions, status

from .models import Survey, Question, AnswerChoice, QuestionType, Answer, User

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger_handler = logging.FileHandler("logs/requests.log")
logger_handler.setLevel(logging.INFO)
logger_handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(logger_handler)


class ValidationError(exceptions.APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = 'invalid'

    def __init__(self, detail=None, status_code=status_code):
        self.detail = detail
        self.status_code = status_code
        if detail:
            logger.info(f"BAD REQUEST: {detail}")


class AnswerChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnswerChoice
        fields = ('body', 'id')


class QuestionSerializer(serializers.ModelSerializer):
    choices = serializers.ListField(required=False)

    class Meta:
        model = Question
        fields = ('body', 'question_type', 'choices')


class QuestionSerializerCreate(serializers.ModelSerializer):
    choices = serializers.ListField(required=False)

    class Meta:
        model = Question
        fields = ('body', 'question_type', 'choices', 'survey_id')

    def validate(self, data):
        super().validate(data)
        survey = Survey.objects.filter(id=data.get('survey_id')).first()
        if not survey:
            raise ValidationError(detail='Опрос не найден')
        return data

    def create(self, data):
        if survey := Survey.objects.filter(data['survey_id'].first()):
            question = Question.objects.create(
                survey=survey,
                question_type=data['question_type'],
                body=data['body']
            )
            for item_choice in data.get('choices', []):
                AnswerChoice.objects.create(
                    question=question,
                    body=item_choice
                )

        return question


class QuestionSerializerUpdate(serializers.ModelSerializer):
    choices = serializers.ListField(required=False)

    class Meta:
        model = Question
        fields = ('id', 'body', 'question_type', 'choices')

    def update(self, instance, data):
        instance.name = data.get('name', instance.name)
        instance.body = data.get('body', instance.body)
        instance.question_type = data.get('question_type', instance.question_type)
        choices = instance.answer_choices.all()
        new_choices = data['choices']
        for choice in choices:
            if choice.body not in data['choices']:
                choice.is_deleted = True
                choice.save()
            else:
                new_choices.remove(choice.body)
        for item in new_choices:
            AnswerChoice.objects.create(
                question=instance,
                body=item
            )

        return instance


class QuestionSerializerList(serializers.ModelSerializer):
    choices = AnswerChoiceSerializer(many=True, default=(), source='answer_choices')

    class Meta:
        model = Question
        fields = ('id', 'body', 'question_type', 'choices')


class SurveySerializer(serializers.ModelSerializer):
    questions = QuestionSerializerList(many=True)

    class Meta:
        model = Survey
        fields = ('id', 'name', 'start_date', 'end_date', 'questions')


class SurveySerializerCreate(serializers.ModelSerializer):
    questions = QuestionSerializer(many=True)

    class Meta:
        model = Survey
        fields = ('name', 'start_date', 'end_date', 'questions')

    def validate(self, data):
        for item in data['questions']:
            if item['question_type'] in (QuestionType.CHOICE, QuestionType.MULTICHOICE) and \
                    not item.get('choices'):
                raise ValidationError(detail='Не переданы варианты ответов')
        return data

    def create(self, data):
        survey = Survey.objects.create(
            name=data['name'],
            start_date=data['start_date'],
            end_date=data['end_date']
        )
        for item in data['questions']:
            question = Question.objects.create(
                survey=survey,
                question_type=item['question_type'],
                body=item['body']
            )
            for item_choice in item.get('choices', []):
                AnswerChoice.objects.create(
                    question=question,
                    body=item_choice
                )

        return survey


class SurveySerializerUpdate(serializers.ModelSerializer):
    class Meta:
        model = Survey
        fields = ('name', 'end_date')
        extra_kwargs = {
            'end_date': {'required': False},
            'name': {'required': False}
        }


class LoginSerializer(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField()


class CredentialsSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    expires = serializers.DateTimeField()
    user_id = serializers.IntegerField()


class AnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    choice_id = serializers.IntegerField(required=False)
    body = serializers.CharField(required=False)


class TakeSurveySerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    answers = AnswerSerializer(many=True)

    def update(self, instance, data):
        user, created = User.objects.get_or_create(
            external_id=data['user_id']
        )
        for item in data['answers']:
            Answer.objects.create(
                user_id=user.id,
                question_id=item['question_id'],
                choice_id=item.get('choice_id'),
                body=item.get('body')
            )
        return instance








