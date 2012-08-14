# encoding=utf-8

import json

import requests

from microsite.models import Option


def getset_bamboo_dataset():
    ''' Retrieve bamboo dataset ID on formhub and update model '''

    data = {'formhub_url': Option.objects.get(key='formhub_uri').value,
            'user': Option.objects.get(key='formhub_user').value,
            'formid': Option.objects.get(key='formhub_form').value}

    # all those required to successfuly retrieve bamboo ID.
    if not all(data):
        return False

    url = u'%(formhub_url)s/%(user)s/forms/%(formid)s/public_api' % data
    print(url)
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
