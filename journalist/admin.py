from django.contrib import admin
from . import models


class SourceInline(admin.TabularInline):
    model = models.Source
    extra = 1


class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'active')
    inlines = (SourceInline,)


class SourceAdmin(admin.ModelAdmin):
    list_display = ('root_url', 'topic', 'active')


class ArticleAdmin(admin.ModelAdmin):
    list_display = (
        'original_title', 'topic', 'status', 'date_modified',
        'date_created')
    change_form_template = 'journalist/admin/article_change_form.html'


admin.site.register(models.Article, ArticleAdmin)
admin.site.register(models.Topic, TopicAdmin)
admin.site.register(models.Source, SourceAdmin)
admin.site.register(models.URLRecommendation)
admin.site.register(models.GCCache)

