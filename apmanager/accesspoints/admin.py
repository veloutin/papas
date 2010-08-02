from django.contrib import admin

from apmanager.accesspoints import models

import apmanager.accesspoints.forms as myforms

class CommandParameterInline(admin.TabularInline):
    model = models.CommandParameter

class InitSectionInline(admin.StackedInline):
    model = models.InitSection

class ArchValueInline(admin.TabularInline):
    model = models.ArchOptionValue

class ConsoleCommandImplementationInline(admin.TabularInline):
    model = models.ConsoleCommandImplementation

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
        ConsoleCommandImplementationInline,
    ]


admin.site.register(models.APGroup, APGroupAdmin)
admin.site.register(models.AccessPoint, AccessPointAdmin)
admin.site.register(models.Command, CommandAdmin)
admin.site.register(models.Architecture, ArchitectureAdmin)
admin.site.register(models.Section)
admin.site.register(models.ArchOption)
admin.site.register(models.InitSection)
admin.site.register(models.ConsoleCommand)
admin.site.register(models.ConsoleCommandImplementation)
