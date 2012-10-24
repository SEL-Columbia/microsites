# encoding=utf-8

import json

import requests
from pybamboo import PyBamboo, ErrorParsingBambooData

from microsite.models import Option
from microsite.formhub import (get_formhub_user_url, 
                               get_formhub_form, get_formhub_ids_form)
from microsite.utils import get_option, load_json
from microsite.caching import cache_result


class Bamboo(PyBamboo):

    def _safe_json_loads(self, req):
        try:
            return load_json(req.text)
        except:
            raise ErrorParsingBambooData

    def info_ident(self, dataset_id):
        return u"get#%(url)s" % {'url': self.get_dataset_info_url(dataset_id)}

    @cache_result(ident=info_ident, store='bamboo')
    def info(self, dataset_id):
        return super(Bamboo, self).info(dataset_id)

    def query_ident(self, dataset_id, select=None, query=None, group=None,
              as_summary=False, first=False, last=False):
        params = {
            'select': select,
            'query': query,
            'group': group
        }

        # remove key with no value
        for key, value in params.items():
            if not value:
                params.pop(key)
            else:
                if isinstance(value, dict):
                    params[key] = json.dumps(value)

        if as_summary:
            url = self.get_dataset_summary_url(dataset_id)
        else:
            url = self.get_dataset_url(dataset_id)

        return (u"get#%(url)s#%(params)s"
                % {'url': url, 'params': json.dumps(params)})

    @cache_result(ident=query_ident, store='bamboo')
    def query(self, dataset_id, select=None, query=None, group=None,
              as_summary=False, first=False, last=False):
        return super(Bamboo, self).query(dataset_id, select, query, group,
              as_summary, first, last)

    def count_submissions_ident(self, dataset_id, field, method='count'):
        url = self.get_dataset_summary_url(dataset_id)
        return u"get#%(url)s" % {'url': url}

    @cache_result(ident=count_submissions_ident, store='bamboo')
    def count_submissions(self, dataset_id, field, method='count'):
        return super(Bamboo, self).count_submissions(dataset_id, field, method)


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


def count_submissions(project, field, method='count', is_registration=False):

    url, dataset_id = get_bamboo_dataset_url(project, is_registration)
    return Bamboo(url).count_submissions(dataset_id, field, method)


def bamboo_query(project,
                 select=None, query=None, group=None,
                 as_summary=False,
                 is_registration=False,
                 first=False, last=False,
                 print_url=False):

    url, dataset_id = get_bamboo_dataset_url(project, is_registration)
    return Bamboo(url).query(dataset_id, select, query, group,
                               as_summary, first, last)


def bamboo_store_calculation(project, formula_name, formula,
                             is_registration=False):

    url, dataset_id = get_bamboo_dataset_url(project, is_registration)
    return Bamboo(url).store_calculation(dataset_id, formula_name, formula)