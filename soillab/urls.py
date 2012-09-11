
from django.conf.urls import patterns, url
from django.views.generic.simple import direct_to_template

from soillab import views


FARMER_ID_REG = r'(?P<farmer_id>[a-zA-Z0-9]+)'


urlpatterns = patterns('',

    url(r'farmers', views.farmers_list, name='farmers'),
    url(r'farmers/' + FARMER_ID_REG, views.farmer_plots, name='farmer_plots'),
    url(r'farmers/' + FARMER_ID_REG + '/(?P<plot_num>[0-9]+)', views.plot_results, name='plot'),
    url(r'^about/?$', 
        direct_to_template, {'template': 'about.html',
                             'extra_context': {'category': 'about'}},
        name='about'),
)
