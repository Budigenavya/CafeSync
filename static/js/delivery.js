/*==========================================================
                CafeSync POS
                delivery.js
                PART 1
==========================================================*/


/*==========================================================
                    API
==========================================================*/

const API = "http://127.0.0.1:5000";


/*==========================================================
                GLOBAL VARIABLES
==========================================================*/

let deliveryOrders = [];

let riders = [];

let selectedOrder = null;

let refreshTimer = null;

let currentPlatform = "all";

let currentStatus = "all";


/*==========================================================
                DOM ELEMENTS
==========================================================*/

const sidebar =
document.getElementById("sidebar");

const main =
document.querySelector(".main");

const menuBtn =
document.getElementById("menuBtn");

const themeBtn =
document.getElementById("themeBtn");

const refreshBtn =
document.getElementById("refreshBtn");

const searchInput =
document.getElementById("searchOrder");

const platformFilter =
document.getElementById("platformFilter");

const statusFilter =
document.getElementById("statusFilter");

const notificationCount =
document.getElementById("notificationCount");


/*==========================================================
                APPLICATION START
==========================================================*/

document.addEventListener("DOMContentLoaded",()=>{

    initializeDashboard();

});


/*==========================================================
            INITIALIZE DASHBOARD
==========================================================*/

async function initializeDashboard(){

    initializeSidebar();

    initializeDarkMode();

    initializeEvents();

    await loadOrders();

    await loadStatistics();

    await loadRiders();

    startAutoRefresh();

}


/*==========================================================
                SIDEBAR
==========================================================*/

function initializeSidebar(){

    if(!menuBtn) return;

    menuBtn.addEventListener("click",()=>{

        sidebar.classList.toggle("collapsed");

        main.classList.toggle("expand");

    });

}


/*==========================================================
                DARK MODE
==========================================================*/

function initializeDarkMode(){

    const saved =
    localStorage.getItem("deliveryTheme");

    if(saved==="dark"){

        document.body.classList.add("dark");

        if(themeBtn){

            themeBtn.innerHTML=
            '<i class="fas fa-sun"></i>';

        }

    }

    if(themeBtn){

        themeBtn.addEventListener("click",()=>{

            document.body.classList.toggle("dark");

            if(document.body.classList.contains("dark")){

                localStorage.setItem(
                    "deliveryTheme",
                    "dark"
                );

                themeBtn.innerHTML=
                '<i class="fas fa-sun"></i>';

            }

            else{

                localStorage.setItem(
                    "deliveryTheme",
                    "light"
                );

                themeBtn.innerHTML=
                '<i class="fas fa-moon"></i>';

            }

        });

    }

}


/*==========================================================
                EVENTS
==========================================================*/

function initializeEvents(){

    if(refreshBtn){

        refreshBtn.addEventListener("click",async()=>{

            refreshBtn.disabled=true;

            refreshBtn.innerHTML=
            '<i class="fas fa-spinner fa-spin"></i>';

            await refreshDashboard();

            refreshBtn.disabled=false;

            refreshBtn.innerHTML=
            '<i class="fas fa-rotate"></i> Refresh';

        });

    }

}


/*==========================================================
            AUTO REFRESH
==========================================================*/

function startAutoRefresh(){

    if(refreshTimer){

        clearInterval(refreshTimer);

    }

    refreshTimer=setInterval(async()=>{

        await refreshDashboard();

    },30000);

}


/*==========================================================
            REFRESH DASHBOARD
==========================================================*/

async function refreshDashboard(){

    try{

        await loadOrders();

        await loadStatistics();

        updateNotificationBadge();

    }

    catch(error){

        console.error(error);

    }

}


/*==========================================================
            STOP AUTO REFRESH
==========================================================*/

window.addEventListener("beforeunload",()=>{

    if(refreshTimer){

        clearInterval(refreshTimer);

    }

});
/*==========================================================
                CafeSync POS
                delivery.js
                PART 2
        LOAD & RENDER DELIVERY ORDERS
==========================================================*/


