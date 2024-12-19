window.onload=function(){
    checkLogin();
    getBookinInfo();
    getUserInfo()
    
}
var bookingDataAttraction;
var bookingDataTime;
var bookingDataDate;
var bookingDataPrice;
var userInfoName;
var userInfoEmail;
function checkLogin(){
    let src="/api/user/auth";
    fetch(src,
            {
                method:"GET",
                headers:{"Content-Type": "application/json"},
            }
    ).then(response => response.json())
    .then(function(data){
            if(data.data){
                userData=JSON.parse(data.data);
                let greedingMessageBlock=document.getElementById("greedingMessage");    
                greedingMessage=greedingMessageBlock.textContent;
                greedingMessage=greedingMessage.replace("，", "，"+userData.name+"，");
                greedingMessageBlock.textContent=greedingMessage;
            }else{
                location.href="/";
            }
        }
    ); 
}

function getBookinInfo(){
    let src="/api/booking";
    fetch(src,
            {
                method:"GET",
                headers:{"Content-Type": "application/json"},
            }
    ).then(response => response.json())
    .then(function(data){
            const getBookingInformation=document.getElementById("getBookingInformation");
            const noBookingInformation=document.getElementById("noBookingInformation");
            if(data.data){
                getBookingInformation.style.display="block";
                noBookingInformation.style.display="none";
                bookingData=data.data;
                bookingAttraction=JSON.parse(bookingData.attraction);
                bookingDataAttraction=bookingAttraction;
                //Get attraction image
                let attractionImageInbookingPage=document.getElementById('attractionImage');
                attractionImageInbookingPage.style.backgroundImage = "url('" + bookingAttraction.image+ "')"; 
                //Get attraction name
                let bookAttractionInBookingPage=document.getElementById('bookAttractionInBookingPage');
                bookAttractionInBookingPage.textContent=bookingAttraction.name;
                //Get booking date
                let bookDateInBookingPage=document.getElementById('bookDateInBookingPage');
                bookingDataDate=bookingData.date;
                bookDateInBookingPage.textContent=bookingData.date;
                //Get time and cost
                let bookTimeInBookingPage=document.getElementById('bookTimeInBookingPage');
                let bookCostInBookingPage=document.getElementById('bookCostInBookingPage');
                let totalCostInBookingPage=document.getElementById('totalCostInBookingPage');
                if(bookingData.time=="morning"){
                    bookTimeInBookingPage.textContent="早上九點到下午四點";
                    bookCostInBookingPage.textContent="新台幣 2000 元";
                    totalCostInBookingPage.textContent="新台幣 2000 元";
                }else if(bookingData.time=="afternoon"){
                    bookTimeInBookingPage.textContent="下午五點到晚上九點";
                    bookCostInBookingPage.textContent="新台幣 2500 元";
                    totalCostInBookingPage.textContent="新台幣 2500 元";
                }         
                bookingDataTime=bookingData.time;
                bookingDataPrice=bookingData.price;
                //Get address
                let bookAddressInBookingPage=document.getElementById('bookAddressInBookingPage');
                bookAddressInBookingPage.textContent=bookingAttraction.address;
            }else{
                getBookingInformation.style.display="none";
                noBookingInformation.style.display="block";
            }
        }
    ); 
}

function getUserInfo(){
    let src="/api/user/auth";
    fetch(src,
            {
                method:"GET",
                headers:{"Content-Type": "application/json"},
            }
    ).then(response => response.json())
    .then(function(data){
            if(data.data){
                let userInfo=JSON.parse(data.data);
                //Get username
                let contactName=document.getElementById('contactName');
                contactName.value=userInfo.name;
                userInfoName=userInfo.name;
                //Get user's mail
                let contactMail=document.getElementById('contactMail');
                contactMail.value=userInfo.email;
                userInfoEmail=userInfo.email;
            }else{
                console.log(data.data);
            }
        }
    ); 
}
const deleteIcon=document.getElementById("deleteIcon");
deleteIcon.addEventListener("click", deleteBooking);
function deleteBooking(){
    let src="/api/booking";
    fetch(src,
            {
                method:"DELETE",
                headers:{"Content-Type": "application/json"},
            }
    ).then(response => response.json())
    .then(function(data){
            if(data.ok==true){
                location.href="/booking";
            }else if(data.error==true){
                console.log(data.message);
            }
        }
    ); 
}
////TapPay////
//Setup SDK//
const APP_KEY="app_cBO7BFUlBqBe4e7tjjRa5iIkBfOA7xQvbCP9XZyQrdJtvGK7pgrTC3wRbuwH";
const APP_ID=126973;

TPDirect.setupSDK(APP_ID, APP_KEY, 'sandbox')
//TPDirect.card.setup(config)//
var fields = {
    number: {
        // css selector
        element: document.getElementById('card-number'),
        placeholder: '**** **** **** ****'
    },
    expirationDate: {
        // DOM object
        element: document.getElementById('card-expiration-date'),
        placeholder: 'MM / YY'
    },
    ccv: {
        element: document.getElementById('card-ccv'),
        placeholder: 'ccv'
    }
}

