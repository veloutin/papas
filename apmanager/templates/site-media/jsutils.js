//---------------------------------------------------------------------
/**
    getAjaxObject attempts to create the XMLHttp object
        to be used for asynchronous ajax requests
    @return the XMLHttp object or false if creation fails
*/
function getAjaxObject()
{
    var xmlHttp;
    try
    {
        // Firefox, Opera 8.0+, Safari
        return new XMLHttpRequest();
    }
    catch (e)
    {
        // Internet Explorer
        try
        {
            return new ActiveXObject("Msxml2.XMLHTTP");
        }
        catch (e)
        {
            try
            {
                return new ActiveXObject("Microsoft.XMLHTTP");
            }
            catch (e)
            {
                alert("Your browser does not support AJAX!");
                return false;
            }
        }
    }
}

//---------------------------------------------------------------------
/**
    addParameter adds a parameter=value pair to a string
    @param pName the name of the parameter
    @param pValue the value of the parameter
    @param replaceIfPresent if it evaluates to True, replace any existing
        occurence of pName parameter by the newly added one
    @return a new string with the parameter added
*/
String.prototype.addParameter = function(pName,pValue,replaceIfPresent)
{
    //We must only search the query part of the urls
    //         foo://example.com:8042/over/there?name=ferret#nose
    //         \_/   \______________/\_________/ \_________/ \__/
    //          |           |            |            |        |
    //       scheme     authority       path        query   fragment
    querystart = this.indexOf("?");

    if(querystart >= 0 && this.indexOf(pName)> querystart && replaceIfPresent){
        //if an existing parameter must be replaced
        return this.replace(new RegExp("(&|\\?)" + pName + "(=[^&#]*)?","g"),"$1" + pName + "=" + pValue);
    }else{
        //otherwise, we must add the parameter append to the url
        if(querystart>=0){
            //if a querystring is present, append to it
            return this.replace(new RegExp("(#.*)?$","g"), "&" + pName + "=" + pValue + "$1");
        }else{
            //no querystring, add one!
            return this.replace(new RegExp("(#.*)?$","g"), "?" + pName + "=" + pValue + "$1");
        }
    }
}


//---------------------------------------------------------------------
/**
    removeParameter removes a parameter=value pair from a string
    @param pName the name of the parameter
    @return a new string with the parameter added
*/
String.prototype.removeParameter = function(pName)
{
    return this.replace(new RegExp("((&)|(\\?))" + pName + "([^&]*)?&?","g"),"$3");
}

function addAllParameters(url){
    if (exists('tablesort') && tablesort!==undefined){
        url = url.addParameter('order_by',tablesort.getSortValue(),true);
    }
    if (exists('panel') && panel!==undefined){
        url = panel.addParametersToUrl(url);
    }
    return url;
}

function exists(varName){
    try{
        var t = eval(varName);
    }catch(err){
        return false;
    }
    return true;
}

