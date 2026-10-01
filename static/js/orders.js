/* ==========================================================
                    CafeSync Orders
========================================================== */

const API = "";

function escapeOrderText(value){
    return String(value ?? "").replace(/[&<>\"']/g, char => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
    })[char]);
}

function orderItemAddonNames(item){
    let addons = item?.addons || [];
    if (typeof addons === "string") { try { addons = JSON.parse(addons); } catch { addons = []; } }
    return Array.isArray(addons) ? addons.map(addon => typeof addon === "string" ? addon : addon.name).filter(Boolean) : [];
}

let orders = [];

let filteredOrders = [];

let currentPage = 1;

const pageSize = 10;

let selectedOrder = null;


/* ==========================================================
                    ELEMENTS
========================================================== */

const ordersBody =
document.getElementById("ordersBody");

const searchInput =
document.getElementById("searchOrder");

const statusFilter =
document.getElementById("statusFilter");

const paymentFilter =
document.getElementById("paymentFilter");

const paymentStateFilter =
document.getElementById("paymentStateFilter");

const dateFilter =
document.getElementById("filterDate");

const refreshBtn =
document.getElementById("refreshOrders");


/* ==========================================================
                    LOAD ORDERS
========================================================== */

async function loadOrders(){

    try{

        showLoading();

        const response = await fetch(

            API + "/orders"

        );

        const result = await response.json();

        hideLoading();

        if(result.success){

            orders = result.data;

            filteredOrders = [...orders];

            await loadDashboard();

            renderOrders();

        }

        else{

            showToast(

                result.message,

                false

            );

        }

    }

    catch(error){

        console.error(error);

        hideLoading();

        showToast(

            "Unable To Load Orders",

            false

        );

    }

}


/* ==========================================================
                    LOAD DASHBOARD
========================================================== */

async function loadDashboard(){

    try{

        const response = await fetch(

            API + "/orders/dashboard"

        );

        const result = await response.json();

        if(!result.success){

            return;

        }

        const d = result.data;

        document.getElementById("todayOrders").textContent =
            d.total_orders;

        document.getElementById("todayRevenue").textContent =
            "₹" + Number(d.revenue).toFixed(2);

        document.getElementById("pendingOrders").textContent =
            d.pending;

        document.getElementById("completedOrders").textContent =
            d.completed;

        document.getElementById("footerOrders").textContent =
            d.total_orders;

        document.getElementById("footerRevenue").textContent =
            "₹" + Number(d.revenue).toFixed(2);

    }

    catch(err){

        console.log(err);

    }

}


/* ==========================================================
                    RENDER
========================================================== */

function renderOrders(){

    ordersBody.innerHTML="";

    const start =

    (currentPage-1)*pageSize;

    const end =

    start+pageSize;

    const pageOrders =

    filteredOrders.slice(

        start,

        end

    );

    pageOrders.forEach(order=>{

        const row = createOrderRow(order);

        ordersBody.appendChild(row);

    });

    document

    .getElementById("pageNumber")

    .textContent =

    "Page "+currentPage;

}
/* ==========================================================
                    CREATE ORDER ROW
========================================================== */

