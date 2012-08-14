# encoding=utf-8

import json

import requests

from microsite.models import Option


class ErrorRetrievingBambooData(IOError):
    pass


def getset_bamboo_dataset():
    ''' Retrieve bamboo dataset ID on formhub and update model '''

    data = {'formhub_url': Option.objects.get(key='formhub_uri').value,
            'user': Option.objects.get(key='formhub_user').value,
            'formid': Option.objects.get(key='formhub_form').value}

    # all those required to successfuly retrieve bamboo ID.
    if not all(data):
        return False

    url = u'%(formhub_url)s/%(user)s/forms/%(formid)s/public_api' % data

    req = requests.get(url)
    if not req.status_code in (200, 202):
        return False

    try:
        response = json.loads(req.text)
        bamboo_dataset = Option.objects.get(key='bamboo_dataset')
        bamboo_dataset.value = response.get('bamboo_dataset')
        bamboo_dataset.save()
    except:
        return False
    return True


def count_submissions(field, method='count'):
    ''' Number of submissions for a given field.

    method is one of: '25%', '50%', '75%', 'count' (default),
                      'max', 'mean', 'min', 'std' '''

    data = {'bamboo_url': Option.objects.get(key='bamboo_uri').value,
            'dataset': Option.objects.get(key='bamboo_dataset').value,}

    if not all(data):
        return False

    url = u'%(bamboo_url)s/datasets/%(dataset)s/summary' % data
    
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