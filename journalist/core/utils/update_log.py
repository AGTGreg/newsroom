import logging
from django.utils import timezone
from journalist.core import journalist_globals as jg

logger = logging.getLogger('newsroom.base')


def __add_to_log(level, msg):
    msg = '{} - {} ==> {}'.format(
        timezone.now().strftime("%d-%m, %H:%M:%S"),
        level,
        msg
    )
    jg.LOG.insert(
        0,
        {
            'level': level,
            'msg': msg
        }
    )


def info(msg):
    logger.info(msg)
    __add_to_log('INFO', msg)


def error(msg):
    logger.error(msg)
    __add_to_log('ERROR', msg)


def warning(msg):
    logging.warning(msg)
    __add_to_log('WARNING', msg)
