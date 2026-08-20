/* ==========================================================
                    API
========================================================== */

const API = "http://127.0.0.1:5000";

let dashboard = {};
let charts = {};

let recentOrders = [];
let topProducts = [];
let refunds = [];
let lowStock = [];


/* ==========================================================
                    DOM
========================================================== */

const reportType =
document.getElementById("reportType");

const startDate =
document.getElementById("startDate");

const endDate =
document.getElementById("endDate");

const loading =
document.getElementById("loadingScreen");

const toast =
document.getElementById("toast");


/* ==========================================================
                    LOADING
========================================================== */

function showLoading(){

    loading.classList.add("active");

}

function hideLoading(){

    loading.classList.remove("active");

}


/* ==========================================================
                    TOAST
========================================================== */

function showToast(

    message,

    success=true

){

    toast.innerHTML = message;

    toast.style.background =

    success

    ? "#4CAF50"

    : "#F44336";

    toast.classList.add("show");

    setTimeout(function(){

        toast.classList.remove("show");

    },3000);

}


/* ==========================================================
                    LOAD DASHBOARD
========================================================== */

async function loadDashboard(){

    try{

        showLoading();

        const response = await fetch(

            API+"/reports/dashboard"

        );

        const result =

        await response.json();

        if(!result.success){

            showToast(

                result.message,

                false

            );

            hideLoading();

            return;

        }

        dashboard = result.data;

        renderDashboard();

        hideLoading();

    }

    catch(err){

        console.log(err);

        hideLoading();

        showToast(

            "Unable To Load Dashboard",

            false

        );

    }

}


/* ==========================================================
                    RENDER DASHBOARD
========================================================== */

function renderDashboard(){

    document.getElementById(

        "todayRevenue"

    ).textContent =

    "₹"+Number(

        dashboard.today_revenue || 0

    ).toFixed(2);

    document.getElementById(

        "todayOrders"

    ).textContent =

    dashboard.today_orders || 0;

    document.getElementById(

        "averageBill"

    ).textContent =

    "₹"+Number(

        dashboard.average_bill || 0

    ).toFixed(2);

    document.getElementById(

        "gstCollected"

    ).textContent =

    "₹"+Number(

        dashboard.gst || 0

    ).toFixed(2);

    document.getElementById(

        "refundAmount"

    ).textContent =

    "₹"+Number(

        dashboard.refunds || 0

    ).toFixed(2);

    document.getElementById(

        "totalCustomers"

    ).textContent =

    dashboard.customers || 0;

    document.getElementById(

        "footerRevenue"

    ).textContent =

    "₹"+Number(

        dashboard.total_revenue || 0

    ).toFixed(2);

    document.getElementById(

        "footerOrders"

    ).textContent =

    dashboard.total_orders || 0;

    document.getElementById(

        "generatedTime"

    ).textContent =

    new Date().toLocaleString();

}
/* ==========================================================
                    LOAD CHART DATA
========================================================== */

async function loadCharts(){

    try{

        const response = await fetch(

            API + "/reports/charts"

        );

        const result = await response.json();
        console.log("🔥 FULL REPORT RESPONSE:", result);
	console.log("🔥 CATEGORIES DATA:", result.data.categories);

        if(!result.success){

            showToast(

                result.message,

                false

            );

            return;

        }

        renderSalesChart(

            result.data

        );

        renderPaymentChart(

            result.data.payment

        );

        renderProductChart(

            result.data.products

        );

        renderCategoryChart(

            result.data.categories

        );

    }

    catch(err){

        console.log(err);

    }

}


/* ==========================================================
                    SALES CHART
========================================================== */

function renderSalesChart(data){

    if(charts.sales){

        charts.sales.destroy();

    }

    charts.sales = new Chart(

        document.getElementById(

            "salesChart"

        ),

        {

            type:"line",

            data:{

                labels:data.labels,

                datasets:[{

                    label:"Sales",

                    data:data.revenue,

                    borderWidth:3,

                    fill:false,

                    tension:.35

                }]

            },

            options:{

                responsive:true,

                maintainAspectRatio:false

            }

        }

    );

}


