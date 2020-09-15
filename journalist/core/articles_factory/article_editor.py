import requests
import json
import re
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.utils import timezone
from gensim.summarization import summarize as gn_summarize
from gensim.summarization import keywords as gn_keywords
from gensim.summarization import textcleaner

from ibm_watson import LanguageTranslatorV3
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator

from journalist.models import GCCache as cache
from journalist.models import EN, READY
from journalist.core.utils import update_log
from journalist.core import journalist_globals as jg


def summarize(text):
    update_log.info('Summarizing...')
    summary = gn_summarize(text, ratio=jg.SAMMARIZE_RATIO)
    return(summary)


def init_watson_translator():
    authenticator = IAMAuthenticator(settings.WATSON_IAM_KEY)
    language_translator = LanguageTranslatorV3(
        version=settings.WATSON_VERSION,
        authenticator=authenticator
    )

    language_translator.set_service_url(settings.WATSON_SERVICE_URL)

    return language_translator


def get_tor_session():
    """ Connects to tor network. Changes IP every 10 minutes.
    """
    session = requests.session()
    session.proxies = {'http':  'socks5://127.0.0.1:9050',
                       'https': 'socks5://127.0.0.1:9050'}
    return session


def mymemory_translate(text, languages="el-en"):
    daily_limit = 1000
    c = cache.get_item('mymemory_words_remaining')
    if c is None or c.is_expired():
        c = cache.set_item('mymemory_words_remaining', daily_limit)
        c.set_expiration_date(timezone.now() + relativedelta(days=+1))

    url = "http://api.mymemory.translated.net/get"
    langpair = languages.replace("-", "|")

    words_to_send = len(re.findall(r'\w+', text))
    words_remaining = int(c.value)
    print('==> Words to send:')
    print(words_to_send)

    def translate(sentence):
        params = {"q": sentence, "langpair": langpair}
        session = get_tor_session()
        response_object = session.post(url, params)
        response = json.loads(response_object.text)
        if response['responseStatus'] != 200:
            update_log.warning(
                'MyMemory responded with {}'.format(
                    response['responseStatus'])
                )
        else:
            return response['responseData']['translatedText']

    if words_remaining > words_to_send:
        translated_text = ""
        # The limit of characters for each request is 500
        if len(text) > 500:
            sentences = textcleaner.split_sentences(text)
            for sent in sentences:
                sentence = translate(sent)
                if sent is not None:
                    translated_text += sentence + "\r\n"
                else:
                    return None
        else:
            translated_text = translate(text)

        words_remaining -= int(words_to_send)
        c.set_value(words_remaining)
        return translated_text
    else:
        update_log.warning('MyMemory reached the daily limit.')
        return None


def watson_translate(text, languages='el-en'):
    """ Translates the text using the watson API.
    Makes sure to not pass the monthly limit by updating and checking on the
    cache.
    """
    monthly_limit = 998000
    c = cache.get_item('watson_characters_remaining')
    if c is None or c.is_expired():
        c = cache.set_item('watson_characters_remaining', monthly_limit)
        c.set_expiration_date(timezone.now() + relativedelta(months=+1))

    chars_remaining = int(c.value)
    chars_to_sent = len(text)

    if chars_remaining > chars_to_sent:
        try:
            language_translator = init_watson_translator()
        except BaseException as err:
            update_log.error('Error in init_watson_translator()')
            update_log.error(err)
        else:
            translation = language_translator.translate(
                text=text, model_id=languages).get_result()
            translated_text = translation['translations'][0]['translation']

            chars_remaining -= int(translation['character_count'])
            c.set_value(chars_remaining)

            return translated_text
    else:
        update_log.warning('Watson reached the monthly limit.')
        print('Watson reached the monthly limit.')
        return None

    return None


def translate_this(text, languages="el-en"):
    """ Translates and returns the given text. First try is with Watson and
    then with MyMemory if Watson Quotas have been maxed out.
    """
    update_log.info('Translating...')

    translated_text = watson_translate(text, languages)
    if translated_text is None:
        translated_text = mymemory_translate(text, languages)

    return translated_text


def edit_article(article):
    """ Gets an article db record reference edits it and saves it.
    """
    update_log.info('Editing {}'.format(article.original_title))
    summary = summarize(article.original_text)

    if article.original_language != EN:
        translate_langs = "{}-{}".format(
            article.original_language, EN
        )
        try:
            title = translate_this(article.original_title, translate_langs)
            summary = translate_this(summary, translate_langs)
        except Exception as err:
            update_log.error(err)
            return None
    else:
        title = article.title

    if summary is not None:
        article.title = title
        html_summary = ""
        for sent in textcleaner.split_sentences(summary):
            html_summary += "<p>{}</p>".format(sent)
        article.summary = html_summary
        article.keywords = gn_keywords(summary).replace("\n", ", ")
        article.status = READY
        article.save()
        update_log.info('Editing finished successfully!')
    else:
        update_log.error('Could not finished editing the article.')

    return article
