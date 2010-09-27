
from django import forms
from django.utils.translation import ugettext_lazy as _

from apmanager.accesspoints import models

class ParameterForm(forms.ModelForm):
    class Meta:
        model = models.Parameter

    no_default_value = forms.BooleanField(
        required=False,
        help_text=_(u"Check this box to remove the default value. Otherwise, a blank value will be used as the default."),
        )

    def __init__(self, *args, **kwargs):
        super(ParameterForm, self).__init__(*args, **kwargs)
        if "instance" in kwargs:
            self.fields["no_default_value"].initial = (
                kwargs["instance"].default_value is None
                )

    def save(self, commit=True):
        res = super(ParameterForm, self).save(commit=commit)
        if self.cleaned_data["no_default_value"]:
            res.default_value = None
            if commit:
                res.save()
        return res

