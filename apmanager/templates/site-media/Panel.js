var panel;

//------------------------------------------------------------------------
/**
    initPanel initialises the parameter panel 
    @param tableid the id of the table to sort
    @param divid the id of the parameter panel table
    @param option objects
*/
function initPanel(tableid,divid,options)
{
    panel = new ParameterPanel(tableid,divid,options);
}

//------------------------------------------------------------------------
/**
    Constructor for the ParameterPanel class
    @param tableID the id of the table to sort
    @param divID the id of the table for the parameter panel
    @param options array of option objects
    @return a ParameterPanel object
*/
function ParameterPanel(tableID,divID,options)
{
    //variables
    this.panelDiv = document.getElementById(divID);
    this.options = options;
    this.controls = new Array();
    this.params = new Array();
    this.table = document.getElementById(tableID);
    //create this
    this.initialize();
}

//------------------------------------------------------------------------
/**
    function initialize()
    initialises the panel 
*/
ParameterPanel.prototype.initialize = function()
{
    //initialize the options
    this.initialize_params(this.options.options);

    //Clear the Div
    this.panelDiv.innerHTML="";
    //wrap everything in a fake form
    var frm = document.createElement("form");
    frm.action="javascript:panel.do_submit();";

    //Create a table for the params
    var table = document.createElement("table");
    table.setAttribute("class","base");
    
    //Create a title if necessary
    if( this.options.title!=undefined ){
        tr = document.createElement("tr");
        td = document.createElement("th");
        td.setAttribute("colspan",2);
        td.appendChild(document.createTextNode(this.options.title));
        tr.appendChild(td);
        table.appendChild(tr);
    }
    
    
    //Create the controls
    this.createControls(this.options.options);
    
    //Add the controls to the table
    for (var i=0; i<this.controls.length; ++i)
    {
        table.appendChild(this.controls[i]);
    } 

    //Add a submit button
    var submit = document.createElement("input");
    submit.setAttribute("value","Afficher");
    submit.setAttribute("type","submit");
    submit.setAttribute("class","param_panel_submit");    
    
    trs = document.createElement("tr");
    tds = document.createElement("td");
    tds.setAttribute("colspan",2);
    tds.setAttribute("align","right");
    tds.appendChild(submit);
    trs.appendChild(tds);
    table.appendChild(trs);
    
    //add the table
    frm.appendChild(table);
    this.panelDiv.appendChild(frm);
}

//------------------------------------------------------------------------
ParameterPanel.prototype.createControls= function()
{
    for (var i=0; i<this.params.length; ++i)
    {
        var row = document.createElement("tr");
        var label = document.createElement("td");
        var valtd = document.createElement("td");
        var input = document.createElement("input");
        var clr = document.createElement("input");
        var toggle = document.createElement("input");
    
        //create the label
        label.setAttribute("id","param_panel_label_"+i);
        label.appendChild(document.createTextNode(this.params[i].display_name));
        
        //create the input
        input.setAttribute("id","param_panel_input_"+i);
        if( this.params[i].value ){
            input.setAttribute("value",this.params[i].value);
        } 
        //input.setAttribute("onclick","panel.enableControl("+i+");");
        input.setAttribute("onchange","panel.field_changed("+i+",this.value);");
    
        //enable/disable checkbox
        toggle.setAttribute("type","checkbox");
        toggle.setAttribute("checked",this.params[i].enabled);
        toggle.setAttribute("onchange","panel.togglecontrol("+i+",this.checked);");

        //clear button
        clr.setAttribute("id","param_panel_clear_"+i);
        clr.setAttribute("value","clear");
        clr.setAttribute("type","button");
        clr.setAttribute("onclick","panel.clearControl("+i+");");        
       
        //styles 
        row.setAttribute("class",i%2==0?"even":"odd");
        clr.setAttribute("class","param_panel_clear");
        input.setAttribute("class",this.params[i].enabled?"param_panel_enabled":"param_panel_disabled");
        label.setAttribute("class","param_panel_label");
        
        //tape everything together
        valtd.appendChild(input);
        valtd.appendChild(toggle);
        valtd.appendChild(clr);
        row.appendChild(label);
        row.appendChild(valtd);
        this.controls[i]=row;
    }

}

