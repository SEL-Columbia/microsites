from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.conf import settings

from django.views.generic.simple import direct_to_template


admin.autodiscover()

urlpatterns = patterns('',

    # root is forwarded to DEFAULT_APP
    url(r'^', include('%(default)s.urls' % {'default': settings.DEFAULT_APP})),

        # django login
    # url(r'^login/$', 'django.contrib.auth.views.login',
    #     {'template_name': 'login.html'}, name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout',
        {'template_name': 'logout.html', 'next_page': '/'}, name='logout'),

    url(r'^login/$', 'microsite.views.login_greeter', name='login'),

    # default home
    url(r'^$', direct_to_template, {'template': 'home.html', 
                                    'extra_context': {'category': 'home'}},
        name='home'),

    # settings management
    url(r'^options/?$', 'microsite.views.options', name='options'),

    # default help page 
    url(r'^help/?$', 
        direct_to_template, {'template': 'help.html',
                             'extra_context': {'category': 'help'}},
        name='help'),

    url(r'^idgen/(?P<nb_ids>[0-9]*)$', 'microsite.views.idgen', name='idgen'),

    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
)
