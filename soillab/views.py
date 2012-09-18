# encoding=utf-8

import json
import re
from collections import OrderedDict

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

DEFAULT_PROJECT = Project.objects.get(slug='soildoc')


@project_required(guests=DEFAULT_PROJECT)
def samples_list(request, search_string=None):
    context = {}

    lookup = request.GET.get('lookup', None)

    # for now, look up will just forward to detail view
    if lookup:
        return sample_detail(request, lookup.strip())

    submissions_list = bamboo_query(request.user.project)
    submissions_list.sort(key=lambda x: x['end'], reverse=True)

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


@project_required(guests=DEFAULT_PROJECT)
def sample_detail(request, sample_id):
    context = {}

    try:
        sample = bamboo_query(request.user.project,
                              query={'sample_id_sample_barcode_id': sample_id},
                              first=True)
    except:
        raise Http404(u"Requested Sample (%(sample)s) does not exist." 
                      % {'sample': sample_id})

    results = soil_results(sample)

    from pprint import pprint as pp ; pp(sample)

    context.update({'sample': sample,
                    'results': results})
    
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

    def field_splitter(field):
        match = re.match(r'.*_([a-h])$', field)
        if match:
            try:
                suffix = match.groups()[0]
            except:
                suffix = None
            if suffix:
                field = field.rsplit('_%s' % suffix, 1)[0]
            return (field, suffix)
        else:
            return (field, None)

    # name of a field which if None marks the form as empty
    # we don't submit empty forms to formhub.
    # must be a suffixed field!
    AVAIL_SUFFIXES = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    empty_trigger = 'sample_id_$$/sample_barcode_id_$$'

    # map field suffixes with IDs in holder
    # we exclude forms with no data on trigger field so it won't be process
    # nor sent to formhub
    indexes = [l for l in AVAIL_SUFFIXES 
                 if jsform.get(empty_trigger.replace('$$', l), None)]

    # initialize holder for each form]
    forms = [{'single_letter': l} for l in indexes]

    for field, value in jsform.iteritems():
        # if fields ends in a-h, only add it to the specified form
        target_field, target_suffix = field_splitter(field)

        if target_suffix in indexes:
            # retrieve suffix, form and build target field (without suffix)
            form = forms[indexes.index(target_suffix)]

            # handle group field differently (parent holding the fields)
            if '/' in field:
                group, real_field = target_field.split('/', 1)
                real_group, group_suffix = field_splitter(group)
                if not real_group in form:
                    form[real_group] = {}
                form[real_group].update({real_field: value})
            else:
                form.update({field: value})
        # otherwise, it's a common field, add to all
        else:
            for form in forms:
                # handle group field differently (parent holding the fields)
                if '/' in field:
                    group, real_field = field.split('/', 1)
                    real_group, group_suffix = field_splitter(group)
                    if not real_group in form:
                        form[real_group] = {}
                    form[real_group].update({real_field: value})
                else:
                    form.update({target_field: value})

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

    xforms = [json2xform(forms[indexes.index(i)].copy()) for i in indexes]

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


