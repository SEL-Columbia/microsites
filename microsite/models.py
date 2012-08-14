# encoding=utf-8

from django.db import models
from microsite.utils import dump_json, load_json


class Option(models.Model):

    class Meta:
        app_label = 'microsite'
        verbose_name = u"Option"
        verbose_name_plural = u"Options"

    key = models.CharField(max_length=75, primary_key=True,
                           verbose_name=u"Key")
    json_value = models.TextField(blank=True, null=True,
                                  verbose_name=u"Value",
                                  help_text=u"JSON formated value.")

    def __unicode__(self):
        return self.key

    def get_value(self):
        if self.json_value:
            return load_json(self.json_value, None)
        return ''
    
    def set_value(self, value):
        self.json_value = dump_json(value)
        
    value = property(get_value, set_value)