/* ==========================================================
                    PAYMENT CHART
========================================================== */

function renderPaymentChart(data){

    if(charts.payment){

        charts.payment.destroy();

    }

    charts.payment = new Chart(

        document.getElementById(

            "paymentChart"

        ),

        {

            type:"doughnut",

            data:{

                labels:data.labels,

                datasets:[{

                    data:data.values

                }]

            },

            options:{

                responsive:true,

                maintainAspectRatio:false

            }

        }

    );

}


/* ==========================================================
                    PRODUCT CHART
========================================================== */

function renderProductChart(data){

    if(charts.product){

        charts.product.destroy();

    }

    charts.product = new Chart(

        document.getElementById(

            "productChart"

        ),

        {

            type:"bar",

            data:{

                labels:data.labels,

                datasets:[{

                    label:"Products Sold",

                    data:data.values

                }]

            },

            options:{

                responsive:true,

                maintainAspectRatio:false

            }

        }

    );

}


/* ==========================================================
                    CATEGORY CHART
========================================================== */

function renderCategoryChart(data){

    console.log("🔥 CATEGORY CHART RECEIVED:", data);

    if (!data) {
        console.warn("⚠️ Category chart data is missing");
        return;
    }

    if(charts.category){

        charts.category.destroy();

    }

    charts.category = new Chart(

        document.getElementById(

            "categoryChart"

        ),

        {

            type:"pie",

            data:{

                labels:data.labels,

                datasets:[{

                    data:data.values

                }]

            },

            options:{

                responsive:true,

                maintainAspectRatio:false

            }

        }

    );

}
/* ==========================================================
                    LOAD REPORT TABLES
========================================================== */

async function loadTables(){

    try{

        const response = await fetch(

            API + "/reports/tables"

        );

        const result = await response.json();

        if(!result.success){

            showToast(

                result.message,

                false

            );

            return;

        }

        recentOrders = result.data.recent_orders || [];

        topProducts = result.data.top_products || [];

        lowStock = result.data.low_stock || [];

        refunds = result.data.refunds || [];

        renderRecentOrders();

        renderTopProducts();

        renderLowStock();

        renderRefunds();

    }

    catch(err){

        console.log(err);

        showToast(

            "Unable To Load Reports",

            false

        );

    }

}


/* ==========================================================
                    RECENT ORDERS
========================================================== */

function renderRecentOrders(){

    const body =

    document.getElementById(

        "recentOrdersBody"

    );

    body.innerHTML = "";

    recentOrders.forEach(order=>{

        const template =

        document

        .getElementById(

            "recentOrderTemplate"

        )

        .content

        .cloneNode(true);

        template.querySelector(

            ".order-number"

        ).textContent =

        order.order_number;

        template.querySelector(

            ".customer-name"

        ).textContent =

        order.customer_name ||

        "Walk-in";

        template.querySelector(

            ".table-number"

        ).textContent =

        order.table_number;

        template.querySelector(

            ".payment-method"

        ).textContent =

        order.payment_method;

        const badge =

        template.querySelector(

            ".status-badge"

        );

        badge.textContent =

        order.status;

        badge.classList.add(

            order.status.toLowerCase()

        );

        template.querySelector(

            ".order-total"

        ).textContent =

        "₹"+Number(

            order.total

        ).toFixed(2);

        template.querySelector(

            ".order-date"

        ).textContent =

        order.created_at;

        body.appendChild(

            template

        );

    });

}


/* ==========================================================
                    TOP PRODUCTS
========================================================== */

function renderTopProducts(){

    const body =

    document.getElementById(

        "topProductsBody"

    );

    body.innerHTML = "";

    topProducts.forEach((product,index)=>{

        const template =

        document

        .getElementById(

            "topProductTemplate"

        )

        .content

        .cloneNode(true);

        template.querySelector(

            ".rank"

        ).textContent =

        index + 1;

        template.querySelector(

            ".product-name"

        ).textContent =

        product.name;

        template.querySelector(

            ".category-name"

        ).textContent =

        product.category;

        template.querySelector(

            ".quantity-sold"

        ).textContent =

        product.quantity;

        template.querySelector(

            ".product-revenue"

        ).textContent =

        "₹"+Number(

            product.revenue

        ).toFixed(2);

        body.appendChild(

            template

        );

    });

}


