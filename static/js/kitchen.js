/* ==========================================================
                    CafeSync Kitchen Display
                    kitchen.js - Part 1
========================================================== */

const API = "http://127.0.0.1:5000";

let kitchenOrders = [];

let previousOrderCount = 0;


/* ==========================================================
                    ELEMENTS
========================================================== */

const pendingContainer =
document.getElementById("pendingOrders");

const preparingContainer =
document.getElementById("preparingOrders");

const readyContainer =
document.getElementById("readyOrders");

const refreshBtn =
document.getElementById("refreshOrders");

const searchInput =
document.getElementById("searchOrder");


/* ==========================================================
                    LIVE CLOCK
========================================================== */

function updateClock(){

    const now = new Date();

    document.getElementById("liveClock").textContent =
        now.toLocaleTimeString();

}

setInterval(updateClock,1000);

updateClock();


/* ==========================================================
                    LOAD ORDERS
========================================================== */

async function loadKitchenOrders(){

    try{

        showLoading();

        const response = await fetch(

            API + "/kitchen/orders"

        );

        const result = await response.json();

        hideLoading();

        if(result.success){

            kitchenOrders = result.data;

            updateSummary();

            renderOrders();

            updateEmptyState();

            checkNewOrders();

        }

        else{

            showToast(result.message,false);

        }

    }

    catch(error){

        hideLoading();

        console.error(error);

        showToast("Unable to Load Orders",false);

    }

}


/* ==========================================================
                    RENDER
========================================================== */

function renderOrders(){

    pendingContainer.innerHTML = "";

    preparingContainer.innerHTML = "";

    readyContainer.innerHTML = "";

    const keyword =
        searchInput.value.toLowerCase();

    kitchenOrders.forEach(order=>{

        if(

            keyword !== "" &&

            !String(order.table_name)
            .toLowerCase()
            .includes(keyword)

            &&

            !String(order.order_number)
            .toLowerCase()
            .includes(keyword)

        ){

            return;

        }

        const card = createOrderCard(order);

        if(order.status==="Pending"){

            pendingContainer.appendChild(card);

        }

        else if(order.status==="Preparing"){

            preparingContainer.appendChild(card);

        }

        else if(order.status==="Ready"){

            readyContainer.appendChild(card);

        }

    });

}


/* ==========================================================
                    CARD
========================================================== */

function createOrderCard(order){

    const template =

    document

    .getElementById("orderCardTemplate")

    .content

    .cloneNode(true);

    const card = template.querySelector(".order-card");

    card.dataset.id = order.id;

    template.querySelector(".table-name")

        .textContent = order.table_name;

    template.querySelector(".order-number")

        .textContent = order.order_number;

    template.querySelector(".customer-name")

        .textContent =

        order.customer_name ||

        "Walk-in Customer";

    template.querySelector(".bill-total")

        .textContent =

        "₹" + Number(order.total).toFixed(2);

    template.querySelector(".item-count")

        .textContent =

        order.total_items + " Items";

    // Live Timer
    const timer = template.querySelector(".order-time span");

    timer.dataset.time = order.created_at;

    timer.textContent = "0 min";

    const itemsBox =

    template.querySelector(".items-list");

    itemsBox.innerHTML = "";

    order.items.forEach(item => {

        itemsBox.innerHTML += `

            <div class="item-row">

                <span>

                    ${item.quantity} × ${item.name}

                </span>

            </div>

        `;

    });

    template.querySelector(".btn-start")

        .onclick = () => startPreparing(order.id);

    template.querySelector(".btn-ready")

        .onclick = () => markReady(order.id);

    template.querySelector(".btn-served")

        .onclick = () => serveOrder(order.id);

    return template;

}

/* ==========================================================
                    SUMMARY
========================================================== */

function updateSummary(){

    document

    .getElementById("pendingCount")

    .textContent =

    kitchenOrders.filter(

        o=>o.status==="Pending"

    ).length;

    document

    .getElementById("preparingCount")

    .textContent =

    kitchenOrders.filter(

        o=>o.status==="Preparing"

    ).length;

    document

    .getElementById("readyCount")

    .textContent =

    kitchenOrders.filter(

        o=>o.status==="Ready"

    ).length;

}


