# encoding=utf-8

import json
import re

from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from dict2xml import dict2xml
from django.core.paginator import EmptyPage, PageNotAnInteger
from microsite.digg_paginator import FlynsarmyPaginator

from microsite.views import DEFAULT_IDS
from microsite.models import Project
from microsite.decorators import project_required
from microsite.barcode import b64_qrcode
from microsite.formhub import (submit_xml_forms_formhub,
                               ErrorUploadingDataToFormhub,
                               ErrorMultipleUploadingDataToFormhub)
from microsite.bamboo import (bamboo_query)

from soillab.spid_ssid import generate_ssids


@project_required
def samples_list(request, search_string=None):
    context = {}

    lookup = request.GET.get('lookup', None)

    # for now, look up will just forward to detail view
    if lookup:
        return sample_detail(request, lookup.strip())

    submissions_list = bamboo_query(request.user.project)

    for sub in submissions_list:
        if sub.get('sample_id_sample_barcode_id', 'n/a') == u'n/a':
            submissions_list.remove(sub)

    from pprint import pprint as pp ; pp(submissions_list)

    paginator = FlynsarmyPaginator(submissions_list, 20, adjacent_pages=2)

    page = request.GET.get('page')
    try:
        submissions = paginator.page(page)
    except PageNotAnInteger:
        submissions = paginator.page(1)
    except EmptyPage:
        submissions = paginator.page(paginator.num_pages)

    context.update({'samples': submissions,
                    'lookup': lookup})

    return render(request, 'samples_list.html', context)


@project_required
def sample_detail(request, sample_id):
    context = {}

    try:
        sample = bamboo_query(request.user.project,
                              query={'sample_id_sample_barcode_id': sample_id},
                              first=True)
    except:
        raise Http404(u"Requested Sample (%(sample)s) does not exist." 
                      % {'sample': sample_id})

    # from pprint import pprint as pp ; pp(sample)

    context.update({'sample': sample})
    
    return render(request, 'sample_detail.html', context)


def idgen(request, nb_ids=DEFAULT_IDS):

    context = {'category': 'idgen'}

    # hard-coded max number of IDs to gen.
    try:
        nb_ids = 100 if int(nb_ids) > 100 else int(nb_ids)
    except ValueError:
        nb_ids = DEFAULT_IDS

    all_ids = []
    
    # for i in xrange(0, nb_ids):
    for ssid in generate_ssids('NG'):
        # this is a tuple of (ID, B64_QRPNG)
        all_ids.append((ssid, b64_qrcode(ssid)))

    context.update({'generated_ids': all_ids})

    return render(request, 'idgen.html', context)


@require_POST
@csrf_exempt
def form_splitter(request, project_slug='soildoc'):
    ''' Master XForm to Sub XFrom

        1. Receives a grouped JSON POST from formhub containing A-Z sample data
        2. Extract and transform data for each sample into a new XForm
        3. Submits the resulting XForms to formhub. '''

    # we need a project to guess formhub URL
    try:
        project = Project.objects.get(slug=project_slug)
    except:
        project = Project.objects.all()[0]

    try:
        jsform = json.loads(request.raw_post_data)
    except:
        return HttpResponse(u"Unable to parse JSON data", status=400)

    # name of a field which if None marks the form as empty
    # we don't submit empty forms to formhub.
    # must be a suffixed field!
    EMPTY_VALUES = (None, u'n/a', u'')
    empty_trigger = 'sample_barcode_id'
    empty_forms = []

    # map field suffixes with IDs in holder
    indexes = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    # initialize holder for each form]
    forms = [{'single_letter': l} for l in indexes]

    for field, value in jsform.iteritems():
        # if fields ends in a-h, only add it to the specified form
        match = re.match(r'.*_([a-h])$', field)
        try:
            target_suffix = match.groups()[0]
        except:
            target_suffix = ''
        if match and target_suffix in indexes:
            # retrieve suffix, form and build target field (without suffix)
            form = forms[indexes.index(target_suffix)]
            target_field = field.rsplit('_%s' % target_suffix, 1)[0]

            # handle group field differently (parent holding the fields)
            if '/' in field:
                group, real_field = target_field.split('/', 1)
                # check for emptyness
                if real_field == empty_trigger and value in EMPTY_VALUES:
                    empty_forms.append(target_suffix)
                if not group in form:
                    form[group] = {}
                form[group].update({real_field: value})
            else:
                if field == empty_trigger and value in EMPTY_VALUES:
                    empty_forms.append(target_suffix)
                form.update({field: value})
        # otherwise, it's a common field, add to all
        else:
            for form in forms:
                # handle group field differently (parent holding the fields)
                if '/' in field:
                    group, real_field = field.split('/', 1)
                    if not group in form:
                        form[group] = {}
                    form[group].update({real_field: value})
                else:
                    form.update({field: value})

    del(jsform)

    # we now have a list of json forms each containing their data.
    def json2xform(jsform):
        # changing the form_id to XXX_single
        dd = {'form_id': u'%s_single' % jsform.get(u'_xform_id_string')}
        xml_head = u"<?xml version='1.0' ?><%(form_id)s id='%(form_id)s'>" % dd
        xml_tail = u"</%(form_id)s>" % dd

        for field in jsform.keys():
            # treat field starting with underscore are internal ones.
            # and remove them
            if field.startswith('_'):
                jsform.pop(field)
        
        return xml_head + dict2xml(jsform) + xml_tail

    xforms = [json2xform(forms[indexes.index(i)].copy()) 
              for i in indexes 
              if not i in empty_forms]

    try:
        submit_xml_forms_formhub(project, xforms, as_bulk=False)
    except (ErrorUploadingDataToFormhub, 
            ErrorMultipleUploadingDataToFormhub) as e:
        return HttpResponse(u"%(intro)s\n%(detail)s" 
                            % {'intro': e,
                               'detail': e.details()}, status=502)
    except Exception as e:
        return HttpResponse(str(e), status=500)

    return HttpResponse('OK', status=201)