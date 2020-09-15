from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.http import HttpResponseRedirect

from .core.app import get_latest_articles
from .core.articles_factory import article_editor
from .core import journalist_globals as jg
from .models import Article


def index(request):
    context = {
        'msg': 'Hello!',
    }
    return render(request, 'journalist/index.html', context)


def get_data(request):
    context = {
        "status": "OK",
        "log": jg.LOG
    }
    return JsonResponse(context)


def start_scaping(request):
    get_latest_articles()
    return JsonResponse({"status": "OK"})


def edit_article(request, pk):
    article = Article.objects.get(pk=pk)
    article_editor.edit_article(article)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
