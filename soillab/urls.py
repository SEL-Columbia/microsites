
from django.conf.urls import patterns, url
from django.views.generic.simple import direct_to_template

from soillab import views


FARMER_ID_REG = r''


urlpatterns = patterns('',

    url(r'^$', views.samples_list, name='home'),
    url(r'form_splitter$', views.form_splitter, name='xform_splitter'),
    url(r'form_splitter\?project=(?P<project_slug>[a-z\_\-0-9]+)$', views.form_splitter, name='xform_splitter_def'),
    url(r'samples/?$', views.samples_list, name='samples_list'),
    url(r'samples/(?P<sample_id>[a-zA-Z0-9\-]+)/?$',
        views.sample_detail, name='sample'),
    url(r'^about/?$', 
        direct_to_template, {'template': 'about.html',
                             'extra_context': {'category': 'about'}},
        name='about'),
    url(r'^idgen/(?P<nb_ids>[0-9]*)$', views.idgen, name='idgen'),
)
