#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: ai ts=4 sts=4 et sw=4 nu

from microsite.models import Option


def ensure_fixtures_ready(project):
    ''' Check if required fixture exist and import if not. '''

    fixtures = [
        (u'ests_dataset', u"ESTS Joined Dataset", u""),
    ]

    for key, name, default_value in fixtures:
        if Option.objects.filter(project=project, key=key).count():
            continue
        Option.objects.create(project=project, key=key,
                              name=name, value=default_value)
