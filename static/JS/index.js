var nextPage=0;
let isLoading=false;
var keywordOfSearch;
let weblocate="https://3.107.150.70"
let webport=""
var src=`${weblocate}:${webport}/aipi/attractions?page=${nextPage}`;
function getCategoryData(){
    srcCategory=`${weblocate}:${webport}/api/categories`;
    fetch(srcCategory,{
            method: "GET",
            headers: {
                'accept': 'application/json'
            }
        }
    ).then(function(response){
        return response.json();
    }).then(function(data){
        
        if(data["data"].length>0){
            let categoryContainer=document.querySelector('.categoryContainer');
            let searchAttraction = document.getElementsByName('searchAttraction');
            for(idx=0;idx<data["data"].length;idx++)
            {
                let categoryItem=document.createElement('div');
                categoryItem.className = "categoryInSearchBar";  
                categoryItem.textContent=data["data"][idx];
                if(data["data"][idx].length==2){
                    categoryItem.style.letterSpacing = "2em";
                }
                categoryItem.addEventListener(
                    "click",
                    function(){
                        searchAttraction[0].setAttribute("value", categoryItem.textContent);
                        categoryContainer.style.display="none";
                    }    
                );         
                categoryContainer.appendChild(categoryItem);
            }
        }
        isLoading=false;
    }).catch((err) => alert(err));
}
function getData(src){
    isLoading=true;
    fetch(src,{
            method: "GET",
            headers: {
                'accept': 'application/json'
            }
        }
    ).then(function(response){
        return response.json();
    }).then(function(data){
        nextPage=data["nextPage"];
        if(data["data"].length>0){
            for(idx=0;idx<data["data"].length;idx++)
            {
                let attractionImage=document.createElement('div');
                attractionImage.className = "attractionImage";  
                let attractionName=document.createElement('div');
                attractionName.className = "attractionName";  
                attractionName.textContent=data["data"][idx]["name"];
                let attractionTopArea=document.createElement('div');
                attractionTopArea.className = "attractionTopArea"; 
                let imageFromAPI=data["data"][idx]["images"][0];
                attractionTopArea.style.backgroundImage = "url('" + imageFromAPI + "')"; 
                attractionTopArea.appendChild(attractionImage);
                attractionTopArea.appendChild(attractionName);

                let MRT=document.createElement('div');
                MRT.className = "MRT"; 
                MRT.textContent=data["data"][idx]["mrt"];
                let category=document.createElement('div');
                category.className = "category"; 
                category.textContent=data["data"][idx]["category"];
                let attractionBottomArea=document.createElement('div');
                attractionBottomArea.className = "attractionBottomArea"; 
                attractionBottomArea.appendChild(MRT);
                attractionBottomArea.appendChild(category);

                let attractionsItem=document.createElement('div');
                attractionsItem.className = "attractionsItem"; 

                let hyperlinkAttraction=document.createElement('a');
                hyperlinkAttraction.setAttribute('href', '/attraction/'+data["data"][idx]["id"]);
                hyperlinkAttraction.appendChild(attractionTopArea);
                hyperlinkAttraction.appendChild(attractionBottomArea);
                
                attractionsItem.appendChild(hyperlinkAttraction);

                
                let attractionsGroup=document.querySelector('.attractionsGroup');
                attractionsGroup.appendChild(attractionsItem);
            }
        }else{
            let attractionName=document.createElement('div');
            attractionName.className = "sloganTitle";  
            attractionName.textContent="No any result about it.";
            let attractionsArea=document.querySelector('.attractionsArea');
            attractionsArea.appendChild(attractionName);
        }
        isLoading=false;
    }).catch((err) => alert(err));
    
}

// Interception Handler
const bottomOfContent = document.querySelector('#bottomOfContent');
const callbackForAttractions = (entries, observer) => {
    for (const entry of entries) {
        console.log(entry);
        // Load more
        if (entry.isIntersecting && isLoading==false && nextPage!=null) {
            src=`${weblocate}:${webport}/api/attractions?page=${nextPage}`;
            getData(src);   
            observer.observe(bottomOfContent);   
        } 
        else if(nextPage==null){
            observer.unobserve(bottomOfContent); 
        }
    }
}

// Observe the end of content in webpage
const observer = new IntersectionObserver(callbackForAttractions, {threshold: 0,});
observer.observe(bottomOfContent);


window.onload=function(){
    observer.observe(bottomOfContent);
    let searchAttraction = document.getElementsByName('searchAttraction');
    searchAttraction[0].addEventListener(
        'click', 
        function () {
            let categoryContainer=document.querySelector('.categoryContainer');
            categoryContainer.style.display="grid";
        }, 
        true
    );
    getCategoryData();
    var body = document.body;
    body.addEventListener(
        'mousedown', 
        function(e)
        {
            if(e.target.className!="categoryInSearchBar"){
                let categoryContainer=document.querySelector('.categoryContainer');
                categoryContainer.style.display="none";
            }
        }  
    ); 
}

function searchAttraction() {
    let categoryContainer=document.querySelector('.categoryContainer');
    categoryContainer.style.display="none";
    observer.disconnect();
    let searchAttraction = document.getElementsByName('searchAttraction');
    keywordOfSearch = searchAttraction[0].value;
    nextPage=0;
    src=`${weblocate}:${webport}/api/attractions?page=${nextPage}&keyword=${keywordOfSearch}`;
    let attractionsGroup=document.querySelector('.attractionsGroup');
    attractionsGroup.replaceChildren();
    
    let callbackForSearch = (entries, observerForSearch) => {
        for (const entry of entries) {
            console.log(entry);
            // Load more
            if (entry.isIntersecting && isLoading==false && nextPage!=null) {
                src=`${weblocate}:${webport}/api/attractions?page=${nextPage}&keyword=${keywordOfSearch}`;
                getData(src);   
                observerForSearch.observe(bottomOfContent);   
            } 
            else if(nextPage==null){
                observerForSearch.unobserve(bottomOfContent);                 
            }
        }
    }
    let observerForSearch = new IntersectionObserver(callbackForSearch, {threshold: 0,});
    observerForSearch.observe(bottomOfContent);

}