/*==========================================================
                LOAD ORDERS
==========================================================*/

async function loadOrders(){

    try{

        const response = await fetch(
            `${API}/delivery/orders`
        );

        if(!response.ok){

            throw new Error("Unable to load orders");

        }

        deliveryOrders = await response.json();

        renderOrders(deliveryOrders);

    }

    catch(error){

        console.error(error);

        showEmptyBoard();

    }

}


/*==========================================================
                RENDER ORDERS
==========================================================*/

function renderOrders(orders){

    clearBoard();

    orders.forEach(order=>{

        addOrderCard(order);

    });

    updateColumnCounts();

}


/*==========================================================
            CLEAR BOARD
==========================================================*/

function clearBoard(){

    document.getElementById("newOrders").innerHTML="";

    document.getElementById("preparingOrders").innerHTML="";

    document.getElementById("readyOrders").innerHTML="";

    document.getElementById("deliveryOrders").innerHTML="";

    document.getElementById("completedOrders").innerHTML="";

}


/*==========================================================
            CREATE ORDER CARD
==========================================================*/

function addOrderCard(order){

    const card=document.createElement("div");

    card.className="order-card";

    card.dataset.id=order.id;

    card.innerHTML=`

        <div class="order-top">

            <div>

                <h3>#${order.order_number}</h3>

                <small>${order.platform}</small>

            </div>

            <span class="payment ${order.payment_status==="Paid"
            ? "paid":"pending-payment"}">

                ${order.payment_status}

            </span>

        </div>

        <hr>

        <div class="customer">

            <i class="fas fa-user"></i>

            ${order.customer_name}

        </div>

        <div class="phone">

            <i class="fas fa-phone"></i>

            ${order.phone}

        </div>

        <div class="address">

            <i class="fas fa-location-dot"></i>

            ${order.address}

        </div>

        <div class="amount">

            ₹${order.total}

        </div>

        <div class="time">

            <i class="fas fa-clock"></i>

            ${order.time}

        </div>

        <div class="actions">

            <button
            class="details-btn"
            onclick="openOrder(${order.id})">

                Details

            </button>

        </div>

    `;

    switch(order.status){

        case "Pending":

            document
            .getElementById("newOrders")
            .appendChild(card);

            break;

        case "Preparing":

            document
            .getElementById("preparingOrders")
            .appendChild(card);

            break;

        case "Ready":

            document
            .getElementById("readyOrders")
            .appendChild(card);

            break;

        case "Out For Delivery":

            document
            .getElementById("deliveryOrders")
            .appendChild(card);

            break;

        case "Delivered":

            document
            .getElementById("completedOrders")
            .appendChild(card);

            break;

    }

}


/*==========================================================
            COLUMN COUNTS
==========================================================*/

function updateColumnCounts(){

    document.getElementById("newCount").textContent=

    document.getElementById("newOrders").children.length;

    document.getElementById("preparingCount").textContent=

    document.getElementById("preparingOrders").children.length;

    document.getElementById("readyCount").textContent=

    document.getElementById("readyOrders").children.length;

    document.getElementById("deliveryCount").textContent=

    document.getElementById("deliveryOrders").children.length;

    document.getElementById("completedCount").textContent=

    document.getElementById("completedOrders").children.length;

}


/*==========================================================
            EMPTY BOARD
==========================================================*/

function showEmptyBoard(){

    clearBoard();

    const html=`

        <div
        style="padding:30px;
        text-align:center;
        color:#888;">

            <i
            class="fas fa-box-open"
            style="font-size:40px;"></i>

            <p>No Orders Available</p>

        </div>

    `;

    document.getElementById("newOrders").innerHTML=html;

}


/*==========================================================
            UPDATE DASHBOARD STATS
==========================================================*/

