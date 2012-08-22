
import json

import requests
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.core.paginator import EmptyPage, PageNotAnInteger

from constants import FORMHUB_URL, DEFAULT_LOGIN, DEFAULT_PASSWORD, BAMBOO_URL
from microsite.utils import download_formhub
from microsite.digg_paginator import FlynsarmyPaginator
from microsite.models import Option
from microsite.decorators import project_required
from microsite.barcode import (build_urlid_with, get_ids_from_url,
                               short_id_from, detailed_id_dict, b64_qrcode)
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
def list_submissions(request):

    context = {'category': 'submissions'}

    submissions_list = bamboo_query(request.user.project)

    for submission in submissions_list:
        submission.update(detailed_id_dict(submission, prefix='teacher_'))

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
               'schoolcat': '%s|%s' 
               % (request.user.project.slug, 'school_names')}

    # redirect to a teacher's page if jump_to matches one.
    jump_to = request.GET.get('jump_to', None)

    teachers_list = bamboo_query(request.user.project,
                                 is_registration=True)

    ''' Not using the `group` method of bamboo here as it's innefiscient
        for our use case: it would request multiple inner-loops and uglify
        the templates.

        Instead, we grab the raw list of teachers and then group them
        by the school name resulting in a 2-dim list.

        While it works, I believe the pagination is done at school level
        making it useless for cases where there are many teachers per school '''

    # school list container ; each key should contain list of teachers.
    school_list = {}

    for teacher in teachers_list:
        if not teacher.get('barcode', None):
            continue

        teacher.update(detailed_id_dict(teacher))

        # requested teacher exists ; redirect
        if teacher.get('sid_') == jump_to:
            return redirect(detail_teacher, uid=teacher.get('uid_'))

        if teacher.get('school') in school_list:
            school_list.get(teacher.get('school')).append(teacher)
        else:
            school_list[teacher.get('school')] = [teacher,]

    paginator = FlynsarmyPaginator(school_list.values(), 10, adjacent_pages=2)

    page = request.GET.get('page', 1)
    try:
        schools = paginator.page(page)
    except PageNotAnInteger:
        schools = paginator.page(1)
    except EmptyPage:
        schools = paginator.page(paginator.num_pages)

    # context.update({'teachers': teachers})
    context.update({'schools': schools})

    return render(request, 'list_teachers.html', context)


@project_required
def detail_teacher(request, uid):

    method = request.GET.get('method', 'django')

    view = detail_teacher_django \
           if method == 'django' else detail_teacher_bamboo
    return view(request, uid)


def detail_teacher_bamboo(request, uid):
    ''' Report Card View leveraging bamboo aggregation '''
    return HttpResponse(u"Not Implemented")


