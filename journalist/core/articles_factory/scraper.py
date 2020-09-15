import random
import requests

from bs4 import BeautifulSoup
from newspaper import Article as ArticleParser
from requests.exceptions import InvalidSchema

from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError

from journalist.core import journalist_globals as jg
from journalist.core.utils import update_log
from journalist.core.articles_factory import article_editor
from journalist.core.utils.user_agents import get_random_user_agent
from journalist.models import Topic, Article, READY
from journalist.models import GCCache as cache


CURRENT_USER_AGENT = get_random_user_agent()
REQUESTS_COUNT = 0


def get_tor_session():
    """ Connects to the tor network. Changes IP every 10 minutes.
    """
    session = requests.session()
    session.proxies = {'http':  'socks5://127.0.0.1:9050',
                       'https': 'socks5://127.0.0.1:9050'}
    return session


def get_page(url):
    """ Sends a request to the url and returns a response or None.
    Rotates random user agents every random intervals.
    """
    global CURRENT_USER_AGENT
    global REQUESTS_COUNT

    headers = {'User-Agent': CURRENT_USER_AGENT}
    session = get_tor_session()

    try:
        response = session.get(url, headers=headers)
    except InvalidSchema as e:
        update_log.error('Error in session.get()')
        update_log.error(e)
        return None
    else:
        # Use a user agent for a random amount of requests
        REQUESTS_COUNT += 1
        r_limit = random.randint(5, 10)
        if REQUESTS_COUNT >= r_limit:
            update_log.info("Changing user agent at {} requests.".format(
                REQUESTS_COUNT))

            # Make sure our new user agent is not the one we allready have.
            for a in range(0, 10):
                new_ua = get_random_user_agent()
                if new_ua != CURRENT_USER_AGENT:
                    CURRENT_USER_AGENT = get_random_user_agent()
                    REQUESTS_COUNT = 0

        if response.status_code == 200:
            return response
        else:
            update_log.warning('Got response code ({})'.format(
                response.status_code))
            return None


def test_connection():
    """ Flight test before we begin...
    """
    # Check user agent
    response = get_page("https://httpbin.org/user-agent")
    if response is not None:
        update_log.info(response.text)

    # Check IP
    response = get_page("http://httpbin.org/ip")
    if response is not None:
        update_log.info(response.text)


def get_urls():
    """ Get a list of urls (sources) for each topic to scrape.
    """
    topics = Topic.objects.filter(active=True)
    urls = {}
    for topic in topics:
        urls[topic.title] = set()
        sources = topic.sources.filter(active=True).values()
        for source in sources:
            urls[topic.title].update(get_urls_from_source(source))
    return urls


def get_urls_from_source(source):
    """ Returns a set of tuples: {(url, lang), (url, lang) ...} so that every
    url-language combination is unique.
    Checks the url_blacklist so we don't scrape a URL more than once.
    """

    urls = set()

    blacklist = cache.get_item('url_blacklist')
    if blacklist is None:
        blacklist = cache.set_item('url_blacklist', "")

    update_log.info('Checking {}'.format(source['root_url']))
    response = get_page(source['root_url'])
    if response is not None:
        soup = None
        if source['root_url'].endswith('.xml'):

            # XML Parsing =====================================================
            xml = response.text
            print('==> Response:')
            print(xml)
            soup = BeautifulSoup(xml)
            if soup is not None:
                links = soup.find_all('loc')
                if len(links) == 0:
                    update_log.warning('No links were fount in this page.')
                for link in links:
                    link_text = link.text
                    print(link_text)
                    if (
                        link_text.startswith(source['url_filter']) and
                        link_text > source['url_filter'] and
                        link_text not in blacklist.value
                    ):
                        urls.add((link_text, source['language']))
            else:
                update_log.warning('Cannot parse this page.')
        else:

            # HTML parsing ====================================================
            soup = BeautifulSoup(response.content, 'html.parser')
            if soup is not None:
                links = soup.find_all('a', href=True)
                if len(links) == 0:
                    update_log.warning('No links were fount in this page.')
                for link in links:
                    if (
                        link['href'].startswith(source['url_filter']) and
                        link['href'] > source['url_filter'] and
                        link['href'] not in blacklist.value
                    ):
                        urls.add((link['href'], source['language']))
            else:
                update_log.warning('Cannot parse this page.')

    if len(urls) == 0:
        update_log.warning('Fount nothing new in {}'.format(
            source['root_url']))

    return urls


def add_url_to_blacklist(url):
    """ Adds a url to the blacklist so that we never try to scrape it again.
    """
    blacklist = cache.get_item('url_blacklist')

    if blacklist is None:
        blacklist = cache.set_item('url_blacklist', url)
        return True

    new_url = ', {}'.format(url)
    blacklist.set_value(blacklist.value + new_url)

    return True


def parse_article(url, min_words_count=jg.MIN_WORDS_TO_SCRAPE):
    """ We download an article by ourselves so that we do it behind the Tor
    network and with a random user agent (Don't let Newspaper do it!).
    Then we fool Newspaper to think that it was the one who downloaded it so we
    can parse it and return the article.

    Returns None if the article is smaller than min_words_count.
    """

    try:
        response = get_page(url)
    except Exception as err:
        update_log.error('Error in get_page()')
        update_log.error(err)
        return None

    if response is not None:
        article = ArticleParser(url="http://something")
        article.html = response.content
        article.download_state = 2

        try:
            article.parse()
        except Exception as err:
            update_log.error('Error in article.parse()')
            update_log.error(err)
            return None
        else:
            add_url_to_blacklist(url)
            if len(article.text.split(' ')) >= min_words_count:
                return article

    return None


def get_articles_from_topics(topics):
    """ This is where it all starts. Scrapes articles from all URLS fount in
    the topics. Edits them and saves them to the database.
    """

    update_log.info('Testing connection.')
    test_connection()

    update_log.info('Looking for latest articles.')

    articles_urls = get_urls()

    if len(articles_urls) > 0:
        for topic_name, url_list in articles_urls.items():
            update_log.info('Fount {} new URLs to scrape for: {}'.format(
                len(url_list), topic_name))
            for url, lang in url_list:
                try:
                    article = Article.objects.get(source=url)
                    update_log.warning('Article allready exists: {}'.format(
                        article.original_title))
                except ObjectDoesNotExist:
                    article_parsed = parse_article(url)
                    if article_parsed is not None:
                        try:
                            new_article = Article.objects.create(
                                source=url,
                                topic_id=int(topics[topic_name]),
                                original_title=article_parsed.title,
                                original_text=article_parsed.text,
                                original_language=lang
                            )
                        except IntegrityError as err:
                            update_log.error('Error in saving new article.')
                            update_log.error(err)
                            continue
                        else:
                            update_log.info('Saved new article: {}'.format(
                                article_parsed.title))
                            article_editor.edit_article(new_article)
                else:
                    if article.status != READY:
                        article_editor.edit_article(new_article)

    update_log.info('Finished scraping.')

    return None