async function loadStatistics(){

    document.getElementById("todayOrders").textContent=

    deliveryOrders.length;

    let revenue=0;

    let pending=0;

    deliveryOrders.forEach(order=>{

        revenue+=Number(order.total);

        if(order.status==="Pending")

            pending++;

    });

    document.getElementById("todayRevenue").textContent=

    "₹"+revenue.toFixed(2);

    document.getElementById("pendingOrders").textContent=

    pending;

}
/*==========================================================
                CafeSync POS
                delivery.js
                PART 3
        SEARCH • FILTER • PLATFORM TABS
==========================================================*/


/*==========================================================
                INITIALIZE FILTERS
==========================================================*/

initializeFilters();

function initializeFilters(){

    if(searchInput){

        searchInput.addEventListener("keyup",filterOrders);

    }

    if(platformFilter){

        platformFilter.addEventListener("change",()=>{

            currentPlatform=platformFilter.value;

            filterOrders();

        });

    }

    if(statusFilter){

        statusFilter.addEventListener("change",()=>{

            currentStatus=statusFilter.value;

            filterOrders();

        });

    }

    initializePlatformTabs();

}


/*==========================================================
                PLATFORM TABS
==========================================================*/

function initializePlatformTabs(){

    const tabs=document.querySelectorAll(".platformTabs .tab");

    tabs.forEach(tab=>{

        tab.addEventListener("click",()=>{

            tabs.forEach(t=>t.classList.remove("active"));

            tab.classList.add("active");

            const text=tab.innerText.trim().toLowerCase();

            if(text.includes("swiggy"))

                currentPlatform="Swiggy";

            else if(text.includes("zomato"))

                currentPlatform="Zomato";

            else if(text.includes("website"))

                currentPlatform="Website";

            else if(text.includes("take"))

                currentPlatform="TakeAway";

            else

                currentPlatform="all";

            if(platformFilter){

                platformFilter.value=currentPlatform;

            }

            filterOrders();

        });

    });

}


/*==========================================================
                FILTER ORDERS
==========================================================*/

function filterOrders(){

    const keyword=searchInput.value
                    .toLowerCase()
                    .trim();

    const filtered=deliveryOrders.filter(order=>{

        /*------------------------------
            SEARCH
        ------------------------------*/

        const matchSearch=

            order.order_number
            .toLowerCase()
            .includes(keyword)

            ||

            order.customer_name
            .toLowerCase()
            .includes(keyword)

            ||

            order.phone
            .toLowerCase()
            .includes(keyword)

            ||

            order.address
            .toLowerCase()
            .includes(keyword);


        /*------------------------------
            PLATFORM
        ------------------------------*/

        const matchPlatform=

            currentPlatform==="all"

            ||

            order.platform===currentPlatform;


        /*------------------------------
            STATUS
        ------------------------------*/

        const matchStatus=

            currentStatus==="all"

            ||

            order.status===currentStatus;


        return(

            matchSearch

            &&

            matchPlatform

            &&

            matchStatus

        );

    });

    renderOrders(filtered);

}


/*==========================================================
                RESET FILTERS
==========================================================*/

function resetFilters(){

    searchInput.value="";

    platformFilter.value="all";

    statusFilter.value="all";

    currentPlatform="all";

    currentStatus="all";

    renderOrders(deliveryOrders);

}


/*==========================================================
                NOTIFICATION BADGE
==========================================================*/

function updateNotificationBadge(){

    const pending=

    deliveryOrders.filter(

        o=>o.status==="Pending"

    ).length;

    if(notificationCount){

        notificationCount.textContent=pending;

    }

}


/*==========================================================
                LIVE SEARCH
==========================================================*/

searchInput.addEventListener("focus",()=>{

    searchInput.select();

});


/*==========================================================
                KEYBOARD SHORTCUTS
==========================================================*/

document.addEventListener("keydown",(e)=>{

    /* Ctrl + F */

    if(e.ctrlKey && e.key==="f"){

        e.preventDefault();

        searchInput.focus();

    }

    /* ESC */

    if(e.key==="Escape"){

        resetFilters();

    }

    /* F5 */

    if(e.key==="F5"){

        e.preventDefault();

        refreshDashboard();

    }

});


/*==========================================================
            HIGHLIGHT SEARCH RESULT
==========================================================*/

