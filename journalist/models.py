from django.db import models
from tinymce import HTMLField
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime
from django.utils import timezone
from django.utils.text import slugify


EL = 'el'
EN = 'en'
RU = 'ru'
LANGUAGES = [
    (EL, 'el'),
    (EN, 'en'),
    (RU, 'ru'),
]

NEW = 'NW'
READY = 'RD'
STATUS_CHOICES = [
    (NEW, 'New'),
    (READY, 'Ready'),
]


class Topic(models.Model):
    title = models.CharField(max_length=200, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class Source(models.Model):
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='sources',
    )
    root_url = models.CharField(
        max_length=300, help_text="Add a sitemap.xml url to scrape.")
    url_filter = models.CharField(
        max_length=300,
        help_text="Only the urls that strart with this filter will be scraped."
    )
    language = models.CharField(max_length=2, choices=LANGUAGES, default=EL)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.root_url


class URLBlacklist(models.Model):
    """
    The scraper checks this list before scraping a url so that it doesn't
    scrape it more than once.
    Every url that gets scraped ends up in this list.
    """
    url = models.CharField(max_length=300, unique=True)

    def __str__(self):
        return self.url


class URLRecommendation(models.Model):
    url = models.CharField(max_length=300, unique=True)
    title = models.CharField(max_length=300)
    description = models.TextField(blank=True, null=True)
    keywords = models.TextField()
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Article(models.Model):
    source = models.CharField(max_length=300, unique=True)
    topic = models.ForeignKey(Topic, on_delete=models.PROTECT)
    original_language = models.CharField(max_length=2, choices=LANGUAGES,
                                         default=EL)
    original_title = models.CharField(max_length=300, unique=True)
    original_text = models.TextField()

    title = models.CharField(max_length=300, blank=True, null=True)
    summary = HTMLField(blank=True, null=True)
    keywords = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES,
                              default=NEW, db_index=True)

    url_recommendations = models.ManyToManyField(
        URLRecommendation, blank=True)

    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.original_title


class GCCache(models.Model):
    key = models.CharField(max_length=100, primary_key=True)
    value = models.TextField(null=True, blank=True)
    expire_on = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.key

    def set_expiration_date(self, expiration_date):
        if (
            type(expiration_date) is datetime and
            (expiration_date - timezone.now()).total_seconds() > 0
        ):
            self.expire_on = expiration_date
            self.save()
            return self
        else:
            raise ValueError(
                """
                expiration_date must be a datetime.datetime pointing to the
                future.
                """
            )

    def is_expired(self):
        res = (
            self.expire_on is not None and
            (self.expire_on - timezone.now()).total_seconds() <= 0
        )
        return res

    def set_value(self, value):
        self.value = value
        self.save()
        return self

    @staticmethod
    def set_item(key, value):
        try:
            c = GCCache.objects.get(pk=key)
        except ObjectDoesNotExist:
            c = GCCache.objects.create(key=key, value=value)
        else:
            c.value = value
            c.save()
        finally:
            return c

    @staticmethod
    def get_item(key):
        try:
            c = GCCache.objects.get(pk=key)
        except ObjectDoesNotExist:
            return None
        else:
            return c
