const urlAbsolute = window.location.href; 
//Get order id from query string in url
let temp = urlAbsolute.split('?');
temp =temp[1].split('=');
const queryStringValue=temp[1];

window.onload=function(){
    const orderIdBlock=document.getElementById("orderIdInThankyouPage");
    orderIdBlock.textContent=queryStringValue;
    checkOrderStatus();
}
function checkOrderStatus(){
    let src=`/api/orders/${queryStringValue}`;

    fetch(src,
            {
                method:"GET",
                headers:{"Content-Type": "application/json"},
            }
    ).then(response => response.json())
    .then(function(data){
            if(data.data){
                const orderStatusBlock=document.getElementById("orderStatusInThankyouPage");
                if(data.data.status==0){
                    orderStatusBlock.textContent=" 成功，已付款。";
                }else{
                    orderStatusBlock.textContent=" 失敗! 若有疑問，請提供訂單編號，我們將為您確認詳情，謝謝。";
                }
                
            }else{
                console.log(data.message);
            }
        }
    ); 
}
