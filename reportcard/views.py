
from django.shortcuts import render, redirect
from django.core.paginator import EmptyPage, PageNotAnInteger
from pybamboo.connection import Connection
from pybamboo.exceptions import BambooError

from constants import (REPORTS_AGE_GROUPS,
                       REPORTS_READING_LEVELS, REPORTS_NUMERACY_LEVELS)
from microsite.digg_paginator import FlynsarmyPaginator
from microsite.decorators import project_required
from microsite.barcode import (build_urlid_with,
                               short_id_from, detailed_id_dict, b64_qrcode)
from microsite.models import Project

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
from microsite.bamboo import (CachedDataset,
                              get_bamboo_url, get_bamboo_dataset_id)

DEFAULT_PROJECT = Project.objects.get(slug='reportcard')


@project_required(guests=DEFAULT_PROJECT)
def home(request):
    context = {'category': 'home'}

    connection = Connection(get_bamboo_url(request.user.project))
    main_dataset = CachedDataset(get_bamboo_dataset_id(request.user.project),
                                 connection=connection)
    teacher_dataset = CachedDataset(get_bamboo_dataset_id(request.user.project,
                                                          is_registration=True),
                                 connection=connection)

    # total number of submissions
    try:
        nb_submissions = int(main_dataset.count(u'general_information_age'))
    except BambooError as e:
        print(e)
        nb_submissions = None

    # total number of registered teachers
    try:
        nb_teachers = int(teacher_dataset.count(u'school_district'))
    except BambooError:
        nb_teachers = None

    context.update({'nb_submissions': nb_submissions,
                    'nb_teachers': nb_teachers})

    return render(request, 'home.html', context)


@project_required(guests=DEFAULT_PROJECT)
def list_submissions(request):

    context = {'category': 'submissions'}

    connection = Connection(get_bamboo_url(request.user.project))
    main_dataset = CachedDataset(get_bamboo_dataset_id(request.user.project),
                                 connection=connection)
    submissions_list = main_dataset.get_data(cache=True)

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


@project_required(guests=DEFAULT_PROJECT)
def list_teachers(request):

    context = {'category': 'teachers',
               'schoolcat': '%s|%s'
               % (request.user.project.slug, 'school_names')}

    # redirect to a teacher's page if jump_to matches one.
    jump_to = request.GET.get('jump_to', None)

    connection = Connection(get_bamboo_url(request.user.project))
    teacher_dataset = CachedDataset(get_bamboo_dataset_id(request.user.project,
                                                          is_registration=True),
                                 connection=connection)

    teachers_list = teacher_dataset.get_data(cache=True)

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
            school_list[teacher.get('school')] = [teacher, ]

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


@project_required(guests=DEFAULT_PROJECT)
def detail_teacher(request, uid):

    method = request.GET.get('method', 'django')

    view = detail_teacher_django \
           if method == 'django' else detail_teacher_bamboo
    return view(request, uid)


@project_required(guests=DEFAULT_PROJECT)
def detail_teacher_bamboo(request, uid):
    ''' Report Card View leveraging bamboo aggregation '''

    context = {'category': 'teachers',
               'schoolcat': '%s|%s'
               % (request.user.project.slug, 'school_names')}

    # retrieve short ID
    sid = request.GET.get('short', None)
    if not sid:
        sid = short_id_from(uid)

    # build barcode (identifier on submissions) from UID param.
    barcode = build_urlid_with(uid, sid)

    connection = Connection(get_bamboo_url(request.user.project))
    teacher_dataset = CachedDataset(get_bamboo_dataset_id(request.user.project,
                                                          is_registration=True),
                                 connection=connection)

    # Retrieve teacher data from bamboo (1req)
    teacher = teacher_dataset.get_data(query={'barcode': barcode})[0]

    context.update({'teacher': teacher})

    teacher.update(detailed_id_dict(teacher))

    return render(request, 'detail_teacher_bamboo.html', context)


