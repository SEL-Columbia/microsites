# encoding=utf-8

from django import template
# from django.template.defaultfilters import stringfilter

from microsite.utils import get_name_for
from microsite.models import Project
from microsite.barcode import get_ids_from_url

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
