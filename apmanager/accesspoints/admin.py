from django.contrib import admin
from contextlib import contextmanager, nested
from django.conf.urls.defaults import patterns
from django.http import Http404, HttpResponseRedirect
from django.contrib.admin.options import (
    _,
    transaction,
    unquote,
    PermissionDenied,
    force_unicode,
    escape,
    helpers,
    mark_safe,
    )

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

@contextmanager
def temp_setattr(obj, attrname, value):
    oldval = getattr(obj, attrname)
    setattr(obj, attrname, value)
    yield obj
    setattr(obj, attrname, oldval)

class AccessPointAdmin(admin.ModelAdmin):
    list_display = ('name', 'ipv4Address', 'macAddress')
    inlines = [
        APParamInline,
    ]

    def get_urls(self):
        urls = super(AccessPointAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^(.+)/clone/$', self.admin_site.admin_view(self.clone_view))
        )
        return my_urls + urls

    @transaction.commit_on_success
    def clone_view(self, request, object_id, extra_context=None):
        # This method is a cut and paste copy of ModelAdmin.change_view with
        # a custom form instead of the admin form. It allows editing the base
        # properties of the AccessPoint, and creates a copy upon saving

        
        ## Access control performed as ModelAdmin.change_view
        model = self.model
        opts = model._meta

        try:
            obj = self.queryset(request).get(pk=unquote(object_id))
        except model.DoesNotExist:
            # Don't raise Http404 just yet, because we haven't checked
            # permissions yet. We don't want an unauthenticated user to be able
            # to determine whether a given object exists.
            obj = None

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_unicode(opts.verbose_name), 'key': escape(object_id)})

        formsets = []

        if request.method == "POST":
            form = myforms.APForm(request.POST)
            if form.is_valid():
                newobj = form.save(commit=False)
                # Remove the id, we want a new one
                newobj.id = None
                newobj.save(force_insert=True)

                # Copy related objects
                for apparam in obj.apparameter_set.all():
                    # Remove the id, we want a new one
                    apparam.id = None
                    apparam.ap = newobj
                    apparam.save(force_insert=True)

                msg = _('The %(name)s "%(obj)s" was cloned successfully.') % {'name': force_unicode(opts.verbose_name), 'obj': force_unicode(obj)}
                # Add new, go back or edit
                if request.POST.has_key("_addanother"):
                    self.message_user(request, msg + ' ' + _("You may clone it again below."))
                    return HttpResponseRedirect("../clone/")
                elif request.POST.has_key("_continue"):
                    self.message_user(request, msg + ' ' + _("You may edit it below."))
                    return HttpResponseRedirect("../../%s/" % newobj._get_pk_val())
                else:
                    self.message_user(request, msg)
                    return HttpResponseRedirect("../../")

        else:
            form = myforms.APForm(instance=obj)

            ## Setup formsets (change_form)
            prefixes = {}
            for FormSet in self.get_formsets(request, obj):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(instance=obj, prefix=prefix)
                formsets.append(formset)

        adminForm = helpers.AdminForm(form, self.get_fieldsets(request, obj), self.prepopulated_fields)
        media = self.media + adminForm.media
        inline_admin_formsets = []

        context = {
            'title': _('Clone %s') % force_unicode(opts.verbose_name),
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': request.REQUEST.has_key('_popup'),
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }

        context.update(extra_context or {})
        with nested(
            temp_setattr(self, "change_form_template", [
                "admin/%s/%s/clone_form.html" % (opts.app_label, opts.object_name.lower()),
                "admin/%s/clone_form.html" % (opts.app_label),
                "admin/clone_form.html",
                ])
            ):
            return self.render_change_form(request, context, change=True, obj=obj)


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
    search_fields = (
        'name',
        'section__name',
        'default_value',
    )
    form = myforms.ParameterForm

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
