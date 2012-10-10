
from django.conf.urls import patterns, url
from django.views.generic.simple import direct_to_template

from soiltrack import views


urlpatterns = patterns('',

    url(r'^$', views.dashboard, name='home'),
    url(r'^about/?$', 
        direct_to_template, {'template': 'about.html',
                             'extra_context': {'category': 'about'}},
        name='about'),
    # overwrite idgen to change ID scheme
    url(r'^idgen/(?P<nb_ids>[0-9]*)$', views.idgen, name='idgen'),
    # overwrite settings management to getset bamboo datasets
    url(r'^options/?$', views.options, name='options'),
)
