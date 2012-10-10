# encoding=utf-8

import json

import requests
from pybamboo import PyBamboo, ErrorParsingBambooData

from microsite.models import Option
from microsite.formhub import get_formhub_user_url, get_formhub_form
from microsite.utils import get_option, load_json
from microsite.caching import cache_result


class Bamboo(PyBamboo):

    def _safe_json_loads(self, req):
        try:
            return load_json(req.text)
        except:
            raise ErrorParsingBambooData

    def info_url(self, dataset_id):
        return self.get_dataset_info_url(dataset_id)

    @cache_result(id_func=info_url, store='bamboo')
    def info(self, dataset_id):
        req = requests.get(self.info_url(dataset_id))
        self._check_response(req)
        return self._safe_json_loads(req)


def getset_bamboo_dataset(project, is_registration=False):
    ''' Retrieve bamboo dataset ID on formhub and update model '''

    key = 'bamboo_ids_dataset' if is_registration else 'bamboo_dataset'

    form = get_formhub_form(project)

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