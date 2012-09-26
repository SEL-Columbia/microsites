# encoding=utf-8

import json

import requests
from pybamboo import PyBamboo, ErrorParsingBambooData

from microsite.models import Option
from microsite.formhub import get_formhub_form_public_api_url
from microsite.utils import get_option, load_json


class Bamboo(PyBamboo):

    def _safe_json_loads(self, req):
        try:
            return load_json(req.text)
        except:
            raise ErrorParsingBambooData


def getset_bamboo_dataset(project, is_registration=False):
    ''' Retrieve bamboo dataset ID on formhub and update model '''

    url = get_formhub_form_public_api_url(project, is_registration)

    key = 'bamboo_ids_dataset' if is_registration else 'bamboo_dataset'

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