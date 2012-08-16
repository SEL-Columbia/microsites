
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from models import Option, Project, MicrositeUser, KeyNamePair

admin.site.register(Project)
admin.site.register(Option)
admin.site.register(KeyNamePair)


class MicrositeUserStacked(admin.StackedInline):
    model = MicrositeUser
    fk_name = 'user'
    max_num = 1


class CustomUserAdmin(UserAdmin):
    inlines = [MicrositeUserStacked, ]

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)