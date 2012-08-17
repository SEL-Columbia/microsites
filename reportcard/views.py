
import json

import requests
from django.http import HttpResponse
from django.shortcuts import render
from django.core.paginator import EmptyPage, PageNotAnInteger

from constants import FORMHUB_URL, DEFAULT_LOGIN, DEFAULT_PASSWORD, BAMBOO_URL
from microsite.utils import download_formhub
from microsite.digg_paginator import FlynsarmyPaginator
from microsite.models import Option
from microsite.decorators import project_required
from microsite.barcode import get_ids_from_url, short_id_from
from microsite.bamboo import (ErrorRetrievingBambooData,
                              count_submissions, bamboo_query)
from microsite.formhub import (get_formhub_form_url, get_formhub_form_api_url,
                               get_formhub_form_public_api_url,
                               get_formhub_form_datacsv_url,
                               get_formhub_form_dataxls_url,
                               get_formhub_form_datakml_url,
                               get_formhub_form_datazip_url,
                               get_formhub_form_gdocs_url,
                               get_formhub_form_map_url,
                               get_formhub_form_instance_url,
                               get_formhub_form_dataentry_url,
                               get_formhub_form_dataview_url,
                               get_formhub_form_formxml_url,
                               get_formhub_form_formxls_url,
                               get_formhub_form_formjson_url)


@project_required
def home(request):
    context = {'category': 'home'}

    # total number of submissions
    try:
        nb_submissions = int(count_submissions(request.user.project,
                                           u'general_information_age'))
    except ErrorRetrievingBambooData:
        nb_submissions = None

    # total number of registered teachers
    try:
        nb_teachers = count_submissions(request.user.project,
                                        u'school_district',
                                        is_registration=True)
    except ErrorRetrievingBambooData:
        nb_teachers = None

    context.update({'nb_submissions': nb_submissions,
                    'nb_teachers': nb_teachers})

    return render(request, 'home.html', context)


@project_required
def list_reports(request):

    context = {'category': 'reports'}

    reports_list = [{'name': u"Kabuyanda P.S",},
                    {'name': u"Markala Zanbugu"},
                    {'name': u"Les mots"}]

    paginator = FlynsarmyPaginator(reports_list, 10, adjacent_pages=2)

    page = request.GET.get('page')
    try:
        reports = paginator.page(page)
    except PageNotAnInteger:
        reports = paginator.page(1)
    except EmptyPage:
        reports = paginator.page(paginator.num_pages)

    context.update({'classes': reports})

    return render(request, 'list_classes.html', context)


@project_required
def list_submissions(request):

    context = {'category': 'submissions'}

    submissions_list = [{'name': u"Kabuyanda P.S",},
                        {'name': u"Markala Zanbugu"},
                        {'name': u"Les mots"}]

    paginator = FlynsarmyPaginator(submissions_list, 10, adjacent_pages=2)

    page = request.GET.get('page')
    try:
        submissions = paginator.page(page)
    except PageNotAnInteger:
        submissions = paginator.page(1)
    except EmptyPage:
        submissions = paginator.page(paginator.num_pages)

    context.update({'submissions': submissions})

    return render(request, 'list_submissions.html', context)


@project_required
def list_teachers(request):

    context = {'category': 'teachers',
               'keycat': '%s|%s' % (request.user.project.slug, 'school_names')}

    teachers_list = bamboo_query(request.user.project,
                                 is_registration=True)

    for index, teacher in enumerate(teachers_list):
        if not teacher.get('barcode', None):
            continue
        
        try:
            uid, sid = get_ids_from_url(teacher.get('barcode', ''))
        # in case barcode is uuid and not urlid
        except ValueError:
            uid = teacher.get('barcode')
            sid = short_id_from(uid)
        
        teacher['uid_'] = teacher.get('barcode', None)
        teacher['short_id_'] = sid
        teachers_list[index] = teacher

    # sort by name
    teachers_list.sort(key=lambda t: t['tchr_name'])

    paginator = FlynsarmyPaginator(teachers_list, 10, adjacent_pages=2)

    page = request.GET.get('page')
    try:
        teachers = paginator.page(page)
    except PageNotAnInteger:
        teachers = paginator.page(1)
    except EmptyPage:
        teachers = paginator.page(paginator.num_pages)

    context.update({'teachers': teachers})

    return render(request, 'list_teachers.html', context)


@project_required
def detail_teacher(request, uuid, sid):

    context = {'category': 'teachers'}

    teacher = bamboo_query(request.user.project,
                           query={'barcode': uuid},
                           first=True,
                           is_registration=True)

    context.update({'teacher': teacher})

    return render(request, 'detail_teacher.html', context)


@project_required
def form(request):

    context = {'category': 'form'}

    context.update({
        'form_url': get_formhub_form_url(request.user.project),
        'form_api_url': get_formhub_form_api_url(request.user.project),
        'form_public_api_url': 
                          get_formhub_form_public_api_url(request.user.project),
        'form_datacsv_url': get_formhub_form_datacsv_url(request.user.project),
        'form_dataxls_url': get_formhub_form_dataxls_url(request.user.project),
        'form_datakml_url': get_formhub_form_datakml_url(request.user.project),
        'form_datazip_url': get_formhub_form_datazip_url(request.user.project),
        'form_gdocs_url': get_formhub_form_gdocs_url(request.user.project),
        'form_map_url': get_formhub_form_map_url(request.user.project),
        'form_instance_url': 
                            get_formhub_form_instance_url(request.user.project),
        'form_dataentry_url': 
                           get_formhub_form_dataentry_url(request.user.project),
        'form_dataview_url': 
                            get_formhub_form_dataview_url(request.user.project),
        'form_formxml_url': get_formhub_form_formxml_url(request.user.project),
        'form_formxls_url': get_formhub_form_formxls_url(request.user.project),
        'form_formjson_url': 
                            get_formhub_form_formjson_url(request.user.project),
        })

    return render(request, 'form.html', context)


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