TPDirect.card.setup({
    fields: fields,
    styles: {
        // Style all elements
        'input': {
            'color': 'gray'
        },
        // Styling ccv field
        'input.ccv': {
            // 'font-size': '16px'
        },
        // Styling expiration-date field
        'input.expiration-date': {
            // 'font-size': '16px'
        },
        // Styling card-number field
        'input.card-number': {
            // 'font-size': '16px'
        },
        // style focus state
        ':focus': {
            // 'color': 'black'
        },
        // style valid state
        '.valid': {
            'color': 'green'
        },
        // style invalid state
        '.invalid': {
            'color': 'red'
        },
        // Media queries
        // Note that these apply to the iframe, not the root window.
        '@media screen and (max-width: 400px)': {
            'input': {
                'color': 'orange'
            }
        }
    },
    // 此設定會顯示卡號輸入正確後，會顯示前六後四碼信用卡卡號
    isMaskCreditCardNumber: true,
    maskCreditCardNumberRange: {
        beginIndex: 6, 
        endIndex: 11
    }
})

// TPDirect.card.onUpdate，得知目前卡片資訊的輸入狀態//

TPDirect.card.onUpdate(function (update) {
    // update.canGetPrime === true
    // --> you can call TPDirect.card.getPrime()
    if (update.canGetPrime) {
        // Enable submit Button to get prime.
        // submitButton.removeAttribute('disabled')
       
    } else {
        // Disable submit Button to get prime.
        // submitButton.setAttribute('disabled', true)
    }
                                            
    // cardTypes = ['mastercard', 'visa', 'jcb', 'amex', 'unknown']
    if (update.cardType === 'visa') {
        // Handle card type visa.
    }

    // number 欄位是錯誤的
    if (update.status.number === 2) {
        // setNumberFormGroupToError()
    } else if (update.status.number === 0) {
        // setNumberFormGroupToSuccess()
    } else {
        // setNumberFormGroupToNormal()
    }
    
    if (update.status.expiry === 2) {
        // setNumberFormGroupToError()
    } else if (update.status.expiry === 0) {
        // setNumberFormGroupToSuccess()
    } else {
        // setNumberFormGroupToNormal()
    }
    
    if (update.status.ccv === 2) {
        // setNumberFormGroupToError()
    } else if (update.status.ccv === 0) {
        // setNumberFormGroupToSuccess()
    } else {
        // setNumberFormGroupToNormal()
    }
});
//Get prime
const bookingSubmitInBookingPage=document.getElementById("bookingSubmitInBookingPage");
bookingSubmitInBookingPage.addEventListener("click", payByCreditCard);
function payByCreditCard(){
    //check input
    let inputFieldsInBookingPage=document.querySelectorAll('.contactItem');
    for (let i = 0; i < inputFieldsInBookingPage.length; i++) {
        if(inputFieldsInBookingPage[i].value==""){
            alert("Please input your information to pay for this order.");
            return;
        }
    }
    inputFieldsInBookingPage=document.querySelectorAll('.tpfield');
    for (let i = 0; i < inputFieldsInBookingPage.length; i++) {
        if(inputFieldsInBookingPage[i].value==""){
            alert("Please input credit card information to pay for this order.");
            return;
        }
    }
    
    //Get prime//
    //TapPay Fields 的 status
    var tappayStatus = TPDirect.card.getTappayFieldsStatus()
    //是否可以 getPrime   
    if (tappayStatus.canGetPrime === false) {
        alert('can not get prime');       
        return;
    }

    // Get prime
    TPDirect.card.getPrime((result) => {
        if (result.status !== 0) {
            alert('get prime error ' + result.msg);
            return;
        }
        // send prime to server, to pay with Pay by Prime API .
        // Pay By Prime Docs: https://docs.tappaysdk.com/tutorial/zh/back.html#pay-by-prime-api
        
        let prime = result.card.prime;
        // send prime to server, to pay with Pay by Prime API
        sendPrimeToBackendServer(prime);
    })
}

function sendPrimeToBackendServer(prime){
    //Prepare request data
    let contactPhone=document.getElementById("contactPhone");
    let requestBody = {
        "prime": prime,
        "order": {
          "price": bookingDataPrice,
          "trip": {
            "attraction": bookingAttraction,
            "date": bookingDataDate,
            "time": bookingDataTime,
          },
          "contact": {
            "name": userInfoName,
            "email": userInfoEmail,
            "phone": contactPhone.value,
          }
        } 
      };
    //Send request to backend 
    let src="/api/orders";
    fetch(src,
            {
                method:"POST",
                headers:{"Content-Type": "application/json"},
                body:JSON.stringify(requestBody),
            }
    ).then(response => response.json())
    .then(function(data){         
            if(data.data){
                window.location.href="thankyou?number=" + data.data.number;         
            }else if(data.error==true){
                alert("Got error:"+data.message); 
                alert("Redirect to home page."); 
                window.location.href="/";             
            }
        }
    ); 
}