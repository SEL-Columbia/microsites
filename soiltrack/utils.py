#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from microsite.models import Option


def ensure_fixtures_ready(project):
    ''' Check if required fixture exist and import if not. '''

    fixtures = [
        (u'ests1_dataset', u"ESTS Step #1 Dataset", u""),
        (u'ests2_dataset', u"ESTS Step #2 Dataset", u""),
        (u'ests3_dataset', u"ESTS Step #3 Dataset", u""),
        (u'ests4_dataset', u"ESTS Step #4 Dataset", u""),
        (u'ests5_dataset', u"ESTS Step #5 Dataset", u""),
        (u'ests6_dataset', u"ESTS Step #6 Dataset", u""),

        (u'ests1_form', u"ESTS Step #1 Formhub Form", 
         u"ESTS_1_send_field_to_PC"),
        (u'ests2_form', u"ESTS Step #2 Formhub Form", 
         u"ESTS_2_arrive_at_PC_from_field"),
        (u'ests3_form', u"ESTS Step #3 Formhub Form", 
         u"ESTS_3_send_PC_to_NSTC"),
        (u'ests4_form', u"ESTS Step #4 Formhub Form", 
         u"ESTS_4_arrive_at_NSTC_from_PC"),
        (u'ests5_form', u"ESTS Step #5 Formhub Form", 
         u"ESTS_5_send_NSTC_to_Archive"),
        (u'ests6_form', u"ESTS Step #6 Formhub Form", 
         u"ESTS_6_arrive_at_Archive_from_NSTC"),
    ]

    for key, name, default_value in fixtures:
        if Option.objects.filter(project=project, key=key).count():
            continue
        Option.objects.create(project=project, key=key, 
                              name=name, value=default_value)
