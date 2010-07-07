from django.contrib import admin

from apmanager.accesspoints.models import AccessPoint, \
    Command, \
    CommandParameter, \
    APGroup

from forms import CommandForm

class CommandParameterInline(admin.TabularInline):
    model = CommandParameter

class AccessPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'ipv4Address', 'macAddress')

class APGroupAdmin(admin.ModelAdmin):
    list_display = ('name', )
    filter_vertical = ('accessPoints', )

class CommandAdmin(admin.ModelAdmin):
    form = CommandForm
    inlines = [
        CommandParameterInline,
    ]

admin.site.register(APGroup, APGroupAdmin)
admin.site.register(AccessPoint, AccessPointAdmin)
admin.site.register(Command, CommandAdmin)
