from django.contrib import admin

from . import models


@admin.register(models.Survey)
class SurveyAdmin(admin.ModelAdmin):
    pass


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Question)
class QuestionAdmin(admin.ModelAdmin):
    pass


@admin.register(models.Answer)
class AnswerAdmin(admin.ModelAdmin):
    pass
