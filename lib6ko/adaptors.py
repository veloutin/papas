
class APParamAdaptor(object):
    def __init__(self, ap):
        self._ap = ap

    def __getattr__(self, attrname):
        """ Handle special scope::attr getters 
        ap::param -> direct lookup on ap
        param::param -> lookup according to PRO
        """
        scope, sep, param = attrname.partition("::")
        if sep == "":
            return object.__getattr__(self, attrname)
        if scope == "ap":
            return getattr(self._ap, attrname)
        elif scope == "param":
            #1. AP Parameters
            try:
                return self._ap.apparameter_set.get(parameter__name=param).value
            except self._ap.apparameter_set.model.DoesNotExist:
                pass
            #3. Architecture Parameters
            try:
                return self._ap.architecture.options_set.get(parameter__name=param).value
            except self._ap.architecture.options_set.model.DoesNotExist:
                pass
            #5 Default Parameter Value
            try:
                from apmanager.accesspoints.models import Parameter
                return Parameter.objects.get(name=param, default_value__isnull=False).default_value
            except Parameter.DoesNotExist:
                pass

            raise AttributeError("Unable to find parameter %s" % param)

        else:
            raise AttributeError("No attribute scope %s" % scope)
            

