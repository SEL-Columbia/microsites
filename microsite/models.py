# encoding=utf-8

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _, ugettext

from microsite.utils import dump_json, load_json


class Project(models.Model):

    slug = models.SlugField(max_length=30, primary_key=True)

    name = models.CharField(max_length=100)

    description = models.TextField(blank=True, null=True,
                                   verbose_name=_(u"description"),
                                   help_text=_(u"About the project"))

    def __unicode__(self):
        return self.name


def add_default_options(sender, instance, created, **kwargs):
    if created:
        fixtures = [
            ('bamboo_uri', u"bamboo URI", 'http://bamboo.io'),
            ('bamboo_dataset', u"bamboo dataset for data", ''),
            ('bamboo_ids_dataset', u"bamboo dataset for IDs", ''),
            ('formhub_uri', u"formhub URI", 'https://formhub.org'),
            ('formhub_user', u"formhub User owning form for data", ''),
            ('formhub_form', u"formhub Form slug for data", ''),
            ('formhub_ids_user', u"formhub User owning form for IDs", ''),
            ('formhub_ids_form', u"formhub Form slug for IDs", '')]
        for fixture in fixtures:
            option = Option(key=fixture[0],
                            name=fixture[1],
                            project=instance)
            option.value = fixture[2]
            option.save()


class Option(models.Model):

    class Meta:
        app_label = 'microsite'
        verbose_name = _(u"Option")
        verbose_name_plural = _(u"Options")
        unique_together = (('key', 'project',),)

    key = models.CharField(max_length=75, primary_key=True,
                           verbose_name=_(u"Key"))
    json_value = models.TextField(blank=True, null=True,
                                  verbose_name=_(u"Value"),
                                  help_text=_(u"JSON formated value."))
    name = models.CharField(max_length=70, blank=True,
                            null=True, help_text=_(u"Option description"))

    project = models.ForeignKey(Project, blank=True,
                                null=True, related_name='options')

    def __unicode__(self):
        return self.key

    def get_value(self):
        if self.json_value:
            return load_json(self.json_value, None)
        return ''
    
    def set_value(self, value):
        self.json_value = dump_json(value)
        
    value = property(get_value, set_value)


class KeyNamePair(models.Model):

    class Meta:
        app_label = 'microsite'
        verbose_name = _(u"Key-Name Pair")
        verbose_name_plural = _(u"Key-Name Pairs")
        unique_together = ('project', 'namespace', 'key')

    project = models.ForeignKey(Project)
    namespace = models.SlugField(max_length=75, verbose_name=_(u"Namespace"),
                                 help_text=_(u"Name of your set"))
    key = models.SlugField(max_length=200, verbose_name=_(u"Key"),
                           help_text=_(u"Identifier of the string"))
    name = models.CharField(max_length=70, blank=True,
                            null=True, help_text=_(u"Correct representation"))

    def __unicode__(self):
        return (ugettext(u"%(cat)s/%(key)s") 
                         % {'key': self.key, 'cat': self.namespace})


class MicrositeUser(models.Model):

    class Meta:
        app_label = 'microsite'
        verbose_name = _(u"User")
        verbose_name_plural = _(u"Users")

    user = models.OneToOneField(User, unique=True, verbose_name=_(u"User"))

    project = models.ForeignKey(Project, null=True, related_name='users')

    # django manager first
    objects = models.Manager()

    def __unicode__(self):
        return self.name()

    def name(self):
        ''' prefered representation of the user's name '''
        if self.first_name and self.last_name:
            return u"%(first)s %(last)s" % {'first': self.first_name.title(),
                                            'last': self.last_name.title()}
        if self.first_name:
            return self.first_name.title()

        if self.last_name:
            return self.last_name.title()

        return self.username

    def get_username(self):
        return self.user.username

    def set_username(self, value):
        self.user.username = value
    username = property(get_username, set_username)

    def get_first_name(self):
        return self.user.first_name

    def set_first_name(self, value):
        self.user.first_name = value
    first_name = property(get_first_name, set_first_name)

    def get_last_name(self):
        return self.user.last_name

    def set_last_name(self, value):
        self.user.last_name = value
    last_name = property(get_last_name, set_last_name)

    def get_email(self):
        return self.user.email

    def set_email(self, value):
        self.user.email = value
    email = property(get_email, set_email)

    def get_is_staff(self):
        return self.user.is_staff

    def set_is_staff(self, value):
        self.user.is_staff = value
    is_staff = property(get_is_staff, set_is_staff)

    def get_is_active(self):
        return self.user.is_active

    def set_is_active(self, value):
        self.user.is_active = value
    is_active = property(get_is_active, set_is_active)

    def get_is_superuser(self):
        return self.user.is_superuser

    def set_is_superuser(self, value):
        self.user.is_superuser = value
    is_superuser = property(get_is_superuser, set_is_superuser)

    def get_last_login(self):
        return self.user.last_login

    def set_last_login(self, value):
        self.user.last_login = value
    last_login = property(get_last_login, set_last_login)

    def get_date_joined(self):
        return self.user.date_joined

    def set_date_joined(self, value):
        self.user.date_joined = value
    date_joined = property(get_date_joined, set_date_joined)

    def is_anonymous(self):
        return self.user.is_anonymous()

    def is_authenticated(self):
        return self.user.is_authenticated()

    # this one is not a proxy
    def get_full_name(self):
        return self.name()

    def set_password(self, raw_password):
        return self.user.set_password(raw_password)

    def check_password(self, raw_password):
        return self.user.check_password(raw_password)

    def set_unusable_password(self):
        return self.user.set_unusable_password()

    def has_usable_password(self):
        return self.user.has_usable_password()

    def get_group_permissions(self, obj=None):
        return self.user.get_group_permissions(obj)

    def get_all_permissions(self, obj=None):
        return self.user.get_all_permissions(obj)

    def has_perm(self, perm, obj=None):
        return self.user.has_perm(perm, obj)

    def has_perms(self, perm_list, obj=None):
        return self.user.has_perms(perm_list, obj)

    def has_module_perms(self, package_name):
        return self.user.has_module_perms(package_name)

    def email_user(self, subject, message, from_email=None):
        return self.user.email_user(subject, message, from_email)

    def get_profile(self):
        return self


def save_associated_user(sender, instance, created, **kwargs):
    if not created:
        instance.user.save()


def create_user_provider(sender, instance, created, **kwargs):
    if created:
        profile, created = MicrositeUser.objects.get_or_create(user=instance)

post_save.connect(create_user_provider, sender=User)
post_save.connect(save_associated_user, sender=MicrositeUser)
post_save.connect(add_default_options, sender=Project)