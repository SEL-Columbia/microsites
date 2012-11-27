# encoding=utf-8

import locale
from datetime import datetime

import pytz
from django import template
from django.template.defaultfilters import stringfilter

from microsite.utils import get_name_for
from microsite.models import Project
from microsite.barcode import get_ids_from_url

locale.setlocale(locale.LC_ALL, '')
register = template.Library()


@register.filter(name='NAdefault')
def default_na(data):
    ''' return N/A if data is None '''

    if data is None:
        return u"n/a"
    return data


@register.filter(name='KeyName')
def name_for_key(key, project_cat):

    if key is None:
        return key

    project, category = project_cat.split('|', 1)

    try:
        project = Project.objects.get(slug=project)
    except Project.DoesNotExist:
        return key

    return get_name_for(project, category, key)


@register.filter(name='shortID')
def short_id_from_urlid(url_id):
    try:
        uid, sid = get_ids_from_url(url_id)
        return sid
    except:
        return url_id


@register.filter(name='UUID')
def uid_from_urlid(url_id):
    try:
        uid, sid = get_ids_from_url(url_id)
        return uid
    except:
        return url_id


@register.filter(name='numberformat')
@stringfilter
def number_format(value, precision=2, french=False):
    try:
        format = '%d'
        value = int(value)
    except:
        try:
            format = '%.' + '%df' % precision
            value = float(value)
        except:
            format = '%s'
        else:
            if value.is_integer():
                format = '%d'
                value = int(value)
    try:
        if french:
            return strnum_french(locale.format(format, value, grouping=True))
        return locale.format(format, value, grouping=True)
    except Exception:
        pass
    return value


def strnum_french(numstr):
    if locale.getdefaultlocale()[0].__str__().startswith('fr'):
        return numstr
    else:
        return numstr.replace(',', ' ').replace('.', ',')


@register.filter(name='percent')
@stringfilter
def format_percent(value, precision=2, french=False):
    if value == u'n/a':
        return value
    try:
        return number_format(float(value) * 100, precision, french) + '%'
    except:
        return value


@register.filter(name='percent_raw')
@stringfilter
def format_percent_raw(value):
    if value == u'n/a':
        return value
    try:
        return float(value) * 100
    except:
        return value


@register.filter(name='truncate')
@stringfilter
def truncate(value, len=2):
    return value[0:int(len)]


@register.filter(name='split')
@stringfilter
def split(value, split_on=u' '):
    try:
        return value.split(split_on)
    except:
        return value


@register.filter(name='ts2date')
@stringfilter
def timestamp_to_datetime(value):
    try:
        return datetime.fromtimestamp(value)
    except:
        return value


@register.filter(name='status2badge')
@stringfilter
def status_to_badge(value):
    try:
        return [u'',
                u'badge-warning',
                u'badge-important',
                u'badge-info',
                u'badge-success',
                u'badge-inverse',
                u'badge-inverse'][int(value)]
    except:
        return u''


@register.filter(name='verbose_status')
@stringfilter
def verbose_status(value):
    from soiltrack.sample import ESTSSample
    try:
        return ESTSSample.get_verbose_status(int(value))
    except:
        return value


def convert_datetime(d):
    if d.utcoffset() is not None:
        return d.astimezone(pytz.UTC).replace(tzinfo=None)
    return d


@register.filter(name='step_delay')
def step_delay(event, sample):
    def step_delta(event, sample):
        if event['status'] == 0:
            return None
        try:
            if event['status'] == 1:
                previous_date = sample.plot['end']
            else:
                previous_date = sample.events()[event['status'] - 1]['end_time']

            return (convert_datetime(event['end_time'])
                    - convert_datetime(previous_date))

        except Exception as e:
            return None
    delta = step_delta(event, sample)
    if delta is None:
        return delta
    if delta.days:
        return u"%dd" % delta.days
    if delta.seconds:
        if delta.seconds > 3600:
            return u"%dh" % (delta.seconds / 3600)
        else:
            return u"%dmn" % (delta.seconds / 60)
    return delta
