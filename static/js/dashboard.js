/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 1-1
==========================================================*/

/*==========================================================
                    API URL
==========================================================*/

const API = "http://127.0.0.1:5000";

/*==========================================================
                GLOBAL VARIABLES
==========================================================*/

let salesChart = null;

let dashboardStats = {};

let notifications = [];

let refreshInterval = null;

/*==========================================================
                DOM READY
==========================================================*/

document.addEventListener("DOMContentLoaded", () => {

    initializeDashboard();

});

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeDashboard(){

    initializeSidebar();

    initializeTheme();

    initializeClock();

    initializeLoading();

}

function safeInit(fn){

    try{

        if(typeof fn === "function"){
            fn();
        }

    }
    catch(error){

        console.error(error);

    }

}

/*==========================================================
                SIDEBAR
==========================================================*/

function initializeSidebar(){

    const sidebar =
        document.querySelector(".sidebar");

    const button =
        document.getElementById("menuToggle");

    if(!sidebar || !button) return;

    button.addEventListener("click",()=>{

        sidebar.classList.toggle("collapsed");

    });

}

/*==========================================================
                DARK MODE
==========================================================*/

function initializeTheme(){

    const btn =
        document.getElementById("themeToggle");

    if(!btn) return;

    let mode =
        localStorage.getItem("cafesync-theme");

    if(mode==="dark"){

        document.body.classList.add("dark");

    }

    btn.addEventListener("click",()=>{

        document.body.classList.toggle("dark");

        if(document.body.classList.contains("dark")){

            localStorage.setItem(
                "cafesync-theme",
                "dark"
            );

        }
        else{

            localStorage.setItem(
                "cafesync-theme",
                "light"
            );

        }

    });

}

/*==========================================================
                LIVE CLOCK
==========================================================*/

function initializeClock(){

    updateClock();

    setInterval(updateClock,1000);

}

function updateClock(){

    const date =
        document.getElementById("currentDate");

    const time =
        document.getElementById("currentTime");

    const now = new Date();

    if(date){

        date.innerHTML =
        now.toLocaleDateString();

    }

    if(time){

        time.innerHTML =
        now.toLocaleTimeString();

    }

}

/*==========================================================
                LOADING SCREEN
==========================================================*/

function initializeLoading(){

    const loader =
        document.getElementById("loadingScreen");

    if(!loader) return;

    window.addEventListener("load",()=>{

        setTimeout(()=>{

            loader.style.display="none";

        },800);

    });

}

/*==========================================================
                TOAST MESSAGE
==========================================================*/

function showToast(message,type="success"){

    const toast =
        document.getElementById("toast");

    if(!toast) return;

    toast.innerHTML=`
        <i class="fas fa-check-circle"></i>
        <span>${message}</span>
    `;

    if(type==="error"){

        toast.style.background="#ef4444";

        toast.innerHTML=`
        <i class="fas fa-times-circle"></i>
        <span>${message}</span>
        `;

    }

    if(type==="warning"){

        toast.style.background="#f59e0b";

        toast.innerHTML=`
        <i class="fas fa-exclamation-circle"></i>
        <span>${message}</span>
        `;

    }

    if(type==="success"){

        toast.style.background="#22c55e";

    }

    toast.classList.add("show");

    setTimeout(()=>{

        toast.classList.remove("show");

    },3000);

}

/*==========================================================
                HELPERS
==========================================================*/

function formatCurrency(value){

    return "₹"+Number(value).toFixed(2);

}

function formatNumber(value){

    return Number(value).toLocaleString();

}

function formatDate(date){

    return new Date(date)
    .toLocaleString();

}
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 1-2
==========================================================*/

/*==========================================================
                NOTIFICATION PANEL
==========================================================*/

function initializeNotifications(){

    const bell =
        document.getElementById("notificationBtn");

    const panel =
        document.getElementById("notificationPanel");

    const close =
        document.getElementById("closeNotifications");

    if(bell && panel){

        bell.addEventListener("click",()=>{

            panel.classList.toggle("show");

        });

    }

    if(close){

        close.addEventListener("click",()=>{

            panel.classList.remove("show");

        });

    }

    document.addEventListener("click",(e)=>{

        if(!panel || !bell) return;

        if(
            !panel.contains(e.target) &&
            !bell.contains(e.target)
        ){

            panel.classList.remove("show");

        }

    });

}

/*==========================================================
                PROFILE MENU
==========================================================*/

function initializeProfileMenu(){

    const profile =
        document.getElementById("profileButton");

    const menu =
        document.getElementById("profileDropdown");

    if(profile && menu){

        profile.addEventListener("click",(e)=>{

            e.stopPropagation();

            menu.classList.toggle("show");

        });

    }

    document.addEventListener("click",()=>{

        if(menu){

            menu.classList.remove("show");

        }

    });

}

/*==========================================================
                SEARCH
==========================================================*/

function initializeSearch(){

    const search =
        document.getElementById("dashboardSearch");

    if(!search) return;

    search.addEventListener("keyup",function(){

        const keyword =
            this.value.toLowerCase();

        document
        .querySelectorAll(".search-item")
        .forEach(item=>{

            item.style.display =
            item.innerText
            .toLowerCase()
            .includes(keyword)
            ? ""
            : "none";

        });

    });

}

/*==========================================================
                FLOATING ACTION BUTTON
==========================================================*/

function initializeFloatingButton(){

    const fab =
        document.getElementById("floatingButton");

    if(!fab) return;

    fab.addEventListener("click",()=>{

        showToast("Quick Menu Opened");

        const quickMenu =
            document.getElementById("quickMenu");

        if(quickMenu){

            quickMenu.classList.toggle("show");

        }

    });

}

/*==========================================================
                LOGOUT
==========================================================*/

function logout(){

    if(confirm("Are you sure you want to logout?")){

        localStorage.removeItem("cafesync-token");

        window.location.href="/login";

    }

}

/*==========================================================
                KEYBOARD SHORTCUTS
==========================================================*/

function initializeShortcuts(){

    document.addEventListener("keydown",(e)=>{

        /* Ctrl + B */

        if(e.ctrlKey && e.key==="b"){

            e.preventDefault();

            window.location.href="/billing";

        }

        /* Ctrl + I */

        if(e.ctrlKey && e.key==="i"){

            e.preventDefault();

            window.location.href="/inventory";

        }

        /* Ctrl + D */

        if(e.ctrlKey && e.key==="d"){

            e.preventDefault();

            window.location.href="/dashboard";

        }

        /* Escape */

        if(e.key==="Escape"){

            document
            .querySelectorAll(".show")
            .forEach(el=>{

                el.classList.remove("show");

            });

        }

    });

}

/*==========================================================
                MOBILE MENU
==========================================================*/

function initializeMobileMenu(){

    const sidebar =
        document.querySelector(".sidebar");

    const overlay =
        document.getElementById("sidebarOverlay");

    const menu =
        document.getElementById("menuToggle");

    if(menu){

        menu.addEventListener("click",()=>{

            if(window.innerWidth<992){

                sidebar.classList.toggle("mobile-open");

                if(overlay){

                    overlay.classList.toggle("show");

                }

            }

        });

    }

    if(overlay){

        overlay.addEventListener("click",()=>{

            sidebar.classList.remove("mobile-open");

            overlay.classList.remove("show");

        });

    }

}

/*==========================================================
                WINDOW RESIZE
==========================================================*/

window.addEventListener("resize",()=>{

    const sidebar =
        document.querySelector(".sidebar");

    const overlay =
        document.getElementById("sidebarOverlay");

    if(window.innerWidth>992){

        if(sidebar){

            sidebar.classList.remove("mobile-open");

        }

        if(overlay){

            overlay.classList.remove("show");

        }

    }

});

/*==========================================================
                INITIALIZE PART 1-2
==========================================================*/

function initializeUI(){

    initializeNotifications();

    initializeProfileMenu();

    initializeSearch();

    initializeFloatingButton();

    initializeShortcuts();

    initializeMobileMenu();

}

/*==========================================================
        CALL FROM initializeDashboard()

        Add this line inside initializeDashboard()

        initializeUI();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 2-1
        Dashboard Statistics & Summary Cards
==========================================================*/

/*==========================================================
                LOAD DASHBOARD
==========================================================*/

async function loadDashboardStats(){

    try{

        const response = await fetch(
            API + "/dashboard/stats"
        );

        if(!response.ok){

            throw new Error("Unable to load dashboard.");

        }

        const data = await response.json();

        dashboardStats = data;

        updateDashboardCards(data);

        updateRevenueSummary(data);

    }

    catch(error){

        console.error(error);

        showToast(
            "Failed to load dashboard",
            "error"
        );

    }

}

/*==========================================================
            UPDATE DASHBOARD CARDS
==========================================================*/

function updateDashboardCards(data){

    setText("todaySales",
        formatCurrency(data.today_sales || 0));

    setText("todayOrders",
        formatNumber(data.today_orders || 0));

    setText("todayCustomers",
        formatNumber(data.today_customers || 0));

    setText("todayRevenue",
        formatCurrency(data.today_revenue || 0));

    setText("pendingOrders",
        formatNumber(data.pending_orders || 0));

    setText("completedOrders",
        formatNumber(data.completed_orders || 0));

    setText("cancelledOrders",
        formatNumber(data.cancelled_orders || 0));

    setText("activeTables",
        formatNumber(data.active_tables || 0));

}

/*==========================================================
            UPDATE REVENUE SUMMARY
==========================================================*/

function updateRevenueSummary(data){

    setText(
        "cashRevenue",
        formatCurrency(data.cash || 0)
    );

    setText(
        "upiRevenue",
        formatCurrency(data.upi || 0)
    );

    setText(
        "cardRevenue",
        formatCurrency(data.card || 0)
    );

    setText(
        "onlineRevenue",
        formatCurrency(data.online || 0)
    );

    setText(
        "gstCollected",
        formatCurrency(data.gst || 0)
    );

    setText(
        "discountAmount",
        formatCurrency(data.discount || 0)
    );

}

/*==========================================================
            UPDATE STATUS BOXES
==========================================================*/

function updateStatusBoxes(data){

    setText(
        "occupiedTables",
        data.occupied_tables || 0
    );

    setText(
        "availableTables",
        data.available_tables || 0
    );

    setText(
        "kitchenQueue",
        data.kitchen_pending || 0
    );

    setText(
        "deliveryOrders",
        data.delivery_orders || 0
    );

}

/*==========================================================
            PERFORMANCE CARDS
==========================================================*/

function updatePerformance(data){

    setText(
        "monthlySales",
        formatCurrency(
            data.monthly_sales || 0
        )
    );

    setText(
        "weeklySales",
        formatCurrency(
            data.weekly_sales || 0
        )
    );

    setText(
        "averageOrder",
        formatCurrency(
            data.average_order || 0
        )
    );

    setText(
        "customerGrowth",
        (data.customer_growth || 0) + "%"
    );

}

/*==========================================================
            INVENTORY SUMMARY
==========================================================*/

function updateInventory(data){

    setText(
        "totalProducts",
        data.total_products || 0
    );

    setText(
        "lowStock",
        data.low_stock || 0
    );

    setText(
        "categories",
        data.categories || 0
    );

    setText(
        "inventoryValue",
        formatCurrency(
            data.inventory_value || 0
        )
    );

}

/*==========================================================
            SET ELEMENT TEXT
==========================================================*/

function setText(id,value){

    const element =
        document.getElementById(id);

    if(element){

        element.textContent = value;

    }

}

/*==========================================================
            REFRESH DASHBOARD
==========================================================*/

async function refreshDashboard(){

    await loadDashboardStats();

    showToast(
        "Dashboard Updated"
    );

}

/*==========================================================
            AUTO REFRESH
==========================================================*/

function startDashboardRefresh(){

    if(refreshInterval){

        clearInterval(refreshInterval);

    }

    refreshInterval =
        setInterval(()=>{

            loadDashboardStats();

        },30000);

}

/*==========================================================
        CALL THESE INSIDE
        initializeDashboard()

        loadDashboardStats();

        startDashboardRefresh();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 2-2
        Recent Bills • Latest Orders • Activity Feed
==========================================================*/

/*==========================================================
                LOAD RECENT BILLS
==========================================================*/

async function loadRecentBills(){

    try{

        const response = await fetch(
            API + "/billing/recent"
        );

        if(!response.ok){

            throw new Error("Unable to load bills");

        }

        const bills = await response.json();

        renderRecentBills(bills);

    }

    catch(error){

        console.error(error);

        showToast(
            "Unable to load recent bills",
            "error"
        );

    }

}

/*==========================================================
                RENDER RECENT BILLS
==========================================================*/

function renderRecentBills(bills){

    const tbody =
        document.getElementById("recentBillsTable");

    if(!tbody) return;

    tbody.innerHTML="";

    if(bills.length===0){

        tbody.innerHTML=`
        <tr>
            <td colspan="8" style="text-align:center;">
                No Bills Available
            </td>
        </tr>
        `;

        return;

    }

    bills.forEach(bill=>{

        tbody.innerHTML+=`

        <tr>

            <td>${bill.bill_no}</td>

            <td>${bill.customer}</td>

            <td>${bill.order_type}</td>

            <td>${formatCurrency(bill.total)}</td>

            <td>${bill.payment_method}</td>

            <td>

                <span class="${bill.status.toLowerCase()}">
                    ${bill.status}
                </span>

            </td>

            <td>${formatDate(bill.created_at)}</td>

            <td>

                <button
                class="action-btn view"
                onclick="viewInvoice(${bill.id})">

                <i class="fas fa-eye"></i>

                </button>

                <button
                class="action-btn print"
                onclick="printInvoice(${bill.id})">

                <i class="fas fa-print"></i>

                </button>

            </td>

        </tr>

        `;

    });

}

/*==========================================================
                LOAD TODAY ORDERS
==========================================================*/

async function loadTodayOrders(){

    try{

        const response = await fetch(
            API + "/orders/today"
        );

        const orders =
            await response.json();

        renderTodayOrders(orders);

    }

    catch(error){

        console.log(error);

    }

}

/*==========================================================
                TODAY ORDERS
==========================================================*/

function renderTodayOrders(orders){

    const container =
        document.getElementById("todayOrders");

    if(!container) return;

    container.innerHTML="";

    orders.forEach(order=>{

        container.innerHTML+=`

        <div class="order-card search-item">

            <h4>${order.bill_no}</h4>

            <p>${order.customer}</p>

            <small>

            ${formatCurrency(order.total)}

            </small>

        </div>

        `;

    });

}

/*==========================================================
                ACTIVITY FEED
==========================================================*/

async function loadActivityFeed(){

    try{

        const response =
        await fetch(
            API + "/dashboard/activity"
        );

        const activities =
        await response.json();

        renderActivityFeed(
            activities
        );

    }

    catch(error){

        console.log(error);

    }

}

/*==========================================================
                RENDER ACTIVITY
==========================================================*/

function renderActivityFeed(list){

    const feed =
    document.getElementById(
        "activityFeed"
    );

    if(!feed) return;

    feed.innerHTML="";

    list.forEach(item=>{

        feed.innerHTML+=`

        <li>

            <i class="fas fa-bell"></i>

            <div>

                <strong>

                ${item.title}

                </strong>

                <br>

                <small>

                ${item.description}

                </small>

            </div>

        </li>

        `;

    });

}

/*==========================================================
                SEARCH BILLS
==========================================================*/

function searchBills(){

    const search =
    document
    .getElementById("billSearch");

    if(!search) return;

    const keyword =
    search.value.toLowerCase();

    const rows =
    document.querySelectorAll(
    "#recentBillsTable tr"
    );

    rows.forEach(row=>{

        const text =
        row.innerText.toLowerCase();

        row.style.display =
        text.includes(keyword)
        ? ""
        : "none";

    });

}

/*==========================================================
                INITIALIZE EVENTS
==========================================================*/

function initializeRecentBills(){

    const search =
    document.getElementById(
        "billSearch"
    );

    if(search){

        search.addEventListener(
            "keyup",
            searchBills
        );

    }

}

/*==========================================================
                LOAD SECTION
==========================================================*/

async function loadDashboardSection(){

    await loadRecentBills();

    await loadTodayOrders();

    await loadActivityFeed();

}

/*==========================================================
        CALL THESE INSIDE
        initializeDashboard()

        initializeRecentBills();

        loadDashboardSection();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 3-1
        SALES ANALYTICS (Chart.js)
==========================================================*/


/*==========================================================
                LOAD SALES CHART
==========================================================*/

async function loadSalesChart(period="daily"){

    try{

        const response = await fetch(

            `${API}/dashboard/sales-chart?period=${period}`

        );

        if(!response.ok){

            throw new Error("Unable to load sales chart");

        }

        const data = await response.json();

        renderSalesChart(data);

        updateChartSummary(data);

    }

    catch(error){

        console.error(error);

        showToast(
            "Unable to load sales chart",
            "error"
        );

    }

}

/*==========================================================
                RENDER CHART
==========================================================*/

function renderSalesChart(data){

    if(!data){
        console.error("Sales chart data is empty:", data);
        return;
    }

    const canvas =
        document.getElementById("salesChart");

    if(!canvas) return;


    const ctx =
        canvas.getContext("2d");


    if(salesChart){

        salesChart.destroy();

    }


    salesChart = new Chart(ctx,{

        type:"line",

        data:{

            labels:data.labels || [],

            datasets:[

                {
                    label:"Revenue",

                    data:data.revenue || [],

                    borderWidth:3,

                    fill:true,

                    tension:.35
                },

                {
                    label:"Orders",

                    data:data.orders || [],

                    borderWidth:3,

                    fill:false,

                    tension:.35
                }

            ]

        }

    });

}
/*==========================================================
                UPDATE SUMMARY
==========================================================*/

function updateChartSummary(data){

    setText(

        "chartTotalRevenue",

        formatCurrency(data.total_revenue)

    );

    setText(

        "chartTotalOrders",

        formatNumber(data.total_orders)

    );

    setText(

        "chartAverageSale",

        formatCurrency(data.average_sale)

    );

    setText(

        "chartGrowth",

        data.growth + "%"

    );

}

/*==========================================================
                CHANGE PERIOD
==========================================================*/

function initializeChartFilter(){

    const filter =
        document.getElementById(
            "chartFilter"
        );

    if(!filter) return;

    filter.addEventListener(

        "change",

        function(){

            loadSalesChart(

                this.value

            );

        }

    );

}