function highlightText(text,keyword){

    if(keyword==="") return text;

    const regex=new RegExp(

        `(${keyword})`,

        "gi"

    );

    return text.replace(

        regex,

        "<mark>$1</mark>"

    );

}
/*==========================================================
                CafeSync POS
                delivery.js
                PART 4
        ORDER DETAILS MODAL
==========================================================*/


/*==========================================================
                OPEN ORDER
==========================================================*/

async function openOrder(orderId){

    try{

        const response=await fetch(

            `${API}/delivery/order/${orderId}`

        );

        if(!response.ok){

            throw new Error("Unable to load order");

        }

        selectedOrder=await response.json();

        populateModal(selectedOrder);

        document
        .getElementById("orderModal")
        .classList
        .add("show");

    }

    catch(error){

        console.error(error);

        alert("Unable to load order details.");

    }

}


/*==========================================================
                CLOSE MODAL
==========================================================*/

document
.getElementById("closeModal")
.addEventListener("click",closeModal);

function closeModal(){

    document
    .getElementById("orderModal")
    .classList
    .remove("show");

}


/*==========================================================
                POPULATE MODAL
==========================================================*/

function populateModal(order){

    document.getElementById("modalCustomer").textContent=
    order.customer_name;

    document.getElementById("modalPhone").textContent=
    order.phone;

    document.getElementById("modalAddress").textContent=
    order.address;

    document.getElementById("modalPlatform").textContent=
    order.platform;

    document.getElementById("modalOrderID").textContent=
    order.order_number;

    document.getElementById("modalPayment").textContent=
    order.payment_status;

    document.getElementById("modalStatus").textContent=
    order.status;

    document.getElementById("modalSubtotal").textContent=
    "₹"+order.subtotal;

    document.getElementById("modalGST").textContent=
    "₹"+order.gst;

    document.getElementById("modalDelivery").textContent=
    "₹"+order.delivery_charge;

    document.getElementById("modalDiscount").textContent=
    "₹"+order.discount;

    document.getElementById("modalTotal").textContent=
    "₹"+order.total;

    loadItems(order.items);

}


/*==========================================================
                LOAD ITEMS
==========================================================*/

function loadItems(items){

    const tbody=document.getElementById("modalItems");

    tbody.innerHTML="";

    items.forEach(item=>{

        tbody.innerHTML+=`

        <tr>

            <td>${item.name}</td>

            <td>${item.quantity}</td>

            <td>₹${item.price}</td>

        </tr>

        `;

    });

}


/*==========================================================
                UPDATE STATUS
==========================================================*/

async function updateOrderStatus(status){

    if(!selectedOrder) return;

    try{

        const response=await fetch(

            `${API}/delivery/update-status/${selectedOrder.id}`,

            {

                method:"PUT",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    status:status

                })

            }

        );

        const result=await response.json();

        if(result.success){

            closeModal();

            await refreshDashboard();

            alert("Order Updated");

        }

        else{

            alert(result.message);

        }

    }

    catch(error){

        console.error(error);

    }

}


/*==========================================================
            BUTTON EVENTS
==========================================================*/

document
.getElementById("acceptOrder")
.onclick=()=>{

    updateOrderStatus("Accepted");

};

document
.getElementById("prepareOrder")
.onclick=()=>{

    updateOrderStatus("Preparing");

};

document
.getElementById("readyOrder")
.onclick=()=>{

    updateOrderStatus("Ready");

};

document
.getElementById("cancelOrder")
.onclick=()=>{

    if(confirm("Cancel this order?")){

        updateOrderStatus("Cancelled");

    }

};


/*==========================================================
                PRINT
==========================================================*/

document
.getElementById("printInvoice")
.onclick=()=>{

    window.print();

};


/*==========================================================
        CLICK OUTSIDE CLOSES MODAL
==========================================================*/

window.onclick=function(e){

    const modal=document.getElementById("orderModal");

    if(e.target===modal){

        closeModal();

    }

};
/*==========================================================
                CafeSync POS
                delivery.js
                PART 5
==========================================================*/


