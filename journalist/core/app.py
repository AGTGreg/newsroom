from journalist.core.articles_factory import scraper, article_editor
from journalist.models import Article, Topic


def available_topics():
    topics = {}
    for topic in Topic.objects.filter(active=True):
        topics[topic.title] = topic.id
    return topics


def get_latest_articles():
    topics = available_topics()
    scraper.get_articles_from_topics(topics)

    return None


def edit_new_articles():
    new_articles = Article.objects.get(pk=495)
    article_editor.edit_article(new_articles)