//------------------------------------------------------------------------
ParameterPanel.prototype.initialize_params = function(optionlist)
{
    for (var i=0; i<optionlist.length; ++i)
    {
        this.params[i] = new Array();
        this.params[i]['name'] = optionlist[i].param_name;
        this.params[i]['display_name'] = optionlist[i].display_name!=undefined?
            optionlist[i].display_name:optionlist[i].param_name;
        this.params[i]['value'] = optionlist[i].value;
        this.params[i]['enabled'] = optionlist[i].enabled
                ==undefined?true:optionlist[i].enabled;
    }
}

//------------------------------------------------------------------------
ParameterPanel.prototype.togglecontrol = function(index,enable)
{
    if(enable)
    {
        this.enableControl(index);
    }else{
        this.disableControl(index);
    }
}

//------------------------------------------------------------------------
ParameterPanel.prototype.enableControl = function(index)
{
    input = document.getElementById("param_panel_input_"+index);
    
    input.readOnly =false;
    input.disabled =false;
    input.setAttribute("class","param_panel_enabled");

    this.params[index].enabled = true;
}

//------------------------------------------------------------------------
ParameterPanel.prototype.disableControl = function(index)
{
    input = document.getElementById("param_panel_input_"+index);
    
    input.readOnly =true;
    input.disabled =true;
    //We could set disabled, but we will just give it the disabled look
    // since disabled controls do not respond to mouse events
    //input.setAttribute("value","");
    input.setAttribute("class","param_panel_disabled");
    this.params[index].enabled = false;
}

//------------------------------------------------------------------------
ParameterPanel.prototype.clearControl = function(index)
{
    //document.getElementById("param_panel_input_"+index).setAttribute("value","");
    document.getElementById("param_panel_input_"+index).value = "";
}

//------------------------------------------------------------------------
ParameterPanel.prototype.field_changed = function(index,value)
{
    this.params[index].value=value;
}

//------------------------------------------------------------------------
ParameterPanel.prototype.toggle = function(set_to)
{
    if(set_to==undefined)
    {
        //set_to=this.panelDiv.getAttribute("display")=="none";
        set_to=document.getElementById('paneldiv').getAttribute("class")=="displaynone";
    }
    //this.panelDiv.setAttribute("display",set_to?"":"none");
    document.getElementById('paneldiv').setAttribute("class",set_to?"param_panel_div":"displaynone");
}

//------------------------------------------------------------------------
ParameterPanel.prototype.addParametersToUrl = function(url)
{
    
    for(var i=0; i<this.params.length; ++i)
    {
        if (this.params[i].enabled==true && this.params[i].value != undefined)
        {
            //enabled control must be submitted
            url = url.addParameter(this.params[i].name,this.params[i].value,true);
        }else{
            url = url.removeParameter(this.params[i].name);
        }

    }
    return url;
} 

//------------------------------------------------------------------------
ParameterPanel.prototype.do_submit = function()
{
    var url = this.addParametersToUrl(document.location.href); 
    if (exists('tablesort') && tablesort != undefined) {
        url = url.addParameter('order_by',tablesort.getSortValue(),true);
    }
    var xmlHttp = getAjaxObject();
    if (xmlHttp!=false)
    {
        url = url.addParameter('callback','',true);
        //Do an AJAX refresh if we can, much cooler :-)
        xmlHttp.onreadystatechange=function(){
             if(xmlHttp.readyState==4)
            {
                panel.table.innerHTML="";
                panel.table.innerHTML=xmlHttp.responseText;
                document.body.style.cursor = "auto";
                if (exists('tablesort') && tablesort != undefined) {
                    tablesort.initSortAction();
                } 
            }
        };

        xmlHttp.open("GET",url,true);
        
        xmlHttp.send(null);
    } else {
        //otherwise just change the url
        document.location.href=url;
    }
}