function createOrderRow(order){

    const template =

    document

    .getElementById("orderRowTemplate")

    .content

    .cloneNode(true);

    const row =

    template.querySelector("tr");

    row.dataset.id = order.id;

    row.classList.add(

        String(order.status || "Pending").toLowerCase()+"-row"

    );

    template.querySelector(".order-number")

        .textContent = order.order_number || order.bill_no || `#${order.id}`;

    template.querySelector(".table-number")

        .textContent =

        order.table_number ||

        order.table ||

        "-";

    template.querySelector(".customer-name")

        .textContent =

        order.customer_name ||

        "Walk-in Customer";

    template.querySelector(".item-count")

        .textContent =

        order.total_items +

        " Items";

    template.querySelector(".order-total")

        .textContent =

        "₹" +

        Number(order.total).toFixed(2);

    template.querySelector(".payment-method")

        .textContent =

        `${order.payment_method || "—"} · ${order.payment_state || order.payment_status || "Pending"}`;

    const badge =

    template.querySelector(".status-badge");

    badge.textContent = order.status || "Pending";

    badge.className =

        "status-badge " +

        String(order.status || "Pending").toLowerCase();

    template.querySelector(".order-time")

        .textContent =

        formatDateTime(order.created_at);

    template.querySelector(".view-btn")

        .onclick = () => viewOrder(order.id);

    template.querySelector(".print-btn")

        .onclick = () => printReceipt(order.id);

    template.querySelector(".cancel-btn")

        .onclick = () => openCancelModal(order.id);

    template.querySelector(".refund-btn")

        .onclick = () => openRefundModal(order.id);

    const paidButton = template.querySelector(".paid-btn");
    const state = String(order.payment_state || order.payment_status || "Pending").toLowerCase();
    const status = String(order.status || "Pending");
    if (paidButton) {
        paidButton.hidden = state === "paid" || state === "refunded" || status === "Cancelled" || status === "Refunded";
        paidButton.onclick = () => markOrderPaid(order.id);
    }
    const refundButton = template.querySelector(".refund-btn");
    if (refundButton) refundButton.hidden = !(["Served", "Completed"].includes(status) && state === "paid");
    const cancelButton = template.querySelector(".cancel-btn");
    if (cancelButton) cancelButton.hidden = ["Served", "Completed", "Cancelled", "Refunded"].includes(status);

    return row;

}


/* ==========================================================
                    FORMAT DATE
========================================================== */

function formatDateTime(date){

    if(!date) return "-";

    return new Date(date)

    .toLocaleString();

}


/* ==========================================================
                    VIEW ORDER
========================================================== */

