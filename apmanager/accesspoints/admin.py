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

class APParamInline(admin.TabularInline):
    model = models.APParameter

class CommandImplementationInline(admin.TabularInline):
    model = models.CommandImplementation

class AccessPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'ipv4Address', 'macAddress')
    inlines = [
        APParamInline,
    ]

class APGroupAdmin(admin.ModelAdmin):
    list_display = ('name', )
    filter_vertical = ('accessPoints', )

class ArchitectureAdmin(admin.ModelAdmin):
    inlines = [
        ArchValueInline,
        InitSectionInline,
    ]

class CommandDefinitionAdmin(admin.ModelAdmin):
    inlines = [
        CommandImplementationInline,
    ]

class InitSectionAdmin(admin.ModelAdmin):
    list_filter = (
        'section',
        'architecture',
    )

class ParameterAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'section',
        'default_value',
    )
    list_filter = (
        'section',
    )
mset = dict(
    filter(
        lambda s: isinstance(s[1], type) and issubclass(s[1], BaseModel), 
        models.__dict__.iteritems(),
        )
)

admin.site.register(mset.pop("APGroup"), APGroupAdmin)
admin.site.register(mset.pop("AccessPoint"), AccessPointAdmin)
admin.site.register(mset.pop("CommandDefinition"), CommandDefinitionAdmin)
admin.site.register(mset.pop("Architecture"), ArchitectureAdmin)
admin.site.register(mset.pop("InitSection"), InitSectionAdmin)
admin.site.register(mset.pop("Parameter"), ParameterAdmin)

#Remove some models to hide them
del mset["APParameter"]
del mset["APProtocolSupport"]
del mset["ArchParameter"]
del mset["APClient"]
del mset["UsedParameter"]
del mset["Command"]
del mset["CommandExecResult"]
del mset["CommandParameter"]
del mset["CommandImplementation"]

#Show every other model in admin
for remaining in mset.itervalues():
    admin.site.register(remaining)
