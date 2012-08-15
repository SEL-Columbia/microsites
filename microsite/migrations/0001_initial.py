# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Project'
        db.create_table('microsite_project', (
            ('slug', self.gf('django.db.models.fields.SlugField')(max_length=30, primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('microsite', ['Project'])

        # Adding model 'Option'
        db.create_table('microsite_option', (
            ('key', self.gf('django.db.models.fields.CharField')(max_length=75, primary_key=True)),
            ('json_value', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=70, null=True, blank=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='options', null=True, to=orm['microsite.Project'])),
        ))
        db.send_create_signal('microsite', ['Option'])

        # Adding unique constraint on 'Option', fields ['key', 'project']
        db.create_unique('microsite_option', ['key', 'project_id'])

        # Adding model 'MicrositeUser'
        db.create_table('microsite_micrositeuser', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['auth.User'], unique=True)),
            ('project', self.gf('django.db.models.fields.related.ForeignKey')(related_name='users', null=True, to=orm['microsite.Project'])),
        ))
        db.send_create_signal('microsite', ['MicrositeUser'])


    def backwards(self, orm):
        # Removing unique constraint on 'Option', fields ['key', 'project']
        db.delete_unique('microsite_option', ['key', 'project_id'])

        # Deleting model 'Project'
        db.delete_table('microsite_project')

        # Deleting model 'Option'
        db.delete_table('microsite_option')

        # Deleting model 'MicrositeUser'
        db.delete_table('microsite_micrositeuser')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'microsite.micrositeuser': {
            'Meta': {'object_name': 'MicrositeUser'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'users'", 'null': 'True', 'to': "orm['microsite.Project']"}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True'})
        },
        'microsite.option': {
            'Meta': {'unique_together': "(('key', 'project'),)", 'object_name': 'Option'},
            'json_value': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'key': ('django.db.models.fields.CharField', [], {'max_length': '75', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '70', 'null': 'True', 'blank': 'True'}),
            'project': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'options'", 'null': 'True', 'to': "orm['microsite.Project']"})
        },
        'microsite.project': {
            'Meta': {'object_name': 'Project'},
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'max_length': '30', 'primary_key': 'True'})
        }
    }

    complete_apps = ['microsite']