def detail_teacher_django(request, uid):

    ''' Report Card View processing data from submissions list/data only '''

    context = {'category': 'teachers',
               'schoolcat': '%s|%s' 
               % (request.user.project.slug, 'school_names')}

    sid = request.GET.get('short', None)
    if not sid:
        sid = short_id_from(uid)

    barcode = build_urlid_with(uid, sid)

    teacher = bamboo_query(request.user.project,
                           query={'barcode': barcode},
                           first=True,
                           is_registration=True)
    teacher.update(detailed_id_dict(teacher))


    age_groups = {
        u"6-9": (6, 9),
        u"10-11": (10, 11),
        u"12-14": (12, 14),
        u"15-17": (15, 17),
        u"all": (18, 99),
    }

    reading_levels = {
        'learning_levels_literacy_nothing': u"Nothing",
        'learning_levels_literacy_letters': u"Letters",
        'learning_levels_literacy_words': u"Words",
        'learning_levels_literacy_paragraphs': u"Paragraphs",
        'learning_levels_literacy_story': u"Story",
    }

    numeracy_levels = {
        'learning_levels_numeracy_nothing': u"Nothing",
        'learning_levels_numeracy_num_recognition_1_9': u"1 to 9",
        'learning_levels_numeracy_num_recognition_10_99': u"10 to 99",
        'learning_levels_numeracy_subtraction': u"Substractions",
        'learning_levels_numeracy_division': u"Divisions",

    }

    def get_age_group(sub):
        for key, age_range in age_groups.items():
            if (sub.get(u'general_information_age', 0)
             in range(age_range[0], age_range[1] + 1)):
                return key
        return u"all"


    def init_reports():
        reports = {}
        for age_group in age_groups.keys():
            reports[age_group] = {}
            for sex in ('male', 'female', 'total'):
                reports[age_group][sex] = {}
                for level in reading_levels.keys() \
                             + numeracy_levels.keys() + ['total']:
                    reports[age_group][sex][level] = {'nb': 0, 'percent': 0}
        return reports

    def compute_report_for(reports, submission):

        age_group = get_age_group(submission)
        sex = submission.get('general_information_sex')
        level = submission.get('learning_levels_reading_nothing')

        #       AGE GRP    SEX     LEVEL
        reports['all']['total']['total']['nb'] += 1
        reports['all']['total'][level]['nb'] += 1

        reports['all'][sex]['total']['nb'] += 1
        reports['all'][sex][level]['nb'] += 1

        reports[age_group][sex][level]['nb'] += 1
        reports[age_group][sex]['total']['nb'] += 1
        reports[age_group]['total']['total']['nb'] += 1

    submissions = bamboo_query(request.user.project,
                               query={'teacher_barcode': barcode},
                               select={'general_information_age': 1,
                                        'general_information_sex': 1,
                                        'learning_levels_numeracy_nothing': 1,
                                        'learning_levels_reading_nothing': 1,
                                        'school_junior_secondary': 1,
                                        'school_primary': 1,
                                        'school_senior_secondary': 1,
                                        'schooling_status_grades': 1})

    reports_dict = init_reports()

    for submission in submissions:
        compute_report_for(reports_dict, submission)

    def sort_reports(reports_dict):
        def cmp_rep(x, y):
            if x == y:
                return 0
            if x == 'all' or y == 'all':
                return 1 if x == 'all' else -1
            xa_min = age_groups.get(x, (100, 0))[0]
            ya_min = age_groups.get(y, (100, 0))[0]
            return 1 if xa_min > ya_min else -1

        reports = []

        for age_group in sorted(reports_dict.keys(), cmp=cmp_rep):
            age_group_data = reports_dict.get(age_group)
            age_group_data.update({'name': age_group})
            age_group_sex = []
            for sex in sorted(age_group_data.keys()):
                if sex == 'name':
                    continue
                sex_data = age_group_data.get(sex)
                sex_data.update({'name': sex})
                age_group_sex.append(sex_data)
            reports.append({'name': age_group,
                            'data': age_group_sex})

        return reports

    reports = sort_reports(reports_dict)

    context.update({'teacher': teacher,
                    'reports': reports})

    return render(request, 'detail_teacher.html', context)


@project_required
def card_teacher(request, uid):

    context = {'category': 'teachers'}

    sid = short_id_from(uid)
    urlid = build_urlid_with(uid, sid)

    teacher = bamboo_query(request.user.project,
                           query={'barcode': urlid},
                           first=True,
                           is_registration=True)

    teacher.update(detailed_id_dict(teacher))
    teacher.update({'qrcode': b64_qrcode(urlid)})

    context.update({'teacher': teacher})

    return render(request, 'card_teacher.html', context)


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
    uid = json_data.get('formhub/uuid', None)
    userform_id = json_data.get('_userform_id', None)

    # we might be interested in going this way in the future
    # but it's not implemented in FH yet.
    if uid and False:
        download_url = ('%(root)s/forms/%(uuid)s/data.csv' 
                        % {'root': FORMHUB_URL, 'uuid': uid})
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