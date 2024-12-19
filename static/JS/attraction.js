var pathname = window.location.pathname;
const attractionId=pathname.split("/")[2];
let weblocate="https://3.107.150.70"
let webport=""
src=`${weblocate}:${webport}/api/attraction/${attractionId}`;
window.onload=function(){
    //Get data of attraction, images
    fetch(src,
        {
            method: "GET",
            headers: {
                'accept': 'application/json'
            }
        }
    ).then(function(response){
            return response.json();
        }
    ).then(function(data){
            //Get detail information
            let description=document.getElementById("description");
            description.textContent =data["data"]["description"];
            let addressContent=document.getElementById("addressContent");
            addressContent.textContent =data["data"]["address"];
            let transportationContent=document.getElementById("transportationContent");
            transportationContent.textContent =data["data"]["transport"];
            let attractionNameInAttracionPage=document.getElementById("attractionNameInAttracionPage");
            attractionNameInAttracionPage.textContent =data["data"]["name"];
            let categoryAndMrt=document.getElementById("categoryAndMrt");
            categoryAndMrt.textContent =data["data"]["category"]+" at "+data["data"]["mrt"];
            //Get image
            let slideShowContainer=document.querySelector('.slideShowContainer');
            
            let dots=document.getElementById("dots");
            dots.style.width=12*(data["data"]["images"].length*2-1+2)+"px";

            for(let idx=0;idx<data["data"]["images"].length;idx++){
                let dot=document.createElement('span');
                dot.onclick="currentSlide("+idx+")";
                dot.setAttribute("onclick", "currentSlide("+idx+")");
                dot.className = "dot"; 
                
                

                let attractionImage=document.createElement('div');
                attractionImage.className = "slide";  
                let imageFromAPI=data["data"]["images"][idx];
                attractionImage.style.backgroundImage = "url('" + imageFromAPI + "')"; 
                if(idx==0){
                    attractionImage.style.display="block";
                    dot.className += " active";
                }
                dots.appendChild(dot);
                slideShowContainer.appendChild(attractionImage);
            }

        }
    ).catch((err) => alert(err));
}
//==============================================
let slideIndex = 0;

function plusSlides(n) {
    showSlides(slideIndex += n);
}

function currentSlide(n) {
    showSlides(slideIndex = n);
}

function showSlides(n) {
    let i;
    let slides = document.getElementsByClassName("slide");
    let dots = document.getElementsByClassName("dot");
    if (n >= slides.length) {slideIndex = slides.length-1}
    if (n < 1) {slideIndex = 0}
    for (i = 0; i < slides.length; i++) {
        slides[i].style.display = "none";
    }
    for (i = 0; i < dots.length; i++) {
        dots[i].className = dots[i].className.replace(" active", "");
    }
    slides[slideIndex].style.display = "block";
    dots[slideIndex].className += " active";
}
function checkRadio(value) {
    if(value == "morning"){
        document.getElementById("bookingCost").textContent = "新台幣 2000 元";
    } else if (value == "afternoon"){
        document.getElementById("bookingCost").textContent = "新台幣 2500 元";
    }
}
//booking submit
const bookingSubmit=document.getElementById("bookingSubmit");
bookingSubmit.addEventListener("click", createBooking);

function createBooking(){
    const srcCheckToken="/api/user/auth"; 
    const srcBooking="/api/booking";          
    fetch(srcCheckToken,
            {
                method:"GET",
                headers:{"Content-Type": "application/json"},
            }
    ).then(response => response.json())
    .then(function(data){
            if(data.data){
                //User already login
                //Get time
                var tripTime=document.getElementsByName('tripTime');
                var getTripTime;
                for(var i = 0; i < tripTime.length; i++){
                    if(tripTime[i].checked){
                        getTripTime = tripTime[i].value;  
                        break;
                    }
                }   
                //"price"
                var price=document.getElementById("bookingCost").textContent;
                var getPrice = parseInt(price.substring(1).substring(1).substring(1));
                
                let body={
                    "attractionId": attractionId,
                    "date": document.getElementById("tripDate").value,
                    "time": getTripTime,
                    "price":getPrice
                };
                
                fetch(srcBooking,
                    {
                        method:"POST",
                        headers:{"Content-Type": "application/json"},
                        body:JSON.stringify(body),
                    }
                ).then(response => response.json())
                .then(function(data){
                        if(data.ok==true){
                            location.href="/booking";
                        }else if(data.error==true) {
                            //Show error message in console 
                            console.log(data.message);
                        }     
                    }
                ).catch(error => (console.log(error)));
                
            }
            else{
                showSignInUpDialog();
            }
        }
    );
    
}