@project_required(guests=DEFAULT_PROJECT)
def detail_teacher_django(request, uid):
    ''' Report Card View processing data from submissions list/data only

        2 bamboo requests:
            - teacher data from uuid
            - list of submissions for that teacher

        All processing/grouping done in python. '''

    context = {'category': 'teachers',
               'schoolcat': '%s|%s'
               % (request.user.project.slug, 'school_names')}

    connection = Connection(get_bamboo_url(request.user.project))
    main_dataset = CachedDataset(get_bamboo_dataset_id(request.user.project),
                                 connection=connection)
    teacher_dataset = CachedDataset(get_bamboo_dataset_id(request.user.project,
                                                          is_registration=True),
                                 connection=connection)

    def get_age_group(sub):
        ''' return age group (key str) of a given submission based on age'''
        for key, age_range in REPORTS_AGE_GROUPS.items():
            if (sub.get(u'general_information_age', 0)
             in range(age_range[0], age_range[1] + 1)):
                return key
        return u"all"

    def init_reports():
        ''' A reports container with initial values '''
        reports = {}
        for age_group in REPORTS_AGE_GROUPS.keys():
            reports[age_group] = {}
            for sex in ('male', 'female', 'total'):
                reports[age_group][sex] = {}
                for level in REPORTS_READING_LEVELS.keys() \
                             + REPORTS_NUMERACY_LEVELS.keys() + ['total']:
                    reports[age_group][sex][level] = {'nb': 0, 'percent': None}
        return reports

    def compute_report_for(reports, submission, is_numeracy=False):
        ''' increment counters on all categories for a submission '''

        age_group = get_age_group(submission)
        sex = submission.get('general_information_sex')
        level = submission.get('learning_levels_numeracy_nothing' if is_numeracy
                               else 'learning_levels_reading_nothing')

        #       AGE GRP    SEX     LEVEL
        reports['all']['total']['total']['nb'] += 1
        reports['all']['total'][level]['nb'] += 1

        reports['all'][sex]['total']['nb'] += 1
        reports['all'][sex][level]['nb'] += 1

        reports[age_group][sex][level]['nb'] += 1
        reports[age_group]['total'][level]['nb'] += 1
        reports[age_group][sex]['total']['nb'] += 1

        reports[age_group]['total']['total']['nb'] += 1

    def compute_percentages(reports):
        ''' calculates the percentages fields for the reports dict '''

        def pc(num, denum):
            try:
                return float(num['nb']) / float(denum['nb'])
            except ZeroDivisionError:
                return 0

        for age_group, ago in reports.items():
            for sex, so in ago.items():
                for level, lo in so.items():
                    reports[age_group][sex][level]['percent'] = \
                                            pc(reports[age_group][sex][level],
                                            reports[age_group][sex]['total'])

    def sort_reports(reports_dict):
        ''' sort report by Age (asc) then gender keeping total/All at last '''

        def cmp_rep(x, y):
            if x == y:
                return 0

            # 'all' age group is last
            if x == 'all' or y == 'all':
                return 1 if x == 'all' else -1
            # compare minimum age for group to sort
            xa_min = REPORTS_AGE_GROUPS.get(x, (100, 0))[0]
            ya_min = REPORTS_AGE_GROUPS.get(y, (100, 0))[0]
            return 1 if xa_min > ya_min else -1

        reports = []

        # loop on dict and transform to:
        #   - dicts composed of {'name': x, 'data': y}
        #   - data is an ordered array of dicts
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

    # retrieve short ID
    sid = request.GET.get('short', None)
    if not sid:
        sid = short_id_from(uid)

    # build barcode (identifier on submissions) from UID param.
    barcode = build_urlid_with(uid, sid)

    # Retrieve teacher data from bamboo (1req)
    teacher = teacher_dataset.get_data(query={'barcode': barcode})[0]
    teacher.update(detailed_id_dict(teacher))

    # retrieve list of submissions from bamboo (1req)
    submissions = main_dataset.get_data(
                               query={'$or': [{'teacher_barcode': barcode},
                                              {'teacher_fallback_ID': sid}]},
                               select=['general_information_age',
                                        'general_information_sex',
                                        'learning_levels_numeracy_nothing',
                                        'learning_levels_reading_nothing',
                                        'school_junior_secondary',
                                        'school_primary',
                                        'school_senior_secondary',
                                        'schooling_status_grades'])

    # initialize containers for reading report and numeracy report.
    reading_dict = init_reports()
    numeracy_dict = init_reports()

    # loop on submissions to fill reading/num reports
    for submission in submissions:
        compute_report_for(reading_dict, submission)
        compute_report_for(numeracy_dict, submission, is_numeracy=True)

    # compute percentages for reading/num reports
    compute_percentages(reading_dict)
    compute_percentages(numeracy_dict)

    # sort/transform reports for template
    reading_reports = sort_reports(reading_dict)
    numeracy_reports = sort_reports(numeracy_dict)

    context.update({'teacher': teacher,
                    'reading_reports': reading_reports,
                    'numeracy_reports': numeracy_reports})

    return render(request, 'detail_teacher.html', context)


@project_required(guests=DEFAULT_PROJECT)
def card_teacher(request, uid):

    context = {'category': 'teachers'}

    sid = short_id_from(uid)
    urlid = build_urlid_with(uid, sid)

    connection = Connection(get_bamboo_url(request.user.project))
    teacher_dataset = CachedDataset(get_bamboo_dataset_id(request.user.project,
                                                          is_registration=True),
                                 connection=connection)
    teacher = teacher_dataset.get_data(query={'barcode': urlid})[0]

    teacher.update(detailed_id_dict(teacher))
    teacher.update({'qrcode': b64_qrcode(urlid, scale=2.0)})

    context.update({'teacher': teacher})

    return render(request, 'card_teacher.html', context)


@project_required(guests=DEFAULT_PROJECT)
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
