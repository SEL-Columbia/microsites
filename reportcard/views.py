
import json

import requests
from django.http import HttpResponse
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from constants import FORMHUB_URL, DEFAULT_LOGIN, DEFAULT_PASSWORD, BAMBOO_URL
from microsite.utils import download_formhub
from microsite.models import Option
from microsite.decorators import login_maybe_required
from microsite.bamboo import ErrorRetrievingBambooData, count_submissions


def home(request):
    context = {'category': 'home'}

    try:
        nb_submissions = count_submissions(u'rating')
    except ErrorRetrievingBambooData:
        nb_submissions = None

    context.update({'nb_submissions': nb_submissions})

    return render(request, 'home.html', context)


@login_maybe_required
def list_classes(request):

    context = {'category': 'classes'}

    classes_list = [{'name': u"Kabuyanda P.S",},
                    {'name': u"Markala Zanbugu"},
                    {'name': u"Les mots"}]
    paginator = Paginator(classes_list, 25)

    page = request.GET.get('page')
    try:
        classes = paginator.page(page)
    except PageNotAnInteger:
        classes = paginator.page(1)
    except EmptyPage:
        classes = paginator.page(paginator.num_pages)

    context.update({'classes': classes})

    return render(request, 'list_classes.html', context)


@login_maybe_required
def list_submissions(request):

    context = {'category': 'submissions'}

    submissions_list = [{'name': u"Kabuyanda P.S",},
                        {'name': u"Markala Zanbugu"},
                        {'name': u"Les mots"}]
    paginator = Paginator(submissions_list, 25)

    page = request.GET.get('page')
    try:
        submissions = paginator.page(page)
    except PageNotAnInteger:
        submissions = paginator.page(1)
    except EmptyPage:
        submissions = paginator.page(paginator.num_pages)

    context.update({'submissions': submissions})

    return render(request, 'list_submissions.html', context)


def update_data(request):

    ''' update full dataset in bamboo by receiving a POST JSON request
        containing the uuid of the form. '''

    if not request.method == 'POST':
        return HttpResponse(u"POST request expected.", status=405)

    # 1. parseJSON or die
    try:
        json_data = json.loads(request.raw_post_data)
    except ValueError:
        return HttpResponse(u"POST request is not valid JSON.", status=400)

    # 2. retrieve uuid or _userform_id
    #    match with expected ID or die
    uuid = json_data.get('formhub/uuid', None)
    userform_id = json_data.get('_userform_id', None)

    # we might be interested in going this way in the future
    # but it's not implemented in FH yet.
    if uuid and False:
        download_url = ('%(root)s/forms/%(uuid)s/data.csv' 
                        % {'root': FORMHUB_URL, 'uuid': 'uuid'})
    else:
        # /!\ UNSAFE. separator (_) is a valid username char.
        username, form_id = userform_id.split('_', 1)
        download_url = ('%(root)s/%(user)s/forms/%(form_id)s/data.csv'
                        % {'root': FORMHUB_URL, 'user': username, 
                           'form_id': form_id})

    # 3. download dataset from formhub or die
    try:
        filename = download_formhub(url=download_url, login=DEFAULT_LOGIN,
                                    password=DEFAULT_PASSWORD, ext='.csv')
    except:
        return HttpResponse(u"Unable to download %(url)s" 
                            % {'url': download_url},
                            status=400)

    # 4. upload to bamboo
    try:
        upload_req = requests.post('%(root)s/datasets' % {'root': BAMBOO_URL}, 
                                   files={'dataset.csv': open(filename, 'rb')})
        uploaded = True
    except:
        uploaded = False
    finally:
        if upload_req.status_code not in (200, 201, 202) or not uploaded:
            return HttpResponse(u"Unable to upload data to bamboo.", 
                                status_code=502)

    # 5. retrieve dataset_id.
    try:
        json_response = json.loads(upload_req.text)
    except ValueError:
        return HttpResponse(u"Bamboo did not answer properly.", status=502)

    dataset_id = json_response.get('id', None)

    if not dataset_id:
        return HttpResponse(u"Bamboo did not returned an ID.", status=502)

    # 5. update dataset_id.
    bamboo_dataset = Option.objects.get_or_create(key='bamboo_dataset')
    bamboo_dataset.data = dataset_id
    bamboo_dataset.save()

    return HttpResponse(u"Sucessfuly updated data", status_code=202)