/* ==========================================================
                    LOW STOCK
========================================================== */

function renderLowStock(){

    const body =

    document.getElementById(

        "lowStockBody"

    );

    body.innerHTML = "";

    lowStock.forEach(product=>{

        const template =

        document

        .getElementById(

            "lowStockTemplate"

        )

        .content

        .cloneNode(true);

        template.querySelector(

            ".stock-product"

        ).textContent =

        product.name;

        template.querySelector(

            ".stock-category"

        ).textContent =

        product.category;

        template.querySelector(

            ".stock-quantity"

        ).textContent =

        product.stock;

        const badge =

        template.querySelector(

            ".stock-status"

        );

        if(product.stock <= 5){

            badge.textContent =

            "LOW";

            badge.classList.add(

                "low"

            );

        }

        else if(product.stock <= 15){

            badge.textContent =

            "MEDIUM";

            badge.classList.add(

                "medium"

            );

        }

        else{

            badge.textContent =

            "GOOD";

            badge.classList.add(

                "good"

            );

        }

        body.appendChild(

            template

        );

    });

}


/* ==========================================================
                    REFUNDS
========================================================== */

function renderRefunds(){

    const body =

    document.getElementById(

        "refundBody"

    );

    body.innerHTML = "";

    refunds.forEach(refund=>{

        const template =

        document

        .getElementById(

            "refundTemplate"

        )

        .content

        .cloneNode(true);

        template.querySelector(

            ".refund-order"

        ).textContent =

        refund.order_number;

        template.querySelector(

            ".refund-customer"

        ).textContent =

        refund.customer_name;

        template.querySelector(

            ".refund-reason"

        ).textContent =

        refund.refund_reason;

        template.querySelector(

            ".refund-amount"

        ).textContent =

        "₹"+Number(

            refund.total

        ).toFixed(2);

        template.querySelector(

            ".refund-date"

        ).textContent =

        refund.refunded_at;

        body.appendChild(

            template

        );

    });

}
/* ==========================================================
                    APPLY FILTER
========================================================== */

document

.getElementById("applyFilter")

.addEventListener(

    "click",

    applyFilter

);

async function applyFilter(){

    try{

        showLoading();

        const response = await fetch(

            API +

            "/reports/filter?" +

            new URLSearchParams({

                type:reportType.value,

                start:startDate.value,

                end:endDate.value

            })

        );

        const result =

        await response.json();

        hideLoading();

        if(!result.success){

            showToast(

                result.message,

                false

            );

            return;

        }

        dashboard =

        result.data.dashboard;

        recentOrders =

        result.data.recent_orders;

        topProducts =

        result.data.top_products;

        lowStock =

        result.data.low_stock;

        refunds =

        result.data.refunds;

        renderDashboard();

        renderRecentOrders();

        renderTopProducts();

        renderLowStock();

        renderRefunds();

        renderSalesChart(

            result.data.sales

        );

        renderPaymentChart(

            result.data.payments

        );

        renderProductChart(

            result.data.products

        );

        renderCategoryChart(

            result.data.categories

        );

        showToast(

            "Report Updated"

        );

    }

    catch(err){

        hideLoading();

        console.log(err);

        showToast(

            "Unable To Apply Filter",

            false

        );

    }

}


/* ==========================================================
                    EXPORT EXCEL
========================================================== */

document

.getElementById("exportExcel")

.addEventListener(

    "click",

    ()=>{

        window.open(

            API +

            "/reports/export/excel",

            "_blank"

        );

    }

);


/* ==========================================================
                    EXPORT PDF
========================================================== */

document

.getElementById("exportPDF")

.addEventListener(

    "click",

    ()=>{

        window.open(

            API +

            "/reports/export/pdf",

            "_blank"

        );

    }

);


/* ==========================================================
                    PRINT REPORT
========================================================== */

document

.getElementById("printReport")

.addEventListener(

    "click",

    ()=>{

        window.print();

    }

);