/*==========================================================
                REFRESH BUTTON
==========================================================*/

function initializeChartRefresh(){

    const button =
        document.getElementById(
            "refreshChart"
        );

    if(!button) return;

    button.addEventListener(

        "click",

        ()=>{

            const filter =
            document.getElementById(
                "chartFilter"
            );

            const period =
            filter
            ? filter.value
            : "daily";

            loadSalesChart(period);

            showToast(
                "Chart Updated"
            );

        }

    );

}

/*==========================================================
                AUTO REFRESH
==========================================================*/

function startChartRefresh(){

    setInterval(()=>{

        const filter =
        document.getElementById(
            "chartFilter"
        );

        const period =
        filter
        ? filter.value
        : "daily";

        loadSalesChart(period);

    },60000);

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeSalesChart(){

    initializeChartFilter();

    initializeChartRefresh();

    loadSalesChart();

    startChartRefresh();

}

/*==========================================================

    ADD INSIDE initializeDashboard()

    initializeSalesChart();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 3-2
        PRODUCT & PAYMENT ANALYTICS
==========================================================*/

let productChart = null;
let paymentChart = null;
let categoryChart = null;
let hourlyChart = null;

/*==========================================================
                LOAD ANALYTICS
==========================================================*/

async function loadAnalyticsCharts(){

    try{

        const response = await fetch(
            API + "/dashboard/analytics"
        );

        if(!response.ok){

            throw new Error("Unable to load analytics");

        }

        const data = await response.json();

        renderProductChart(data.products);

        renderPaymentChart(data.payments);

        renderCategoryChart(data.categories);

        renderHourlyChart(data.hourly);

    }

    catch(error){

        console.error(error);

        showToast(
            "Unable to load analytics",
            "error"
        );

    }

}

/*==========================================================
                PRODUCT SALES CHART
==========================================================*/

function renderProductChart(data){

    const canvas =
        document.getElementById("productChart");

    if(!canvas) return;

    if(productChart){

        productChart.destroy();

    }

    productChart = new Chart(canvas,{

        type:"bar",

        data:{

            labels:data.labels,

            datasets:[{

                label:"Products Sold",

                data:data.values,

                backgroundColor:"#ff6b00",

                borderRadius:8

            }]

        },

        options:{

            responsive:true,

            maintainAspectRatio:false,

            plugins:{

                legend:{display:false}

            },

            scales:{

                y:{beginAtZero:true}

            }

        }

    });

}

/*==========================================================
                PAYMENT PIE CHART
==========================================================*/

function renderPaymentChart(data){

    const canvas =
        document.getElementById("paymentChart");

    if(!canvas) return;

    if(paymentChart){

        paymentChart.destroy();

    }

    paymentChart = new Chart(canvas,{

        type:"pie",

        data:{

            labels:data.labels,

            datasets:[{

                data:data.values,

                backgroundColor:[

                    "#22c55e",

                    "#3b82f6",

                    "#f59e0b",

                    "#ef4444"

                ]

            }]

        },

        options:{

            responsive:true,

            maintainAspectRatio:false

        }

    });

}

/*==========================================================
                CATEGORY CHART
==========================================================*/

function renderCategoryChart(data){

    const canvas =
        document.getElementById("categoryChart");

    if(!canvas) return;

    if(categoryChart){

        categoryChart.destroy();

    }

    categoryChart = new Chart(canvas,{

        type:"doughnut",

        data:{

            labels:data.labels,

            datasets:[{

                data:data.values,

                backgroundColor:[

                    "#ff6b00",

                    "#2563eb",

                    "#16a34a",

                    "#9333ea",

                    "#f59e0b",

                    "#dc2626"

                ]

            }]

        },

        options:{

            responsive:true,

            maintainAspectRatio:false

        }

    });

}

/*==========================================================
                HOURLY SALES
==========================================================*/

function renderHourlyChart(data){

    const canvas =
        document.getElementById("hourlyChart");

    if(!canvas) return;

    if(hourlyChart){

        hourlyChart.destroy();

    }

    hourlyChart = new Chart(canvas,{

        type:"line",

        data:{

            labels:data.labels,

            datasets:[{

                label:"Hourly Sales",

                data:data.values,

                borderColor:"#16a34a",

                backgroundColor:

                "rgba(22,163,74,.15)",

                fill:true,

                tension:.4

            }]

        },

        options:{

            responsive:true,

            maintainAspectRatio:false,

            scales:{

                y:{beginAtZero:true}

            }

        }

    });

}

/*==========================================================
                REFRESH
==========================================================*/

function refreshAnalytics(){

    loadAnalyticsCharts();

    showToast("Analytics Updated");

}

/*==========================================================
                AUTO REFRESH
==========================================================*/

function startAnalyticsRefresh(){

    setInterval(()=>{

        loadAnalyticsCharts();

    },60000);

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeAnalytics(){

    loadAnalyticsCharts();

    startAnalyticsRefresh();

}

/*==========================================================

    ADD INSIDE initializeDashboard()

    initializeAnalytics();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 4-1
        RECENT BILLS & INVOICE MANAGEMENT
==========================================================*/

let currentInvoiceId = null;

/*==========================================================
                LOAD RECENT BILLS
==========================================================*/

async function loadRecentBills(){

    try{

        const response = await fetch(
            API + "/billing/recent"
        );

        if(!response.ok){

            throw new Error("Unable to load recent bills");

        }

        const bills = await response.json();

        renderRecentBills(bills);

    }

    catch(error){

        console.error(error);

        showToast(
            "Failed to load recent bills",
            "error"
        );

    }

}

/*==========================================================
                RENDER BILLS
==========================================================*/

function renderRecentBills(bills){

    const tbody =
        document.getElementById("recentBillsTable");

    if(!tbody) return;

    tbody.innerHTML = "";

    if(bills.length===0){

        tbody.innerHTML=`
        <tr>
            <td colspan="8" class="text-center">
                No Bills Found
            </td>
        </tr>
        `;

        return;

    }

    bills.forEach(bill=>{

        tbody.innerHTML += `

        <tr>

            <td>${bill.bill_no}</td>

            <td>${bill.customer}</td>

            <td>${bill.order_type}</td>

            <td>${formatCurrency(bill.total)}</td>

            <td>${bill.payment_method}</td>

            <td>

                <span class="${bill.status.toLowerCase()}">

                    ${bill.status}

                </span>

            </td>

            <td>

                ${formatDate(bill.created_at)}

            </td>

            <td>

                <button
                class="action-btn view"
                onclick="viewInvoice(${bill.id})">

                    <i class="fas fa-eye"></i>

                </button>

                <button
                class="action-btn print"
                onclick="printInvoice(${bill.id})">

                    <i class="fas fa-print"></i>

                </button>

                <button
                class="action-btn pdf"
                onclick="downloadInvoice(${bill.id})">

                    <i class="fas fa-file-pdf"></i>

                </button>

            </td>

        </tr>

        `;

    });

}

/*==========================================================
                VIEW INVOICE
==========================================================*/

async function viewInvoice(orderId){

    currentInvoiceId = orderId;

    try{

        const response = await fetch(

            API + "/billing/invoice/" + orderId

        );

        if(!response.ok){

            throw new Error("Invoice not found");

        }

        const result = await response.json();

        showInvoiceModal(result);

    }

    catch(error){

        console.error(error);

        showToast(
            "Unable to load invoice",
            "error"
        );

    }

}

/*==========================================================
                SHOW MODAL
==========================================================*/

function showInvoiceModal(data){

    const modal =
        document.getElementById("invoiceModal");

    const body =
        document.getElementById("invoiceContent");

    if(!modal || !body) return;

    const invoice = data.invoice;

    body.innerHTML = `

        <h2>CafeSync</h2>

        <hr>

        <p>

            <strong>Bill No:</strong>

            ${invoice.bill_no}

        </p>

        <p>

            <strong>Date:</strong>

            ${invoice.invoice_date}

        </p>

        <p>

            <strong>Customer:</strong>

            ${invoice.customer.name}

        </p>

        <p>

            <strong>Phone:</strong>

            ${invoice.customer.phone}

        </p>

        <p>

            <strong>Payment:</strong>

            ${invoice.payment_method}

        </p>

        <br>

        <table class="bill-table">

            <thead>

                <tr>

                    <th>Item</th>

                    <th>Qty</th>

                    <th>Price</th>

                    <th>Total</th>

                </tr>

            </thead>

            <tbody>

                ${invoice.items.map(item=>`

                <tr>

                    <td>${item.name}</td>

                    <td>${item.quantity}</td>

                    <td>${formatCurrency(item.price)}</td>

                    <td>${formatCurrency(item.total)}</td>

                </tr>

                `).join("")}

            </tbody>

        </table>

        <br>

        <h3>

            Grand Total :

            ${formatCurrency(
                invoice.summary.grand_total
            )}

        </h3>

    `;

    modal.classList.add("active");

}

/*==========================================================
                CLOSE MODAL
==========================================================*/

function closeInvoice(){

    const modal =
        document.getElementById("invoiceModal");

    if(modal){

        modal.classList.remove("active");

    }

}

/*==========================================================
                INITIALIZE MODAL
==========================================================*/

function initializeInvoiceModal(){

    const closeBtn =
        document.getElementById("closeModal");

    if(closeBtn){

        closeBtn.addEventListener(

            "click",

            closeInvoice

        );

    }

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeBills(){

    loadRecentBills();

    initializeInvoiceModal();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeBills();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 4-2
        PRINT • PDF • PAYMENT HISTORY • SEARCH
==========================================================*/

/*==========================================================
                PRINT INVOICE
==========================================================*/

function printInvoice(orderId){

    window.open(

        API + "/billing/print/" + orderId,

        "_blank"

    );

}

/*==========================================================
                DOWNLOAD PDF
==========================================================*/

function downloadInvoice(orderId){

    window.open(

        API + "/billing/pdf/" + orderId,

        "_blank"

    );

}

/*==========================================================
                PAYMENT HISTORY
==========================================================*/

async function loadPaymentHistory(orderId){

    try{

        const response = await fetch(

            API + "/billing/payment-history/" + orderId

        );

        if(!response.ok){

            throw new Error("Unable to load payment history");

        }

        const history = await response.json();

        renderPaymentHistory(history);

    }

    catch(error){

        console.error(error);

        showToast(

            "Payment history unavailable",

            "error"

        );

    }

}

/*==========================================================
                RENDER PAYMENT HISTORY
==========================================================*/

function renderPaymentHistory(history){

    const container =

        document.getElementById(

            "paymentHistory"

        );

    if(!container) return;

    container.innerHTML="";

    if(history.length===0){

        container.innerHTML=`

        <p>No Payment History</p>

        `;

        return;

    }

    history.forEach(payment=>{

        container.innerHTML+=`

        <div class="payment-item">

            <h4>

                ${payment.payment_method}

            </h4>

            <p>

                Amount :

                ${formatCurrency(payment.amount)}

            </p>

            <p>

                Status :

                ${payment.status}

            </p>

            <small>

                ${formatDate(payment.created_at)}

            </small>

        </div>

        `;

    });

}

/*==========================================================
                SEARCH INVOICES
==========================================================*/

function searchInvoices(){

    const search =

        document.getElementById(

            "billSearch"

        );

    if(!search) return;

    const keyword =

        search.value.toLowerCase();

    const rows =

        document.querySelectorAll(

            "#recentBillsTable tr"

        );

    rows.forEach(row=>{

        const text =

            row.innerText.toLowerCase();

        row.style.display =

            text.includes(keyword)

            ? ""

            : "none";

    });

}

/*==========================================================
                FILTER STATUS
==========================================================*/

function filterInvoices(){

    const filter =

        document.getElementById(

            "statusFilter"

        );

    if(!filter) return;

    const value =

        filter.value.toLowerCase();

    const rows =

        document.querySelectorAll(

            "#recentBillsTable tr"

        );

    rows.forEach(row=>{

        if(value==="all"){

            row.style.display="";

            return;

        }

        const status =

            row.innerText.toLowerCase();

        row.style.display=

            status.includes(value)

            ? ""

            : "none";

    });

}

/*==========================================================
                REFRESH BILL LIST
==========================================================*/

async function refreshBills(){

    await loadRecentBills();

    showToast(

        "Bills Refreshed"

    );

}

/*==========================================================
                EVENTS
==========================================================*/

function initializeBillEvents(){

    const search =

        document.getElementById(

            "billSearch"

        );

    if(search){

        search.addEventListener(

            "keyup",

            searchInvoices

        );

    }

    const filter =

        document.getElementById(

            "statusFilter"

        );

    if(filter){

        filter.addEventListener(

            "change",

            filterInvoices

        );

    }

    const refresh =

        document.getElementById(

            "refreshBills"

        );

    if(refresh){

        refresh.addEventListener(

            "click",

            refreshBills

        );

    }

}

/*==========================================================
                AUTO REFRESH
==========================================================*/

function autoRefreshBills(){

    setInterval(()=>{

        loadRecentBills();

    },30000);

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeInvoiceModule(){

    initializeBillEvents();

    autoRefreshBills();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeInvoiceModule();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 5-1
        LIVE TRANSACTIONS & PAYMENT SUMMARY
==========================================================*/

let liveTransactions = [];

/*==========================================================
                LOAD LIVE TRANSACTIONS
==========================================================*/

async function loadLiveTransactions(){

    try{

        const response = await fetch(
            API + "/billing/live-transactions"
        );

        if(!response.ok){

            throw new Error("Unable to load transactions");

        }

        const data = await response.json();

        liveTransactions = data;

        renderLiveTransactions(data);

    }

    catch(error){

        console.error(error);

        showToast(
            "Failed to load live transactions",
            "error"
        );

    }

}

/*==========================================================
                RENDER LIVE TRANSACTIONS
==========================================================*/

function renderLiveTransactions(transactions){

    const container =
        document.getElementById(
            "transactionList"
        );

    if(!container) return;

    container.innerHTML="";

    if(transactions.length===0){

        container.innerHTML=`

        <div class="empty-data">

            <i class="fas fa-receipt"></i>

            <p>No Transactions Available</p>

        </div>

        `;

        return;

    }

    transactions.forEach(transaction=>{

        container.innerHTML+=`

        <div class="transaction-item">

            <div>

                <h4>

                    ${transaction.bill_no}

                </h4>

                <small>

                    ${transaction.customer}

                </small>

            </div>

            <div>

                <strong>

                    ${formatCurrency(transaction.total)}

                </strong>

                <br>

                <small>

                    ${transaction.payment_method}

                </small>

            </div>

        </div>

        `;

    });

}

/*==========================================================
                LOAD PAYMENT SUMMARY
==========================================================*/

async function loadPaymentSummary(){

    try{

        const response = await fetch(
            API + "/billing/payment-summary"
        );

        if(!response.ok){

            throw new Error("Unable to load summary");

        }

        const summary =
            await response.json();

        updatePaymentSummary(summary);

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                UPDATE PAYMENT CARDS
==========================================================*/

function updatePaymentSummary(summary){

    setText(
        "cashTotal",
        formatCurrency(summary.cash || 0)
    );

    setText(
        "upiTotal",
        formatCurrency(summary.upi || 0)
    );

    setText(
        "cardTotal",
        formatCurrency(summary.card || 0)
    );

    setText(
        "onlineTotal",
        formatCurrency(summary.online || 0)
    );

    setText(
        "totalCollection",
        formatCurrency(summary.total || 0)
    );

}

/*==========================================================
                PAYMENT DISTRIBUTION
==========================================================*/

function updatePaymentPercentage(summary){

    const total = summary.total || 0;

    if(total===0){

        return;

    }

    setText(
        "cashPercent",
        Math.round(
            (summary.cash/total)*100
        )+"%"
    );

    setText(
        "upiPercent",
        Math.round(
            (summary.upi/total)*100
        )+"%"
    );

    setText(
        "cardPercent",
        Math.round(
            (summary.card/total)*100
        )+"%"
    );

    setText(
        "onlinePercent",
        Math.round(
            (summary.online/total)*100
        )+"%"
    );

}

/*==========================================================
                RECENT PAYMENTS
==========================================================*/

async function loadRecentPayments(){

    try{

        const response = await fetch(
            API + "/billing/recent-payments"
        );

        const payments =
            await response.json();

        renderRecentPayments(payments);

    }

    catch(error){

        console.error(error);

    }

}

function renderRecentPayments(payments){

    const table =
        document.getElementById(
            "recentPayments"
        );

    if(!table) return;

    table.innerHTML="";

    payments.forEach(payment=>{

        table.innerHTML+=`

        <tr>

            <td>

                ${payment.bill_no}

            </td>

            <td>

                ${payment.customer}

            </td>

            <td>

                ${payment.payment_method}

            </td>

            <td>

                ${formatCurrency(
                    payment.amount
                )}

            </td>

            <td>

                ${formatDate(
                    payment.created_at
                )}

            </td>

        </tr>

        `;

    });

}

/*==========================================================
                REFRESH
==========================================================*/

async function refreshTransactions(){

    await loadLiveTransactions();

    await loadPaymentSummary();

    await loadRecentPayments();

    showToast(
        "Transactions Updated"
    );

}

/*==========================================================
                AUTO REFRESH
==========================================================*/

function startTransactionRefresh(){

    setInterval(async()=>{

        await loadLiveTransactions();

        await loadPaymentSummary();

    },20000);

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeTransactions(){

    loadLiveTransactions();

    loadPaymentSummary();

    loadRecentPayments();

    startTransactionRefresh();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeTransactions();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 5-2-1
                REFUND MANAGEMENT
==========================================================*/

let refundHistory = [];

/*==========================================================
                LOAD REFUNDS
==========================================================*/

async function loadRefunds(){

    try{

        const response = await fetch(

            API + "/billing/refunds"

        );

        if(!response.ok){

            throw new Error("Unable to load refunds");

        }

        const refunds = await response.json();

        refundHistory = refunds;

        renderRefunds(refunds);

    }

    catch(error){

        console.error(error);

        showToast(

            "Unable to load refunds",

            "error"

        );

    }

}

/*==========================================================
                RENDER REFUNDS
==========================================================*/

function renderRefunds(refunds){

    const tbody =

        document.getElementById(

            "refundTable"

        );

    if(!tbody) return;

    tbody.innerHTML="";

    if(refunds.length===0){

        tbody.innerHTML=`

        <tr>

            <td colspan="7"

            class="text-center">

            No Refund Records

            </td>

        </tr>

        `;

        return;

    }

    refunds.forEach(refund=>{

        tbody.innerHTML+=`

        <tr>

            <td>${refund.bill_no}</td>

            <td>${refund.customer}</td>

            <td>${formatCurrency(refund.amount)}</td>

            <td>${refund.payment_method}</td>

            <td>${refund.reason}</td>

            <td>${formatDate(refund.created_at)}</td>

            <td>

                <span class="paid">

                    Refunded

                </span>

            </td>

        </tr>

        `;

    });

}

/*==========================================================
                PROCESS REFUND
==========================================================*/

async function refundInvoice(orderId){

    const reason = prompt(

        "Refund Reason"

    );

    if(!reason) return;

    try{

        const response = await fetch(

            API + "/billing/refund/" + orderId,

            {

                method:"POST",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    reason:reason

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Refund Successful"

            );

            loadRefunds();

            loadRecentBills();

            loadPaymentSummary();

        }

        else{

            showToast(

                result.message,

                "error"

            );

        }

    }

    catch(error){

        console.error(error);

        showToast(

            "Refund Failed",

            "error"

        );

    }

}

/*==========================================================
                REFUND DETAILS
==========================================================*/

async function viewRefund(orderId){

    try{

        const response = await fetch(

            API +

            "/billing/refund-details/" +

            orderId

        );

        const data =

            await response.json();

        displayRefundModal(data);

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                REFUND MODAL
==========================================================*/

function displayRefundModal(data){

    const modal =

        document.getElementById(

            "refundModal"

        );

    const body =

        document.getElementById(

            "refundContent"

        );

    if(!modal || !body) return;

    body.innerHTML = `

        <h3>

            Refund Details

        </h3>

        <hr>

        <p>

        <strong>Bill :</strong>

        ${data.bill_no}

        </p>

        <p>

        <strong>Customer :</strong>

        ${data.customer}

        </p>

        <p>

        <strong>Refund :</strong>

        ${formatCurrency(data.amount)}

        </p>

        <p>

        <strong>Reason :</strong>

        ${data.reason}

        </p>

        <p>

        <strong>Date :</strong>

        ${formatDate(data.created_at)}

        </p>

    `;

    modal.classList.add("active");

}

/*==========================================================
                CLOSE REFUND MODAL
==========================================================*/

function closeRefundModal(){

    const modal =

        document.getElementById(

            "refundModal"

        );

    if(modal){

        modal.classList.remove(

            "active"

        );

    }

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeRefundModule(){

    loadRefunds();

    const close =

        document.getElementById(

            "closeRefundModal"

        );

    if(close){

        close.addEventListener(

            "click",

            closeRefundModal

        );

    }

}
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 5-2-2-1
            CASH DRAWER & SHIFT START
==========================================================*/

let currentShift = null;

/*==========================================================
                LOAD CURRENT SHIFT
==========================================================*/

async function loadCurrentShift(){

    try{

        const response = await fetch(

            API + "/cash/current-shift"

        );

        if(!response.ok){

            throw new Error("Unable to load shift");

        }

        const data = await response.json();

        currentShift = data;

        updateShiftCard(data);

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                UPDATE SHIFT CARD
==========================================================*/

function updateShiftCard(data){

    setText(

        "shiftNumber",

        data.shift_no || "--"

    );

    setText(

        "cashierName",

        data.cashier || "--"

    );

    setText(

        "shiftStartTime",

        data.start_time || "--"

    );

    setText(

        "openingCash",

        formatCurrency(data.opening_cash || 0)

    );

}

/*==========================================================
                OPEN CASH DRAWER
==========================================================*/

async function openCashDrawer(){

    const openingCash = parseFloat(

        document.getElementById("openingCashInput").value

    );

    if(isNaN(openingCash)){

        showToast(

            "Enter opening cash",

            "warning"

        );

        return;

    }

    try{

        const response = await fetch(

            API + "/cash/open",

            {

                method:"POST",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    opening_cash:openingCash

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Cash Drawer Opened"

            );

            loadCurrentShift();

        }

        else{

            showToast(

                result.message,

                "error"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                START SHIFT
==========================================================*/

async function startShift(){

    try{

        const response = await fetch(

            API + "/cash/start-shift",

            {

                method:"POST"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Shift Started"

            );

            loadCurrentShift();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeCashDrawer(){

    loadCurrentShift();

    const btn =

        document.getElementById(

            "openDrawerBtn"

        );

    if(btn){

        btn.addEventListener(

            "click",

            openCashDrawer

        );

    }

    const shiftBtn =

        document.getElementById(

            "startShiftBtn"

        );

    if(shiftBtn){

        shiftBtn.addEventListener(

            "click",

            startShift

        );

    }

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeCashDrawer();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 5-2-2-2
        CASH IN • CASH OUT • CASH MOVEMENTS
==========================================================*/

let cashMovements = [];

/*==========================================================
                LOAD CASH MOVEMENTS
==========================================================*/

async function loadCashMovements(){

    try{

        const response = await fetch(

            API + "/cash/movements"

        );

        if(!response.ok){

            throw new Error("Unable to load cash movements");

        }

        const data = await response.json();

        cashMovements = data;

        renderCashMovements(data);

    }

    catch(error){

        console.error(error);

        showToast(

            "Unable to load cash movements",

            "error"

        );

    }

}

/*==========================================================
                RENDER CASH MOVEMENTS
==========================================================*/

function renderCashMovements(data){

    const tbody =
        document.getElementById(
            "cashMovementTable"
        );

    if(!tbody) return;

    tbody.innerHTML = "";

    if(data.length===0){

        tbody.innerHTML = `

        <tr>

            <td colspan="6"
            class="text-center">

                No Cash Movements

            </td>

        </tr>

        `;

        return;

    }

    data.forEach(item=>{

        tbody.innerHTML += `

        <tr>

            <td>${formatDate(item.created_at)}</td>

            <td>${item.type}</td>

            <td>${formatCurrency(item.amount)}</td>

            <td>${item.reason}</td>

            <td>${item.employee}</td>

            <td>

                <span class="${item.type.toLowerCase()}">

                    ${item.type}

                </span>

            </td>

        </tr>

        `;

    });

}

/*==========================================================
                CASH IN
==========================================================*/

async function cashIn(){

    const amount = parseFloat(

        document.getElementById(
            "cashInAmount"
        ).value

    );

    const reason =

        document.getElementById(
            "cashInReason"
        ).value;

    if(isNaN(amount) || amount<=0){

        showToast(

            "Enter valid amount",

            "warning"

        );

        return;

    }

    try{

        const response = await fetch(

            API + "/cash/in",

            {

                method:"POST",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    amount,

                    reason

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Cash Added"

            );

            clearCashForms();

            loadCashMovements();

            loadCurrentShift();

        }

        else{

            showToast(

                result.message,

                "error"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                CASH OUT
==========================================================*/

async function cashOut(){

    const amount = parseFloat(

        document.getElementById(
            "cashOutAmount"
        ).value

    );

    const reason =

        document.getElementById(
            "cashOutReason"
        ).value;

    if(isNaN(amount) || amount<=0){

        showToast(

            "Enter valid amount",

            "warning"

        );

        return;

    }

    try{

        const response = await fetch(

            API + "/cash/out",

            {

                method:"POST",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    amount,

                    reason

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Cash Removed"

            );

            clearCashForms();

            loadCashMovements();

            loadCurrentShift();

        }

        else{

            showToast(

                result.message,

                "error"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                CLEAR FORMS
==========================================================*/

function clearCashForms(){

    const fields = [

        "cashInAmount",

        "cashInReason",

        "cashOutAmount",

        "cashOutReason"

    ];

    fields.forEach(id=>{

        const input =
            document.getElementById(id);

        if(input){

            input.value = "";

        }

    });

}

/*==========================================================
                UPDATE DRAWER BALANCE
==========================================================*/

function updateDrawerBalance(balance){

    setText(

        "drawerBalance",

        formatCurrency(balance)

    );

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeCashMovement(){

    loadCashMovements();

    const inBtn =
        document.getElementById(
            "cashInBtn"
        );

    if(inBtn){

        inBtn.addEventListener(

            "click",

            cashIn

        );

    }

    const outBtn =
        document.getElementById(
            "cashOutBtn"
        );

    if(outBtn){

        outBtn.addEventListener(

            "click",

            cashOut

        );

    }

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeCashMovement();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 5-2-2-3
        CLOSE DRAWER • SHIFT END • RECONCILIATION
==========================================================*/

/*==========================================================
                LOAD RECONCILIATION
==========================================================*/

async function loadReconciliation(){

    try{

        const response = await fetch(

            API + "/cash/reconciliation"

        );

        if(!response.ok){

            throw new Error("Unable to load reconciliation");

        }

        const data = await response.json();

        updateReconciliation(data);

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                UPDATE RECONCILIATION
==========================================================*/

function updateReconciliation(data){

    setText(

        "expectedCash",

        formatCurrency(data.expected_cash || 0)

    );

    setText(

        "actualCash",

        formatCurrency(data.actual_cash || 0)

    );

    setText(

        "cashDifference",

        formatCurrency(data.difference || 0)

    );

    const badge =

        document.getElementById("differenceStatus");

    if(!badge) return;

    if(data.difference === 0){

        badge.textContent = "Balanced";

        badge.className = "paid";

    }

    else if(data.difference > 0){

        badge.textContent = "Over";

        badge.className = "pending";

    }

    else{

        badge.textContent = "Short";

        badge.className = "cancelled";

    }

}

/*==========================================================
                CLOSE CASH DRAWER
==========================================================*/

async function closeCashDrawer(){

    const actualCash = parseFloat(

        document.getElementById(

            "actualCashInput"

        ).value

    );

    if(isNaN(actualCash)){

        showToast(

            "Enter actual cash amount",

            "warning"

        );

        return;

    }

    try{

        const response = await fetch(

            API + "/cash/close",

            {

                method:"POST",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    actual_cash:actualCash

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Cash Drawer Closed"

            );

            loadReconciliation();

            loadCurrentShift();

        }

        else{

            showToast(

                result.message,

                "error"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                END SHIFT
==========================================================*/

async function endShift(){

    if(!confirm(

        "End current shift?"

    )) return;

    try{

        const response = await fetch(

            API + "/cash/end-shift",

            {

                method:"POST"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Shift Closed Successfully"

            );

            loadCurrentShift();

            loadReconciliation();

        }

        else{

            showToast(

                result.message,

                "error"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                PRINT X REPORT
==========================================================*/

function printXReport(){

    window.open(

        API + "/cash/x-report",

        "_blank"

    );

}

/*==========================================================
                PRINT Z REPORT
==========================================================*/

function printZReport(){

    window.open(

        API + "/cash/z-report",

        "_blank"

    );

}

/*==========================================================
                INITIALIZE EVENTS
==========================================================*/

function initializeShiftClosing(){

    loadReconciliation();

    const closeBtn =

        document.getElementById(

            "closeDrawerBtn"

        );

    if(closeBtn){

        closeBtn.addEventListener(

            "click",

            closeCashDrawer

        );

    }

    const shiftBtn =

        document.getElementById(

            "endShiftBtn"

        );

    if(shiftBtn){

        shiftBtn.addEventListener(

            "click",

            endShift

        );

    }

    const xBtn =

        document.getElementById(

            "printXReport"

        );

    if(xBtn){

        xBtn.addEventListener(

            "click",

            printXReport

        );

    }

    const zBtn =

        document.getElementById(

            "printZReport"

        );

    if(zBtn){

        zBtn.addEventListener(

            "click",

            printZReport

        );

    }

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeShiftClosing();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 6-1
            KITCHEN DISPLAY SYSTEM (KDS)
==========================================================*/

let kitchenOrders = [];

/*==========================================================
                LOAD KITCHEN ORDERS
==========================================================*/

async function loadKitchenOrders(){

    try{

        const response = await fetch(

            API + "/kitchen/orders"

        );

        if(!response.ok){

            throw new Error("Unable to load kitchen orders");

        }

        const orders = await response.json();

        kitchenOrders = orders;

        renderKitchenOrders(orders);

    }

    catch(error){

        console.error(error);

        showToast(

            "Unable to load kitchen orders",

            "error"

        );

    }

}

/*==========================================================
                RENDER ORDERS
==========================================================*/

function renderKitchenOrders(orders){

    const pending =
        document.getElementById("pendingOrders");

    const preparing =
        document.getElementById("preparingOrders");

    const ready =
        document.getElementById("readyOrders");

    if(!pending || !preparing || !ready){

        return;

    }

    pending.innerHTML = "";

    preparing.innerHTML = "";

    ready.innerHTML = "";

    orders.forEach(order=>{

        const card = createKitchenCard(order);

        switch(order.status){

            case "Pending":

                pending.appendChild(card);

                break;

            case "Preparing":

                preparing.appendChild(card);

                break;

            case "Ready":

                ready.appendChild(card);

                break;

        }

    });

}

/*==========================================================
                CREATE ORDER CARD
==========================================================*/

function createKitchenCard(order){

    const card = document.createElement("div");

    card.className = "kitchen-card";

    card.innerHTML = `

        <div class="kitchen-header">

            <h3>#${order.order_no}</h3>

            <span class="table-name">

                ${order.table_name}

            </span>

        </div>

        <div class="kitchen-body">

            <p>

                <strong>Customer:</strong>

                ${order.customer}

            </p>

            <p>

                <strong>Items:</strong>

            </p>

            <ul>

                ${order.items.map(item=>`

                    <li>

                        ${item.quantity} × ${item.name}

                    </li>

                `).join("")}

            </ul>

        </div>

        <div class="kitchen-footer">

            <span id="timer-${order.id}">

                --:--

            </span>

            <button

                onclick="nextKitchenStatus(${order.id})">

                Next

            </button>

        </div>

    `;

    startKitchenTimer(

        order.id,

        order.created_at

    );

    return card;

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeKitchen(){

    loadKitchenOrders();

}
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 6-2
        KDS TIMERS • STATUS • CHEF ASSIGNMENT
==========================================================*/

let kitchenRefresh = null;

/*==========================================================
                LIVE ORDER TIMER
==========================================================*/

function startKitchenTimer(orderId, createdAt){

    const timer = document.getElementById(

        "timer-" + orderId

    );

    if(!timer) return;

    function update(){

        const start = new Date(createdAt);

        const now = new Date();

        const seconds = Math.floor(

            (now - start) / 1000

        );

        const minutes = Math.floor(

            seconds / 60

        );

        const hrs = Math.floor(

            minutes / 60

        );

        const mins = minutes % 60;

        const secs = seconds % 60;

        timer.innerHTML =

            String(hrs).padStart(2,"0")

            + ":"

            + String(mins).padStart(2,"0")

            + ":"

            + String(secs).padStart(2,"0");

    }

    update();

    setInterval(update,1000);

}

/*==========================================================
                NEXT STATUS
==========================================================*/

async function nextKitchenStatus(orderId){

    try{

        const response = await fetch(

            API +

            "/kitchen/next-status/" +

            orderId,

            {

                method:"PUT"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Kitchen Updated"

            );

            loadKitchenOrders();

            loadKitchenSummary();

        }

        else{

            showToast(

                result.message,

                "error"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                CHEF ASSIGNMENT
==========================================================*/

async function assignChef(orderId){

    const chef = prompt(

        "Enter Chef Name"

    );

    if(!chef) return;

    try{

        const response = await fetch(

            API +

            "/kitchen/assign-chef/" +

            orderId,

            {

                method:"PUT",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    chef:chef

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Chef Assigned"

            );

            loadKitchenOrders();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                KITCHEN SUMMARY
==========================================================*/

async function loadKitchenSummary(){

    try{

        const response = await fetch(

            API +

            "/kitchen/summary"

        );

        const data =

            await response.json();

        setText(

            "pendingCount",

            data.pending

        );

        setText(

            "preparingCount",

            data.preparing

        );

        setText(

            "readyCount",

            data.ready

        );

        setText(

            "servedCount",

            data.served

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                KITCHEN NOTIFICATION
==========================================================*/

function kitchenNotification(message){

    if(

        "Notification" in window

    ){

        if(

            Notification.permission

            === "granted"

        ){

            new Notification(

                "CafeSync Kitchen",

                {

                    body:message

                }

            );

        }

    }

}

/*==========================================================
                REQUEST PERMISSION
==========================================================*/

function requestKitchenPermission(){

    if(

        "Notification" in window

    ){

        Notification.requestPermission();

    }

}

/*==========================================================
                AUTO REFRESH
==========================================================*/

function startKitchenRefresh(){

    if(kitchenRefresh){

        clearInterval(

            kitchenRefresh

        );

    }

    kitchenRefresh =

        setInterval(()=>{

            loadKitchenOrders();

            loadKitchenSummary();

        },10000);

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeKitchenModule(){

    requestKitchenPermission();

    loadKitchenOrders();

    loadKitchenSummary();

    startKitchenRefresh();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeKitchenModule();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 6-3
        FINAL KITCHEN DISPLAY SYSTEM (KDS)
==========================================================*/

/*==========================================================
                MARK AS SERVED
==========================================================*/

async function serveKitchenOrder(orderId){

    try{

        const response = await fetch(

            API + "/kitchen/serve/" + orderId,

            {

                method:"PUT"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast("Order Served");

            loadKitchenOrders();

            loadKitchenSummary();

        }

        else{

            showToast(result.message,"error");

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                CANCEL ORDER
==========================================================*/

async function cancelKitchenOrder(orderId){

    if(!confirm("Cancel this kitchen order?")){

        return;

    }

    try{

        const response = await fetch(

            API + "/kitchen/cancel/" + orderId,

            {

                method:"PUT"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast("Order Cancelled");

            loadKitchenOrders();

            loadKitchenSummary();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                PRINT KOT
==========================================================*/

function printKitchenTicket(orderId){

    window.open(

        API + "/kitchen/print/" + orderId,

        "_blank"

    );

}

/*==========================================================
                SEARCH KITCHEN ORDERS
==========================================================*/

function searchKitchenOrders(){

    const search =

        document.getElementById(

            "kitchenSearch"

        );

    if(!search) return;

    const keyword =

        search.value.toLowerCase();

    document

        .querySelectorAll(".kitchen-card")

        .forEach(card=>{

            card.style.display =

                card.innerText

                .toLowerCase()

                .includes(keyword)

                ? ""

                : "none";

        });

}

/*==========================================================
                OVERDUE HIGHLIGHT
==========================================================*/

function highlightOverdueOrders(){

    document

        .querySelectorAll(".kitchen-card")

        .forEach(card=>{

            const timer =

                card.querySelector(

                    "[id^='timer-']"

                );

            if(!timer) return;

            const value =

                timer.textContent.split(":");

            const hours =

                parseInt(value[0]);

            const minutes =

                parseInt(value[1]);

            if(hours>0 || minutes>=20){

                card.classList.add(

                    "overdue"

                );

            }

            else{

                card.classList.remove(

                    "overdue"

                );

            }

        });

}

/*==========================================================
                CLEAR READY ORDERS
==========================================================*/

function clearReadyOrders(){

    const ready =

        document.getElementById(

            "readyOrders"

        );

    if(!ready) return;

    ready.innerHTML = "";

}

/*==========================================================
                PLAY ALERT
==========================================================*/

function playKitchenAlert(){

    const audio =

        document.getElementById(

            "kitchenAlert"

        );

    if(audio){

        audio.play().catch(()=>{});

    }

}

/*==========================================================
                CHECK NEW ORDERS
==========================================================*/

let lastKitchenCount = 0;

async function checkNewKitchenOrders(){

    try{

        const response = await fetch(

            API + "/kitchen/orders"

        );

        const orders =

            await response.json();

        if(

            orders.length >

            lastKitchenCount

        ){

            playKitchenAlert();

            kitchenNotification(

                "New Kitchen Order"

            );

        }

        lastKitchenCount =

            orders.length;

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                INITIALIZE EVENTS
==========================================================*/

function initializeKitchenEvents(){

    const search =

        document.getElementById(

            "kitchenSearch"

        );

    if(search){

        search.addEventListener(

            "keyup",

            searchKitchenOrders

        );

    }

    const clear =

        document.getElementById(

            "clearReadyOrders"

        );

    if(clear){

        clear.addEventListener(

            "click",

            clearReadyOrders

        );

    }

}

/*==========================================================
                AUTO TASKS
==========================================================*/

function startKitchenTasks(){

    setInterval(()=>{

        highlightOverdueOrders();

        checkNewKitchenOrders();

    },5000);

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeKitchenFinal(){

    initializeKitchenEvents();

    startKitchenTasks();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeKitchenFinal();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 7-1
        SWIGGY & ZOMATO ONLINE ORDERS
==========================================================*/

let swiggyOrders = [];
let zomatoOrders = [];

/*==========================================================
                LOAD ONLINE ORDERS
==========================================================*/

async function loadOnlineOrders(){

    await Promise.all([

        loadSwiggyOrders(),

        loadZomatoOrders()

    ]);

}

/*==========================================================
                SWIGGY ORDERS
==========================================================*/

async function loadSwiggyOrders(){

    try{

        const response = await fetch(

            API + "/delivery/swiggy"

        );

        if(!response.ok){

            throw new Error("Unable to load Swiggy orders");

        }

        const orders = await response.json();

        swiggyOrders = orders;

        renderSwiggyOrders(orders);

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                ZOMATO ORDERS
==========================================================*/

async function loadZomatoOrders(){

    try{

        const response = await fetch(

            API + "/delivery/zomato"

        );

        if(!response.ok){

            throw new Error("Unable to load Zomato orders");

        }

        const orders = await response.json();

        zomatoOrders = orders;

        renderZomatoOrders(orders);

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                RENDER SWIGGY
==========================================================*/

function renderSwiggyOrders(orders){

    const container =

        document.getElementById(

            "swiggyOrders"

        );

    if(!container) return;

    container.innerHTML = "";

    if(orders.length===0){

        container.innerHTML =

        "<p>No Swiggy Orders</p>";

        return;

    }

    orders.forEach(order=>{

        container.appendChild(

            createDeliveryCard(

                order,

                "Swiggy"

            )

        );

    });

}

/*==========================================================
                RENDER ZOMATO
==========================================================*/

function renderZomatoOrders(orders){

    const container =

        document.getElementById(

            "zomatoOrders"

        );

    if(!container) return;

    container.innerHTML = "";

    if(orders.length===0){

        container.innerHTML =

        "<p>No Zomato Orders</p>";

        return;

    }

    orders.forEach(order=>{

        container.appendChild(

            createDeliveryCard(

                order,

                "Zomato"

            )

        );

    });

}

/*==========================================================
                DELIVERY CARD
==========================================================*/

function createDeliveryCard(order, platform){

    const card = document.createElement("div");

    card.className = "delivery-card";

    card.innerHTML = `

        <div class="delivery-header">

            <h3>

                ${platform}

            </h3>

            <span>

                #${order.order_no}

            </span>

        </div>

        <div class="delivery-body">

            <p>

                <strong>Customer:</strong>

                ${order.customer}

            </p>

            <p>

                <strong>Phone:</strong>

                ${order.phone}

            </p>

            <p>

                <strong>Total:</strong>

                ${formatCurrency(order.total)}

            </p>

            <p>

                <strong>Status:</strong>

                ${order.status}

            </p>

            <p>

                <strong>Items:</strong>

            </p>

            <ul>

                ${order.items.map(item=>`

                    <li>

                        ${item.quantity} × ${item.name}

                    </li>

                `).join("")}

            </ul>

        </div>

        <div class="delivery-footer">

            <button

                onclick="acceptDeliveryOrder(${order.id})">

                Accept

            </button>

            <button

                onclick="rejectDeliveryOrder(${order.id})">

                Reject

            </button>

        </div>

    `;

    return card;

}

/*==========================================================
                DELIVERY SUMMARY
==========================================================*/

async function loadDeliverySummary(){

    try{

        const response = await fetch(

            API + "/delivery/summary"

        );

        const data = await response.json();

        setText(

            "onlineOrders",

            data.total_orders || 0

        );

        setText(

            "swiggyCount",

            data.swiggy || 0

        );

        setText(

            "zomatoCount",

            data.zomato || 0

        );

        setText(

            "deliveryRevenue",

            formatCurrency(

                data.revenue || 0

            )

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                AUTO REFRESH
==========================================================*/

function startDeliveryRefresh(){

    setInterval(()=>{

        loadOnlineOrders();

        loadDeliverySummary();

    },15000);

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeDeliveryModule(){

    loadOnlineOrders();

    loadDeliverySummary();

    startDeliveryRefresh();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeDeliveryModule();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 7-2
        ONLINE ORDER PROCESSING
==========================================================*/

/*==========================================================
                ACCEPT ORDER
==========================================================*/

async function acceptDeliveryOrder(orderId){

    try{

        const response = await fetch(

            API + "/delivery/accept/" + orderId,

            {

                method:"PUT"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast("Order Accepted");

            loadOnlineOrders();

            loadDeliverySummary();

        }
        else{

            showToast(result.message,"error");

        }

    }

    catch(error){

        console.error(error);

        showToast("Unable to accept order","error");

    }

}

/*==========================================================
                REJECT ORDER
==========================================================*/

async function rejectDeliveryOrder(orderId){

    const reason = prompt(

        "Reason for rejection"

    );

    if(reason===null) return;

    try{

        const response = await fetch(

            API + "/delivery/reject/" + orderId,

            {

                method:"PUT",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    reason:reason

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast("Order Rejected");

            loadOnlineOrders();

            loadDeliverySummary();

        }
        else{

            showToast(result.message,"error");

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                SEND TO KITCHEN
==========================================================*/

async function sendOrderToKitchen(orderId){

    try{

        const response = await fetch(

            API + "/delivery/send-kitchen/" + orderId,

            {

                method:"PUT"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast("Sent To Kitchen");

            loadOnlineOrders();

            loadKitchenOrders();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                READY FOR PICKUP
==========================================================*/

async function readyForPickup(orderId){

    try{

        const response = await fetch(

            API + "/delivery/ready/" + orderId,

            {

                method:"PUT"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast("Ready For Pickup");

            loadOnlineOrders();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                DISPATCH ORDER
==========================================================*/

async function dispatchDelivery(orderId){

    try{

        const response = await fetch(

            API + "/delivery/dispatch/" + orderId,

            {

                method:"PUT"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast("Order Dispatched");

            loadOnlineOrders();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                BULK REFRESH
==========================================================*/

async function refreshDeliveryDashboard(){

    await loadOnlineOrders();

    await loadDeliverySummary();

    showToast("Delivery Dashboard Updated");

}

/*==========================================================
                DELIVERY ACTIONS
==========================================================*/

function initializeDeliveryActions(){

    const refreshBtn =

        document.getElementById(

            "refreshDelivery"

        );

    if(refreshBtn){

        refreshBtn.addEventListener(

            "click",

            refreshDeliveryDashboard

        );

    }

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeDeliveryProcessing(){

    initializeDeliveryActions();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeDeliveryProcessing();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 7-3
        DELIVERY TRACKING & NOTIFICATIONS
==========================================================*/

let deliveryOrders = [];
let lastDeliveryCount = 0;

/*==========================================================
                LOAD DELIVERY TRACKING
==========================================================*/

async function loadDeliveryTracking(){

    try{

        const response = await fetch(

            API + "/delivery/tracking"

        );

        if(!response.ok){

            throw new Error("Unable to load delivery tracking");

        }

        const data = await response.json();

        deliveryOrders = data;

        renderDeliveryTracking(data);

        updateDeliverySummary(data);

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                RENDER DELIVERY TRACKING
==========================================================*/

function renderDeliveryTracking(data){

    const container =

        document.getElementById(

            "deliveryTracking"

        );

    if(!container) return;

    container.innerHTML = "";

    if(data.length===0){

        container.innerHTML =

        "<p>No Active Deliveries</p>";

        return;

    }

    data.forEach(order=>{

        container.innerHTML += `

        <div class="delivery-track-card">

            <h3>#${order.order_no}</h3>

            <p>

                <strong>Platform :</strong>

                ${order.platform}

            </p>

            <p>

                <strong>Customer :</strong>

                ${order.customer}

            </p>

            <p>

                <strong>Partner :</strong>

                ${order.partner || "Not Assigned"}

            </p>

            <p>

                <strong>Status :</strong>

                ${order.status}

            </p>

            <p>

                <strong>ETA :</strong>

                ${order.eta} mins

            </p>

            <button
                onclick="assignDeliveryPartner(${order.id})">

                Assign Rider

            </button>

        </div>

        `;

    });

}

/*==========================================================
                ASSIGN DELIVERY PARTNER
==========================================================*/

async function assignDeliveryPartner(orderId){

    const partner = prompt(

        "Enter delivery partner name"

    );

    if(!partner) return;

    try{

        const response = await fetch(

            API +

            "/delivery/assign/" +

            orderId,

            {

                method:"PUT",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    partner:partner

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Delivery Partner Assigned"

            );

            loadDeliveryTracking();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                UPDATE SUMMARY
==========================================================*/

function updateDeliverySummary(data){

    let active = 0;

    let delivered = 0;

    let preparing = 0;

    data.forEach(order=>{

        if(order.status==="Preparing"){

            preparing++;

        }

        else if(order.status==="Delivered"){

            delivered++;

        }

        else{

            active++;

        }

    });

    setText(

        "activeDeliveryCount",

        active

    );

    setText(

        "preparingDeliveryCount",

        preparing

    );

    setText(

        "deliveredDeliveryCount",

        delivered

    );

}

/*==========================================================
                NEW ORDER ALERT
==========================================================*/

function notifyDeliveryOrder(){

    if(

        "Notification" in window &&

        Notification.permission==="granted"

    ){

        new Notification(

            "CafeSync",

            {

                body:

                "New online delivery order received."

            }

        );

    }

}

/*==========================================================
                CHECK NEW ORDERS
==========================================================*/

async function checkDeliveryOrders(){

    try{

        const response = await fetch(

            API + "/delivery/orders"

        );

        const orders = await response.json();

        if(

            orders.length >

            lastDeliveryCount

        ){

            notifyDeliveryOrder();

            playDeliveryAlert();

        }

        lastDeliveryCount =

            orders.length;

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                DELIVERY ALERT SOUND
==========================================================*/

function playDeliveryAlert(){

    const audio =

        document.getElementById(

            "deliveryAlert"

        );

    if(audio){

        audio.play().catch(()=>{});

    }

}

/*==========================================================
                REQUEST NOTIFICATION
==========================================================*/

function requestDeliveryPermission(){

    if(

        "Notification" in window

    ){

        Notification.requestPermission();

    }

}

/*==========================================================
                AUTO REFRESH
==========================================================*/

function startDeliveryTracking(){

    setInterval(()=>{

        loadDeliveryTracking();

        checkDeliveryOrders();

    },10000);

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeDeliveryTracking(){

    requestDeliveryPermission();

    loadDeliveryTracking();

    startDeliveryTracking();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeDeliveryTracking();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 7-4
        DELIVERY ANALYTICS & HISTORY
==========================================================*/

/*==========================================================
                SEARCH DELIVERY ORDERS
==========================================================*/

function searchDeliveryOrders(){

    const input =

        document.getElementById(

            "deliverySearch"

        );

    if(!input) return;

    const keyword =

        input.value.toLowerCase();

    document

        .querySelectorAll(".delivery-card")

        .forEach(card=>{

            const text =

                card.innerText.toLowerCase();

            card.style.display =

                text.includes(keyword)

                ? ""

                : "none";

        });

}

/*==========================================================
                FILTER PLATFORM
==========================================================*/

function filterDeliveryPlatform(){

    const filter =

        document.getElementById(

            "deliveryPlatform"

        );

    if(!filter) return;

    const value =

        filter.value.toLowerCase();

    document

        .querySelectorAll(".delivery-card")

        .forEach(card=>{

            if(

                value==="all"

            ){

                card.style.display="";

                return;

            }

            const text =

                card.innerText.toLowerCase();

            card.style.display =

                text.includes(value)

                ? ""

                : "none";

        });

}

/*==========================================================
                DELIVERY ANALYTICS
==========================================================*/

async function loadDeliveryAnalytics(){

    try{

        const response = await fetch(

            API + "/delivery/analytics"

        );

        if(!response.ok){

            throw new Error();

        }

        const data = await response.json();

        setText(

            "deliveryRevenue",

            formatCurrency(data.revenue || 0)

        );

        setText(

            "deliveryOrdersCount",

            data.orders || 0

        );

        setText(

            "averageDeliveryTime",

            data.average_time || "0 min"

        );

        setText(

            "deliverySuccessRate",

            (data.success_rate || 0) + "%"

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                DELIVERY HISTORY
==========================================================*/

async function loadDeliveryHistory(){

    try{

        const response = await fetch(

            API + "/delivery/history"

        );

        if(!response.ok){

            throw new Error();

        }

        const history = await response.json();

        renderDeliveryHistory(history);

    }

    catch(error){

        console.error(error);

    }

}

function renderDeliveryHistory(history){

    const tbody =

        document.getElementById(

            "deliveryHistoryTable"

        );

    if(!tbody) return;

    tbody.innerHTML = "";

    if(history.length===0){

        tbody.innerHTML = `

        <tr>

            <td colspan="7">

                No Delivery History

            </td>

        </tr>

        `;

        return;

    }

    history.forEach(order=>{

        tbody.innerHTML += `

        <tr>

            <td>${order.order_no}</td>

            <td>${order.platform}</td>

            <td>${order.customer}</td>

            <td>${formatCurrency(order.total)}</td>

            <td>${order.status}</td>

            <td>${formatDate(order.completed_at)}</td>

            <td>${order.partner || "-"}</td>

        </tr>

        `;

    });

}

/*==========================================================
                EXPORT REPORT
==========================================================*/

function exportDeliveryReport(){

    window.open(

        API + "/delivery/export",

        "_blank"

    );

}

/*==========================================================
                CLEAR COMPLETED
==========================================================*/

async function clearCompletedDeliveries(){

    if(!confirm(

        "Clear completed deliveries?"

    )) return;

    try{

        const response = await fetch(

            API + "/delivery/clear",

            {

                method:"DELETE"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Completed deliveries cleared"

            );

            loadDeliveryHistory();

            loadOnlineOrders();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                INITIALIZE EVENTS
==========================================================*/

function initializeDeliveryEvents(){

    const search =

        document.getElementById(

            "deliverySearch"

        );

    if(search){

        search.addEventListener(

            "keyup",

            searchDeliveryOrders

        );

    }

    const filter =

        document.getElementById(

            "deliveryPlatform"

        );

    if(filter){

        filter.addEventListener(

            "change",

            filterDeliveryPlatform

        );

    }

    const exportBtn =

        document.getElementById(

            "exportDeliveryReport"

        );

    if(exportBtn){

        exportBtn.addEventListener(

            "click",

            exportDeliveryReport

        );

    }

    const clearBtn =

        document.getElementById(

            "clearCompletedDeliveries"

        );

    if(clearBtn){

        clearBtn.addEventListener(

            "click",

            clearCompletedDeliveries

        );

    }

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeDeliveryFinal(){

    loadDeliveryAnalytics();

    loadDeliveryHistory();

    initializeDeliveryEvents();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeDeliveryFinal();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 8-1
        TABLE MANAGEMENT & FLOOR LAYOUT
==========================================================*/

let cafeTables = [];

/*==========================================================
                LOAD TABLES
==========================================================*/

async function loadCafeTables(){

    try{

        const response = await fetch(

            API + "/tables"

        );

        if(!response.ok){

            throw new Error(

                "Unable to load tables"

            );

        }

        const tables = await response.json();

        cafeTables = tables;

        renderCafeTables(tables);

        updateTableSummary(tables);

    }

    catch(error){

        console.error(error);

        showToast(

            "Unable to load tables",

            "error"

        );

    }

}

/*==========================================================
                RENDER TABLES
==========================================================*/

function renderCafeTables(tables){

    const container =

        document.getElementById(

            "tableLayout"

        );

    if(!container) return;

    container.innerHTML = "";

    if(tables.length===0){

        container.innerHTML = `

        <div class="empty-data">

            <i class="fas fa-chair"></i>

            <p>No Tables Available</p>

        </div>

        `;

        return;

    }

    tables.forEach(table=>{

        container.appendChild(

            createTableCard(table)

        );

    });

}

/*==========================================================
                CREATE TABLE CARD
==========================================================*/

function createTableCard(table){

    const card =

        document.createElement("div");

    card.className =

        "table-card " +

        table.status.toLowerCase();

    card.innerHTML = `

        <div class="table-header">

            <h3>

                ${table.table_name}

            </h3>

            <span>

                ${table.status}

            </span>

        </div>

        <div class="table-body">

            <p>

                Capacity :
                ${table.capacity}

            </p>

            <p>

                Guests :
                ${table.guests || 0}

            </p>

            <p>

                Waiter :
                ${table.waiter || "-"}

            </p>

        </div>

        <div class="table-footer">

            <button

                onclick="viewTable(${table.id})">

                View

            </button>

        </div>

    `;

    return card;

}

/*==========================================================
                VIEW TABLE
==========================================================*/

async function viewTable(tableId){

    try{

        const response = await fetch(

            API +

            "/tables/" +

            tableId

        );

        if(!response.ok){

            throw new Error();

        }

        const table =

            await response.json();

        displayTableDetails(table);

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                TABLE DETAILS MODAL
==========================================================*/

function displayTableDetails(table){

    const modal =

        document.getElementById(

            "tableModal"

        );

    const content =

        document.getElementById(

            "tableModalContent"

        );

    if(!modal || !content) return;

    content.innerHTML = `

        <h3>

            ${table.table_name}

        </h3>

        <hr>

        <p>

            Status :
            ${table.status}

        </p>

        <p>

            Capacity :
            ${table.capacity}

        </p>

        <p>

            Guests :
            ${table.guests || 0}

        </p>

        <p>

            Waiter :
            ${table.waiter || "-"}

        </p>

        <p>

            Current Bill :
            ${formatCurrency(table.bill || 0)}

        </p>

    `;

    modal.classList.add(

        "active"

    );

}

/*==========================================================
                CLOSE MODAL
==========================================================*/

function closeTableModal(){

    const modal =

        document.getElementById(

            "tableModal"

        );

    if(modal){

        modal.classList.remove(

            "active"

        );

    }

}

/*==========================================================
                TABLE SUMMARY
==========================================================*/

function updateTableSummary(tables){

    let available = 0;

    let occupied = 0;

    let reserved = 0;

    let cleaning = 0;

    tables.forEach(table=>{

        switch(table.status){

            case "Available":

                available++;

                break;

            case "Occupied":

                occupied++;

                break;

            case "Reserved":

                reserved++;

                break;

            case "Cleaning":

                cleaning++;

                break;

        }

    });

    setText(

        "availableTables",

        available

    );

    setText(

        "occupiedTables",

        occupied

    );

    setText(

        "reservedTables",

        reserved

    );

    setText(

        "cleaningTables",

        cleaning

    );

}

/*==========================================================
                AUTO REFRESH
==========================================================*/

function startTableRefresh(){

    setInterval(()=>{

        loadCafeTables();

    },10000);

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeTableManagement(){

    loadCafeTables();

    startTableRefresh();

    const close =

        document.getElementById(

            "closeTableModal"

        );

    if(close){

        close.addEventListener(

            "click",

            closeTableModal

        );

    }

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeTableManagement();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 8-2
        RESERVATION & TABLE OPERATIONS
==========================================================*/

let activeTableTimers = {};

/*==========================================================
                RESERVE TABLE
==========================================================*/

async function reserveTable(tableId){

    const customer = prompt("Customer Name");

    if(!customer) return;

    const guests = parseInt(

        prompt("Number of Guests")

    );

    if(isNaN(guests)) return;

    try{

        const response = await fetch(

            API + "/tables/reserve/" + tableId,

            {

                method:"PUT",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    customer,

                    guests

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Table Reserved"

            );

            loadCafeTables();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                CANCEL RESERVATION
==========================================================*/

async function cancelReservation(tableId){

    if(!confirm(

        "Cancel reservation?"

    )) return;

    try{

        const response = await fetch(

            API +

            "/tables/cancel/" +

            tableId,

            {

                method:"PUT"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Reservation Cancelled"

            );

            loadCafeTables();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                CHECK IN
==========================================================*/

async function checkInTable(tableId){

    try{

        const response = await fetch(

            API +

            "/tables/checkin/" +

            tableId,

            {

                method:"PUT"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Guests Checked In"

            );

            loadCafeTables();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                CHECK OUT
==========================================================*/

async function checkOutTable(tableId){

    if(!confirm(

        "Checkout this table?"

    )) return;

    try{

        const response = await fetch(

            API +

            "/tables/checkout/" +

            tableId,

            {

                method:"PUT"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Table Checked Out"

            );

            loadCafeTables();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                ASSIGN WAITER
==========================================================*/

async function assignWaiter(tableId){

    const waiter = prompt(

        "Waiter Name"

    );

    if(!waiter) return;

    try{

        const response = await fetch(

            API +

            "/tables/assign-waiter/" +

            tableId,

            {

                method:"PUT",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    waiter

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Waiter Assigned"

            );

            loadCafeTables();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                TABLE TIMER
==========================================================*/

function startTableTimer(

    tableId,

    occupiedAt

){

    if(

        activeTableTimers[tableId]

    ){

        clearInterval(

            activeTableTimers[tableId]

        );

    }

    const timer =

        document.getElementById(

            "tableTimer-" +

            tableId

        );

    if(!timer) return;

    function update(){

        const start =

            new Date(

                occupiedAt

            );

        const now =

            new Date();

        const seconds = Math.floor(

            (now-start)/1000

        );

        const hrs = Math.floor(

            seconds/3600

        );

        const mins = Math.floor(

            (seconds%3600)/60

        );

        const secs =

            seconds%60;

        timer.innerHTML =

            String(hrs).padStart(2,"0")

            + ":"

            + String(mins).padStart(2,"0")

            + ":"

            + String(secs).padStart(2,"0");

    }

    update();

    activeTableTimers[tableId] =

        setInterval(

            update,

            1000

        );

}

/*==========================================================
                RESERVATION NOTES
==========================================================*/

async function saveReservationNote(

    tableId

){

    const note =

        document.getElementById(

            "reservationNote"

        );

    if(!note) return;

    try{

        await fetch(

            API +

            "/tables/note/" +

            tableId,

            {

                method:"PUT",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    note:note.value

                })

            }

        );

        showToast(

            "Note Saved"

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeReservationModule(){

    loadCafeTables();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeReservationModule();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 8-3
        ADVANCED TABLE OPERATIONS
==========================================================*/

/*==========================================================
                MERGE TABLES
==========================================================*/

async function mergeTables(){

    const sourceTable =

        document.getElementById(

            "mergeSourceTable"

        )?.value;

    const targetTable =

        document.getElementById(

            "mergeTargetTable"

        )?.value;

    if(!sourceTable || !targetTable){

        showToast(

            "Select both tables",

            "warning"

        );

        return;

    }

    try{

        const response = await fetch(

            API + "/tables/merge",

            {

                method:"PUT",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    source_table:sourceTable,

                    target_table:targetTable

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast("Tables Merged");

            loadCafeTables();

        }else{

            showToast(result.message,"error");

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                SPLIT TABLE
==========================================================*/

async function splitTable(tableId){

    const guests = parseInt(

        prompt(

            "Guests to move"

        )

    );

    if(isNaN(guests)) return;

    try{

        const response = await fetch(

            API +

            "/tables/split/" +

            tableId,

            {

                method:"PUT",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    guests

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Table Split"

            );

            loadCafeTables();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                TRANSFER ORDER
==========================================================*/

async function transferOrder(){

    const fromTable =

        document.getElementById(

            "transferFrom"

        )?.value;

    const toTable =

        document.getElementById(

            "transferTo"

        )?.value;

    if(!fromTable || !toTable){

        showToast(

            "Select both tables",

            "warning"

        );

        return;

    }

    try{

        const response = await fetch(

            API +

            "/tables/transfer-order",

            {

                method:"PUT",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    from_table:fromTable,

                    to_table:toTable

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Order Transferred"

            );

            loadCafeTables();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                MOVE TABLE
==========================================================*/

async function moveGuests(tableId){

    const newTable = prompt(

        "Move guests to table number"

    );

    if(!newTable) return;

    try{

        const response = await fetch(

            API +

            "/tables/move/" +

            tableId,

            {

                method:"PUT",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    target_table:newTable

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Guests Moved"

            );

            loadCafeTables();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                GENERATE QR CODE
==========================================================*/

function generateTableQR(tableId){

    window.open(

        API +

        "/tables/qr/" +

        tableId,

        "_blank"

    );

}

/*==========================================================
                TRANSFER BILL
==========================================================*/

async function transferBill(){

    const fromTable =

        document.getElementById(

            "billTransferFrom"

        )?.value;

    const toTable =

        document.getElementById(

            "billTransferTo"

        )?.value;

    if(!fromTable || !toTable){

        showToast(

            "Select source & destination",

            "warning"

        );

        return;

    }

    try{

        const response = await fetch(

            API +

            "/tables/transfer-bill",

            {

                method:"PUT",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    from_table:fromTable,

                    to_table:toTable

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Bill Transferred"

            );

            loadCafeTables();

        }else{

            showToast(

                result.message,

                "error"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeAdvancedTableModule(){

    document

        .getElementById(

            "mergeTablesBtn"

        )

        ?.addEventListener(

            "click",

            mergeTables

        );

    document

        .getElementById(

            "transferOrderBtn"

        )

        ?.addEventListener(

            "click",

            transferOrder

        );

    document

        .getElementById(

            "transferBillBtn"

        )

        ?.addEventListener(

            "click",

            transferBill

        );

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeAdvancedTableModule();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 8-4
        TABLE ANALYTICS & MAINTENANCE
==========================================================*/

let reservationHistory = [];

/*==========================================================
                SEARCH TABLES
==========================================================*/

function searchTables(){

    const search = document.getElementById(
        "tableSearch"
    );

    if(!search) return;

    const keyword = search.value
        .toLowerCase();

    document
        .querySelectorAll(".table-card")
        .forEach(card=>{

            card.style.display =

                card.innerText
                    .toLowerCase()
                    .includes(keyword)

                ? ""

                : "none";

        });

}

/*==========================================================
                FILTER TABLE STATUS
==========================================================*/

function filterTables(){

    const filter = document.getElementById(
        "tableFilter"
    );

    if(!filter) return;

    const value = filter.value;

    document
        .querySelectorAll(".table-card")
        .forEach(card=>{

            if(value==="All"){

                card.style.display="";

                return;

            }

            card.style.display =

                card.classList.contains(
                    value.toLowerCase()
                )

                ? ""

                : "none";

        });

}

/*==========================================================
                LOAD RESERVATION HISTORY
==========================================================*/

async function loadReservationHistory(){

    try{

        const response = await fetch(

            API + "/tables/history"

        );

        if(!response.ok){

            throw new Error();

        }

        reservationHistory =
            await response.json();

        renderReservationHistory();

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                RENDER HISTORY
==========================================================*/

function renderReservationHistory(){

    const tbody = document.getElementById(
        "reservationHistoryTable"
    );

    if(!tbody) return;

    tbody.innerHTML="";

    if(reservationHistory.length===0){

        tbody.innerHTML = `

        <tr>

            <td colspan="7">

                No Reservation History

            </td>

        </tr>

        `;

        return;

    }

    reservationHistory.forEach(item=>{

        tbody.innerHTML += `

        <tr>

            <td>${item.table_name}</td>

            <td>${item.customer}</td>

            <td>${item.guests}</td>

            <td>${item.status}</td>

            <td>${formatDate(item.date)}</td>

            <td>${item.waiter || "-"}</td>

            <td>${item.notes || "-"}</td>

        </tr>

        `;

    });

}

/*==========================================================
                OCCUPANCY ANALYTICS
==========================================================*/

async function loadOccupancyAnalytics(){

    try{

        const response = await fetch(

            API + "/tables/analytics"

        );

        const data = await response.json();

        setText(

            "totalTables",

            data.total_tables || 0

        );

        setText(

            "occupiedPercentage",

            data.occupied_percentage + "%"

        );

        setText(

            "averageDiningTime",

            data.average_time || "--"

        );

        setText(

            "todayReservations",

            data.today_reservations || 0

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                EXPORT TABLE REPORT
==========================================================*/

function exportTableReport(){

    window.open(

        API +

        "/tables/export",

        "_blank"

    );

}

/*==========================================================
                MAINTENANCE MODE
==========================================================*/

async function toggleMaintenance(tableId){

    try{

        const response = await fetch(

            API +

            "/tables/maintenance/" +

            tableId,

            {

                method:"PUT"

            }

        );

        const result =
            await response.json();

        if(result.success){

            showToast(

                "Maintenance Updated"

            );

            loadCafeTables();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                AUTO REFRESH
==========================================================*/

function startTableAutoRefresh(){

    setInterval(()=>{

        loadCafeTables();

        loadOccupancyAnalytics();

    },15000);

}

/*==========================================================
                INITIALIZE EVENTS
==========================================================*/

function initializeTableEvents(){

    document
        .getElementById(
            "tableSearch"
        )
        ?.addEventListener(

            "keyup",

            searchTables

        );

    document
        .getElementById(
            "tableFilter"
        )
        ?.addEventListener(

            "change",

            filterTables

        );

    document
        .getElementById(
            "exportTableReport"
        )
        ?.addEventListener(

            "click",

            exportTableReport

        );

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeTableFinal(){

    loadReservationHistory();

    loadOccupancyAnalytics();

    initializeTableEvents();

    startTableAutoRefresh();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeTableFinal();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 9-1
        REPORTS DASHBOARD & SALES REPORTS
==========================================================*/

let reportData = {};

/*==========================================================
                LOAD REPORT DASHBOARD
==========================================================*/

async function loadReportDashboard(){

    try{

        const response = await fetch(

            API + "/reports/dashboard"

        );

        if(!response.ok){

            throw new Error(

                "Unable to load reports"

            );

        }

        reportData = await response.json();

        updateReportKPIs(reportData);

        renderSalesSummary(reportData);

    }

    catch(error){

        console.error(error);

        showToast(

            "Unable to load reports",

            "error"

        );

    }

}

/*==========================================================
                KPI CARDS
==========================================================*/

function updateReportKPIs(data){

    setText(

        "todaySales",

        formatCurrency(

            data.today_sales || 0

        )

    );

    setText(

        "weeklySales",

        formatCurrency(

            data.weekly_sales || 0

        )

    );

    setText(

        "monthlySales",

        formatCurrency(

            data.monthly_sales || 0

        )

    );

    setText(

        "yearlySales",

        formatCurrency(

            data.yearly_sales || 0

        )

    );

    setText(

        "totalOrders",

        data.total_orders || 0

    );

    setText(

        "averageOrderValue",

        formatCurrency(

            data.average_order || 0

        )

    );

}

/*==========================================================
                SALES SUMMARY
==========================================================*/

function renderSalesSummary(data){

    const tbody =

        document.getElementById(

            "salesSummaryTable"

        );

    if(!tbody) return;

    tbody.innerHTML = "";

    const reports = [

        {

            period:"Today",

            sales:data.today_sales,

            orders:data.today_orders

        },

        {

            period:"This Week",

            sales:data.weekly_sales,

            orders:data.weekly_orders

        },

        {

            period:"This Month",

            sales:data.monthly_sales,

            orders:data.monthly_orders

        },

        {

            period:"This Year",

            sales:data.yearly_sales,

            orders:data.yearly_orders

        }

    ];

    reports.forEach(item=>{

        tbody.innerHTML += `

        <tr>

            <td>${item.period}</td>

            <td>${item.orders || 0}</td>

            <td>${formatCurrency(item.sales || 0)}</td>

        </tr>

        `;

    });

}

/*==========================================================
                DAILY REPORT
==========================================================*/

async function loadDailyReport(){

    await loadPeriodReport(

        "daily"

    );

}

/*==========================================================
                WEEKLY REPORT
==========================================================*/

async function loadWeeklyReport(){

    await loadPeriodReport(

        "weekly"

    );

}

/*==========================================================
                MONTHLY REPORT
==========================================================*/

async function loadMonthlyReport(){

    await loadPeriodReport(

        "monthly"

    );

}

/*==========================================================
                YEARLY REPORT
==========================================================*/

async function loadYearlyReport(){

    await loadPeriodReport(

        "yearly"

    );

}

/*==========================================================
                COMMON REPORT
==========================================================*/

async function loadPeriodReport(period){

    try{

        const response = await fetch(

            API +

            "/reports/" +

            period

        );

        if(!response.ok){

            throw new Error();

        }

        const report =

            await response.json();

        renderPeriodReport(

            report,

            period

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                REPORT TABLE
==========================================================*/

function renderPeriodReport(

    report,

    period

){

    const tbody =

        document.getElementById(

            "periodReportTable"

        );

    if(!tbody) return;

    tbody.innerHTML = "";

    report.forEach(row=>{

        tbody.innerHTML += `

        <tr>

            <td>${row.date}</td>

            <td>${row.orders}</td>

            <td>${formatCurrency(row.sales)}</td>

            <td>${formatCurrency(row.tax)}</td>

            <td>${formatCurrency(row.discount)}</td>

            <td>${formatCurrency(row.net_sales)}</td>

        </tr>

        `;

    });

    setText(

        "currentReport",

        period.toUpperCase()

    );

}

/*==========================================================
                REFRESH REPORTS
==========================================================*/

async function refreshReports(){

    await loadReportDashboard();

    showToast(

        "Reports Updated"

    );

}

/*==========================================================
                INITIALIZE EVENTS
==========================================================*/

function initializeReportEvents(){

    document

        .getElementById(

            "dailyReportBtn"

        )

        ?.addEventListener(

            "click",

            loadDailyReport

        );

    document

        .getElementById(

            "weeklyReportBtn"

        )

        ?.addEventListener(

            "click",

            loadWeeklyReport

        );

    document

        .getElementById(

            "monthlyReportBtn"

        )

        ?.addEventListener(

            "click",

            loadMonthlyReport

        );

    document

        .getElementById(

            "yearlyReportBtn"

        )

        ?.addEventListener(

            "click",

            loadYearlyReport

        );

    document

        .getElementById(

            "refreshReports"

        )

        ?.addEventListener(

            "click",

            refreshReports

        );

}

/*==========================================================
                AUTO REFRESH
==========================================================*/

function startReportRefresh(){

    setInterval(()=>{

        loadReportDashboard();

    },30000);

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeReportsModule(){

    loadReportDashboard();

    initializeReportEvents();

    startReportRefresh();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeReportsModule();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 9-2
        FINANCIAL ANALYTICS & REPORTS
==========================================================*/

let financialReport = {};

/*==========================================================
                LOAD FINANCIAL REPORT
==========================================================*/

async function loadFinancialReport(){

    try{

        const response = await fetch(

            API + "/reports/financial"

        );

        if(!response.ok){

            throw new Error(

                "Unable to load financial report"

            );

        }

        financialReport = await response.json();

        updateFinancialKPIs(financialReport);

        renderPaymentReport(

            financialReport.payments || []

        );

    }

    catch(error){

        console.error(error);

        showToast(

            "Unable to load financial report",

            "error"

        );

    }

}

/*==========================================================
                FINANCIAL KPI CARDS
==========================================================*/

function updateFinancialKPIs(data){

    setText(

        "totalRevenue",

        formatCurrency(

            data.revenue || 0

        )

    );

    setText(

        "totalProfit",

        formatCurrency(

            data.profit || 0

        )

    );

    setText(

        "totalExpense",

        formatCurrency(

            data.expense || 0

        )

    );

    setText(

        "totalTax",

        formatCurrency(

            data.tax || 0

        )

    );

    setText(

        "grossMargin",

        (data.margin || 0) + "%"

    );

    setText(

        "netIncome",

        formatCurrency(

            data.net_income || 0

        )

    );

}

/*==========================================================
                PAYMENT REPORT
==========================================================*/

function renderPaymentReport(payments){

    const tbody =

        document.getElementById(

            "paymentReportTable"

        );

    if(!tbody) return;

    tbody.innerHTML = "";

    if(payments.length===0){

        tbody.innerHTML = `

        <tr>

            <td colspan="4">

                No Payment Data

            </td>

        </tr>

        `;

        return;

    }

    payments.forEach(item=>{

        tbody.innerHTML += `

        <tr>

            <td>${item.method}</td>

            <td>${item.transactions}</td>

            <td>${formatCurrency(item.amount)}</td>

            <td>${item.percentage}%</td>

        </tr>

        `;

    });

}

/*==========================================================
                EXPENSE REPORT
==========================================================*/

async function loadExpenseReport(){

    try{

        const response = await fetch(

            API + "/reports/expenses"

        );

        const expenses = await response.json();

        renderExpenseReport(expenses);

    }

    catch(error){

        console.error(error);

    }

}

function renderExpenseReport(expenses){

    const tbody =

        document.getElementById(

            "expenseReportTable"

        );

    if(!tbody) return;

    tbody.innerHTML = "";

    expenses.forEach(item=>{

        tbody.innerHTML += `

        <tr>

            <td>${item.category}</td>

            <td>${item.description}</td>

            <td>${formatCurrency(item.amount)}</td>

            <td>${formatDate(item.date)}</td>

        </tr>

        `;

    });

}

/*==========================================================
                TAX REPORT
==========================================================*/

async function loadTaxReport(){

    try{

        const response = await fetch(

            API + "/reports/tax"

        );

        const tax = await response.json();

        setText(

            "taxCollected",

            formatCurrency(

                tax.collected || 0

            )

        );

        setText(

            "taxPaid",

            formatCurrency(

                tax.paid || 0

            )

        );

        setText(

            "taxBalance",

            formatCurrency(

                tax.balance || 0

            )

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                PAYMENT METHOD SUMMARY
==========================================================*/

async function loadPaymentAnalytics(){

    try{

        const response = await fetch(

            API + "/reports/payment-summary"

        );

        const summary = await response.json();

        setText(

            "cashPayments",

            summary.cash || 0

        );

        setText(

            "cardPayments",

            summary.card || 0

        );

        setText(

            "upiPayments",

            summary.upi || 0

        );

        setText(

            "walletPayments",

            summary.wallet || 0

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                REFRESH FINANCIAL REPORTS
==========================================================*/

async function refreshFinancialReports(){

    await Promise.all([

        loadFinancialReport(),

        loadExpenseReport(),

        loadTaxReport(),

        loadPaymentAnalytics()

    ]);

    showToast(

        "Financial Reports Updated"

    );

}

/*==========================================================
                INITIALIZE EVENTS
==========================================================*/

function initializeFinancialEvents(){

    document

        .getElementById(

            "refreshFinancialReports"

        )

        ?.addEventListener(

            "click",

            refreshFinancialReports

        );

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeFinancialReports(){

    loadFinancialReport();

    loadExpenseReport();

    loadTaxReport();

    loadPaymentAnalytics();

    initializeFinancialEvents();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeFinancialReports();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 9-3
    PRODUCT • INVENTORY • CUSTOMER ANALYTICS
==========================================================*/

let analyticsData = {};

/*==========================================================
                LOAD ANALYTICS
==========================================================*/

async function loadBusinessAnalytics(){

    try{

        const response = await fetch(

            API + "/reports/analytics"

        );

        if(!response.ok){

            throw new Error(

                "Unable to load analytics"

            );

        }

        analyticsData = await response.json();

        renderTopProducts(

            analyticsData.top_products || []

        );

        renderCategoryAnalytics(

            analyticsData.categories || []

        );

        renderInventoryAnalytics(

            analyticsData.inventory || []

        );

        renderCustomerAnalytics(

            analyticsData.customers || {}

        );

        renderEmployeeAnalytics(

            analyticsData.employees || []

        );

    }

    catch(error){

        console.error(error);

        showToast(

            "Analytics loading failed",

            "error"

        );

    }

}

/*==========================================================
                TOP PRODUCTS
==========================================================*/

function renderTopProducts(products){

    const tbody =

        document.getElementById(

            "topProductsTable"

        );

    if(!tbody) return;

    tbody.innerHTML = "";

    products.forEach((product,index)=>{

        tbody.innerHTML += `

        <tr>

            <td>${index+1}</td>

            <td>${product.name}</td>

            <td>${product.quantity}</td>

            <td>${formatCurrency(product.sales)}</td>

        </tr>

        `;

    });

}

/*==========================================================
                CATEGORY ANALYTICS
==========================================================*/

function renderCategoryAnalytics(categories){

    const tbody =

        document.getElementById(

            "categoryAnalyticsTable"

        );

    if(!tbody) return;

    tbody.innerHTML = "";

    categories.forEach(category=>{

        tbody.innerHTML += `

        <tr>

            <td>${category.name}</td>

            <td>${category.products}</td>

            <td>${category.orders}</td>

            <td>${formatCurrency(category.sales)}</td>

        </tr>

        `;

    });

}

/*==========================================================
                INVENTORY ANALYTICS
==========================================================*/

function renderInventoryAnalytics(items){

    const tbody =

        document.getElementById(

            "inventoryAnalyticsTable"

        );

    if(!tbody) return;

    tbody.innerHTML="";

    items.forEach(item=>{

        tbody.innerHTML +=`

        <tr>

            <td>${item.product}</td>

            <td>${item.stock}</td>

            <td>${item.minimum}</td>

            <td>${item.status}</td>

        </tr>

        `;

    });

}

/*==========================================================
                CUSTOMER ANALYTICS
==========================================================*/

function renderCustomerAnalytics(customer){

    setText(

        "totalCustomers",

        customer.total || 0

    );

    setText(

        "newCustomers",

        customer.new || 0

    );

    setText(

        "repeatCustomers",

        customer.repeat || 0

    );

    setText(

        "customerRetention",

        (customer.retention || 0) + "%"

    );

}

/*==========================================================
                EMPLOYEE PERFORMANCE
==========================================================*/

function renderEmployeeAnalytics(employees){

    const tbody =

        document.getElementById(

            "employeeAnalyticsTable"

        );

    if(!tbody) return;

    tbody.innerHTML="";

    employees.forEach(emp=>{

        tbody.innerHTML +=`

        <tr>

            <td>${emp.name}</td>

            <td>${emp.orders}</td>

            <td>${formatCurrency(emp.sales)}</td>

            <td>${emp.rating}</td>

        </tr>

        `;

    });

}

/*==========================================================
                LOW STOCK REPORT
==========================================================*/

async function loadLowStockReport(){

    try{

        const response = await fetch(

            API +

            "/reports/low-stock"

        );

        const items =

            await response.json();

        setText(

            "lowStockItems",

            items.length

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                CUSTOMER RANKING
==========================================================*/

async function loadTopCustomers(){

    try{

        const response = await fetch(

            API +

            "/reports/top-customers"

        );

        const customers =

            await response.json();

        const tbody =

            document.getElementById(

                "topCustomersTable"

            );

        if(!tbody) return;

        tbody.innerHTML="";

        customers.forEach(customer=>{

            tbody.innerHTML +=`

            <tr>

                <td>${customer.name}</td>

                <td>${customer.orders}</td>

                <td>${formatCurrency(customer.total)}</td>

            </tr>

            `;

        });

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                REFRESH ANALYTICS
==========================================================*/

async function refreshBusinessAnalytics(){

    await Promise.all([

        loadBusinessAnalytics(),

        loadLowStockReport(),

        loadTopCustomers()

    ]);

    showToast(

        "Business Analytics Updated"

    );

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeBusinessAnalytics(){

    loadBusinessAnalytics();

    loadLowStockReport();

    loadTopCustomers();

    document

        .getElementById(

            "refreshAnalytics"

        )

        ?.addEventListener(

            "click",

            refreshBusinessAnalytics

        );

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeBusinessAnalytics();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 9-4
        CHARTS • EXPORT • PRINT REPORTS
==========================================================*/


let revenueChart = null;
let profitChart = null;

/*==========================================================
                LOAD CHART DATA
==========================================================*/

async function loadCharts(){

    try{

        const response = await fetch(
            API + "/reports/charts"
        );


        if(!response.ok){

            throw new Error();

        }


        const result = await response.json();


        console.log(
            "Charts API response:",
            result
        );


        const data = result.data;


        renderSalesChart(data.sales);

        renderRevenueChart(data.revenue);

        renderProfitChart(data.profit);


    }
    catch(error){

        console.error(error);

        showToast(
            "Unable to load charts",
            "error"
        );

    }

}
/*==========================================================
                SALES CHART
==========================================================*/

function renderSalesChart(data){

    const canvas =

        document.getElementById(

            "salesChart"

        );

    if(!canvas) return;

    if(salesChart){

        salesChart.destroy();

    }

    salesChart = new Chart(canvas,{

        type:"line",

        data:{

            labels:data.labels,

            datasets:[{

                label:"Sales",

                data:data.values,

                tension:0.4,

                fill:false

            }]

        },

        options:{

            responsive:true,

            maintainAspectRatio:false

        }

    });

}

/*==========================================================
                REVENUE CHART
==========================================================*/

function renderRevenueChart(data){

    const canvas =

        document.getElementById(

            "revenueChart"

        );

    if(!canvas) return;

    if(revenueChart){

        revenueChart.destroy();

    }

    revenueChart = new Chart(canvas,{

        type:"bar",

        data:{

            labels:data.labels,

            datasets:[{

                label:"Revenue",

                data:data.values

            }]

        },

        options:{

            responsive:true,

            maintainAspectRatio:false

        }

    });

}

/*==========================================================
                PROFIT CHART
==========================================================*/

function renderProfitChart(data){

    const canvas =

        document.getElementById(

            "profitChart"

        );

    if(!canvas) return;

    if(profitChart){

        profitChart.destroy();

    }

    profitChart = new Chart(canvas,{

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

    });

}

/*==========================================================
                EXPORT PDF
==========================================================*/

function exportPDFReport(){

    window.open(

        API +

        "/reports/export/pdf",

        "_blank"

    );

}

/*==========================================================
                EXPORT EXCEL
==========================================================*/

function exportExcelReport(){

    window.open(

        API +

        "/reports/export/excel",

        "_blank"

    );

}

/*==========================================================
                PRINT REPORT
==========================================================*/

function printReport(){

    window.print();

}

/*==========================================================
                SCHEDULE REPORT
==========================================================*/

async function scheduleReport(){

    const email = prompt(

        "Enter Email Address"

    );

    if(!email) return;

    const frequency = prompt(

        "Frequency (Daily/Weekly/Monthly)"

    );

    if(!frequency) return;

    try{

        const response = await fetch(

            API +

            "/reports/schedule",

            {

                method:"POST",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    email,

                    frequency

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Report Scheduled"

            );

        }

        else{

            showToast(

                result.message,

                "error"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                REFRESH CHARTS
==========================================================*/

async function refreshCharts(){

    await loadCharts();

    showToast(

        "Charts Updated"

    );

}

/*==========================================================
                INITIALIZE EVENTS
==========================================================*/

function initializeChartEvents(){

    document

        .getElementById(

            "exportPDF"

        )

        ?.addEventListener(

            "click",

            exportPDFReport

        );

    document

        .getElementById(

            "exportExcel"

        )

        ?.addEventListener(

            "click",

            exportExcelReport

        );

    document

        .getElementById(

            "printReport"

        )

        ?.addEventListener(

            "click",

            printReport

        );

    document

        .getElementById(

            "scheduleReport"

        )

        ?.addEventListener(

            "click",

            scheduleReport

        );

    document

        .getElementById(

            "refreshCharts"

        )

        ?.addEventListener(

            "click",

            refreshCharts

        );

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeChartsModule(){

    loadCharts();

    initializeChartEvents();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeChartsModule();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 9-5
      AI INSIGHTS • FORECASTING • TREND ANALYSIS
==========================================================*/

let businessInsights = {};

/*==========================================================
                LOAD BUSINESS INSIGHTS
==========================================================*/

async function loadBusinessInsights(){

    try{

        const response = await fetch(

            API + "/reports/business-insights"

        );

        if(!response.ok){

            throw new Error("Unable to load insights");

        }

        businessInsights = await response.json();

        renderBusinessInsights();

    }

    catch(error){

        console.error(error);

        showToast(

            "Unable to load business insights",

            "error"

        );

    }

}

/*==========================================================
                RENDER INSIGHTS
==========================================================*/

function renderBusinessInsights(){

    setText(

        "businessHealth",

        businessInsights.health || "Good"

    );

    setText(

        "salesTrend",

        businessInsights.sales_trend || "--"

    );

    setText(

        "growthRate",

        (businessInsights.growth_rate || 0) + "%"

    );

    setText(

        "forecastRevenue",

        formatCurrency(

            businessInsights.forecast_revenue || 0

        )

    );

}

/*==========================================================
                SALES FORECAST
==========================================================*/

async function loadSalesForecast(){

    try{

        const response = await fetch(

            API + "/reports/sales-forecast"

        );

        const forecast = await response.json();

        const tbody = document.getElementById(

            "forecastTable"

        );

        if(!tbody) return;

        tbody.innerHTML = "";

        forecast.forEach(item=>{

            tbody.innerHTML += `

            <tr>

                <td>${item.period}</td>

                <td>${formatCurrency(item.predicted_sales)}</td>

                <td>${item.confidence}%</td>

            </tr>

            `;

        });

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                PEAK HOURS
==========================================================*/

async function loadPeakHours(){

    try{

        const response = await fetch(

            API + "/reports/peak-hours"

        );

        const data = await response.json();

        const tbody = document.getElementById(

            "peakHoursTable"

        );

        if(!tbody) return;

        tbody.innerHTML = "";

        data.forEach(hour=>{

            tbody.innerHTML += `

            <tr>

                <td>${hour.hour}</td>

                <td>${hour.orders}</td>

                <td>${formatCurrency(hour.sales)}</td>

            </tr>

            `;

        });

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                REPORT FILTER
==========================================================*/

async function applyReportFilter(){

    const fromDate =

        document.getElementById(

            "reportFromDate"

        )?.value;

    const toDate =

        document.getElementById(

            "reportToDate"

        )?.value;

    try{

        const response = await fetch(

            API + "/reports/filter",

            {

                method:"POST",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify({

                    from_date:fromDate,

                    to_date:toDate

                })

            }

        );

        const filtered = await response.json();

        renderPeriodReport(

            filtered,

            "CUSTOM"

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                TREND ANALYSIS
==========================================================*/

async function loadTrendAnalysis(){

    try{

        const response = await fetch(

            API + "/reports/trends"

        );

        const trends = await response.json();

        setText(

            "fastestGrowingCategory",

            trends.category || "-"

        );

        setText(

            "bestSellingHour",

            trends.best_hour || "-"

        );

        setText(

            "topEmployee",

            trends.employee || "-"

        );

        setText(

            "topCustomer",

            trends.customer || "-"

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                AUTO REFRESH
==========================================================*/

function startAnalyticsRefresh(){

    setInterval(()=>{

        loadBusinessInsights();

        loadSalesForecast();

        loadPeakHours();

        loadTrendAnalysis();

    },60000);

}

/*==========================================================
                INITIALIZE EVENTS
==========================================================*/

function initializeInsightEvents(){

    document

        .getElementById(

            "applyReportFilter"

        )

        ?.addEventListener(

            "click",

            applyReportFilter

        );

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeBusinessInsights(){

    loadBusinessInsights();

    loadSalesForecast();

    loadPeakHours();

    loadTrendAnalysis();

    initializeInsightEvents();

    startAnalyticsRefresh();

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeBusinessInsights();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 10-1
        EMPLOYEE MANAGEMENT & DIRECTORY
==========================================================*/

let employees = [];

/*==========================================================
                LOAD EMPLOYEES
==========================================================*/

async function loadEmployees(){

    try{

        const response = await fetch(

            API + "/employees"

        );

        if(!response.ok){

            throw new Error(
                "Unable to load employees"
            );

        }

        employees = await response.json();

        renderEmployees(employees);

        updateEmployeeSummary(employees);

    }

    catch(error){

        console.error(error);

        showToast(

            "Unable to load employees",

            "error"

        );

    }

}

/*==========================================================
                RENDER EMPLOYEES
==========================================================*/

function renderEmployees(list){

    const tbody = document.getElementById(
        "employeeTable"
    );

    if(!tbody) return;

    tbody.innerHTML = "";

    if(list.length===0){

        tbody.innerHTML = `

        <tr>

            <td colspan="8">

                No Employees Found

            </td>

        </tr>

        `;

        return;

    }

    list.forEach(employee=>{

        tbody.innerHTML += `

        <tr>

            <td>${employee.id}</td>

            <td>${employee.name}</td>

            <td>${employee.designation}</td>

            <td>${employee.phone}</td>

            <td>${employee.shift}</td>

            <td>${employee.status}</td>

            <td>${employee.salary}</td>

            <td>

                <button
                onclick="viewEmployee(${employee.id})">

                    View

                </button>

            </td>

        </tr>

        `;

    });

}

/*==========================================================
                EMPLOYEE SUMMARY
==========================================================*/

function updateEmployeeSummary(list){

    let active = 0;

    let inactive = 0;

    let managers = 0;

    let staff = 0;

    list.forEach(emp=>{

        if(emp.status==="Active"){

            active++;

        }

        else{

            inactive++;

        }

        if(emp.designation==="Manager"){

            managers++;

        }

        else{

            staff++;

        }

    });

    setText(

        "totalEmployees",

        list.length

    );

    setText(

        "activeEmployees",

        active

    );

    setText(

        "inactiveEmployees",

        inactive

    );

    setText(

        "managerCount",

        managers

    );

    setText(

        "staffCount",

        staff

    );

}

/*==========================================================
                VIEW EMPLOYEE
==========================================================*/

async function viewEmployee(id){

    try{

        const response = await fetch(

            API +

            "/employees/" +

            id

        );

        if(!response.ok){

            throw new Error();

        }

        const employee =

            await response.json();

        showEmployeeModal(employee);

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                EMPLOYEE MODAL
==========================================================*/

function showEmployeeModal(employee){

    const modal =

        document.getElementById(

            "employeeModal"

        );

    const body =

        document.getElementById(

            "employeeModalBody"

        );

    if(!modal || !body) return;

    body.innerHTML = `

        <h2>${employee.name}</h2>

        <hr>

        <p>

            Designation :
            ${employee.designation}

        </p>

        <p>

            Phone :
            ${employee.phone}

        </p>

        <p>

            Email :
            ${employee.email}

        </p>

        <p>

            Shift :
            ${employee.shift}

        </p>

        <p>

            Salary :
            ${formatCurrency(employee.salary)}

        </p>

        <p>

            Status :
            ${employee.status}

        </p>

    `;

    modal.classList.add(

        "active"

    );

}

/*==========================================================
                CLOSE MODAL
==========================================================*/

function closeEmployeeModal(){

    document

        .getElementById(

            "employeeModal"

        )

        ?.classList.remove(

            "active"

        );

}

/*==========================================================
                SEARCH EMPLOYEE
==========================================================*/

function searchEmployees(){

    const keyword =

        document

        .getElementById(

            "employeeSearch"

        )

        ?.value

        .toLowerCase();

    if(keyword===undefined) return;

    renderEmployees(

        employees.filter(emp=>

            emp.name

            .toLowerCase()

            .includes(keyword)

            ||

            emp.designation

            .toLowerCase()

            .includes(keyword)

        )

    );

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeEmployeeModule(){

    loadEmployees();

    document

        .getElementById(

            "employeeSearch"

        )

        ?.addEventListener(

            "keyup",

            searchEmployees

        );

    document

        .getElementById(

            "closeEmployeeModal"

        )

        ?.addEventListener(

            "click",

            closeEmployeeModal

        );

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeEmployeeModule();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 10-2
        EMPLOYEE CRUD & ROLE MANAGEMENT
==========================================================*/

/*==========================================================
                ADD EMPLOYEE
==========================================================*/

async function addEmployee(){

    const data = {

        name:

            document.getElementById(

                "employeeName"

            ).value,

        designation:

            document.getElementById(

                "employeeDesignation"

            ).value,

        phone:

            document.getElementById(

                "employeePhone"

            ).value,

        email:

            document.getElementById(

                "employeeEmail"

            ).value,

        shift:

            document.getElementById(

                "employeeShift"

            ).value,

        salary:

            document.getElementById(

                "employeeSalary"

            ).value,

        role:

            document.getElementById(

                "employeeRole"

            ).value

    };

    try{

        const response = await fetch(

            API + "/employees",

            {

                method:"POST",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify(data)

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Employee Added"

            );

            loadEmployees();

            clearEmployeeForm();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                EDIT EMPLOYEE
==========================================================*/

async function editEmployee(id){

    const data={

        name:

            document.getElementById(

                "employeeName"

            ).value,

        designation:

            document.getElementById(

                "employeeDesignation"

            ).value,

        phone:

            document.getElementById(

                "employeePhone"

            ).value,

        email:

            document.getElementById(

                "employeeEmail"

            ).value,

        shift:

            document.getElementById(

                "employeeShift"

            ).value,

        salary:

            document.getElementById(

                "employeeSalary"

            ).value,

        role:

            document.getElementById(

                "employeeRole"

            ).value

    };

    try{

        const response = await fetch(

            API +

            "/employees/" +

            id,

            {

                method:"PUT",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify(data)

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Employee Updated"

            );

            loadEmployees();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                DELETE EMPLOYEE
==========================================================*/

async function deleteEmployee(id){

    if(!confirm(

        "Delete this employee?"

    )) return;

    try{

        const response = await fetch(

            API +

            "/employees/" +

            id,

            {

                method:"DELETE"

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Employee Deleted"

            );

            loadEmployees();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                PHOTO UPLOAD
==========================================================*/

async function uploadEmployeePhoto(id){

    const input =

        document.getElementById(

            "employeePhoto"

        );

    if(

        !input ||

        input.files.length===0

    ) return;

    const formData =

        new FormData();

    formData.append(

        "photo",

        input.files[0]

    );

    try{

        const response = await fetch(

            API +

            "/employees/photo/" +

            id,

            {

                method:"POST",

                body:formData

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Photo Uploaded"

            );

            loadEmployees();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                EMPLOYEE ID
==========================================================*/

async function generateEmployeeID(){

    try{

        const response = await fetch(

            API +

            "/employees/generate-id"

        );

        const data =

            await response.json();

        document.getElementById(

            "employeeId"

        ).value =

            data.employee_id;

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                ROLE UPDATE
==========================================================*/

async function updateEmployeeRole(id){

    const role =

        document.getElementById(

            "employeeRole"

        ).value;

    try{

        const response = await fetch(

            API +

            "/employees/role/" +

            id,

            {

                method:"PUT",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify({

                    role

                })

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Role Updated"

            );

            loadEmployees();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                CLEAR FORM
==========================================================*/

function clearEmployeeForm(){

    [

        "employeeName",

        "employeeDesignation",

        "employeePhone",

        "employeeEmail",

        "employeeShift",

        "employeeSalary",

        "employeeRole",

        "employeeId"

    ].forEach(id=>{

        const element =

            document.getElementById(id);

        if(element){

            element.value="";

        }

    });

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeEmployeeCRUD(){

    document

        .getElementById(

            "addEmployeeBtn"

        )

        ?.addEventListener(

            "click",

            addEmployee

        );

    document

        .getElementById(

            "generateEmployeeId"

        )

        ?.addEventListener(

            "click",

            generateEmployeeID

        );

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeEmployeeCRUD();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 10-3
        ATTENDANCE • PAYROLL • PERFORMANCE
==========================================================*/

let attendanceRecords = [];
let payrollRecords = [];

/*==========================================================
                LOAD ATTENDANCE
==========================================================*/

async function loadAttendance(){

    try{

        const response = await fetch(

            API + "/employees/attendance"

        );

        if(!response.ok){

            throw new Error();

        }

        attendanceRecords =

            await response.json();

        renderAttendance();

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                ATTENDANCE TABLE
==========================================================*/

function renderAttendance(){

    const tbody =

        document.getElementById(

            "attendanceTable"

        );

    if(!tbody) return;

    tbody.innerHTML="";

    attendanceRecords.forEach(record=>{

        tbody.innerHTML += `

        <tr>

            <td>${record.employee}</td>

            <td>${record.date}</td>

            <td>${record.check_in || "-"}</td>

            <td>${record.check_out || "-"}</td>

            <td>${record.status}</td>

        </tr>

        `;

    });

}

/*==========================================================
                CHECK IN
==========================================================*/

async function employeeCheckIn(id){

    try{

        const response = await fetch(

            API +

            "/employees/checkin/" +

            id,

            {

                method:"POST"

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Check-in Successful"

            );

            loadAttendance();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                CHECK OUT
==========================================================*/

async function employeeCheckOut(id){

    try{

        const response = await fetch(

            API +

            "/employees/checkout/" +

            id,

            {

                method:"POST"

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Check-out Successful"

            );

            loadAttendance();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                LEAVE MANAGEMENT
==========================================================*/

async function applyLeave(){

    const employeeId =

        document.getElementById(

            "leaveEmployee"

        ).value;

    const fromDate =

        document.getElementById(

            "leaveFrom"

        ).value;

    const toDate =

        document.getElementById(

            "leaveTo"

        ).value;

    const reason =

        document.getElementById(

            "leaveReason"

        ).value;

    try{

        const response = await fetch(

            API +

            "/employees/leave",

            {

                method:"POST",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify({

                    employee_id:employeeId,

                    from_date:fromDate,

                    to_date:toDate,

                    reason

                })

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Leave Request Submitted"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                PAYROLL
==========================================================*/

async function loadPayroll(){

    try{

        const response = await fetch(

            API +

            "/employees/payroll"

        );

        payrollRecords =

            await response.json();

        renderPayroll();

    }

    catch(error){

        console.error(error);

    }

}

function renderPayroll(){

    const tbody =

        document.getElementById(

            "payrollTable"

        );

    if(!tbody) return;

    tbody.innerHTML="";

    payrollRecords.forEach(item=>{

        tbody.innerHTML += `

        <tr>

            <td>${item.employee}</td>

            <td>${formatCurrency(item.salary)}</td>

            <td>${formatCurrency(item.bonus)}</td>

            <td>${formatCurrency(item.deduction)}</td>

            <td>${formatCurrency(item.net_salary)}</td>

        </tr>

        `;

    });

}

/*==========================================================
                PERFORMANCE
==========================================================*/

async function loadPerformance(){

    try{

        const response = await fetch(

            API +

            "/employees/performance"

        );

        const performance =

            await response.json();

        const tbody =

            document.getElementById(

                "performanceTable"

            );

        if(!tbody) return;

        tbody.innerHTML="";

        performance.forEach(emp=>{

            tbody.innerHTML += `

            <tr>

                <td>${emp.employee}</td>

                <td>${emp.orders}</td>

                <td>${emp.rating}</td>

                <td>${emp.score}</td>

            </tr>

            `;

        });

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                ATTENDANCE SUMMARY
==========================================================*/

async function loadAttendanceSummary(){

    try{

        const response = await fetch(

            API +

            "/employees/attendance-summary"

        );

        const data =

            await response.json();

        setText(

            "presentEmployees",

            data.present || 0

        );

        setText(

            "absentEmployees",

            data.absent || 0

        );

        setText(

            "leaveEmployees",

            data.leave || 0

        );

        setText(

            "attendanceRate",

            (data.rate || 0) + "%"

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                REFRESH
==========================================================*/

async function refreshEmployeeReports(){

    await Promise.all([

        loadAttendance(),

        loadPayroll(),

        loadPerformance(),

        loadAttendanceSummary()

    ]);

    showToast(

        "Employee Reports Updated"

    );

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeEmployeeReports(){

    loadAttendance();

    loadPayroll();

    loadPerformance();

    loadAttendanceSummary();

    document

        .getElementById(

            "applyLeaveBtn"

        )

        ?.addEventListener(

            "click",

            applyLeave

        );

    document

        .getElementById(

            "refreshEmployeeReports"

        )

        ?.addEventListener(

            "click",

            refreshEmployeeReports

        );

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeEmployeeReports();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 10-4
EMPLOYEE PROFILE • PERMISSIONS • ID CARDS • IMPORT/EXPORT
==========================================================*/

/*==========================================================
                LOAD PROFILE
==========================================================*/

async function loadEmployeeProfile(id){

    try{

        const response = await fetch(

            API + "/employees/profile/" + id

        );

        if(!response.ok){

            throw new Error();

        }

        const employee =

            await response.json();

        renderEmployeeProfile(employee);

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                PROFILE
==========================================================*/

function renderEmployeeProfile(employee){

    setText(

        "profileName",

        employee.name

    );

    setText(

        "profileDesignation",

        employee.designation

    );

    setText(

        "profileEmail",

        employee.email

    );

    setText(

        "profilePhone",

        employee.phone

    );

    setText(

        "profileShift",

        employee.shift

    );

    setText(

        "profileRole",

        employee.role

    );

    const photo =

        document.getElementById(

            "profilePhoto"

        );

    if(photo){

        photo.src =

            employee.photo ||

            "assets/images/user.png";

    }

}

/*==========================================================
                UPDATE PERMISSIONS
==========================================================*/

async function updatePermissions(id){

    const permissions=[];

    document

        .querySelectorAll(

            ".permission-check"

        )

        .forEach(item=>{

            if(item.checked){

                permissions.push(

                    item.value

                );

            }

        });

    try{

        const response = await fetch(

            API +

            "/employees/permissions/" +

            id,

            {

                method:"PUT",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify({

                    permissions

                })

            }

        );

        const result=

            await response.json();

        if(result.success){

            showToast(

                "Permissions Updated"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                REWARD EMPLOYEE
==========================================================*/

async function rewardEmployee(id){

    const reward = prompt(

        "Reward"

    );

    if(!reward) return;

    try{

        const response = await fetch(

            API +

            "/employees/reward/" +

            id,

            {

                method:"POST",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify({

                    reward

                })

            }

        );

        const result=

            await response.json();

        if(result.success){

            showToast(

                "Reward Added"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                TRAINING
==========================================================*/

async function assignTraining(id){

    const course = prompt(

        "Training Course"

    );

    if(!course) return;

    try{

        const response = await fetch(

            API +

            "/employees/training/" +

            id,

            {

                method:"POST",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify({

                    course

                })

            }

        );

        const result=

            await response.json();

        if(result.success){

            showToast(

                "Training Assigned"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                SEND NOTIFICATION
==========================================================*/

async function notifyEmployee(id){

    const message = prompt(

        "Notification"

    );

    if(!message) return;

    try{

        const response = await fetch(

            API +

            "/employees/notify/" +

            id,

            {

                method:"POST",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify({

                    message

                })

            }

        );

        const result=

            await response.json();

        if(result.success){

            showToast(

                "Notification Sent"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                GENERATE ID CARD
==========================================================*/

function generateEmployeeCard(id){

    window.open(

        API +

        "/employees/id-card/" +

        id,

        "_blank"

    );

}

/*==========================================================
                EXPORT
==========================================================*/

function exportEmployees(){

    window.open(

        API +

        "/employees/export",

        "_blank"

    );

}

/*==========================================================
                IMPORT
==========================================================*/

async function importEmployees(){

    const file =

        document.getElementById(

            "employeeImport"

        );

    if(

        !file ||

        file.files.length===0

    ) return;

    const formData =

        new FormData();

    formData.append(

        "file",

        file.files[0]

    );

    try{

        const response = await fetch(

            API +

            "/employees/import",

            {

                method:"POST",

                body:formData

            }

        );

        const result=

            await response.json();

        if(result.success){

            showToast(

                "Employees Imported"

            );

            loadEmployees();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeEmployeeAdvanced(){

    document

        .getElementById(

            "employeeExport"

        )

        ?.addEventListener(

            "click",

            exportEmployees

        );

    document

        .getElementById(

            "employeeImportBtn"

        )

        ?.addEventListener(

            "click",

            importEmployees

        );

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeEmployeeAdvanced();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 11-1
        GENERAL SETTINGS & CAFE PROFILE
==========================================================*/

let systemSettings = {};

/*==========================================================
                LOAD SETTINGS
==========================================================*/

async function loadSystemSettings(){

    try{

        const response = await fetch(

            API + "/settings"

        );

        if(!response.ok){

            throw new Error();

        }

        systemSettings =

            await response.json();

        populateSettingsForm();

    }

    catch(error){

        console.error(error);

        showToast(

            "Unable to load settings",

            "error"

        );

    }

}

/*==========================================================
                POPULATE FORM
==========================================================*/

function populateSettingsForm(){

    const fields={

        cafeName:

            systemSettings.cafe_name,

        ownerName:

            systemSettings.owner_name,

        phone:

            systemSettings.phone,

        email:

            systemSettings.email,

        address:

            systemSettings.address,

        gst:

            systemSettings.gst,

        tax:

            systemSettings.tax,

        currency:

            systemSettings.currency,

        timezone:

            systemSettings.timezone

    };

    Object.keys(fields).forEach(id=>{

        const element =

            document.getElementById(id);

        if(element){

            element.value =

                fields[id] || "";

        }

    });

}

/*==========================================================
                SAVE SETTINGS
==========================================================*/

async function saveSystemSettings(){

    const data={

        cafe_name:

            document.getElementById(

                "cafeName"

            ).value,

        owner_name:

            document.getElementById(

                "ownerName"

            ).value,

        phone:

            document.getElementById(

                "phone"

            ).value,

        email:

            document.getElementById(

                "email"

            ).value,

        address:

            document.getElementById(

                "address"

            ).value,

        gst:

            document.getElementById(

                "gst"

            ).value,

        tax:

            document.getElementById(

                "tax"

            ).value,

        currency:

            document.getElementById(

                "currency"

            ).value,

        timezone:

            document.getElementById(

                "timezone"

            ).value

    };

    try{

        const response = await fetch(

            API + "/settings",

            {

                method:"PUT",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify(data)

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Settings Saved"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                LOGO UPLOAD
==========================================================*/

async function uploadCafeLogo(){

    const file =

        document.getElementById(

            "logoUpload"

        );

    if(

        !file ||

        file.files.length===0

    ) return;

    const formData =

        new FormData();

    formData.append(

        "logo",

        file.files[0]

    );

    try{

        const response = await fetch(

            API +

            "/settings/logo",

            {

                method:"POST",

                body:formData

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Logo Updated"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                RESET SETTINGS
==========================================================*/

async function resetSettings(){

    if(

        !confirm(

            "Reset all settings?"

        )

    ) return;

    try{

        const response = await fetch(

            API +

            "/settings/reset",

            {

                method:"POST"

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Settings Reset"

            );

            loadSystemSettings();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                TEST EMAIL
==========================================================*/

async function sendTestEmail(){

    try{

        const response = await fetch(

            API +

            "/settings/test-email",

            {

                method:"POST"

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Test Email Sent"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeSettingsModule(){

    loadSystemSettings();

    document

        .getElementById(

            "saveSettings"

        )

        ?.addEventListener(

            "click",

            saveSystemSettings

        );

    document

        .getElementById(

            "uploadLogo"

        )

        ?.addEventListener(

            "click",

            uploadCafeLogo

        );

    document

        .getElementById(

            "resetSettings"

        )

        ?.addEventListener(

            "click",

            resetSettings

        );

    document

        .getElementById(

            "testEmail"

        )

        ?.addEventListener(

            "click",

            sendTestEmail

        );

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeSettingsModule();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 11-2
        SECURITY • USERS • ROLES • SESSIONS
==========================================================*/

let userAccounts = [];
let loginHistory = [];

/*==========================================================
                LOAD USERS
==========================================================*/

async function loadUserAccounts(){

    try{

        const response = await fetch(

            API + "/settings/users"

        );

        if(!response.ok){

            throw new Error();

        }

        userAccounts = await response.json();

        renderUserAccounts();

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                USERS TABLE
==========================================================*/

function renderUserAccounts(){

    const tbody = document.getElementById(

        "userAccountsTable"

    );

    if(!tbody) return;

    tbody.innerHTML="";

    userAccounts.forEach(user=>{

        tbody.innerHTML += `

        <tr>

            <td>${user.username}</td>

            <td>${user.role}</td>

            <td>${user.status}</td>

            <td>${user.last_login || "-"}</td>

            <td>

                <button
                onclick="editUserRole(${user.id})">

                    Role

                </button>

            </td>

        </tr>

        `;

    });

}

/*==========================================================
                CHANGE PASSWORD
==========================================================*/

async function changePassword(){

    const oldPassword =

        document.getElementById(

            "oldPassword"

        ).value;

    const newPassword =

        document.getElementById(

            "newPassword"

        ).value;

    const confirmPassword =

        document.getElementById(

            "confirmPassword"

        ).value;

    if(newPassword !== confirmPassword){

        showToast(

            "Passwords do not match",

            "error"

        );

        return;

    }

    try{

        const response = await fetch(

            API +

            "/settings/change-password",

            {

                method:"POST",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify({

                    old_password:oldPassword,

                    new_password:newPassword

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Password Updated"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                UPDATE ROLE
==========================================================*/

async function editUserRole(id){

    const role = prompt(

        "New Role"

    );

    if(!role) return;

    try{

        const response = await fetch(

            API +

            "/settings/user-role/" +

            id,

            {

                method:"PUT",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify({

                    role

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Role Updated"

            );

            loadUserAccounts();

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                ENABLE 2FA
==========================================================*/

async function toggleTwoFactor(){

    const enabled =

        document.getElementById(

            "enable2FA"

        ).checked;

    try{

        const response = await fetch(

            API +

            "/settings/two-factor",

            {

                method:"PUT",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify({

                    enabled

                })

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                enabled ?

                "2FA Enabled"

                :

                "2FA Disabled"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                LOGIN HISTORY
==========================================================*/

async function loadLoginHistory(){

    try{

        const response = await fetch(

            API +

            "/settings/login-history"

        );

        loginHistory = await response.json();

        renderLoginHistory();

    }

    catch(error){

        console.error(error);

    }

}

function renderLoginHistory(){

    const tbody =

        document.getElementById(

            "loginHistoryTable"

        );

    if(!tbody) return;

    tbody.innerHTML="";

    loginHistory.forEach(log=>{

        tbody.innerHTML += `

        <tr>

            <td>${log.user}</td>

            <td>${log.time}</td>

            <td>${log.ip}</td>

            <td>${log.device}</td>

            <td>${log.status}</td>

        </tr>

        `;

    });

}

/*==========================================================
                LOGOUT ALL DEVICES
==========================================================*/

async function logoutAllSessions(){

    if(!confirm(

        "Logout all devices?"

    )) return;

    try{

        const response = await fetch(

            API +

            "/settings/logout-all",

            {

                method:"POST"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "All Sessions Closed"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeSecuritySettings(){

    loadUserAccounts();

    loadLoginHistory();

    document

        .getElementById(

            "changePasswordBtn"

        )

        ?.addEventListener(

            "click",

            changePassword

        );

    document

        .getElementById(

            "enable2FA"

        )

        ?.addEventListener(

            "change",

            toggleTwoFactor

        );

    document

        .getElementById(

            "logoutAllSessions"

        )

        ?.addEventListener(

            "click",

            logoutAllSessions

        );

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeSecuritySettings();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 11-3
 BACKUP • RESTORE • EMAIL • PRINTER • NOTIFICATIONS
==========================================================*/

let notificationSettings = {};

/*==========================================================
                DATABASE BACKUP
==========================================================*/

async function backupDatabase(){

    try{

        const response = await fetch(

            API + "/settings/backup",

            {

                method:"POST"

            }

        );

        const result = await response.json();

        if(result.success){

            showToast(

                "Database Backup Created"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                RESTORE DATABASE
==========================================================*/

async function restoreDatabase(){

    const input =

        document.getElementById(

            "restoreDatabaseFile"

        );

    if(

        !input ||

        input.files.length===0

    ) return;

    if(

        !confirm(

            "Restore database backup?"

        )

    ) return;

    const formData =

        new FormData();

    formData.append(

        "backup",

        input.files[0]

    );

    try{

        const response = await fetch(

            API +

            "/settings/restore",

            {

                method:"POST",

                body:formData

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Database Restored"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                CLOUD SYNC
==========================================================*/

async function synchronizeCloud(){

    try{

        const response = await fetch(

            API +

            "/settings/cloud-sync",

            {

                method:"POST"

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Cloud Sync Complete"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                EMAIL SETTINGS
==========================================================*/

async function saveEmailSettings(){

    const data={

        smtp_server:

            document.getElementById(

                "smtpServer"

            ).value,

        smtp_port:

            document.getElementById(

                "smtpPort"

            ).value,

        sender_email:

            document.getElementById(

                "senderEmail"

            ).value,

        sender_password:

            document.getElementById(

                "senderPassword"

            ).value

    };

    try{

        const response = await fetch(

            API +

            "/settings/email",

            {

                method:"PUT",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify(data)

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Email Settings Saved"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                PRINTER SETTINGS
==========================================================*/

async function savePrinterSettings(){

    const printer =

        document.getElementById(

            "printerName"

        ).value;

    const paper =

        document.getElementById(

            "paperSize"

        ).value;

    try{

        const response = await fetch(

            API +

            "/settings/printer",

            {

                method:"PUT",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify({

                    printer,

                    paper

                })

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Printer Saved"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                INVOICE SETTINGS
==========================================================*/

async function saveInvoiceSettings(){

    const invoice={

        footer:

            document.getElementById(

                "invoiceFooter"

            ).value,

        prefix:

            document.getElementById(

                "invoicePrefix"

            ).value,

        show_logo:

            document.getElementById(

                "showInvoiceLogo"

            ).checked

    };

    try{

        const response = await fetch(

            API +

            "/settings/invoice",

            {

                method:"PUT",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify(invoice)

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Invoice Updated"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                NOTIFICATION SETTINGS
==========================================================*/

async function saveNotificationSettings(){

    notificationSettings={

        email:

            document.getElementById(

                "emailNotifications"

            ).checked,

        sms:

            document.getElementById(

                "smsNotifications"

            ).checked,

        desktop:

            document.getElementById(

                "desktopNotifications"

            ).checked,

        low_stock:

            document.getElementById(

                "lowStockAlert"

            ).checked

    };

    try{

        const response = await fetch(

            API +

            "/settings/notifications",

            {

                method:"PUT",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify(

                    notificationSettings

                )

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Notification Settings Saved"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeAdvancedSettings(){

    document

        .getElementById(

            "backupDatabase"

        )

        ?.addEventListener(

            "click",

            backupDatabase

        );

    document

        .getElementById(

            "restoreDatabase"

        )

        ?.addEventListener(

            "click",

            restoreDatabase

        );

    document

        .getElementById(

            "cloudSync"

        )

        ?.addEventListener(

            "click",

            synchronizeCloud

        );

    document

        .getElementById(

            "saveEmailSettings"

        )

        ?.addEventListener(

            "click",

            saveEmailSettings

        );

    document

        .getElementById(

            "savePrinterSettings"

        )

        ?.addEventListener(

            "click",

            savePrinterSettings

        );

    document

        .getElementById(

            "saveInvoiceSettings"

        )

        ?.addEventListener(

            "click",

            saveInvoiceSettings

        );

    document

        .getElementById(

            "saveNotificationSettings"

        )

        ?.addEventListener(

            "click",

            saveNotificationSettings

        );

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeAdvancedSettings();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 11-4
 API SETTINGS • SYSTEM MAINTENANCE • AUDIT • LICENSE
==========================================================*/

/*==========================================================
                SAVE API SETTINGS
==========================================================*/

async function saveAPISettings(){

    const data={

        swiggy_key:

            document.getElementById(

                "swiggyApiKey"

            ).value,

        zomato_key:

            document.getElementById(

                "zomatoApiKey"

            ).value,

        razorpay_key:

            document.getElementById(

                "razorpayKey"

            ).value,

        stripe_key:

            document.getElementById(

                "stripeKey"

            ).value

    };

    try{

        const response = await fetch(

            API +

            "/settings/api",

            {

                method:"PUT",

                headers:{

                    "Content-Type":

                    "application/json"

                },

                body:JSON.stringify(data)

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "API Settings Saved"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                SYSTEM UPDATE
==========================================================*/

async function checkSystemUpdate(){

    try{

        const response = await fetch(

            API +

            "/settings/check-update"

        );

        const result =

            await response.json();

        showToast(

            result.message ||

            "System is Up To Date"

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                CLEAR CACHE
==========================================================*/

async function clearSystemCache(){

    if(

        !confirm(

            "Clear application cache?"

        )

    ) return;

    try{

        const response = await fetch(

            API +

            "/settings/clear-cache",

            {

                method:"POST"

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Cache Cleared"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                STORAGE INFO
==========================================================*/

async function loadStorageInformation(){

    try{

        const response = await fetch(

            API +

            "/settings/storage"

        );

        const storage =

            await response.json();

        setText(

            "diskUsage",

            storage.disk_usage

        );

        setText(

            "databaseSize",

            storage.database_size

        );

        setText(

            "backupSize",

            storage.backup_size

        );

        setText(

            "freeSpace",

            storage.free_space

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                AUDIT LOGS
==========================================================*/

async function loadAuditLogs(){

    try{

        const response = await fetch(

            API +

            "/settings/audit"

        );

        const logs =

            await response.json();

        const tbody =

            document.getElementById(

                "auditLogTable"

            );

        if(!tbody) return;

        tbody.innerHTML="";

        logs.forEach(log=>{

            tbody.innerHTML += `

            <tr>

                <td>${log.time}</td>

                <td>${log.user}</td>

                <td>${log.action}</td>

                <td>${log.ip}</td>

            </tr>

            `;

        });

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                LICENSE
==========================================================*/

async function loadLicense(){

    try{

        const response = await fetch(

            API +

            "/settings/license"

        );

        const license =

            await response.json();

        setText(

            "licenseKey",

            license.key

        );

        setText(

            "licenseExpiry",

            license.expiry

        );

        setText(

            "licenseStatus",

            license.status

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                ABOUT
==========================================================*/

async function loadAboutCafeSync(){

    try{

        const response = await fetch(

            API +

            "/settings/about"

        );

        const about =

            await response.json();

        setText(

            "appVersion",

            about.version

        );

        setText(

            "buildNumber",

            about.build

        );

        setText(

            "developerName",

            about.developer

        );

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                FACTORY RESET
==========================================================*/

async function factoryReset(){

    if(

        !confirm(

            "Factory Reset? This cannot be undone."

        )

    ) return;

    try{

        const response = await fetch(

            API +

            "/settings/factory-reset",

            {

                method:"POST"

            }

        );

        const result =

            await response.json();

        if(result.success){

            showToast(

                "Factory Reset Completed"

            );

        }

    }

    catch(error){

        console.error(error);

    }

}

/*==========================================================
                INITIALIZE
==========================================================*/

function initializeMaintenanceModule(){

    loadStorageInformation();

    loadAuditLogs();

    loadLicense();

    loadAboutCafeSync();

    document

        .getElementById(

            "saveAPISettings"

        )

        ?.addEventListener(

            "click",

            saveAPISettings

        );

    document

        .getElementById(

            "checkUpdate"

        )

        ?.addEventListener(

            "click",

            checkSystemUpdate

        );

    document

        .getElementById(

            "clearCache"

        )

        ?.addEventListener(

            "click",

            clearSystemCache

        );

    document

        .getElementById(

            "factoryReset"

        )

        ?.addEventListener(

            "click",

            factoryReset

        );

}

/*==========================================================

ADD INSIDE initializeDashboard()

initializeMaintenanceModule();

==========================================================*/
/*==========================================================
                CafeSync Dashboard
                dashboard.js
                PART 12
        FINAL UTILITIES & APPLICATION BOOTSTRAP
==========================================================*/

/*==========================================================
                GLOBAL VARIABLES
==========================================================*/

const REFRESH_INTERVAL = 60000;

let autoRefreshTimer = null;

/*==========================================================
                TOAST NOTIFICATION
==========================================================*/

function showToast(

    message,

    type="success"

){

    const toast =

        document.createElement(

            "div"

        );

    toast.className =

        "toast " + type;

    toast.innerText =

        message;

    document.body.appendChild(

        toast

    );

    setTimeout(()=>{

        toast.classList.add(

            "show"

        );

    },100);

    setTimeout(()=>{

        toast.remove();

    },3500);

}

/*==========================================================
                TEXT HELPER
==========================================================*/

function setText(id,value){

    const element =

        document.getElementById(id);

    if(element){

        element.textContent = value;

    }

}

/*==========================================================
                DATE FORMAT
==========================================================*/

function formatDate(date){

    if(!date) return "-";

    return new Date(date)

        .toLocaleDateString();

}

/*==========================================================
                CURRENCY FORMAT
==========================================================*/

function formatCurrency(value){

    return Number(value || 0)

        .toLocaleString(

            "en-IN",

            {

                style:"currency",

                currency:"INR"

            }

        );

}

/*==========================================================
                LOADING
==========================================================*/

function showLoader(){

    document
        .getElementById("loadingScreen")
        ?.classList.add("active");

}


function hideLoader(){

    console.log("HIDING LOADER");

    const loader =
        document.getElementById("loadingScreen");

    console.log("Loader element:", loader);

    if(loader){

        loader.classList.remove("active");

        loader.style.display = "none";

    }

}

/*==========================================================
                THEME
==========================================================*/

function toggleTheme(){

    document.body.classList.toggle(

        "dark"

    );

    localStorage.setItem(

        "theme",

        document.body.classList.contains(

            "dark"

        )

    );

}

function loadTheme(){

    if(

        localStorage.getItem(

            "theme"

        )==="true"

    ){

        document.body.classList.add(

            "dark"

        );

    }

}

function initializeSalesModule(){

    console.log("Sales module initialized");

}

/*==========================================================
                AUTO REFRESH
==========================================================*/

function startAutoRefresh(){

    autoRefreshTimer =

        setInterval(()=>{

            loadDashboard();

        },REFRESH_INTERVAL);

}

function stopAutoRefresh(){

    clearInterval(

        autoRefreshTimer

    );

}

/*==========================================================
                ONLINE / OFFLINE
==========================================================*/

window.addEventListener(

    "offline",

    ()=>{

        showToast(

            "Offline",

            "error"

        );

    }

);

window.addEventListener(

    "online",

    ()=>{

        showToast(

            "Back Online"

        );

    }

);

/*==========================================================
                SHORTCUTS
==========================================================*/

document.addEventListener(

    "keydown",

    function(e){

        if(e.ctrlKey && e.key==="b"){

            e.preventDefault();

            window.location="/billing";

        }

        if(e.ctrlKey && e.key==="d"){

            e.preventDefault();

            window.location="/dashboard";

        }

        if(e.ctrlKey && e.key==="i"){

            e.preventDefault();

            window.location="/inventory";

        }

    }

);

/*==========================================================
                GLOBAL ERROR
==========================================================*/

window.onerror=function(

    message,

    source,

    line

){

    console.error(

        message,

        source,

        line

    );

    showToast(

        "Unexpected Error",

        "error"

    );

};

function initializeNavigation(){

    const links = document.querySelectorAll(
        ".sidebar a"
    );

    links.forEach(link => {

        link.addEventListener("click", function(){

            console.log(
                "Navigating:",
                this.href
            );

        });

    });

}

function updateDashboard(data){

    if(!data){
        return;
    }


    const products =
        document.getElementById("totalProducts");


    const categories =
        document.getElementById("totalCategories");


    const orders =
        document.getElementById("totalOrders");


    const revenue =
        document.getElementById("totalRevenue");


    if(products)
        products.textContent =
        data.total_products || 0;


    if(categories)
        categories.textContent =
        data.total_categories || 0;


    if(orders)
        orders.textContent =
        data.total_orders || 0;


    if(revenue)
        revenue.textContent =
        "₹ " + (data.revenue || 0);

}

async function loadDashboard(){

    try{

        const response = await fetch(
            "/dashboard/data"
        );


        if(!response.ok){

            throw new Error(
                "Dashboard API failed"
            );

        }


        const result =
            await response.json();


        console.log(
            "Dashboard Data:",
            result
        );


        updateDashboard(
            result.data
        );


    }
    catch(error){

        console.error(
            "Dashboard Error:",
            error
        );

    }

}


/*==========================================================
                DASHBOARD LOADER
==========================================================*/

async function loadDashboard(){

    try {

        showLoader();

        const response = await fetch("/dashboard/data");

        const data = await response.json();

        updateDashboard(data);

    }
    catch(error){

        console.error("Dashboard Error:", error);

    }
    finally {

        hideLoader();

    }

}

async function initializeDashboard(){

    try{

        loadTheme();

        initializeSidebar();

        initializeChartsModule();

        initializeSalesModule();

        await loadDashboard();

        startAutoRefresh();

        showToast("CafeSync Ready");

    }
    catch(error){

        console.error(
            "Dashboard initialization failed:",
            error
        );

    }
    finally{

        hideLoader();

    }

}


/*==========================================================
                START
==========================================================*/

document.addEventListener("DOMContentLoaded", function(){

    initializeDashboard();

});

/*==========================================================
                END OF FILE
==========================================================*/