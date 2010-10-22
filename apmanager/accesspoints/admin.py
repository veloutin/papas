
from itertools import groupby, chain

from django.contrib import admin
from contextlib import contextmanager, nested
from django.conf.urls.defaults import patterns
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext, Context
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

class InitSectionInline(admin.StackedInline):
    model = models.InitSection

class ArchValueInline(admin.TabularInline):
    model = models.ArchParameter

class APParamInline(admin.TabularInline):
    model = models.APParameter

class ProSupportInline(admin.TabularInline):
    model = models.APProtocolSupport
    fields = (
        'protocol',
        'priority',
        'status',
        )

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
        ProSupportInline,
    ]

    def get_urls(self):
        urls = super(AccessPointAdmin, self).get_urls()
        my_urls = patterns('',
            (r'^(.+)/clone/$', self.admin_site.admin_view(self.clone_view)),
            (r'^(.+)/parameters/$', self.admin_site.admin_view(self.init_parameters_view)),
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

                # Copy related parameters
                for apparam in obj.apparameter_set.all():
                    # Remove the id, we want a new one
                    apparam.id = None
                    apparam.ap = newobj
                    apparam.save(force_insert=True)

                # Copy related protocol support
                for psup in obj.protocol_support.all():
                    #Remove the id, we want a enw one
                    psup.id = None
                    psup.ap = newobj
                    psup.save(force_insert=True)

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

    def param_iterator(self, param_info_dict, parameters=None):
        """
        Get an iterator that will return 
        (section name, param_iterator) for each parameter section

        Parameters:
        - param_info_dict: result of AccessPoint.get_full_param_information()
        - parameters: list of parameters to allow, or None for all
        """
        if parameters is None:
            filter_func = lambda a: True
        else:
            filter_func = lambda (key, val): key in parameters

        # groupby(iterable, keyfunc) returns an iterator that returns
        # (key, sub-iterator) grouped by keyfunc(value)
        for key, group in groupby(
            sorted(
                filter(
                    # Remove entries that are not used in initialization
                    filter_func,
                    param_info_dict.iteritems(),
                ),
                key=lambda (key, val) : (
                    val["parameter"].section.name,
                    val["parameter"].name,
                ),
            ),
            # Group by section name
            lambda (key, val): val["parameter"].section,
            ):
            # Only return non-empty groups
            group= tuple(group)
            if group:
                yield key, group



    def init_parameters_view(self, request, object_id, extra_context=None):
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

        show_trace = request.GET.get("show_trace", "no") == "yes"
        limit = request.GET.get("limit", None) is not None

        limit_params = None
        if limit:
            tracer = models.ParamTracer()
            ctx = Context({"ap":obj, tracer.tracer_key:tracer})
            for init_section in obj.architecture.initsection_set.order_by('section__name'):
                init_section.compile_template().render(ctx)
            limit_params = tracer.params.keys()

        full_param_info = obj.get_full_param_information()

        return render_to_response("admin/accesspoints/accesspoint/init_parameters.html",
            {
                "app_label":opts.app_label,
                "original":obj,
                "opts":opts,
                "parameters":self.param_iterator(full_param_info, limit_params),
                "full":show_trace,
                "title":_(u"Parameters Overview"),
            },
            context_instance=RequestContext(request),
            )

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
del mset["CommandImplementation"]

#Show every other model in admin
for remaining in mset.itervalues():
    admin.site.register(remaining)