/* ==========================================================
                    REFRESH
========================================================== */

document

.getElementById("refreshReport")

.addEventListener(

    "click",

    async()=>{

        await initializeReports();

        showToast(

            "Reports Refreshed"

        );

    }

);


/* ==========================================================
                    FLOATING EXPORT MENU
========================================================== */

const exportMenu =

document.getElementById(

    "exportMenu"

);

document

.getElementById(

    "floatingExport"

)

.onclick=function(){

    exportMenu.classList.toggle(

        "show"

    );

};

document

.addEventListener(

    "click",

    function(e){

        if(

            !exportMenu.contains(

                e.target

            )

            &&

            e.target.id !==

            "floatingExport"

        ){

            exportMenu.classList.remove(

                "show"

            );

        }

    }

);


/* ==========================================================
                    EXPORT MENU BUTTONS
========================================================== */

document

.getElementById(

    "downloadPDF"

)

.onclick=function(){

    window.open(

        API+

        "/reports/export/pdf",

        "_blank"

    );

};

document

.getElementById(

    "downloadExcel"

)

.onclick=function(){

    window.open(

        API+

        "/reports/export/excel",

        "_blank"

    );

};

document

.getElementById(

    "printFullReport"

)

.onclick=function(){

    window.print();

};
/* ==========================================================
                    INITIALIZE REPORTS
========================================================== */

async function initializeReports(){

    showLoading();

    try{

        await loadDashboard();

        await loadCharts();

        await loadTables();

        hideLoading();

    }

    catch(err){

        console.log(err);

        hideLoading();

        showToast(

            "Unable To Load Reports",

            false

        );

    }

}


/* ==========================================================
                    AUTO REFRESH
========================================================== */

setInterval(

    initializeReports,

    60000

);


/* ==========================================================
                    CHART FULLSCREEN
========================================================== */

const chartModal =

document.getElementById(

    "chartModal"

);

document

.querySelectorAll(

    ".chart-card"

)

.forEach(card=>{

    card.addEventListener(

        "dblclick",

        function(){

            chartModal

            .classList

            .add(

                "active"

            );

        }

    );

});


/* ==========================================================
                    CLOSE MODALS
========================================================== */

document

.querySelectorAll(

    ".close-modal"

)

.forEach(button=>{

    button.onclick=function(){

        document

        .querySelectorAll(

            ".modal"

        )

        .forEach(modal=>{

            modal

            .classList

            .remove(

                "active"

            );

        });

    };

});

window.onclick=function(e){

    document

    .querySelectorAll(

        ".modal"

    )

    .forEach(modal=>{

        if(e.target===modal){

            modal

            .classList

            .remove(

                "active"

            );

        }

    });

};


/* ==========================================================
                    PRINT SINGLE ORDER
========================================================== */

document

.getElementById(

    "printOrderBtn"

)

.addEventListener(

    "click",

    function(){

        window.print();

    }

);


/* ==========================================================
                    EMPTY STATE
========================================================== */

function toggleEmptyState(){

    const empty =

    document.getElementById(

        "emptyState"

    );

    if(

        recentOrders.length===0

    ){

        empty.style.display=

        "block";

    }

    else{

        empty.style.display=

        "none";

    }

}


/* ==========================================================
                    UPDATE AFTER TABLE LOAD
========================================================== */

const originalLoadTables = loadTables;

loadTables = async function(){

    await originalLoadTables();

    toggleEmptyState();

};


/* ==========================================================
                    PAGE LOAD
========================================================== */

window.addEventListener(

    "load",

    initializeReports

);


/* ==========================================================
                    PAGE VISIBILITY
========================================================== */

document.addEventListener(

    "visibilitychange",

    function(){

        if(

            !document.hidden

        ){

            initializeReports();

        }

    }

);


/* ==========================================================
                    NETWORK STATUS
========================================================== */

window.addEventListener(

    "offline",

    function(){

        showToast(

            "You are Offline",

            false

        );

    }

);

window.addEventListener(

    "online",

    function(){

        showToast(

            "Connection Restored"

        );

        initializeReports();

    }

);


/* ==========================================================
                    END
========================================================== */