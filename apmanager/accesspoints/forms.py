from models import Command

from django.forms import ModelForm

class CommandForm(ModelForm):
    class Meta:
        model = Command

    def clean(self):
        cleaned_data = self.cleaned_data

        script = cleaned_data.get("script")
        script_txt = cleaned_data.get("script_text")

        if not (script is None) ^ (script_txt is None):
            msg = u"You must provide either a script file or text"
            self._errors["script"] - self.error_class([msg])
            self._errors["script_text"] - self.error_class([msg])

            del cleaned_data["script"]
            del cleaned_data["script_text"]

        return cleaned_data

