    var tablesort;
    //---------------------------------------------------------------------
    /**
        initSort initialises sorting on the designated table
        @param tableid the id of the table to sort
        @param sortid the id of the div that will receive the sorting "bar"
    */
    function initSort(tableid,sortid,media_root)
    {
        tablesort = new TableSort(tableid,sortid,media_root);
    }

    //---------------------------------------------------------------------
    /**
        Constructor for the TableSort class
        @param tableID the id of the table to sort
        @param sortBar the id of the div that will receive the sorting bar
        @return a TableSort object
    */
    function TableSort(tableID,sortBar,media_root)
    {
        //variables
        this.table = document.getElementById(tableID);
        this.sortDiv = document.getElementById(sortBar);
        this.sortOrder = new Array();
        this.sortLength = 0;
        this.sortCriterias = new Array();
        this.usedCriterias = new Array();
        this.media_root = media_root;

        //initialisation
        this.initSortAction();
        /*for(var i=0;i<this.table.rows[0].cells.length;i++)
        {
            th = this.table.rows[0].cells[i];
            this.sortCriterias[th.innerHTML] = i;
            this.addSortAction(th,th.innerHTML);
            
        }*/
    }

    //---------------------------------------------------------------------
    /**
        initSortAction attaches sorting behavior to the first row,
            hopefully the header row, of the table
    */
    TableSort.prototype.initSortAction = function(){
        var i=0;
        for(i=0;i<this.table.rows[0].cells.length;i++)
        {
            th = this.table.rows[0].cells[i];
            //this.sortCriterias[th.innerHTML] = i + 1;
            this.sortCriterias[i+1] = th.innerHTML;
            //this.addSortAction(th,th.innerHTML);
            this.addSortAction(th,"" + (i+1));
        }
    }

    //---------------------------------------------------------------------
    /**
        addSortAction attaches sorting behavior to a cell
        @param th the cell to attach sorting behavior to
        @param sortId the column number according to which 
                    to sort when clicking this cell
    */
    TableSort.prototype.addSortAction = function(th,sortId)
    {
        header_text =  th.innerHTML;
        th.innerHTML = "";
        div = document.createElement("a");
        div.innerHTML = header_text;
        div.setAttribute("onclick","tablesort.setTopLevelSort(this,'" + sortId + "'); return false;");
        url = document.location.href;
        if (url.indexOf("order_by="+sortId) >= 0 && url.indexOf("order_by="+sortId+" DESC") == -1){
            url=url.addParameter('order_by',sortId + ' DESC', true);
        } else {
            url=url.addParameter('order_by',sortId, true);
        }
        div.setAttribute("href",url);
        th.setAttribute("class","clickable");
        th.appendChild(div);
        ////alert(th.innerHTML);
        //this.buildSortBar();
    }

    //---------------------------------------------------------------------
    /**
        setTopLevelSort changes the currently active sort parameter
            then rebuilds the sortbar
        @param sortBy the column number to sort by
    */
    TableSort.prototype.setTopLevelSort = function(caller,sortBy){
        caller.style.cursor="wait";
        var sindex = this.sortLength;
        if(this.sortOrder[sindex] == sortBy + ' ')
        {
            this.sortOrder[sindex] = sortBy + ' DESC';
        }else{
           this.sortOrder[sindex] = sortBy + ' ';
        }
        this.buildSortBar();
        
    }

    //---------------------------------------------------------------------
    /**
        removeSort removes the sort at the specified level
        @param sortLevel the level of sorting to remove
    */
    TableSort.prototype.removeSort = function(sortLevel){
        this.sortOrder.splice(sortLevel,1);
        this.sortLength = this.sortLength==0?0:this.sortLength-1;
        this.buildSortBar();
    }

    //---------------------------------------------------------------------
    /**
        createLineRemoveElement creates the element that allows
            to remove a sort level
        @param lineid the sort level that the element will remove
        @return the DOM element that was created
    */
    TableSort.prototype.createLineRemoveElement = function(lineId){
        var elm = document.createElement("img");
        elm.setAttribute("alt","remove");
        elm.setAttribute("title","Enlever le tri");
        elm.setAttribute("class","clickable");
        elm.setAttribute("src",this.media_root + "ximg.gif");
        elm.setAttribute("onclick","tablesort.removeSort("+lineId+")");
        return elm;
    }
    
    //---------------------------------------------------------------------
    /**
        createLineLockElement creates the element that allows
            to lock in the active sort level to allow for another level
        @return the DOM element that was created
    */
    TableSort.prototype.createLineLockElement = function(){
        var elm = document.createElement("img");
        elm.setAttribute("alt","add");
        elm.setAttribute("title","AJouter un autre niveau de tri");
        elm.setAttribute("class","clickable");
        elm.setAttribute("src",this.media_root + "add.gif");
        elm.setAttribute("onclick","tablesort.lockCurrentSort()");
        return elm;
    }

    //---------------------------------------------------------------------
    /**
        lockCurrentSort locks in the active sort level to allow
            for another level of sorting
    */
    TableSort.prototype.lockCurrentSort = function(){
        this.sortLength = this.sortOrder.length;
        this.buildSortBar();

    }

    //---------------------------------------------------------------------
    /**
        createSortElement creates the element to show the sort 
            criteria for a given sort level
        @param sortBy the sort column and direction, i.e. "4 DESC", "1 "
    */
    TableSort.prototype.createSortElement = function(sortBy){
        return document.createTextNode("  "+this.sortCriterias[sortBy.split(' ')[0]]+" ")
    }
    
    //---------------------------------------------------------------------
    /**
        toggleSortDir changes the sort direction for a given sort level
        @param sortLevel the level of sorting to toggle
    */
    TableSort.prototype.toggleSortDir = function(sortLevel){
        var newSort = this.sortOrder[sortLevel].split(' ');
        newSort[1] = newSort[1]=="DESC"?"":"DESC";
        this.sortOrder[sortLevel]= newSort.join(' ');
        this.buildSortBar();
    }

    //---------------------------------------------------------------------
    /**
        createSortDirElement creates the element that allows
            to toggle the sort direction for a sort level
        @param sortBy the sort column and direction, i.e. "4 DESC", "1 "
        @param sortLevel the sort level
        @return the DOM element that was created
    */
    TableSort.prototype.createSortDirElement = function(sortBy,sortLevel){
        //is the <a> useless?... probably
        var elm = document.createElement("a");
        var imgurl = "";
        var mimgurl = "";
        elm.setAttribute("onclick","tablesort.toggleSortDir("+sortLevel+")");
        elm.setAttribute("title","Changer la direction du tri");
        elm.setAttribute("class","clickable");
        if(sortBy.split(' ')[1]=="DESC"){
            imgurl=this.media_root + "down.gif"
            mimgurl=this.media_root + "down-to-up.gif"
        }else{
            imgurl=this.media_root + "up.gif"
            mimgurl=this.media_root + "up-to-down.gif"
        }
        var img = document.createElement("img");
        img.setAttribute("alt",imgurl);
        img.setAttribute("src",imgurl);
        img.setAttribute("onmouseover","this.src='" + mimgurl + "'");
        img.setAttribute("onmouseout","this.src='" + imgurl + "'");
        elm.appendChild(img);
        return elm;
    }

    //---------------------------------------------------------------------
    /**
        buildSortBar creates the sort bar within the sort div
    */
    TableSort.prototype.buildSortBar = function(){
        this.doSort();
        //remove the current caption is needed
        this.sortDiv.innerHTML="";

        if(this.sortOrder.length<=0){
            return;
        }

        //create the bar
        this.sortDiv.appendChild(document.createTextNode(" Tri  ::  "));
        //div = document.createElement("div");
        
        //treat each line of sort
        for(var i=0;i<this.sortOrder.length;i++)
        {
            //create sort criteria object
            sort_ele = this.createSortElement(this.sortOrder[i]);

            //create order direction object
            sort_dir_ele = this.createSortDirElement(this.sortOrder[i],i);
            //add em up
            if(i>0){
                this.sortDiv.appendChild(document.createTextNode(" ::  "));
                //this.sortDiv.appendChild(document.createElement("br"));
            }
            this.sortDiv.appendChild(this.createLineRemoveElement(i));
            this.sortDiv.appendChild(sort_ele);
            this.sortDiv.appendChild(sort_dir_ele);
            
        }//end for each line
        //this.sortDiv.appendChild(document.createTextNode(this.sortOrder.join(":")));
        this.sortDiv.appendChild(document.createTextNode(" ::  "));
        if(this.sortLength<this.sortOrder.length){
            this.sortDiv.appendChild(this.createLineLockElement());
        }
        //add it to the table (give it a scope)
        //this.table.appendChild(this.sortDiv);
        
    }

    //---------------------------------------------------------------------
    /**
        @deprecated
        getSortString returns the query string associated with the sorting
        @return the query string, i.e.: "order_by=1 DESC,2,3"
    */
    TableSort.prototype.getSortString = function(){
        var str = ""
        for(var i=0;i<this.sortOrder.length;i++)
        {
            if(i>0){str += ",";}else{str="order_by=";}
            //str += this.sortCriterias[this.sortOrder[i].split(' ')[0]]+" "+this.sortOrder[i].split(' ')[1];
            str += this.sortOrder[i]
        }
        return str;
    }
    
    //---------------------------------------------------------------------
    /**
        getSortValue returns the query string value associated with the sorting
        @return the query string value, i.e.: "1 DESC,2,3"
    */
    TableSort.prototype.getSortValue = function(){
        var str = ""
        for(var i=0;i<this.sortOrder.length;i++)
        {
            if(i>0){str += ",";}
            //str += this.sortCriterias[this.sortOrder[i].split(' ')[0]]+" "+this.sortOrder[i].split(' ')[1];
            str += this.sortOrder[i]
        }
        return str;
    }
    
    
    //---------------------------------------------------------------------
    /**
        doSort performs the sorting and replaces the content of the table with 
            new, sorted data
    */
    TableSort.prototype.doSort = function(){
        document.body.style.cursor = "wait";
        //var url=document.location.href.split('?')[0]+'?callback&'+this.getSortString();
        //first remove any existing order by in the url and prepending ? or &
        var url = document.location.href.addParameter('callback','',true).addParameter('order_by',this.getSortValue(),true);
        
        //If a param panel is present, ask for its parameters
        if (exists('panel') && panel != undefined)
        {
            url = panel.addParametersToUrl(url);
        }
        var xmlHttp = getAjaxObject();
        if(xmlHttp==false){ 
            document.location.href = url;
        } else {
            xmlHttp.onreadystatechange=function(){
                 if(xmlHttp.readyState==4)
                {
                    tablesort.table.innerHTML="";
                    tablesort.table.innerHTML=xmlHttp.responseText;
                    tablesort.initSortAction();
                    document.body.style.cursor = "auto";
            
                }
            };
            
            xmlHttp.open("GET",url,true);

            xmlHttp.send(null);
        }
    }

