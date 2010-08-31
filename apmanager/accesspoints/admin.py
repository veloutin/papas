from django.contrib import admin

from django.db.models import Model as BaseModel
from apmanager.accesspoints import models

import apmanager.accesspoints.forms as myforms

class CommandParameterInline(admin.TabularInline):
    model = models.CommandParameter

class InitSectionInline(admin.StackedInline):
    model = models.InitSection

class ArchValueInline(admin.TabularInline):
    model = models.ArchParameter

class CommandImplementationInline(admin.TabularInline):
    model = models.CommandImplementation

class AccessPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'ipv4Address', 'macAddress')

class APGroupAdmin(admin.ModelAdmin):
    list_display = ('name', )
    filter_vertical = ('accessPoints', )

class CommandAdmin(admin.ModelAdmin):
    form = myforms.CommandForm
    inlines = [
        CommandParameterInline,
    ]

class ArchitectureAdmin(admin.ModelAdmin):
    inlines = [
        ArchValueInline,
        InitSectionInline,
        CommandImplementationInline,
    ]

mset = dict(
    filter(lambda s: isinstance(s[1], type) and issubclass(s[1], BaseModel), models.__dict__.iteritems())
)

admin.site.register(mset.pop("APGroup"), APGroupAdmin)
admin.site.register(mset.pop("AccessPoint"), AccessPointAdmin)
admin.site.register(mset.pop("Command"), CommandAdmin)
admin.site.register(mset.pop("Architecture"), ArchitectureAdmin)
for remaining in mset.itervalues():
    admin.site.register(remaining)