def soil_results(sample):

    def level_in_range(value, levels):
        for max_value, level in levels.iteritems():
            if not isinstance(max_value, (int, float)):
                return level
            if value < max_value:
                return level
        return levels[-1]

    # initialize results dict with labels
    n = 'name'
    v = 'value'
    b = 'badge'
    lvl = 'level_text'
    lvlt = 'level_text_verbose'

    lvlel = u"Extremely Low"
    lvlvl = u"Very Low"
    lvll = u"Low"
    lvlm = u"Medium"
    lvlmh = u"Medium/High"
    lvlh = u"High"
    lvlvh = u"Very High"
    lvlg = u"Good"
    lvlo = u"Optimal"
    lvlb = u"No Data"

    bvl = 'important' # very low
    bvh = 'important' # very high
    bl = 'warning' # low
    bh = 'warning' # high
    bh = 'warning' # high
    bn = 'info' # neutral
    bg = 'success' # good
    bb = 'inverse' # blank

    # initialize the result dict for ordering.
    results = OrderedDict([
        ('ec', {n: u"EC", v: 0, b: bb, lvl: lvlb}),
        ('ph_water', {n: u"pH Water", v: 0, b: bb, lvl: lvlb}),
        ('ph_cacl', {n: u"pH Salt", v: 0, b: bb, lvl: lvlb}),
        ('delta_ph', {n: u"Δ pH", v: 0, b: bb, lvl: lvlb}),
        ('soil_bulk_density', {n: u"Soil Bulk Density", v: 0, b: bb, lvl: lvlb}),
        ('soil_moisture', {n: u"Soil Moisture at Sampling", v: 0, b: bb, lvl: lvlb}),
        ('soil_nitrate', {n: u"Soil Nitrate", v: 0, b: bb, lvl: lvlb}),
        ('soil_potassium', {n: u"Soil Potassium", v: 0, b: bb, lvl: lvlb}),
        ('soil_phosphorus', {n: u"Soil Phosphorus", v: 0, b: bb, lvl: lvlb}),
        ('soil_sulfate', {n: u"Soil Sulfate", v: 0, b: bb, lvl: lvlb}),
        # ('soil_organic_matter', {n: u"Soil Organic Matter", v: 0, b: bb, lvl: lvlb}),
    ])

    #
    # EC GROUP
    #
    soil_units = {
        'microseimens_per_cm': 1000,
        'parts_per_million': 640,
        'milliseimens_per_cm': 0.001,
        'decisiemens_per_meter': 1,
        'mmhos_per_cm': 1,
    }

    ec_levels = OrderedDict([
        (0.1, {b: bl, lvl: lvll, lvlt: u"Low fertility, leached nutrients."}),
        (0.3, {b: bn, lvl: lvlm, lvlt: u"Medium fertility, especially in acid soils."}),
        (0.6, {b: bn, lvl: lvlm, lvlt: u"Slightly saline. Limiting for salt-sensitive crops."}),
        (1.2, {b: bh, lvl: lvlh, lvlt: u"Very saline. Limiting for salt-sensitive crops. Some intolerance for salt-enduring crops."}),
        (2.4, {b: bh, lvl: lvlh, lvlt: u"Severe salinity. Strong limitations for both salt-sensitive and tolerant crops."}),
        (4.0, {b: bvh, lvl: lvlvh, lvlt: u"Very severe salinity. Few crops survive."}),
        ('_', {b: bvh, lvl: lvlvh, lvlt: u"Very few crops can grow."}),
        ])

    try:
        soil_ec = sample.get('ec_sample_ec', None) - sample.get('ec_sample_water_ec', None)
    except:
        soil_ec = None

    try:
        results['ec'][v] = soil_ec * soil_units.get('ec_units', 1)
    except:
        results['ec'][v] = None

    # update badge levels
    if results['ec'][v]:
        results['ec'].update(level_in_range(results['ec'][v], ec_levels))

    #
    # pH H2O
    #
    results['ph_water'][v] = sample.get('ph_water_sample_ph_water', None)

    #
    # pH CaCl
    #
    ph_cacl_levels = OrderedDict([
        (4.0, {b: bl, lvl: lvll, lvlt: u"pH is limiting: soil exhibits severe aluminum toxicity"}),
        (5.0, {b: bl, lvl: lvll, lvlt: u"pH is limiting: soil exhibits aluminum and manganese toxicity."}),
        (5.5, {b: bn, lvl: lvlm, lvlt: u"pH is somewhat limiting."}),
        (6.5, {b: bg, lvl: lvlo, lvlt: u"Optimal pH for good plant productivity."}),
        (7.5, {b: bh, lvl: lvlh, lvlt: u"pH is not limiting. However, may be Fe, Mn, Zn deficiencies in sandy soils."}),
        (8.5, {b: bh, lvl: lvlh, lvlt: u"pH is somewhat limiting (calcareous soil). Will likely observe Fe, Mn, Zn, deficiencies."}),
        ('_', {b: bvh, lvl: lvlvh, lvlt: u"Severe pH limitations with sodium problems (sodic)"}),
        ])

    results['ph_cacl'][v] = sample.get('ph_cacl2_sample_ph_cacl2', None)

     # update badge levels
    if results['ph_cacl'][v]:
        results['ph_cacl'].update(level_in_range(results['ph_cacl'][v], ph_cacl_levels))

    #
    # Δ pH
    #
    try:
        results['delta_ph'][v] = (sample.get('ph_water_sample_ph_water') 
                                  - sample.get('ph_cacl2_sample_ph_cacl2'))
    except:
        results['delta_ph'][v] = None

    #
    # soil bulk density
    #
    soil_densities = {
        'coarse': 1.6,
        'moderately_coarse': 1.4,
        'medium': 1.2,
        'fine': 1.0
    }
    results['soil_bulk_density'][v] = soil_densities.get(sample.get('sample_id_sample_soil_texture', None), None)

    # TODO: find out which fields.
    # percent moisture by weight
    # 3 fields of testing averaged.
    moisture_values = ['sample_id_sample_soil_moisture', ]
    for field in moisture_values:
        if sample.get(field, None) is None:
            moisture_values.pop(field)
    percent_moisture_by_weight = results['soil_moisture'][v] # sum([sample.get(x, 0.0) for x in moisture_values], 0.0) / len(moisture_values)

    #
    # soil moisture at sampling
    #
    try:
        results['soil_moisture'][v] = (sample.get('sample_id_sample_automated_soil_moisture') 
                                       / results['soil_bulk_density'][v])
    except:
        results['soil_moisture'][v] = None

    #
    # soil nitrate
    #
    nitrate_fertility_levels = OrderedDict([
        (21, {b: bvl, lvl: lvlvl, lvlt: u"Yes-Full N recommended."}),
        (42, {b: bl, lvl: lvll, lvlt: u"Yes-3/4 N recommended."}),
        (65, {b: bn, lvl: lvlm, lvlt: u"Yes-1/2 N recommended."}),
        (90, {b: bh, lvl: u"Medium/High", lvlt: u"Yes, 1/4 N recommended."}),
        (120, {b: bh, lvl: lvlh, lvlt: u"No N more recommended."}),
        ('_', {b: bvh, lvl: lvlvh, lvlt: u"No N recommended."}),
        ])

    try:
        results['soil_nitrate'][v] = (
            (sample.get('nitrate_sample_nitrate') 
             - sample.get('nitrate_blank_nitrate')) 
            * (30 / (1 - (percent_moisture_by_weight * 15))) )
    except:
        results['soil_nitrate'][v] = None

     # update badge levels
    if results['soil_nitrate'][v]:
        results['soil_nitrate'].update(level_in_range(results['soil_nitrate'][v], nitrate_fertility_levels))

    #
    # soil potassium
    #
    potassium_fertility_levels = OrderedDict([
        (30, {b: bvl, lvl: lvlvl, lvlt: u"K fertilizer needed: Very Likely."}),
        (60, {b: bl, lvl: lvll, lvlt: u"K fertilizer needed: Likely."}),
        (90, {b: bn, lvl: lvlm, lvlt: u"K fertilizer needed: 50/50."}),
        (120, {b: bh, lvl: lvlh, lvlt: u"K fertilizer needed: Unlikely."}),
        ('_', {b: bvh, lvl: lvlvh, lvlt: u"No K fertilizer needed."}),
        ])

    try:
        results['soil_potassium'][v] = (
            (sample.get('potassium_sample_potassium') 
             - sample.get('potassium_blank_potassium')) 
            * (30 / (1 - (percent_moisture_by_weight * 15))) )
    except:
        results['soil_potassium'][v] = None

     # update badge levels
    if results['soil_potassium'][v]:
        results['soil_potassium'].update(level_in_range(results['soil_potassium'][v], potassium_fertility_levels))

    #
    # soil phosphorus
    #
    phosphorus_fertility_levels = OrderedDict([
        (0.05, {b: bvl, lvl: lvlel, lvlt: u"Increasing P is top priority."}),
        (0.1, {b: bvl, lvl: lvlvl, lvlt: u"P fertilizer needed: Very Likely."}),
        (0.3, {b: bl, lvl: lvll, lvlt: u"P fertilizer needed: Likely."}),
        (0.5, {b: bn, lvl: lvlm, lvlt: u"P fertilizer needed: 50/50 chance of response."}),
        ('_', {b: bh, lvl: lvlh, lvlt: u"No P fertilizer needed."}),
        ])

    try:
        soil_phosphorus_ppb = ((sample.get('phosphorus_ppb_meter_blank_phosphorus_ppb_meter', None) 
                                - sample.get('phosphorus_ppb_meter_blank_phosphorus_ppb_meter', None))
                               * (10 / 2) 
                               * ( 30 / 
                                  (1 - (percent_moisture_by_weight * 15))) )
    except:
        soil_phosphorus_ppb = None

    try:
        soil_phosphorus_ppm = ((sample.get('phosphorus_ppm_meter_sample_phosphorus_ppm_meter', None)
                                - sample.get('phosphorus_ppm_meter_blank_phosphorus_ppm_meter'))
                               * (10 / 2) 
                               * (30 / (1 - (percent_moisture_by_weight * 15)))
                               * (30.97 / 94.97))
    except:
        soil_phosphorus_ppm = None

    # PPB measure is preffered over PPM but might not be available.
    if soil_phosphorus_ppb is None:
        results['soil_phosphorus'][v] = soil_phosphorus_ppm
    else:
        results['soil_phosphorus'][v] = soil_phosphorus_ppb

     # update badge levels
    if results['soil_phosphorus'][v]:
        results['soil_phosphorus'].update(level_in_range(results['soil_phosphorus'][v], phosphorus_fertility_levels))

    #
    # soil sulfate
    #
    sulfate_fertility_levels = OrderedDict([
        (10, {b: bvl, lvl: lvlvl, lvlt: u"S fertilizer needed: Very Likely."}),
        (15, {b: bl, lvl: lvll, lvlt: u"S fertilizer needed: Likely."}),
        (20, {b: bn, lvl: lvlm, lvlt: u"S fertilizer needed: 50/50 chance of response."}),
        ('_', {b: bh, lvl: lvlh, lvlt: u"No S fertilizer needed."}),
        ])

    try:
        slope_low_spike_ppb = 6 / sample.get('sulfur_ppb_meter_blank_sulfur_vial_ppb', None)
    except:
        slope_low_spike_ppb = None

    try:
        slope_high_spike_ppm = 16 / sample.get('sulfur_ppm_meter_high_spike_sulfur_analysis_vial_ppm', None)
    except:
        slope_high_spike_ppm = None

    try:
        soil_sulfur_ppb =  (
                            ((sample.get('sulfur_ppb_meter_sample_sulfur_ppb_meter', None) * slope_low_spike_ppb)
                              - sample.get('sulfur_ppb_meter_blank_sulfur_ppb_meter', None))
                            * (sample.get('sulfur_analysis_sample_sulfur_analysis_vial_water', None) / sample.get('sulfur_analysis_sample_sulfur_analysis_vial_extract', None))
                            * (30 / (1 - (percent_moisture_by_weight * 15)))
                           )
    except:
        soil_sulfur_ppb = None

    try:
        soil_sulfur_ppm = (
                            ((sample.get('sulfur_ppm_meter_sample_sulfur_ppm_meter', None) * slope_high_spike_ppm)
                              - sample.get('sulfur_ppm_meter_blank_sulfur_ppm_meter', None))
                            * (sample.get('sulfur_analysis_sample_sulfur_analysis_vial_water', None) / sample.get('sulfur_analysis_sample_sulfur_analysis_vial_extract', None))
                            * (30 / (1 - (percent_moisture_by_weight * 15)))
                           )
    except:
        soil_sulfur_ppm = None

    # PPB measure is preffered over PPM but might not be available.
    if soil_sulfur_ppb is None:
        results['soil_sulfate'][v] = soil_sulfur_ppm
    else:
        results['soil_sulfate'][v] = soil_sulfur_ppb

     # update badge levels
    if results['soil_sulfate'][v]:
        results['soil_sulfate'].update(level_in_range(results['soil_sulfate'][v], sulfate_fertility_levels))

    # soil organic matter
    # no input

    return results