/* ==========================================================
                    REFRESH
========================================================== */

refreshBtn.onclick = loadKitchenOrders;

searchInput.addEventListener(

    "keyup",

    renderOrders

);
/* ==========================================================
                    START PREPARING
========================================================== */

async function startPreparing(orderId){

    try{

        const response = await fetch(

            API + "/kitchen/start-preparing/" + orderId,

            {

                method:"PUT"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(result.message);

            loadKitchenOrders();

        }

        else{

            showToast(result.message,false);

        }

    }

    catch(error){

        console.error(error);

        showToast("Unable to Start Preparing",false);

    }

}


/* ==========================================================
                    MARK READY
========================================================== */

async function markReady(orderId){

    try{

        const response = await fetch(

            API + "/kitchen/ready/" + orderId,

            {

                method:"PUT"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(result.message);

            loadKitchenOrders();

        }

        else{

            showToast(result.message,false);

        }

    }

    catch(error){

        console.error(error);

        showToast("Unable to Mark Ready",false);

    }

}


/* ==========================================================
                    SERVE ORDER
========================================================== */

async function serveOrder(orderId){

    if(!confirm("Serve this order?")){

        return;

    }

    try{

        const response = await fetch(

            API + "/kitchen/serve/" + orderId,

            {

                method:"PUT"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(result.message);

            loadKitchenOrders();

        }

        else{

            showToast(result.message,false);

        }

    }

    catch(error){

        console.error(error);

        showToast("Unable to Serve Order",false);

    }

}


/* ==========================================================
                    AUTO REFRESH
========================================================== */

setInterval(function(){

    loadKitchenOrders();

},5000);


/* ==========================================================
                    NEW ORDER ALERT
========================================================== */

function checkNewOrders(){

    const currentCount = kitchenOrders.length;

    if(previousOrderCount !== 0 && currentCount > previousOrderCount){

        showNotification("New Kitchen Order Received");

        playOrderSound();

    }

    previousOrderCount = currentCount;

}


/* ==========================================================
                    PLAY SOUND
========================================================== */

function playOrderSound(){

    const audio =

    document.getElementById("newOrderSound");

    if(audio){

        audio.currentTime = 0;

        audio.play().catch(()=>{});

    }

}


/* ==========================================================
                    NOTIFICATION
========================================================== */

function showNotification(message){

    const box =

    document.getElementById("notification");

    document

    .getElementById("notificationText")

    .textContent = message;

    box.classList.add("show");

    setTimeout(function(){

        box.classList.remove("show");

    },4000);

}
/* ==========================================================
                    LIVE ORDER TIMER
========================================================== */

function updateOrderTimers(){

    const timers = document.querySelectorAll(".order-time span");

    timers.forEach(timer=>{

        const created = timer.dataset.time;

        if(!created) return;

        const createdTime = new Date(created);

        const now = new Date();

        const minutes = Math.floor(

            (now - createdTime)/60000

        );

        timer.textContent = minutes + " min";

        if(minutes >= 15){

            const card = timer.closest(".order-card");

            if(card){

                card.style.borderLeft =
                "6px solid #d32f2f";

                addPriorityBadge(card);

            }

        }

    });

}

setInterval(updateOrderTimers,60000);


/* ==========================================================
                    PRIORITY BADGE
========================================================== */

function addPriorityBadge(card){

    if(card.querySelector(".priority-badge")){

        return;

    }

    const badge =

    document

    .getElementById("priorityTemplate")

    .content

    .cloneNode(true);

    card.appendChild(badge);

}


/* ==========================================================
                    ORDER DETAILS
========================================================== */

function openOrderDetails(order){

    const modal =

    document.getElementById("orderModal");

    const body =

    document.getElementById("orderDetails");

    body.innerHTML = `

        <h2>${order.order_number}</h2>

        <p>

            <b>Table :</b>

            ${order.table_name}

        </p>

        <p>

            <b>Customer :</b>

            ${order.customer_name || "Walk-in"}

        </p>

        <p>

            <b>Status :</b>

            ${order.status}

        </p>

        <hr>

    `;

    order.items.forEach(item=>{

        body.innerHTML += `

            <p>

                ${item.quantity} × ${item.name}

            </p>

        `;

    });

    body.innerHTML += `

        <hr>

        <h3>

            Total :

            ₹${Number(order.total).toFixed(2)}

        </h3>

    `;

    modal.classList.add("active");

}


/* ==========================================================
                    CLOSE MODALS
========================================================== */

document

.querySelectorAll(".close-modal")

.forEach(btn=>{

    btn.onclick=function(){

        document

        .querySelectorAll(".modal")

        .forEach(m=>{

            m.classList.remove("active");

        });

    };

});


/* ==========================================================
                    CHEF NOTES
========================================================== */

let selectedOrderId = null;

function openChefNotes(orderId){

    selectedOrderId = orderId;

    document

    .getElementById("chefNoteModal")

    .classList.add("active");

}


document

.getElementById("saveChefNotes")

.onclick = async function(){

    const notes =

    document

    .getElementById("chefNotes")

    .value;

    try{

        await fetch(

            API+"/kitchen/notes/"+selectedOrderId,

            {

                method:"PUT",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    notes:notes

                })

            }

        );

        showToast("Chef Notes Saved");

        document

        .getElementById("chefNoteModal")

        .classList.remove("active");

    }

    catch{

        showToast(

            "Unable to Save Notes",

            false

        );

    }

};


/* ==========================================================
                    LAST UPDATED
========================================================== */

function updateLastUpdated(){

    document

    .getElementById("lastUpdated")

    .textContent =

    new Date()

    .toLocaleTimeString();

}

setInterval(updateLastUpdated,1000);

updateLastUpdated();


/* ==========================================================
                    DOUBLE CLICK
========================================================== */

document.addEventListener("dblclick",function(e){

    const card =

    e.target.closest(".order-card");

    if(!card) return;

    const id = Number(card.dataset.id);

    const order =

    kitchenOrders.find(

        o=>o.id===id

    );

    if(order){

        openOrderDetails(order);

    }

});
/* ==========================================================
                    TOAST
========================================================== */

function showToast(message, success = true){

    let toast = document.getElementById("toast");

    if(!toast){

        toast = document.createElement("div");

        toast.id = "toast";

        toast.style.position = "fixed";
        toast.style.bottom = "25px";
        toast.style.right = "25px";
        toast.style.padding = "15px 25px";
        toast.style.borderRadius = "10px";
        toast.style.color = "#fff";
        toast.style.fontWeight = "bold";
        toast.style.zIndex = "9999";

        document.body.appendChild(toast);

    }

    toast.style.background = success ? "#4CAF50" : "#F44336";

    toast.textContent = message;

    toast.style.display = "block";

    setTimeout(function(){

        toast.style.display = "none";

    },3000);

}


/* ==========================================================
                    LOADING
========================================================== */

function showLoading(){

    document

    .getElementById("loadingScreen")

    .classList.add("active");

}

function hideLoading(){

    document

    .getElementById("loadingScreen")

    .classList.remove("active");

}


/* ==========================================================
                    EMPTY STATE
========================================================== */

function updateEmptyState(){

    const total =

        pendingContainer.children.length +

        preparingContainer.children.length +

        readyContainer.children.length;

    document

    .getElementById("emptyOrders")

    .style.display =

    total===0 ? "block" : "none";

}


/* ==========================================================
                    UPDATE STATUS
========================================================== */

function updateKitchenStatus(){

    document

    .getElementById("kitchenStatus")

    .textContent = "Online";

}


/* ==========================================================
                    AFTER RENDER
========================================================== */

const originalRender = renderOrders;

renderOrders = function(){

    originalRender();

    updateEmptyState();

    updateOrderTimers();

};


/* ==========================================================
                    INITIALIZE
========================================================== */

window.onload = function(){

    updateKitchenStatus();

    updateClock();

    updateLastUpdated();

    loadKitchenOrders();

};