function viewOrder(orderId){

    selectedOrder =

    orders.find(

        o=>o.id===orderId

    );

    if(!selectedOrder){

        return;

    }

    const container =

    document

    .getElementById("orderDetails");

    container.innerHTML = "";

    container.innerHTML += `

        <div class="detail-section">

            <h3>Order Information</h3>

            <div class="detail-row">

                <span class="detail-label">

                    Order No

                </span>

                <span class="detail-value">

                    ${selectedOrder.order_number || selectedOrder.bill_no || `#${selectedOrder.id}`}

                </span>

            </div>

            <div class="detail-row">

                <span class="detail-label">

                    Customer

                </span>

                <span class="detail-value">

                    ${selectedOrder.customer_name || "Walk-in"}

                </span>

            </div>

            <div class="detail-row">

                <span class="detail-label">

                    Table

                </span>

                <span class="detail-value">

                    ${selectedOrder.table_number || selectedOrder.order_type || "—"}

                </span>

            </div>

            <div class="detail-row">

                <span class="detail-label">

                    Payment

                </span>

                <span class="detail-value">

                    ${selectedOrder.payment_method || "—"} · ${selectedOrder.payment_state || selectedOrder.payment_status || "Pending"}

                </span>

            </div>

            <div class="detail-row">

                <span class="detail-label">

                    Status

                </span>

                <span class="detail-value">

                    ${selectedOrder.status}

                </span>

            </div>

        </div>

    `;

    container.innerHTML +=

    `<div class="detail-section">

        <h3>Items</h3>

        <div class="detail-items">

    `;

    selectedOrder.items.forEach(item=>{

        container.innerHTML += `

            <div class="detail-item">

                <span>

                    ${item.quantity} × ${escapeOrderText(item.name)}

                </span>

                <span>

                    ₹${Number(item.price).toFixed(2)}

                </span>

            </div>

        `;

        if (item.chef_note) {
            const note = document.createElement("small");
            note.className = "item-note-detail";
            note.textContent = `Note: ${item.chef_note}`;
            container.lastElementChild.appendChild(note);
        }
        const extras = orderItemAddonNames(item);
        if (extras.length) {
            const addonLabel = document.createElement("small");
            addonLabel.className = "item-note-detail";
            addonLabel.textContent = `Extras: ${extras.join(", ")}`;
            container.lastElementChild.appendChild(addonLabel);
        }

    });

    const splitSummary = selectedOrder.split_details?.people?.length
        ? `<div class="detail-section"><h3>Split by person</h3>${selectedOrder.split_details.people.map(person => {
            const assigned = (person.items || []).map(allocation => {
                const item = selectedOrder.items[allocation.line_index];
                return item ? `${allocation.quantity} × ${escapeOrderText(item.name)}` : "";
            }).filter(Boolean).join(", ");
            return `<p><strong>Person ${Number(person.person_number)} · ₹${Number(person.amount).toFixed(2)}</strong><br><small>${assigned}</small></p>`;
        }).join("")}</div>`
        : "";

    container.innerHTML += `

        </div>

        ${splitSummary}

        <h2 class="text-right mt-20">

            Total :

            ₹${Number(selectedOrder.total).toFixed(2)}

        </h2>

    </div>

    `;

    document

    .getElementById("orderModal")

    .classList.add("active");

}
/* ==========================================================
                    PRINT RECEIPT
========================================================== */

function printReceipt(orderId){

    const order = orders.find(

        o => o.id === orderId

    );

    if(!order){

        return;

    }

    const preview =

    document.getElementById(

        "receiptPreview"

    );

    preview.innerHTML = `

        <div class="receipt">

            <div class="receipt-header">

                <h2>CafeSync</h2>

                <p>Cafe Receipt</p>

                <hr>

            </div>

            <p>

                <b>Order :</b>

                ${order.order_number || order.bill_no || `#${order.id}`}

            </p>

            <p>

                <b>Customer :</b>

                ${order.customer_name || "Walk-in"}

            </p>

            <p>

                <b>Table :</b>

                ${order.table_number || order.order_type || "—"}

            </p>

            <table class="receipt-table">

                <thead>

                    <tr>

                        <th>Item</th>

                        <th>Qty</th>

                        <th>Price</th>

                    </tr>

                </thead>

                <tbody>

                    ${order.items.map(item => `

                        <tr>

                            <td>${escapeOrderText(item.name)}${orderItemAddonNames(item).length ? `<br><small>Extras: ${escapeOrderText(orderItemAddonNames(item).join(", "))}</small>` : ""}${item.chef_note ? `<br><small>Note: ${escapeOrderText(item.chef_note)}</small>` : ""}</td>

                            <td>${item.quantity}</td>

                            <td>

                                ₹${Number(item.price).toFixed(2)}

                            </td>

                        </tr>

                    `).join("")}

                </tbody>

            </table>

            <div class="receipt-total">

                Total :

                ₹${Number(order.total).toFixed(2)}

            </div>

        </div>

    `;

    document

    .getElementById("receiptModal")

    .classList.add("active");

}

document

.getElementById("printReceipt")

.onclick = function(){

    window.print();

};


/* ==========================================================
                    CANCEL ORDER
========================================================== */

let cancelOrderId = null;

function openCancelModal(orderId){

    cancelOrderId = orderId;

    document

    .getElementById("cancelModal")

    .classList.add("active");

}

async function markOrderPaid(orderId){
    try {
        const response = await fetch(`${API}/orders/${orderId}/payment`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({})
        });
        const result = await response.json();
        showToast(result.message, result.success);
        if (result.success) loadOrders();
    } catch (error) {
        showToast("Unable To Update Payment", false);
    }
}

document

.getElementById("confirmCancel")

.onclick = async function(){

    try{

        const response = await fetch(

            API +

            "/orders/cancel/" +

            cancelOrderId,

            {

                method:"PUT"

            }

        );

        const result =

        await response.json();

        showToast(result.message);

        document

        .getElementById("cancelModal")

        .classList.remove("active");

        loadOrders();

    }

    catch{

        showToast(

            "Unable To Cancel Order",

            false

        );

    }

};


/* ==========================================================
                    REFUND ORDER
========================================================== */

let refundOrderId = null;

function openRefundModal(orderId){

    refundOrderId = orderId;

    document

    .getElementById("refundModal")

    .classList.add("active");

}

document

.getElementById("confirmRefund")

.onclick = async function(){

    const reason =

    document

    .getElementById("refundReason")

    .value;

    try{

        const response = await fetch(

            API +

            "/orders/refund/" +

            refundOrderId,

            {

                method:"PUT",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify({

                    reason:reason

                })

            }

        );

        const result =

        await response.json();

        showToast(result.message);

        document

        .getElementById("refundModal")

        .classList.remove("active");

        loadOrders();

    }

    catch{

        showToast(

            "Unable To Refund Order",

            false

        );

    }

};


/* ==========================================================
                    REFRESH
========================================================== */

refreshBtn.onclick = loadOrders;


/* ==========================================================
                    TOAST
========================================================== */

function showToast(

    message,

    success=true

){

    const toast =

    document

    .getElementById("toast");

    toast.textContent = message;

    toast.style.display = "block";

    toast.style.background =

    success

    ? "#4CAF50"

    : "#F44336";

    setTimeout(function(){

        toast.style.display="none";

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
                    SEARCH & FILTER
========================================================== */

function applyFilters(){

    const search =

    searchInput.value.toLowerCase().trim();

    const status =

    statusFilter.value;

        const payment =

    paymentFilter.value;

    const paymentState = paymentStateFilter ? paymentStateFilter.value : "";

    const date =

    dateFilter.value;

    filteredOrders = orders.filter(order=>{

        const matchesSearch =

            !search ||

            String(order.order_number || order.bill_no || order.id).toLowerCase().includes(search) ||

            (order.customer_name || "")

            .toLowerCase()

            .includes(search) ||

            String(order.table_number || order.order_type || "")

            .toLowerCase()

            .includes(search);

        const matchesStatus =

            !status ||

            order.status === status;

        const matchesPayment =

            !payment ||

            order.payment_method === payment;

        const matchesPaymentState = !paymentState ||
            String(order.payment_state || order.payment_status || "Pending").toLowerCase() === paymentState.toLowerCase();

        let matchesDate = true;

        if(date){

            const orderDate =

            new Date(order.created_at)

            .toISOString()

            .split("T")[0];

            matchesDate =

            orderDate === date;

        }

        return (

            matchesSearch &&

            matchesStatus &&

            matchesPayment &&

            matchesPaymentState &&

            matchesDate

        );

    });

    currentPage = 1;

    renderOrders();

    toggleEmptyState();

}

searchInput.addEventListener(

    "input",

    applyFilters

);

statusFilter.addEventListener(

    "change",

    applyFilters

);

paymentFilter.addEventListener(

    "change",

    applyFilters

);

dateFilter.addEventListener(

    "change",

    applyFilters

);


/* ==========================================================
                    EMPTY STATE
========================================================== */

function toggleEmptyState(){

    document

    .getElementById("emptyState")

    .style.display =

    filteredOrders.length===0

    ? "block"

    : "none";

}


/* ==========================================================
                    PAGINATION
========================================================== */

document

.getElementById("prevPage")

.onclick=function(){

    if(currentPage>1){

        currentPage--;

        renderOrders();

    }

};

document

.getElementById("nextPage")

.onclick=function(){

    const maxPage =

    Math.ceil(

        filteredOrders.length /

        pageSize

    );

    if(currentPage<maxPage){

        currentPage++;

        renderOrders();

    }

};


/* ==========================================================
                    CLOSE MODALS
========================================================== */

document

.querySelectorAll(".close-modal")

.forEach(btn=>{

    btn.onclick=function(){

        document

        .querySelectorAll(".modal")

        .forEach(modal=>{

            modal.classList.remove(

                "active"

            );

        });

    };

});


/* ==========================================================
                    EXPORT MENU
========================================================== */

const exportButton =

document.getElementById(

    "exportButton"

);

const exportMenu =

document.getElementById(

    "exportMenu"

);

exportButton.onclick=function(){

    exportMenu.classList.toggle(

        "show"

    );

};

document.addEventListener(

    "click",

    function(e){

        if(

            !exportButton.contains(e.target)

            &&

            !exportMenu.contains(e.target)

        ){

            exportMenu.classList.remove(

                "show"

            );

        }

    }

);


/* ==========================================================
                    EXPORT
========================================================== */

document

.getElementById("exportExcel")

.onclick=function(){

    window.open(

        API+

        "/orders/export/excel"

    );

};

document

.getElementById("exportPDF")

.onclick=function(){

    window.open(

        API+

        "/orders/export/pdf"

    );

};


/* ==========================================================
                    AUTO REFRESH
========================================================== */

setInterval(function(){

    loadOrders();

},30000);
/* ==========================================================
                    INITIALIZATION
========================================================== */

window.onload = async function(){

    await loadDashboard();

    await loadOrders();

}


/* ==========================================================
                    ESC CLOSE MODALS
========================================================== */

document.addEventListener(

    "keydown",

    function(e){

        if(e.key === "Escape"){

            document

            .querySelectorAll(".modal")

            .forEach(modal=>{

                modal.classList.remove(

                    "active"

                );

            });

        }

    }

);


/* ==========================================================
                    CLICK OUTSIDE MODAL
========================================================== */

document

.querySelectorAll(".modal")

.forEach(modal=>{

    modal.addEventListener(

        "click",

        function(e){

            if(e.target===modal){

                modal.classList.remove(

                    "active"

                );

            }

        }

    );

});


/* ==========================================================
                    TABLE ROW ANIMATION
========================================================== */

function highlightRow(orderId){

    const row =

    document.querySelector(

        `tr[data-id="${orderId}"]`

    );

    if(!row){

        return;

    }

    row.classList.add(

        "table-highlight"

    );

    setTimeout(function(){

        row.classList.remove(

            "table-highlight"

        );

    },1000);

}


/* ==========================================================
                    BETTER TOAST
========================================================== */

const oldToast = showToast;

showToast = function(

    message,

    success=true

){

    oldToast(

        message,

        success

    );

};


/* ==========================================================
                    RECEIPT PRINT
========================================================== */

document

.getElementById("printReceipt")

.addEventListener(

    "click",

    function(){

        const content =

        document

        .getElementById(

            "receiptPreview"

        )

        .innerHTML;

        const printWindow =

        window.open(

            "",

            "_blank",

            "width=400,height=700"

        );

        printWindow.document.write(`

            <html>

            <head>

                <title>

                    CafeSync Receipt

                </title>

                <style>

                    body{

                        font-family:Arial;

                        padding:20px;

                    }

                    table{

                        width:100%;

                        border-collapse:collapse;

                    }

                    th,td{

                        padding:8px;

                        border-bottom:1px solid #ddd;

                    }

                    h2{

                        text-align:center;

                    }

                </style>

            </head>

            <body>

                ${content}

            </body>

            </html>

        `);

        printWindow.document.close();

        printWindow.focus();

        printWindow.print();

        printWindow.close();

    }

);


/* ==========================================================
                    PERFORMANCE
========================================================== */

window.addEventListener(

    "focus",

    function(){

        loadOrders();

    }

);


/* ==========================================================
                    SHORTCUTS
========================================================== */

document.addEventListener(

    "keydown",

    function(e){

        if(e.ctrlKey && e.key==="r"){

            e.preventDefault();

            loadOrders();

        }

        if(e.ctrlKey && e.key==="f"){

            e.preventDefault();

            searchInput.focus();

        }

    }

);


/* ==========================================================
                    END
========================================================== */

console.log(

    "CafeSync Orders Module Loaded"

);

if (paymentStateFilter) paymentStateFilter.addEventListener("change", applyFilters);
