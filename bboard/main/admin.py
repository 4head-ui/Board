from django.contrib import admin
import datetime


from .models import AdvUser,SuperRubric,SubRubric,Bb,AdditionalImage,Comment
from .forms import SubRubricForm
from .utilities import send_activation_notification


def send_activation_notifications(modeladmin, request, queryset):
    for rec in queryset:
        if not rec.is_activated:
            send_activation_notification(rec)
    modeladmin.message_user(request, 'Письма с оповещениями отправлены')


send_activation_notifications.short_description = 'Отправка писем с ' \
                                                  'оповещениями об активации'

class NonactivatedFilter(admin.SimpleListFilter):
    title = 'Прошли активацию?'
    parameter_name = 'actstate'

    def lookups(self, request, model_admin):
        return (
            ('activated', 'Прошли'),
            ('notactivated', 'Не прошли'),
            ('threedays', 'Не прошли более 3 дней'),
            ('week', 'Не прошли более недели'),
        )

    def queryset(self, request, queryset):
        val = self.value()
        if val == 'activated':
            return queryset.filter(is_active=True, is_activated=True)
        elif val == 'notactivated':
            return queryset.filter(is_active=False, is_activated=False)
        elif val == 'threedays':
            d = datetime.date.today() - datetime.timedelta(days=3)
            return queryset.filter(is_active=False, is_activated=False, date_joined__date__lt=d)
        elif val == 'week':
            d = datetime.date.today() - datetime.timedelta(weeks=1)
            return queryset.filter(is_active=False, is_activated=False, date_joined__date__lt=d)


class AdvUserAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_activated', 'date_joined')  # __str__ - строковое предаставление записи.
    # Реализовано в модели AbstractUser, от которой наследует наша модель
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = (NonactivatedFilter,)
    fields = (('username', 'email'), ('first_name', 'last_name'),
              ('send_messages', 'is_active', 'is_activated'),
              ('is_superuser'),
              'groups', 'user_permissions',
              ('last_login', 'date_joined'),
              'password',)
    readonly_fields = ('last_login', 'date_joined', 'password')
    actions = (send_activation_notifications,)

class SubRubricInline(admin.TabularInline):
    model = SubRubric

class SuperRubricAdmin(admin.ModelAdmin):
    exclude = ('super_rubric',)
    inlines = (SubRubricInline,)


class SubRubricAdmin(admin.ModelAdmin):
    form=SubRubricForm

class AdditionalImageInline(admin.TabularInline):
    model = AdditionalImage


class CommentInLine(admin.TabularInline):
    model = Comment


class BbAdmin(admin.ModelAdmin):
    list_display = ('rubric','title','content','author','created_at',)
    fields = (('rubric','author'),'title','content','price','contacts','image',
              'is_active')#поля при клике на объявление в лист дисплее
    inlines = (AdditionalImageInline,CommentInLine)








admin.site.register(AdvUser,AdvUserAdmin)
admin.site.register(SuperRubric,SuperRubricAdmin)
admin.site.register(SubRubric,SubRubricAdmin)
admin.site.register(Bb,BbAdmin)