/*==========================================================
                LOAD RIDERS
==========================================================*/

async function loadRiders(){

    try{

        const response=await fetch(

            `${API}/delivery/riders`

        );

        if(!response.ok){

            throw new Error();

        }

        riders=await response.json();

    }

    catch(error){

        console.log("Unable to load riders");

    }

}


/*==========================================================
            ASSIGN RIDER
==========================================================*/

document
.getElementById("assignRider")
.addEventListener("click",assignRider);

async function assignRider(){

    if(!selectedOrder){

        return;

    }

    const riderId=prompt("Enter Rider ID");

    if(!riderId) return;

    try{

        const response=await fetch(

            `${API}/delivery/assign-rider`,

            {

                method:"POST",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    order_id:selectedOrder.id,

                    rider_id:riderId

                })

            }

        );

        const result=await response.json();

        alert(result.message);

        refreshDashboard();

    }

    catch(error){

        console.log(error);

    }

}


/*==========================================================
                CALL CUSTOMER
==========================================================*/

const callBtn=document.getElementById("callCustomer");

if(callBtn){

callBtn.onclick=()=>{

    if(!selectedOrder) return;

    window.location.href=

    `tel:${selectedOrder.phone}`;

};

}


/*==========================================================
                SMS CUSTOMER
==========================================================*/

const smsBtn=document.getElementById("messageCustomer");

if(smsBtn){

smsBtn.onclick=()=>{

    if(!selectedOrder) return;

    window.location.href=

    `sms:${selectedOrder.phone}`;

};

}


/*==========================================================
            GOOGLE MAP NAVIGATION
==========================================================*/

const navBtn=document.getElementById("navigationBtn");

if(navBtn){

navBtn.onclick=()=>{

    if(!selectedOrder) return;

    const address=

    encodeURIComponent(

        selectedOrder.address

    );

    window.open(

`https://www.google.com/maps/search/?api=1&query=${address}`,

"_blank"

    );

};

}


/*==========================================================
            LIVE NOTIFICATIONS
==========================================================*/

function addNotification(message,type="info"){

    const panel=

    document.getElementById(

        "notificationList"

    );

    if(!panel) return;

    const div=

    document.createElement("div");

    div.className=

    `notify-item ${type}`;

    div.innerHTML=

    `

    <i class="fas fa-bell"></i>

    <div>

        <strong>

        ${message}

        </strong>

        <small>

        ${new Date().toLocaleTimeString()}

        </small>

    </div>

    `;

    panel.prepend(div);

    while(panel.children.length>15){

        panel.removeChild(

            panel.lastChild

        );

    }

}


/*==========================================================
            ORDER TIMER
==========================================================*/

function updateTimers(){

    const cards=

    document.querySelectorAll(

        ".order-card"

    );

    cards.forEach(card=>{

        const time=

        card.querySelector(".time");

        if(!time) return;

    });

}

setInterval(updateTimers,1000);


/*==========================================================
        AUTO REFRESH NOTIFICATION
==========================================================*/

setInterval(async()=>{

    const before=

    deliveryOrders.length;

    await loadOrders();

    if(deliveryOrders.length>before){

        addNotification(

            "New Delivery Order",

            "new"

        );

    }

},30000);


/*==========================================================
            REFRESH RIDERS
==========================================================*/

const refreshRiderBtn=

document.getElementById(

"refreshRiders"

);

if(refreshRiderBtn){

refreshRiderBtn.onclick=async()=>{

    await loadRiders();

    addNotification(

        "Rider list updated",

        "success"

    );

};

}


/*==========================================================
            WINDOW ONLINE/OFFLINE
==========================================================*/

window.addEventListener(

"offline",

()=>{

addNotification(

"Internet Connection Lost",

"warning"

);

}

);

window.addEventListener(

"online",

()=>{

addNotification(

"Internet Connected",

"success"

);

}

);


/*==========================================================
            PAGE LOADED
==========================================================*/

addNotification(

"Delivery Dashboard Ready",

"success"

);