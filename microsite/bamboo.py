# encoding=utf-8

import json

import requests

from microsite.models import Option
from microsite.formhub import get_formhub_form_public_api_url
from microsite.utils import get_option, load_json


class ErrorRetrievingBambooData(IOError):
    pass


class ErrorParsingBambooData(ValueError):
    pass


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


def get_bamboo_datasets_url(project):

    data = {'bamboo_url': get_bamboo_url(project)}
    return u'%(bamboo_url)s/datasets' % data


def get_bamboo_url(project):
    return get_option(project, 'bamboo_uri')


def get_bamboo_dataset(project):
    return get_option(project, 'bamboo_dataset')


def get_bamboo_ids_dataset(project):
    return get_option(project, 'bamboo_ids_dataset')


def get_bamboo_dataset_url(project, is_registration=False):

    dataset = (get_bamboo_ids_dataset(project) if is_registration 
                                         else get_bamboo_dataset(project))
    data = {'bamboo_url': get_bamboo_url(project),
            'dataset': dataset}
    return u'%(bamboo_url)s/datasets/%(dataset)s' % data


def get_bamboo_dataset_summary_url(project, is_registration=False):
    data = {'dataset_url': get_bamboo_dataset_url(project, is_registration)}
    return u'%(dataset_url)s/summary' % data


def get_bamboo_dataset_info_url(project, is_registration=False):
    data = {'dataset_url': get_bamboo_dataset_url(project, is_registration)}
    return u'%(dataset_url)s/info' % data


def get_bamboo_dataset_calculations_url(project, is_registration=False):
    
    dataset = (get_bamboo_ids_dataset(project) if is_registration 
                                         else get_bamboo_dataset(project))
    data = {'bamboo_url': get_bamboo_url(project),
            'dataset': dataset}
    return u'%(bamboo_url)s/calculations/%(dataset)s' % data


def count_submissions(project, field, method='count', is_registration=False):
    ''' Number of submissions for a given field.

    method is one of: '25%', '50%', '75%', 'count' (default),
                      'max', 'mean', 'min', 'std' '''

    data = {'bamboo_url': Option.objects.get(key='bamboo_uri',
                                             project=project).value,
            'dataset': Option.objects.get(key='bamboo_dataset',
                                          project=project).value,}

    if not all(data):
        return False

    url = get_bamboo_dataset_summary_url(project, is_registration)
    
    req = requests.get(url)
    if not req.status_code in (200, 202):
        raise ErrorRetrievingBambooData

    try:
        response = json.loads(req.text)

        value = response.get(field).get('summary')
        if method in value:
            return float(value.get(method))
        else:
            return sum([int(relval) for relval in value.values()])

    except:
        raise ErrorRetrievingBambooData
    return 0


def bamboo_query(project,
                 select=None, query=None, group=None,
                 as_summary=False,
                 is_registration=False):

    params = {
        'select': select,
        'query': query,
        'group': group
    }

    # remove key with no value
    for key, value in params.items():
        if not value:
            params.pop(key)

    if as_summary:
        url = get_bamboo_dataset_summary_url(project, is_registration)
    else:
        url = get_bamboo_dataset_url(project, is_registration)

    req = requests.get(url, params=params)

    if not req.status_code in (200, 202):
        raise ErrorRetrievingBambooData(u"%d Status Code received."
                                        % req.status_code)

    try:
        return load_json(req.text)
    except Exception as e:
        raise ErrorParsingBambooData(e.message)


def bamboo_store_calculation(project, formula_name, formula,
                             is_registration=False):

    url = get_bamboo_dataset_calculations_url(project, is_registration)

    params = {'name': formula_name,
              'formula': formula}

    req = requests.post(url, params=params)

    if not req.status_code in (200, 201, 202):
        raise ErrorRetrievingBambooData(u"%d Status Code received."
                                        % req.status_code)

    try:
        return load_json(req.text)
    except Exception as e:
        raise ErrorParsingBambooData(e.message)

