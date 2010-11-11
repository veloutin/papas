# PAPAS Access Point Administration System
# Copyright (c) 2010 Revolution Linux inc. <info@revolutionlinux.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


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

