# encoding=utf-8

import json

import requests
# from pybamboo import PyBamboo, ErrorParsingBambooData
from pybamboo.dataset import Dataset

from microsite.models import Option
from microsite.formhub import (get_formhub_user_url,
                               get_formhub_form, get_formhub_ids_form)
from microsite.utils import get_option
from microsite.caching import cache_result


class CachedDataset(Dataset):

    @classmethod
    def _flat_dict(cls, d):
        if not isinstance(d, dict):
            return u'none'
        return u"#".join([u"%s|%s" % (k, d.get(k))
                          for k in sorted(d.iterkeys())])

    def generic_ident(self, method, *args, **kwargs):

        def ss(o):
            return o.__str__().replace(' ', '_')

        id_string = u"%(method)s__"
        for k, v in kwargs.items():
            if k in ('num_retries', ):
                continue
            id_string += u"%(key)s:%(value)s" % {'key': k.upper(),
                                                 'value': ss(v)}
        if len(args):
            id_string += u"##"
            id_string += u"|#|".join([ss(arg) for arg in args])

        return id_string

    def data_ident(self, *args, **kwargs):
        return self.generic_ident('get_data', *args, **kwargs)

    @cache_result(ident=data_ident, store='bamboo')
    def get_data(self, *args, **kwargs):
        return super(CachedDataset, self).get_data(*args, **kwargs)

    def info_ident(self, *args, **kwargs):
        return self.generic_ident('get_info', *args, **kwargs)

    @cache_result(ident=info_ident, store='bamboo')
    def get_info(self, *args, **kwargs):
        return super(CachedDataset, self).get_info(*args, **kwargs)

    def count_ident(self, *args, **kwargs):
        return self.generic_ident('count', *args, **kwargs)

    @cache_result(ident=count_ident, store='bamboo')
    def count(self, *args, **kwargs):
        return super(CachedDataset, self).count(*args, **kwargs)


def getset_bamboo_dataset(project, is_registration=False):
    ''' Retrieve bamboo dataset ID on formhub and update model '''

    key = 'bamboo_ids_dataset' if is_registration else 'bamboo_dataset'

    form_func = get_formhub_ids_form if is_registration else get_formhub_form
    form = form_func(project)

    return raw_getset_bamboo_dataset(project, form, key, is_registration)


def raw_getset_bamboo_dataset(project, form, key, is_registration=False):
    ''' Retrieve bamboo dataset ID on formhub and update model '''

    data = {'user_url': get_formhub_user_url(project, is_registration),
            'form': form}
    url = u'%(user_url)s/forms/%(form)s/public_api' % data

    req = requests.get(url)
    if not req.status_code in (200, 202):
        return False

    try:
        response = json.loads(req.text)
        bamboo_dataset = Option.objects.get(key=key, project=project)
        bamboo_dataset.value = response.get('bamboo_dataset')
        bamboo_dataset.save()
    except:
        return False
    return True


def get_bamboo_url(project):
    return get_option(project, 'bamboo_uri')


def get_bamboo_dataset_id(project, is_registration=False):

    return (get_bamboo_ids_dataset(project) if is_registration
                                         else get_bamboo_dataset(project))


def get_bamboo_dataset_url(project, is_registration=False):

    dataset = get_bamboo_dataset_id(project, is_registration)
    url = get_bamboo_url(project)
    return (url, dataset)


def get_bamboo_dataset(project):
    return get_option(project, 'bamboo_dataset')


def get_bamboo_ids_dataset(project):
    return get_option(project, 'bamboo_ids_dataset')
