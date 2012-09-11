# encoding=utf-8

from django.shortcuts import render, redirect
from django.core.paginator import EmptyPage, PageNotAnInteger

from microsite.digg_paginator import FlynsarmyPaginator
from microsite.decorators import project_required
from microsite.barcode import (build_urlid_with,
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
def farmers_list(request):
    context = {}

    return render(request, 'farmers_list.html', context)


@project_required
def farmer_plots(request, farmer_id):
    context = {}
    
    return render(request, 'farmer_plots.html', context)


@project_required
def plot_results(request, farmer_id, plot_num):
    context = {}
    
    return render(request, 'plot_results.html', context)