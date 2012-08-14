# encoding=utf-8

from django import template
# from django.template.defaultfilters import stringfilter


register = template.Library()


@register.filter(name='NAdefault')
def phone_number_formatter(data):
    """ apply json load to string """

    if data is None:
        return u"n/a"
    return data

