/*==========================================================
                CafeSync POS
                billing.js
                PART 1
==========================================================*/

//==========================================================
// API
//==========================================================

// Use same-origin URLs so POS works both locally and when deployed.
const API = "";

//==========================================================
// GLOBAL VARIABLES
//==========================================================

let products = [];

let categories = [];

let cart = [];

let selectedCategory = "All";

let paymentMethod = "Cash";

let gstPercentage = 5;
let defaultDiscountPercentage = 0;
let maximumDiscountPercentage = 30;
let allowManualDiscount = false;
let showGSTOnReceipt = true;

let currentOrder = null;

let selectedOrderType = "Dine In";

let pendingAddonProduct = null;
let pendingProductAddons = [];
let heldOrdersCache = [];

//==========================================================
// DOM ELEMENTS
//==========================================================

const productGrid = document.getElementById("productGrid");

const categoryList = document.getElementById("categoryList");

const cartItems = document.getElementById("cartItems");

const searchInput = document.getElementById("searchProduct");

const menuBtn = document.getElementById("menuBtn");

const sidebar = document.getElementById("sidebar");

const themeBtn = document.getElementById("themeBtn");

const clock = document.getElementById("clock");

//==========================================================
// PAGE LOAD
//==========================================================

document.addEventListener("DOMContentLoaded", () => {

    initializePOS();

});

//==========================================================
// INITIALIZE
//==========================================================

async function initializePOS(){

    startClock();

    initializeSidebar();

    initializeTheme();

    await loadBillingPreferences();

    await loadCategories();

    await loadProducts();

    await loadTables();

    initializeOrderType();

    updateTotals();

}

async function loadBillingPreferences(){
    try{
        const response = await fetch(`${API}/settings/billing-preferences`, {credentials: "same-origin"});
        if(!response.ok) return;
        const result = await response.json();
        if(!result.success) return;
        const preferences = result.settings;
        gstPercentage = Number(preferences.tax_percentage ?? 5);
        defaultDiscountPercentage = Number(preferences.default_discount ?? 0);
        maximumDiscountPercentage = Number(preferences.maximum_discount ?? 30);
        allowManualDiscount = Boolean(preferences.allow_manual_discount);
        showGSTOnReceipt = Boolean(preferences.show_gst_on_receipt);
        const gstLabel = document.querySelector(".bill-summary .summary-row:nth-child(2) span:first-child");
        if(gstLabel) gstLabel.textContent = `GST (${gstPercentage}%)`;
        const input = document.getElementById("discount");
        if(input){
            input.value = defaultDiscountPercentage;
            input.max = allowManualDiscount ? maximumDiscountPercentage : defaultDiscountPercentage;
            input.disabled = !allowManualDiscount;
            input.setAttribute("aria-label", "Discount percentage");
        }
    }catch(error){ console.warn("Billing settings could not be loaded", error); }
}

function getDiscountAmount(subtotal){
    const input = document.getElementById("discount");
    let percentage = Number(input?.value ?? defaultDiscountPercentage);
    if(!allowManualDiscount) percentage = defaultDiscountPercentage;
    percentage = Math.max(0, Math.min(percentage, maximumDiscountPercentage));
    if(input && allowManualDiscount && Number(input.value) !== percentage) input.value = percentage;
    return subtotal * percentage / 100;
}

async function loadTables(){

    const selector = document.getElementById("tableNo");

    if(!selector) return;

    try{

        const response = await fetch(`${API}/tables`);

        if(!response.ok) return;

        const tables = await response.json();

        if(!Array.isArray(tables) || tables.length === 0) return;

        selector.innerHTML = '<option value="">Choose a table</option>';

        tables.forEach(table => {

            const option = document.createElement("option");
            option.value = table.id;
            option.textContent = `${table.table_name}${table.status && table.status !== "Available" ? ` · ${table.status}` : ""}`;
            option.disabled = table.status && table.status !== "Available";
            selector.appendChild(option);

        });

    }catch(error){
        console.warn("Table list unavailable", error);
    }

}

function initializeOrderType(){

    const buttons = document.querySelectorAll(".order-type-btn");
    const selector = document.getElementById("tableNo");
    const tableField = selector?.parentElement;

    buttons.forEach(button => button.addEventListener("click", () => {

        selectedOrderType = button.dataset.orderType || "Dine In";
        buttons.forEach(item => item.classList.toggle("active", item === button));

        if(tableField){
            tableField.classList.toggle("table-hidden", selectedOrderType !== "Dine In");
        }

        if(selectedOrderType !== "Dine In" && selector) selector.value = "";

    }));

}

//==========================================================
// LIVE CLOCK
//==========================================================

function startClock(){

    updateClock();

    setInterval(updateClock,1000);

}

function updateClock(){

    const now = new Date();

    clock.innerHTML = now.toLocaleTimeString();

}

//==========================================================
// SIDEBAR
//==========================================================

function initializeSidebar(){

    menuBtn.addEventListener("click",()=>{

        sidebar.classList.toggle("hide");

        document.querySelector(".main").classList.toggle("full");

    });

}

//==========================================================
// DARK MODE
//==========================================================

function initializeTheme(){

    const savedTheme = localStorage.getItem("theme");

    if(savedTheme==="dark"){

        document.body.classList.add("dark");

    }

    themeBtn.addEventListener("click",()=>{

        document.body.classList.toggle("dark");

        if(document.body.classList.contains("dark")){

            localStorage.setItem("theme","dark");

        }

        else{

            localStorage.setItem("theme","light");

        }

    });

}

//==========================================================
// LOAD CATEGORIES
//==========================================================

async function loadCategories(){

    try{

        const response = await fetch(
            `${API}/inventory/categories`
        );

        if(!response.ok){

            throw new Error(
                "Failed to load categories"
            );

        }

        const result = await response.json();

        console.log(
            "Categories API response:",
            result
        );

        // IMPORTANT:
        // Backend sends the array inside result.data

        categories = result.data || [];

        renderCategories();

    }

    catch(error){

        console.error(
            "Category loading error:",
            error
        );

        categories = [];

        showToast(
            "Unable to load categories",
            "error"
        );

    }

}

//==========================================================
// LOAD PRODUCTS
//==========================================================

async function loadProducts(){

    try{

        showLoader();

        const response = await fetch(
            `${API}/inventory/products`
        );

        if(!response.ok){

            throw new Error(
                "Failed to load products"
            );

        }

        const result = await response.json();

        console.log(
            "Products API response:",
            result
        );

        // IMPORTANT:
        // Backend sends products inside result.data

        products = result.data || [];

        hideLoader();

        renderProducts(products);

    }

    catch(error){

        hideLoader();

        console.error(
            "Product loading error:",
            error
        );

        products = [];

        showToast(
            "Unable to load products",
            "error"
        );

    }

}

//==========================================================
// LOADER
//==========================================================

function showLoader(){

    productGrid.innerHTML=`

        <div class="loader"></div>

    `;

}

function hideLoader(){

}

//==========================================================
// TOAST
//==========================================================

function showToast(message,type="success"){

    const toast=document.createElement("div");

    toast.className=`toast ${type}`;

    toast.innerHTML=message;

    document.body.appendChild(toast);

    setTimeout(()=>{

        toast.remove();

    },3000);

}
/*==========================================================
                CafeSync POS
                billing.js
                PART 2
        PRODUCTS & CATEGORIES
==========================================================*/

//==========================================================
// RENDER CATEGORIES
//==========================================================

function renderCategories() {

    categoryList.innerHTML = "";

    //======================================================
    // ALL CATEGORY
    //======================================================

    const allBtn = document.createElement("button");

    allBtn.className = "category active";

    allBtn.innerHTML = "🍽️ All";

    allBtn.onclick = () => {

        document.querySelectorAll(".category")
            .forEach(btn => btn.classList.remove("active"));

        allBtn.classList.add("active");

        selectedCategory = "All";

        renderProducts(products);

    };

    categoryList.appendChild(allBtn);


    //======================================================
    // DATABASE CATEGORIES
    //======================================================

    categories.forEach(category => {

        const btn = document.createElement("button");

        btn.className = "category";

        btn.innerHTML = category.name;

        btn.onclick = () => {

            document.querySelectorAll(".category")
                .forEach(item =>
                    item.classList.remove("active")
                );

            btn.classList.add("active");

            selectedCategory = category.name;

            console.log(
                "Selected Category:",
                category.name
            );

            console.log(
                "Category ID:",
                category.id
            );


            //==================================================
            // FILTER USING CATEGORY ID
            //==================================================

            const filtered = products.filter(product => {

                return Number(product.category_id) ===
                       Number(category.id);

            });


            console.log(
                "Filtered Products:",
                filtered
            );


            renderProducts(filtered);

        };

        categoryList.appendChild(btn);

    });

}

//==========================================================
// RENDER PRODUCTS
//==========================================================

function renderProducts(productList){

    productList = productList.filter(product => Number(product.is_available ?? 1) === 1);

    productGrid.innerHTML="";

    if(productList.length===0){

        productGrid.innerHTML=`

            <div class="empty-products">

                <i class="fas fa-box-open"></i>

                <h3>No Products Found</h3>

                <p>Add products from Inventory.</p>

            </div>

        `;

        return;

    }

    productList.forEach(product=>{

        const card=document.createElement("div");

        card.className="product-card";

        card.innerHTML=`

            <div class="product-image">

                <img src="/static/images/products/${product.image || 'default.png'}">

            </div>

            <div class="product-body">

                <div class="product-name">

                    ${product.name}

                </div>

                <div class="product-category">

                    ${product.category_name || product.category || ""}

                </div>

                <div class="product-price">

                    ₹${Number(product.price).toFixed(2)}

                </div>

                <button
                    class="add-btn">

                    <i class="fas fa-cart-plus"></i>

                    Add

                </button>

            </div>

        `;

        card.querySelector(".add-btn")
            .addEventListener("click",(e)=>{

                e.stopPropagation();

                selectProductAddons(product);

            });

        productGrid.appendChild(card);

    });

}

//==========================================================
// SEARCH PRODUCTS
//==========================================================

searchInput.addEventListener("keyup",function(){

    const keyword=this.value.toLowerCase();

    const filtered=products.filter(product=>{

        return(

            product.name.toLowerCase().includes(keyword)

            ||

            (product.category_name || "")
                .toLowerCase()
                .includes(keyword)

        );

    });

    renderProducts(filtered);

});

//==========================================================
// ADD TO CART
//==========================================================

async function selectProductAddons(product){
    try {
        const response = await fetch(`${API}/inventory/products/${product.id}/addons`, {credentials:"same-origin"});
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error(result.message || "Could not load item add-ons");
        const addons = result.data || [];
        if (!addons.length) {
            addToCart(product, []);
            return;
        }
        pendingAddonProduct = product;
        pendingProductAddons = addons;
        document.getElementById("addonPickerTitle").textContent = product.name;
        document.getElementById("addonPickerBasePrice").textContent = `Base price · ₹${Number(product.price).toFixed(2)}`;
        const list = document.getElementById("addonChoices");
        list.replaceChildren();
        addons.forEach(addon => {
            const label = document.createElement("label");
            label.className = "addon-choice";
            const check = document.createElement("input");
            check.type = "checkbox";
            check.value = addon.id;
            check.addEventListener("change", updateAddonPickerTotal);
            const name = document.createElement("span");
            name.textContent = addon.name;
            const price = document.createElement("b");
            price.textContent = `+₹${Number(addon.price).toFixed(2)}`;
            label.append(check, name, price);
            list.appendChild(label);
        });
        updateAddonPickerTotal();
        document.getElementById("addonPickerModal").classList.add("active");
        document.getElementById("addonPickerModal").setAttribute("aria-hidden", "false");
    } catch (error) {
        showToast(error.message || "Could not load item add-ons", "error");
    }
}

function updateAddonPickerTotal(){
    const selectedIds = new Set([...document.querySelectorAll("#addonChoices input:checked")].map(input => Number(input.value)));
    const extra = pendingProductAddons.filter(addon => selectedIds.has(Number(addon.id))).reduce((sum, addon) => sum + Number(addon.price), 0);
    document.getElementById("addonPickerTotal").textContent = `Item total · ₹${(Number(pendingAddonProduct?.price || 0) + extra).toFixed(2)}`;
}

function closeAddonPicker(){
    document.getElementById("addonPickerModal").classList.remove("active");
    document.getElementById("addonPickerModal").setAttribute("aria-hidden", "true");
    pendingAddonProduct = null;
    pendingProductAddons = [];
}

document.getElementById("closeAddonPicker")?.addEventListener("click", closeAddonPicker);
document.getElementById("confirmAddons")?.addEventListener("click", () => {
    if (!pendingAddonProduct) return;
    const selectedIds = new Set([...document.querySelectorAll("#addonChoices input:checked")].map(input => Number(input.value)));
    const selected = pendingProductAddons.filter(addon => selectedIds.has(Number(addon.id)));
    const product = pendingAddonProduct;
    closeAddonPicker();
    addToCart(product, selected);
});

function cartLineKey(item){
    return item.line_key || `${item.id}:base`;
}

function addToCart(product, selectedAddons=[]){

    const addonIds = selectedAddons.map(addon => Number(addon.id)).sort((a,b) => a-b);
    const lineKey = `${product.id}:${addonIds.length ? addonIds.join(".") : "base"}`;
    const existing=cart.find(item=>cartLineKey(item)===lineKey);

    if(existing){

        existing.quantity++;

    }

    else{

        cart.push({

            id:product.id,

            line_key:lineKey,

            name:product.name,

            base_price:Number(product.price),

            price:Number(product.price) + selectedAddons.reduce((sum, addon) => sum + Number(addon.price), 0),

            addons:selectedAddons.map(addon => ({id:Number(addon.id), name:addon.name, price:Number(addon.price)})),

            image:product.image,

            chef_note:"",

            quantity:1

        });

    }

    renderCart();

    updateTotals();

    showToast(product.name+" added");

}
/*==========================================================
                CafeSync POS
                billing.js
                PART 3
                CART FUNCTIONS
==========================================================*/

//==========================================================
// RENDER CART
//==========================================================

function renderCart() {

    cartItems.innerHTML = "";

    if (cart.length === 0) {

        cartItems.innerHTML = `

            <div class="empty-cart">

                <i class="fas fa-shopping-cart"></i>

                <h3>Cart is Empty</h3>

                <p>Add products to start billing</p>

            </div>

        `;

        return;

    }

    cart.forEach(item => {

        const cartCard = document.createElement("div");

        cartCard.className = "cart-item";

        cartCard.innerHTML = `

            <div class="cart-left">

                <img
                    class="cart-image"
                    src="/static/images/products/${item.image || 'default.png'}">

                <div class="cart-info">

                    <div class="cart-name">

                        ${item.name}

                    </div>

                    <div class="cart-price">

                        ₹${item.price.toFixed(2)}

                    </div>

                    <div class="cart-addons"></div>

                    <button type="button" class="customize-toggle">Add kitchen note</button>
                    <textarea class="item-note" maxlength="180" placeholder="e.g. no sugar, oat milk" hidden></textarea>

                </div>

            </div>

            <div class="cart-right">

                <div class="quantity">

                    <button
                        onclick="decreaseQuantity('${cartLineKey(item)}')">

                        -

                    </button>

                    <span>

                        ${item.quantity}

                    </span>

                    <button
                        onclick="increaseQuantity('${cartLineKey(item)}')">

                        +

                    </button>

                </div>

                <div
                    style="
                    margin-top:8px;
                    text-align:right;
                    font-weight:600;">

                    ₹${(item.price * item.quantity).toFixed(2)}

                </div>

                <button
                    class="remove-item"
                    onclick="removeItem('${cartLineKey(item)}')">

                    <i class="fas fa-trash"></i>

                </button>

            </div>

        `;

        const noteInput = cartCard.querySelector(".item-note");
        const noteToggle = cartCard.querySelector(".customize-toggle");
        const addonSummary = cartCard.querySelector(".cart-addons");
        addonSummary.textContent = (item.addons || []).map(addon => addon.name).join(", ");
        addonSummary.hidden = !(item.addons || []).length;
        noteInput.value = item.chef_note || "";
        noteToggle.textContent = item.chef_note ? "Edit kitchen note" : "Add kitchen note";
        noteToggle.addEventListener("click", () => {
            noteInput.hidden = !noteInput.hidden;
            if (!noteInput.hidden) noteInput.focus();
        });
        noteInput.addEventListener("input", () => {
            item.chef_note = noteInput.value.trim();
            noteToggle.textContent = item.chef_note ? "Edit kitchen note" : "Add kitchen note";
        });

        cartItems.appendChild(cartCard);

    });

}

//==========================================================
// INCREASE QUANTITY
//==========================================================

function increaseQuantity(id){

    const item = cart.find(p => cartLineKey(p) === String(id));

    if(!item) return;

    item.quantity++;

    renderCart();

    updateTotals();

}

//==========================================================
// DECREASE QUANTITY
//==========================================================

function decreaseQuantity(id){

    const item = cart.find(p => cartLineKey(p) === String(id));

    if(!item) return;

    item.quantity--;

    if(item.quantity <= 0){

        cart = cart.filter(p => cartLineKey(p) !== String(id));

    }

    renderCart();

    updateTotals();

}

//==========================================================
// REMOVE ITEM
//==========================================================

function removeItem(id){

    cart = cart.filter(item => cartLineKey(item) !== String(id));

    renderCart();

    updateTotals();

    showToast("Item Removed","warning");

}

//==========================================================
// CLEAR CART
//==========================================================

const clearBtn = document.getElementById("clearCart");

if(clearBtn){

    clearBtn.addEventListener("click",()=>{

        if(cart.length===0){

            showToast("Cart already empty","warning");

            return;

        }

        if(confirm("Clear current order?")){

            cart=[];

            renderCart();

            updateTotals();

            showToast("Cart Cleared");

        }

    });

}

//==========================================================
// CART ITEM COUNT
//==========================================================

function getTotalItems(){

    let total = 0;

    cart.forEach(item=>{

        total += item.quantity;

    });

    return total;

}

//==========================================================
// FIND PRODUCT
//==========================================================

function getCartItem(id){

    return cart.find(item=>item.id===id);

}

//==========================================================
// CHECK CART
//==========================================================

function isCartEmpty(){

    return cart.length===0;

}
/*==========================================================
                CafeSync POS
                billing.js
                PART 4
          TOTALS • PAYMENT • CHECKOUT
==========================================================*/

//==========================================================
// UPDATE TOTALS
//==========================================================

function updateTotals() {

    let subtotal = 0;

    cart.forEach(item => {

        subtotal += item.price * item.quantity;

    });

    const discountInput = document.getElementById("discount");

    const discount = getDiscountAmount(subtotal);

    const gst =
        subtotal * gstPercentage / 100;

    const grandTotal =
        subtotal + gst - discount;

    document.getElementById("subtotal").innerHTML =
        "₹" + subtotal.toFixed(2);

    const discountAmountElement = document.getElementById("discountAmount");
    if(discountAmountElement) discountAmountElement.textContent = "₹" + discount.toFixed(2);

    document.getElementById("gstAmount").innerHTML =
        "₹" + gst.toFixed(2);

    document.getElementById("grandTotal").innerHTML =
        "₹" + grandTotal.toFixed(2);

}

//==========================================================
// DISCOUNT
//==========================================================

const discountBox =
document.getElementById("discount");

if(discountBox){

    discountBox.addEventListener("input",()=>{

        updateTotals();

    });

}

//==========================================================
// PAYMENT BUTTONS
//==========================================================

document
.querySelectorAll(".payment-btn[data-payment]")
.forEach(btn=>{

    btn.addEventListener("click",()=>{

        document
        .querySelectorAll(".payment-btn")
        .forEach(b=>b.classList.remove("active"));

        btn.classList.add("active");

        paymentMethod =
        btn.dataset.payment;

        showToast(
            paymentMethod+" Selected"
        );

    });

});

//==========================================================
// CHECKOUT
//==========================================================

const checkoutBtn =
document.getElementById("checkoutBtn");

if(checkoutBtn){

checkoutBtn.addEventListener("click",checkout);

}

async function checkout(options={}){

    if(cart.length===0){

        showToast(
            "Cart is Empty",
            "error"
        );

        return;

    }

    const printWindow = options.printAfter ? window.open("", "_blank") : null;

    let subtotal=0;

    cart.forEach(item=>{

        subtotal+=
        item.price*item.quantity;

    });

    const discount=getDiscountAmount(subtotal);

    const gst=
    subtotal*gstPercentage/100;

    const total=
    subtotal+gst-discount;

    const payload={

        items:cart,

        subtotal:subtotal,

        gst:gst,

        discount:discount,

        total:total,

        payment_method:paymentMethod,

        table:
        document.getElementById("tableNo").value,

        table_id:
        document.getElementById("tableNo").value || null,

        order_type: selectedOrderType,

        customer:
        document.getElementById("customerName").value,

        customer_id: customerInput?.dataset.customerId || null,

        is_paid: options.splitOrder ? false : (document.getElementById("isPaid")?.checked || false),

        split_details: options.splitOrder?.details || null

    };

    try{

        const response=
        await fetch(

            API+"/billing/create-order",

            {

                method:"POST",

                headers:{

                    "Content-Type":"application/json"

                },

                body:JSON.stringify(payload)

            }

        );

        const data=
        await response.json();

        if(data.success){

            let splitPaymentSaved = true;
            if(options.splitOrder){
                try{
                    const paymentResponse = await fetch(`${API}/billing/split-payment/${data.order_id}`, {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        credentials: "same-origin",
                        body: JSON.stringify({shares: options.splitOrder.payments})
                    });
                    const paymentResult = await paymentResponse.json();
                    if(!paymentResponse.ok || !paymentResult.success) throw new Error(paymentResult.message || "Payment failed");
                }catch(paymentError){
                    splitPaymentSaved = false;
                    console.error("Split payments could not be recorded", paymentError);
                }
            }

            if(data.bill_no){
                document.getElementById("billNo").textContent = data.bill_no;
            }

            if(printWindow){
                printWindow.document.write(generateReceiptHTML());
                printWindow.document.close();
                printWindow.focus();
                printWindow.print();
            }

            const splitMessage = !options.splitOrder
                ? "Bill Saved Successfully"
                : !splitPaymentSaved
                    ? "Order saved, but split payments were not recorded. Check the order before retrying."
                    : options.splitOrder.payments.length
                        ? "Bill saved with split payments"
                        : "Split order saved as unpaid";
            showToast(splitMessage, splitPaymentSaved ? undefined : "error");

            cart=[];

            clearLocalData();

            renderCart();

            updateTotals();

        }

        else{

            if(printWindow) printWindow.close();

            showToast(

                data.message,

                "error"

            );

        }

    }

    catch(err){

        if(printWindow) printWindow.close();

        console.error(err);

        showToast(

            "Server Error",

            "error"

        );

    }

}

//==========================================================
// HOLD ORDER
//==========================================================

const holdBtn=
document.getElementById("holdOrder");

if(holdBtn){
    holdBtn.addEventListener("click", holdCurrentOrder);

}

document.getElementById("holdOrderBottom")?.addEventListener("click", holdCurrentOrder);

//==========================================================
// PRINT BILL
//==========================================================

const printBtn=
document.getElementById("printBtn");

//==========================================================
// KOT
//==========================================================
const kotBtn = document.getElementById("kotBtn");

if (kotBtn) {

    kotBtn.addEventListener("click", async () => {

        // ------------------------------------------
        // CHECK CART
        // ------------------------------------------

        if (cart.length === 0) {

            showToast(
                "Cart Empty",
                "warning"
            );

            return;
        }

        const kotPrintWindow = window.open("", "_blank");


        // ------------------------------------------
        // GET TABLE
        // ------------------------------------------

        const tableSelect =
            document.getElementById("tableNo");

        const tableId =
            tableSelect.value || null;


        // ------------------------------------------
        // GET CUSTOMER
        // ------------------------------------------

        const customerInput =
            document.getElementById("customerName");

        const customerName =
            customerInput
                ? customerInput.value
                : "";


        // ------------------------------------------
        // CREATE ORDER DATA
        // ------------------------------------------

        // ==========================================
	// CALCULATE ORDER TOTALS
	// ==========================================

	const subtotalValue = cart.reduce(
    	    (sum, item) =>
        	sum + (Number(item.price) * Number(item.quantity)),
    	    0
	);

	const gstValue = subtotalValue * gstPercentage / 100;

	const discountValue = getDiscountAmount(subtotalValue);

	const grandTotalValue =
    	    subtotalValue +
    	    gstValue -
    	    discountValue;


	// ==========================================
	// CREATE KOT DATA
	// ==========================================

	const data = {

            table_id: tableId,

            customer_name: customerName,

            customer_id: customerInput?.dataset.customerId || null,

	    order_type: selectedOrderType,

    	    subtotal: subtotalValue,

    	    gst: gstValue,

    	    discount: discountValue,

    	    total: grandTotalValue,

    	    payment_method: "Pending",

    	    items: cart.map(item => ({

        	product_id: item.id,

        	quantity: Number(item.quantity),

                price: Number(item.price),

                chef_note: item.chef_note || "",

                addons: (item.addons || []).map(addon => addon.id)

    	    }))

	};


        console.log(
            "🔥 SENDING KOT:",
            data
        );


        // ------------------------------------------
        // SEND TO FLASK
        // ------------------------------------------

        try {

            const response = await fetch(
                `${API}/billing/kot`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify(data)
                }
            );


            const result =
                await response.json();


            console.log(
                "🔥 KOT RESPONSE:",
                result
            );


            // ------------------------------------------
            // SUCCESS
            // ------------------------------------------

            if (result.success) {

                if(result.data?.bill_no){
                    document.getElementById("billNo").textContent = result.data.bill_no;
                }

                if(kotPrintWindow){
                    const ticket = generateReceiptHTML()
                        .replace("<title>Invoice</title>", "<title>Kitchen Ticket</title>")
                        .replace("<h2>CafeSync POS</h2>", "<h2>CafeSync Kitchen Ticket</h2>");
                    kotPrintWindow.document.write(ticket);
                    kotPrintWindow.document.close();
                    kotPrintWindow.focus();
                    kotPrintWindow.print();
                }

                showToast(
                    "Kitchen Order Sent",
                    "success"
                );

                console.log(
                    "Order ID:",
                    result.data.order_id
                );

                console.log(
                    "Bill No:",
                    result.data.bill_no
                );

                cart=[];
                clearLocalData();
                renderCart();
                updateTotals();

            }

            else {

                if(kotPrintWindow) kotPrintWindow.close();

                showToast(
                    result.message ||
                    "Unable to send order",
                    "error"
                );

            }

        }

        catch (error) {

            if(kotPrintWindow) kotPrintWindow.close();

            console.error(
                "🔥 KOT ERROR:",
                error
            );

            showToast(
                "Unable to send kitchen order",
                "error"
            );

        }

    });

}
//==========================================================
// BILL NUMBER
//==========================================================

function generateBillNo(){

    const now=new Date();

    const id=

    now.getFullYear()

    +

    String(

        now.getMonth()+1

    ).padStart(2,"0")

    +

    String(

        now.getDate()

    ).padStart(2,"0")

    +

    "-"

    +

    Math.floor(

        Math.random()*9000+1000

    );

    document
    .getElementById("billNo")
    .innerHTML=id;

}

generateBillNo();

//==========================================================
// DATE & TIME
//==========================================================

function updateBillDate(){

    const now=new Date();

    document
    .getElementById("billDate")
    .innerHTML=

    now.toLocaleDateString();

    document
    .getElementById("billTime")
    .innerHTML=

    now.toLocaleTimeString();

}

updateBillDate();

setInterval(updateBillDate,1000);
/*==========================================================
                CafeSync POS
                billing.js
                PART 5A
        BARCODE • SHORTCUTS • SEARCH
==========================================================*/

//==========================================================
// AUTO FOCUS SEARCH
//==========================================================

window.addEventListener("load",()=>{

    if(searchInput){

        searchInput.focus();

    }

});

//==========================================================
// BARCODE SEARCH
//==========================================================

let barcodeBuffer="";

document.addEventListener("keypress",(e)=>{

    if(document.activeElement===searchInput)
        return;

    if(e.key==="Enter"){

        if(barcodeBuffer.length>0){

            searchBarcode(barcodeBuffer);

            barcodeBuffer="";

        }

        return;

    }

    barcodeBuffer+=e.key;

});

function searchBarcode(code){

    const product=

    products.find(item=>

        item.barcode===code

    );

    if(product){

        selectProductAddons(product);

    }

    else{

        showToast(

            "Barcode Not Found",

            "error"

        );

    }

}

//==========================================================
// SEARCH BOX
//==========================================================

if(searchInput){

searchInput.addEventListener("keyup",function(){

    const value=

    this.value

    .toLowerCase()

    .trim();

    const filtered=

    products.filter(item=>{

        return(

            item.name

            .toLowerCase()

            .includes(value)

            ||

            (item.category_name||"")

            .toLowerCase()

            .includes(value)

            ||

            (item.barcode||"")

            .includes(value)

        );

    });

    renderProducts(filtered);

});

}

//==========================================================
// CUSTOMER SEARCH
//==========================================================

const customerInput=

document.getElementById(

"customerName"

);

const customerSuggestions = document.getElementById("customerSuggestions");
let customerSearchTimer = null;
let customerSearchController = null;

async function searchCustomerSuggestions(){
    const query = customerInput?.value.trim() || "";
    if(query.length < 2){
        customerSuggestions.hidden = true;
        customerSuggestions.replaceChildren();
        return;
    }
    if(customerSearchController) customerSearchController.abort();
    customerSearchController = new AbortController();
    try{
        const response = await fetch(`${API}/billing/customers/search?q=${encodeURIComponent(query)}`, {
            credentials: "same-origin", signal: customerSearchController.signal
        });
        if(!response.ok) return;
        const result = await response.json();
        customerSuggestions.replaceChildren();
        (result.customers || []).forEach(customer => {
            const option = document.createElement("div");
            option.className = "customer-suggestion";
            option.tabIndex = 0;
            const details = document.createElement("span");
            const name = document.createElement("strong");
            name.textContent = customer.name || "Customer";
            const contact = document.createElement("small");
            contact.textContent = [customer.phone, customer.email].filter(Boolean).join(" · ") || "No contact details";
            details.append(name, contact);
            const points = document.createElement("span");
            points.className = "customer-points";
            points.textContent = `${Number(customer.points || 0)} pts · ${Number(customer.visit_count || 0)} visits`;
            option.append(details, points);
            const choose = event => {
                event.preventDefault();
                customerInput.value = customer.name || "";
                customerInput.dataset.customerId = customer.id;
                customerSuggestions.hidden = true;
                customerSuggestions.replaceChildren();
                saveCustomer();
            };
            option.addEventListener("mousedown", choose);
            option.addEventListener("keydown", event => {
                if(event.key === "Enter" || event.key === " ") choose(event);
            });
            customerSuggestions.appendChild(option);
        });
        customerSuggestions.hidden = customerSuggestions.childElementCount === 0;
    }catch(error){
        if(error.name !== "AbortError") console.warn("Customer search failed", error);
    }
}

if(customerInput){
    customerInput.addEventListener("input", () => {
        delete customerInput.dataset.customerId;
        clearTimeout(customerSearchTimer);
        customerSearchTimer = setTimeout(searchCustomerSuggestions, 180);
    });
    customerInput.addEventListener("focus", searchCustomerSuggestions);
    customerInput.addEventListener("keydown", event => {
        if(event.key === "Escape") customerSuggestions.hidden = true;
    });
    document.addEventListener("click", event => {
        if(!event.target.closest(".customer-field")) customerSuggestions.hidden = true;
    });
}

//==========================================================
// SHORTCUT KEYS
//==========================================================

document.addEventListener(

"keydown",

function(e){

// Ctrl+F

if(e.ctrlKey && e.key==="f"){

    e.preventDefault();

    searchInput.focus();

}

// Ctrl+B

if(e.ctrlKey && e.key==="b"){

    e.preventDefault();

    checkout();

}

// Ctrl+P

if(e.ctrlKey && e.key==="p"){

    e.preventDefault();

    window.print();

}

// Ctrl+H

if(e.ctrlKey && e.key==="h"){

    e.preventDefault();

    holdBtn.click();

}

// Escape

if(e.key==="Escape"){

    searchInput.value="";

    renderProducts(products);

}

});

//==========================================================
// QUICK QUANTITY
//==========================================================

document.addEventListener(

"keydown",

function(e){

if(cart.length===0)

return;

// +

if(e.key==="+"){

cart[0].quantity++;

renderCart();

updateTotals();

}

// -

if(e.key==="-" &&

cart[0].quantity>1){

cart[0].quantity--;

renderCart();

updateTotals();

}

});

/*==========================================================
                CafeSync POS
                billing.js
                PART 5B-1
        LOCAL STORAGE & RESTORE CART
==========================================================*/

//==========================================================
// SAVE CART
//==========================================================

function saveCart(){

    localStorage.setItem(

        "cafesync_cart",

        JSON.stringify(cart)

    );

}

//==========================================================
// LOAD CART
//==========================================================

function loadCart(){

    const saved=

    localStorage.getItem(

        "cafesync_cart"

    );

    if(saved){

        cart=JSON.parse(saved);

        renderCart();

        updateTotals();

    }

}

//==========================================================
// SAVE CUSTOMER
//==========================================================

function saveCustomer(){

    localStorage.setItem(

        "cafesync_customer",

        document.getElementById(

        "customerName"

        ).value

    );

}

//==========================================================
// RESTORE CUSTOMER
//==========================================================

function restoreCustomer(){

    const customer=

    localStorage.getItem(

        "cafesync_customer"

    );

    if(customer){

        document.getElementById(

        "customerName"

        ).value=customer;

    }

}

//==========================================================
// SAVE TABLE
//==========================================================

function saveTable(){

    localStorage.setItem(

        "cafesync_table",

        document.getElementById(

        "tableNo"

        ).value

    );

}

//==========================================================
// RESTORE TABLE
//==========================================================

function restoreTable(){

    const table=

    localStorage.getItem(

        "cafesync_table"

    );

    if(table){

        document.getElementById(

        "tableNo"

        ).value=table;

    }

}

//==========================================================
// AUTO SAVE
//==========================================================

setInterval(()=>{

    saveCart();

    saveCustomer();

    saveTable();

},5000);

//==========================================================
// RESTORE DATA
//==========================================================

window.addEventListener(

"load",

()=>{

    loadCart();

    restoreCustomer();

    restoreTable();

});

//==========================================================
// HOLD ORDER
//==========================================================

function saveHeldOrder(){

    localStorage.setItem(

        "held_order",

        JSON.stringify(cart)

    );

}

function restoreHeldOrder(){

    const order=

    localStorage.getItem(

        "held_order"

    );

    if(order){

        cart=

        JSON.parse(order);

        renderCart();

        updateTotals();

        showToast(

            "Held Order Restored"

        );

    }

}

//==========================================================
// HOLD BUTTON
//==========================================================

if(holdBtn){

holdBtn.addEventListener(

"dblclick",

()=>{

    restoreHeldOrder();

});

}

//==========================================================
// CLEAR LOCAL STORAGE
//==========================================================

function clearLocalData(){

    localStorage.removeItem(

        "cafesync_cart"

    );

    localStorage.removeItem(

        "cafesync_customer"

    );

    localStorage.removeItem(

        "cafesync_table"

    );

}

//==========================================================
// CHECKOUT SUCCESS
//==========================================================

function checkoutSuccess(){

    clearLocalData();

    cart=[];

    renderCart();

    updateTotals();

    showToast(

        "Order Completed"

    );

}
/*==========================================================
                CafeSync POS
                billing.js
                PART 5B-2
         RECEIPT & INVOICE PREVIEW
==========================================================*/

//==========================================================
// RECEIPT HTML
//==========================================================

function escapeReceiptText(value){
    return String(value ?? "").replace(/[&<>\"']/g, char => ({
        "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
    })[char]);
}

function getItemAddonNames(item){
    let addons = item?.addons || [];
    if (typeof addons === "string") {
        try { addons = JSON.parse(addons); } catch { addons = []; }
    }
    return Array.isArray(addons) ? addons.map(addon => typeof addon === "string" ? addon : addon.name).filter(Boolean) : [];
}

function generateReceiptHTML(){

    let itemsHTML="";

    let subtotal=0;

    cart.forEach(item=>{

        subtotal+=item.price*item.quantity;

        itemsHTML+=`

        <tr>

            <td>${escapeReceiptText(item.name)}${getItemAddonNames(item).length ? `<br><small>Extras: ${escapeReceiptText(getItemAddonNames(item).join(", "))}</small>` : ""}${item.chef_note ? `<br><small>Note: ${escapeReceiptText(item.chef_note)}</small>` : ""}</td>

            <td>${item.quantity}</td>

            <td>₹${item.price.toFixed(2)}</td>

            <td>₹${(item.price*item.quantity).toFixed(2)}</td>

        </tr>

        `;

    });

    const discount=getDiscountAmount(subtotal);

    const gst=
    subtotal*gstPercentage/100;

    const total=
    subtotal+gst-discount;

    return `

    <html>

    <head>

        <title>Invoice</title>

        <style>

            body{

                font-family:Arial;

                padding:20px;

            }

            h2{

                text-align:center;

            }

            table{

                width:100%;

                border-collapse:collapse;

                margin-top:20px;

            }

            table,th,td{

                border:1px solid #ddd;

            }

            th,td{

                padding:8px;

                text-align:center;

            }

            .total{

                margin-top:20px;

                text-align:right;

                font-size:18px;

                font-weight:bold;

            }

        </style>

    </head>

    <body>

        <h2>CafeSync POS</h2>

        <p>

            Bill No :
            ${document.getElementById("billNo").innerHTML}

        </p>

        <p>

            Customer :
            ${document.getElementById("customerName").value}

        </p>

        <table>

            <thead>

                <tr>

                    <th>Item</th>

                    <th>Qty</th>

                    <th>Price</th>

                    <th>Total</th>

                </tr>

            </thead>

            <tbody>

                ${itemsHTML}

            </tbody>

        </table>

        <div class="total">

            <p>Subtotal : ₹${subtotal.toFixed(2)}</p>

            ${showGSTOnReceipt ? `<p>GST (${gstPercentage}%) : ₹${gst.toFixed(2)}</p>` : ""}

            <p>Discount : ₹${discount.toFixed(2)}</p>

            <hr>

            <h3>

                Grand Total :
                ₹${total.toFixed(2)}

            </h3>

        </div>

    </body>

    </html>

    `;

}

//==========================================================
// PREVIEW RECEIPT
//==========================================================

function previewReceipt(){

    if(cart.length===0){

        showToast(

            "Cart Empty",

            "warning"

        );

        return;

    }

    const win=
    window.open("","_blank");

    win.document.write(

        generateReceiptHTML()

    );

    win.document.close();

}

//==========================================================
// PRINT RECEIPT
//==========================================================

function printReceipt(){

    if(cart.length===0){

        showToast(

            "Nothing to Print",

            "warning"

        );

        return;

    }

    const win=
    window.open("","_blank");

    win.document.write(

        generateReceiptHTML()

    );

    win.document.close();

    win.focus();

    win.print();

}

//==========================================================
// PRINT BUTTON
//==========================================================

if(printBtn){
    printBtn.onclick=()=>cart.length ? printReceipt() : (location.href="/orders");
}

//==========================================================
// PREVIEW SHORTCUT
//==========================================================

document.addEventListener(

"keydown",

function(e){

    if(e.ctrlKey && e.shiftKey && e.key==="P"){

        e.preventDefault();

        previewReceipt();

    }

});
/*==========================================================
                CafeSync POS
                billing.js
                PART 5B-3
      OFFLINE QUEUE • DAILY SALES • SOUNDS
==========================================================*/

//==========================================================
// SUCCESS SOUND
//==========================================================

const successSound = new Audio(
    "/static/sounds/success.mp3"
);

const errorSound = new Audio(
    "/static/sounds/error.mp3"
);

function playSuccess(){

    successSound.currentTime = 0;

    successSound.play().catch(()=>{});

}

function playError(){

    errorSound.currentTime = 0;

    errorSound.play().catch(()=>{});

}

//==========================================================
// OFFLINE QUEUE
//==========================================================

function saveOfflineOrder(order){

    const queue = JSON.parse(

        localStorage.getItem("offline_orders")

        || "[]"

    );

    queue.push(order);

    localStorage.setItem(

        "offline_orders",

        JSON.stringify(queue)

    );

}

function getOfflineOrders(){

    return JSON.parse(

        localStorage.getItem("offline_orders")

        || "[]"

    );

}

function clearOfflineOrders(){

    localStorage.removeItem(

        "offline_orders"

    );

}

//==========================================================
// RESEND OFFLINE ORDERS
//==========================================================

async function resendOfflineOrders(){

    const queue = getOfflineOrders();

    if(queue.length===0)

        return;

    for(const order of queue){

        try{

            const response = await fetch(

                API+"/billing/create-order",

                {

                    method:"POST",

                    headers:{

                        "Content-Type":"application/json"

                    },

                    body:JSON.stringify(order)

                }

            );

            if(!response.ok)

                throw new Error();

        }

        catch(err){

            console.log(

                "Offline order still pending."

            );

            return;

        }

    }

    clearOfflineOrders();

    showToast(

        "Offline Orders Synced"

    );

}

//==========================================================
// AUTO SYNC
//==========================================================

window.addEventListener(

"online",

()=>{

    resendOfflineOrders();

});

//==========================================================
// SAVE DAILY SALES
//==========================================================

function updateDailySales(total){

    const today =

    new Date()

    .toLocaleDateString();

    let sales = JSON.parse(

        localStorage.getItem(

            "daily_sales"

        ) || "{}"

    );

    if(!sales[today]){

        sales[today]={

            revenue:0,

            orders:0

        };

    }

    sales[today].revenue+=total;

    sales[today].orders++;

    localStorage.setItem(

        "daily_sales",

        JSON.stringify(sales)

    );

}

//==========================================================
// GET TODAY SALES
//==========================================================

function getTodaySales(){

    const today=

    new Date()

    .toLocaleDateString();

    const sales=

    JSON.parse(

        localStorage.getItem(

        "daily_sales"

        ) || "{}"

    );

    return sales[today] ||

    {

        revenue:0,

        orders:0

    };

}

//==========================================================
// UPDATE DASHBOARD
//==========================================================

function refreshTodaySales(){

    const stats=

    getTodaySales();

    const revenue=

    document.getElementById(

    "todayRevenue"

    );

    const orders=

    document.getElementById(

    "todayOrders"

    );

    if(revenue)

    revenue.innerHTML=

    "₹"+stats.revenue.toFixed(2);

    if(orders)

    orders.innerHTML=

    stats.orders;

}

//==========================================================
// CHECKOUT SUCCESS
//==========================================================

function orderCompleted(total){

    playSuccess();

    updateDailySales(total);

    refreshTodaySales();

}

//==========================================================
// CHECKOUT FAILED
//==========================================================

function orderFailed(){

    playError();

}

//==========================================================
// AUTO REFRESH SALES
//==========================================================

setInterval(

refreshTodaySales,

5000

);

//==========================================================
// LOAD SALES
//==========================================================

window.addEventListener(

"load",

()=>{

    refreshTodaySales();

    resendOfflineOrders();

});
/*==========================================================
                CafeSync POS
                billing.js
                PART 5C
        CASH • CHANGE • LOYALTY • QR
==========================================================*/

//==========================================================
// CASH RECEIVED
//==========================================================

const cashInput =
document.getElementById("cashReceived");

if(cashInput){

cashInput.addEventListener(

"input",

calculateChange

);

}

function calculateChange(){

    const cash=

    Number(

        cashInput.value||0

    );

    const total=

    Number(

        document

        .getElementById("grandTotal")

        .innerHTML

        .replace("₹","")

    );

    let change=

    cash-total;

    if(change<0)

        change=0;

    const box=

    document.getElementById(

        "changeAmount"

    );

    if(box)

        box.innerHTML=

        "₹"+change.toFixed(2);

}

//==========================================================
// CUSTOMER POINTS
//==========================================================

function calculatePoints(total){

    return Math.floor(total/100);

}

function updateCustomerPoints(total){

    const pts=

    calculatePoints(total);

    const lbl=

    document.getElementById(

        "earnedPoints"

    );

    if(lbl){

        lbl.innerHTML=

        pts+" Points";

    }

}

// Screenshot-inspired counter workflow controls.
document.getElementById("saveBillBtn")?.addEventListener("click", () => checkout());
document.getElementById("savePrintBtn")?.addEventListener("click", () => checkout({printAfter:true}));

document.getElementById("newOrderBtn")?.addEventListener("click", () => {
    if(cart.length && !confirm("Start a new order? The current cart will be cleared.")) return;
    cart = [];
    document.getElementById("customerName").value = "";
    delete document.getElementById("customerName").dataset.customerId;
    document.getElementById("tableNo").value = "";
    document.getElementById("discount").value = defaultDiscountPercentage;
    document.getElementById("isPaid").checked = false;
    selectedOrderType = "Dine In";
    paymentMethod = "Cash";
    document.querySelectorAll(".order-type-btn").forEach(b => b.classList.toggle("active", b.dataset.orderType === selectedOrderType));
    document.querySelectorAll(".payment-btn[data-payment]").forEach(b => b.classList.toggle("active", b.dataset.payment === paymentMethod));
    document.getElementById("tableNo").parentElement.classList.remove("table-hidden");
    clearLocalData();
    renderCart();
    updateTotals();
    generateBillNo();
});

document.getElementById("morePaymentToggle")?.addEventListener("click", () => {
    const options = document.getElementById("morePaymentOptions");
    options.hidden = !options.hidden;
});

document.getElementById("logoutPos")?.addEventListener("click", async () => {
    await fetch("/logout", {method:"POST", credentials:"same-origin"});
    location.href = "/login";
});

const lookupModal = document.getElementById("lookupModal");
async function lookupTicket(inputId){
    const query = document.getElementById(inputId).value.trim();
    if(!query){ showToast("Enter a bill or KOT number", "warning"); return; }
    try{
        const response = await fetch(`${API}/billing/lookup?q=${encodeURIComponent(query)}`, {credentials:"same-origin"});
        const result = await response.json();
        if(!response.ok || !result.success){ showToast(result.message || "Order not found", "error"); return; }
        const order = result.data;
        const details = document.getElementById("lookupDetails");
        details.replaceChildren();
        const facts = document.createElement("p");
        facts.className = "lookup-facts";
        facts.textContent = `${order.bill_no} · ${order.table_name || order.order_type || "Takeaway"} · ${order.status} · ₹${Number(order.total || 0).toFixed(2)}`;
        details.appendChild(facts);
        const list = document.createElement("ul");
        (order.items || []).forEach(item => {
            const li = document.createElement("li");
            const addonNames = getItemAddonNames(item);
            li.textContent = `${item.quantity} × ${item.name}${addonNames.length ? ` · ${addonNames.join(", ")}` : ""}${item.chef_note ? ` · Note: ${item.chef_note}` : ""}`;
            list.appendChild(li);
        });
        details.appendChild(list);
        lookupModal.classList.add("open");
        lookupModal.setAttribute("aria-hidden", "false");
    }catch(error){ console.error(error); showToast("Could not look up this order", "error"); }
}

document.querySelectorAll("[data-lookup]").forEach(button => button.addEventListener("click", () => lookupTicket(button.dataset.lookup)));
[["billLookup","billLookup"],["kotLookup","kotLookup"]].forEach(([id,key]) => document.getElementById(id)?.addEventListener("keydown", e => { if(e.key === "Enter") lookupTicket(key); }));
document.getElementById("closeLookup")?.addEventListener("click", () => { lookupModal.classList.remove("open"); lookupModal.setAttribute("aria-hidden", "true"); });
lookupModal?.addEventListener("click", e => { if(e.target === lookupModal) document.getElementById("closeLookup").click(); });

const itemsModal = document.getElementById("itemsModal");
function renderAvailabilityList(){
    const host = document.getElementById("availabilityList");
    host.replaceChildren();
    if(!products.length){ host.textContent = "No menu items found."; return; }
    products.forEach(product => {
        const row = document.createElement("div"); row.className = "availability-row";
        const name = document.createElement("span"); name.className = "availability-name";
        name.textContent = product.name;
        const price = document.createElement("small"); price.textContent = `₹${Number(product.price).toFixed(2)}`; name.appendChild(price);
        const toggle = document.createElement("button");
        const available = Number(product.is_available ?? 1) === 1;
        toggle.className = `availability-toggle${available ? " is-on" : ""}`;
        toggle.type = "button"; toggle.setAttribute("aria-pressed", String(available));
        toggle.innerHTML = `<i class="fas ${available ? "fa-toggle-on" : "fa-toggle-off"}"></i> ${available ? "On" : "Off"}`;
        toggle.addEventListener("click", async () => {
            toggle.disabled = true;
            try{
                const response = await fetch(`${API}/inventory/products/${product.id}/availability`, {
                    method:"PUT", credentials:"same-origin", headers:{"Content-Type":"application/json"},
                    body:JSON.stringify({is_available:!available})
                });
                const result = await response.json();
                if(!response.ok || !result.success) throw new Error(result.message || "Update failed");
                product.is_available = available ? 0 : 1;
                renderProducts(products.filter(p => Number(p.is_available ?? 1) === 1));
                renderAvailabilityList();
            }catch(error){ showToast(error.message, "error"); toggle.disabled = false; }
        });
        row.append(name,toggle); host.appendChild(row);
    });
}
document.getElementById("itemsAvailabilityBtn")?.addEventListener("click", () => {
    renderAvailabilityList(); itemsModal.classList.add("open"); itemsModal.setAttribute("aria-hidden", "false");
});
document.getElementById("closeItemsModal")?.addEventListener("click", () => { itemsModal.classList.remove("open"); itemsModal.setAttribute("aria-hidden", "true"); });
itemsModal?.addEventListener("click", e => { if(e.target === itemsModal) document.getElementById("closeItemsModal").click(); });

document.addEventListener("keydown", e => {
    if(e.key === "Escape"){
        document.querySelectorAll(".lookup-modal.open").forEach(modal => {
            modal.classList.remove("open"); modal.setAttribute("aria-hidden", "true");
        });
    }
    if(e.key === "/" && !["INPUT","TEXTAREA"].includes(document.activeElement?.tagName)){
        e.preventDefault(); searchInput?.focus();
    }
    if(e.key === "F2"){
        e.preventDefault(); document.getElementById("newOrderBtn")?.click();
    }
});

//==========================================================
// QR PAYMENT
//==========================================================

function showQRCode(){

    const modal=

    document.getElementById(

        "qrModal"

    );

    if(modal)

        modal.style.display="flex";

}

function closeQRCode(){

    const modal=

    document.getElementById(

        "qrModal"

    );

    if(modal)

        modal.style.display="none";

}

document

.querySelectorAll(".payment-btn")

.forEach(btn=>{

    btn.addEventListener(

        "click",

        ()=>{

            if(btn.dataset.payment==="UPI"){

                showQRCode();

            }

        }

    );

});

//==========================================================
// RECEIPT FOOTER
//==========================================================

function receiptFooter(){

    return `

    <hr>

    <center>

    <h4>

    Thank You ❤️

    </h4>

    Visit Again

    <br>

    CafeSync POS

    </center>

    `;

}

//==========================================================
// SUCCESS ANIMATION
//==========================================================

function orderAnimation(){

    const div=

    document.createElement("div");

    div.className="bill-success";

    div.innerHTML=`

        ✔ Order Completed

    `;

    document.body.appendChild(div);

    setTimeout(()=>{

        div.remove();

    },2500);

}

//==========================================================
// COMPLETE ORDER
//==========================================================

function finishOrder(total){

    updateCustomerPoints(total);

    orderAnimation();

    playSuccess();

}
/*==========================================================
                CafeSync POS
                billing.js
                PART 5D-1
          MULTIPLE HOLD ORDERS
==========================================================*/

//==========================================================
// HOLD ORDER
//==========================================================

async function holdCurrentOrder(){
    if(cart.length===0){
        showToast("Cart Empty", "warning");
        return;
    }
    try{
        const response = await fetch(`${API}/billing/held-orders`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            credentials: "same-origin",
            body: JSON.stringify({
                customer: document.getElementById("customerName").value,
                customer_id: document.getElementById("customerName").dataset.customerId || null,
                table_id: document.getElementById("tableNo").value || null,
                order_type: selectedOrderType,
                payment_method: paymentMethod,
                is_paid: document.getElementById("isPaid")?.checked || false,
                items: cart
            })
        });
        const result = await response.json();
        if(!response.ok || !result.success) throw new Error(result.message || "Could not hold order");
    }catch(error){
        console.error("Could not hold order", error);
        showToast("Could not save the held order. Your cart is still open.", "error");
        return;
    }
    cart=[];
    clearLocalData();
    renderCart();
    updateTotals();
    showToast("Order Held");
    loadHeldOrders();
}

//==========================================================
// LOAD HOLD ORDERS
//==========================================================

async function loadHeldOrders(){
    const container = document.getElementById("heldOrders");
    if(!container) return;
    container.innerHTML = "";
    try{
        const response = await fetch(`${API}/billing/held-orders`, {credentials: "same-origin"});
        if(!response.ok) throw new Error("Held orders unavailable");
        const result = await response.json();
        heldOrdersCache = result.orders || [];
    }catch(error){
        console.error(error);
        container.textContent = "Held orders unavailable";
        return;
    }

    // Migrate orders saved by older POS versions in this browser.
    let legacy = [];
    try{ legacy = JSON.parse(localStorage.getItem("held_orders") || "[]"); }catch{}
    const remainingLegacy = [];
    for(const oldOrder of legacy){
        try{
            const response = await fetch(`${API}/billing/held-orders`, {
                method: "POST", headers: {"Content-Type": "application/json"}, credentials: "same-origin",
                body: JSON.stringify({customer: oldOrder.customer, table_id: oldOrder.table,
                    order_type: oldOrder.orderType, payment_method: oldOrder.payment,
                    is_paid: oldOrder.isPaid, items: oldOrder.cart})
            });
            const result = await response.json();
            if(!response.ok || !result.success) throw new Error(result.message || "Migration failed");
            heldOrdersCache.unshift(result.order);
        }catch(error){
            console.warn("A locally held order could not be migrated", error);
            remainingLegacy.push(oldOrder);
        }
    }
    localStorage.setItem("held_orders", JSON.stringify(remainingLegacy));

    heldOrdersCache.forEach(order=>{
        const card = document.createElement("div");
        card.className = "hold-card";
        const tableOption = Array.from(document.getElementById("tableNo")?.options || [])
            .find(option => String(option.value) === String(order.table_id));
        const title = document.createElement("h4");
        title.textContent = order.table_id ? `Table: ${tableOption?.textContent || order.table_id}` : (order.order_type || "Take Away");
        const customer = document.createElement("p");
        customer.textContent = order.customer || "Walk-in";
        const date = document.createElement("small");
        date.textContent = new Date(String(order.created_at).replace(" ", "T") + "Z").toLocaleString();
        const resume = document.createElement("button");
        resume.textContent = "Resume";
        resume.addEventListener("click", () => resumeOrder(order.id));
        const discard = document.createElement("button");
        discard.textContent = "Discard";
        discard.addEventListener("click", () => deleteHeldOrder(order.id));
        card.append(title, customer, date, resume, discard);
        container.appendChild(card);
    });
}

//==========================================================
// RESUME ORDER
//==========================================================

async function resumeOrder(id){
    const order = heldOrdersCache.find(item => Number(item.id) === Number(id));
    if(!order) return;
    try{
        const response = await fetch(`${API}/billing/held-orders/${id}`, {method: "DELETE", credentials: "same-origin"});
        const result = await response.json();
        if(!response.ok || !result.success) throw new Error(result.message || "Could not resume held order");
    }catch(error){
        showToast("Could not resume held order. It remains saved.", "error");
        return;
    }
    cart=order.items;
    selectedOrderType = order.order_type || (order.table_id ? "Dine In" : "Parcel");
    document.querySelectorAll(".order-type-btn").forEach(b => b.classList.toggle("active", b.dataset.orderType === selectedOrderType));
    document.getElementById("isPaid").checked = !!order.is_paid;
    document.getElementById("tableNo").parentElement.classList.toggle("table-hidden", selectedOrderType !== "Dine In");

    document.getElementById(

    "customerName"

    ).value=

    order.customer;

    if(order.customer_id) document.getElementById("customerName").dataset.customerId = order.customer_id;

    document.getElementById(

    "tableNo"

    ).value=

    order.table_id || "";

    paymentMethod = order.payment_method || "Cash";
    document.querySelectorAll(".payment-btn[data-payment]").forEach(button => button.classList.toggle("active", button.dataset.payment === paymentMethod));

    renderCart();

    updateTotals();

    saveCart();
    heldOrdersCache = heldOrdersCache.filter(item => Number(item.id) !== Number(id));

    loadHeldOrders();

}

//==========================================================
// DELETE HOLD ORDER
//==========================================================

async function deleteHeldOrder(id){
    try{
        const response = await fetch(`${API}/billing/held-orders/${id}`, {method: "DELETE", credentials: "same-origin"});
        const result = await response.json();
        if(!response.ok || !result.success) throw new Error(result.message || "Delete failed");
        heldOrdersCache = heldOrdersCache.filter(item => Number(item.id) !== Number(id));
        loadHeldOrders();
    }catch(error){ showToast("Could not discard held order", "error"); }
}

//==========================================================
// INITIAL LOAD
//==========================================================

window.addEventListener(

"load",

()=>{

    loadHeldOrders();

});
/*==========================================================
                CafeSync POS
                billing.js
                PART 5D-2
                 SPLIT BILL
==========================================================*/

//==========================================================
// SPLIT BILL
//==========================================================

function splitBill(){

    if(cart.length===0){

        showToast(
            "Cart Empty",
            "warning"
        );

        return;

    }

    const people=parseInt(

        prompt(

            "Split bill between how many people?",

            "2"

        )

    );

    if(!people || people<1 || people>30){
        if(people>30) showToast("Split bills can include up to 30 people", "error");

        return;

    }

    showSplitBill(people);

}

//==========================================================
// SHOW SPLIT BILL
//==========================================================

function showSplitBill(people){
    const lineData = cart.map(item => ({quantity: Number(item.quantity), price: Number(item.price)}));
    let rows = "";
    cart.forEach((item, lineIndex) => {
        const addonText = getItemAddonNames(item).map(escapeReceiptText).join(", ");
        const label = `${escapeReceiptText(item.name)}${addonText ? `<small>Extras: ${addonText}</small>` : ""}${item.chef_note ? `<small>Note: ${escapeReceiptText(item.chef_note)}</small>` : ""}`;
        rows += `<tr><td>${label}<small>Qty ${Number(item.quantity)} · ₹${Number(item.price).toFixed(2)} each</small></td>`;
        for(let person = 0; person < people; person++){
            rows += `<td><input class="split-qty" type="number" min="0" max="${Number(item.quantity)}" step="1" value="${person === 0 ? Number(item.quantity) : 0}" data-line="${lineIndex}" data-person="${person}" aria-label="Quantity for person ${person+1}"></td>`;
        }
        rows += `</tr>`;
    });

    let personCards = "";
    for(let person = 0; person < people; person++){
        personCards += `<section class="split-person"><strong>Person ${person+1}: <span class="split-person-total" data-person="${person}">₹0.00</span></strong>
            <label><input class="split-paid" type="checkbox" data-person="${person}"> Paid now</label>
            <select class="split-method" data-person="${person}"><option>Cash</option><option>Card</option><option>UPI</option><option>Wallet</option><option>Paytm EDC</option><option>Other</option></select></section>`;
    }

    const win = window.open("", "_blank", "width=900,height=760");
    if(!win){
        showToast("Allow pop-ups to review and save the item split", "error");
        return;
    }
    win.document.write(`<!doctype html><html><head><title>Split Bill by Items</title><meta charset="utf-8"><style>
        body{font:14px Arial,sans-serif;padding:20px;color:#26372d}h2{margin-top:0}p{color:#69786e}
        .split-table{width:100%;border-collapse:collapse;margin:14px 0}.split-table th,.split-table td{padding:8px;border-bottom:1px solid #e3e9e4;text-align:center}
        .split-table th:first-child,.split-table td:first-child{text-align:left}.split-table td:first-child{min-width:180px}
        .split-table small{display:block;color:#7c887f;font-size:11px;margin-top:3px}.split-qty{width:54px;padding:6px}
        .split-person{display:flex;align-items:center;gap:14px;padding:10px;border:1px solid #e3e9e4;border-radius:8px;margin:8px 0}
        .split-person strong{flex:1}.split-person label{white-space:nowrap}button{padding:10px 14px;border:0;border-radius:6px;background:#33805a;color:#fff;font-weight:bold;cursor:pointer}
    </style></head><body><h2>Split Bill by Items</h2>
        <p>Assign every item quantity to a person. Tax and discount are divided in proportion to each person’s items.</p>
        <table class="split-table"><thead><tr><th>Item</th>${Array.from({length: people}, (_, i) => `<th>Person ${i+1}</th>`).join("")}</tr></thead><tbody>${rows}</tbody></table>
        ${personCards}<h3>Order total: <span id="splitGrand">₹0.00</span></h3>
        <p>Mark only shares collected now. Unpaid shares stay due on the order.</p>
        <button id="saveSplit">Save order and record selected payments</button>
    </body></html>`);
    win.document.close();

    const discountBase = getDiscountAmount(lineData.reduce((sum, line) => sum + line.price * line.quantity, 0));
    const discountRate = lineData.reduce((sum, line) => sum + line.price * line.quantity, 0)
        ? discountBase / lineData.reduce((sum, line) => sum + line.price * line.quantity, 0) : 0;
    const recalculate = () => {
        const allocated = Array.from({length: people}, () => 0);
        const allocatedSubtotals = Array.from({length: people}, () => 0);
        const assignedByLine = Array.from({length: lineData.length}, () => 0);
        let valid = true;
        win.document.querySelectorAll(".split-qty").forEach(input => {
            const line = Number(input.dataset.line), person = Number(input.dataset.person);
            let quantity = Number(input.value || 0);
            quantity = Math.max(0, Math.min(lineData[line].quantity, Math.floor(quantity)));
            if(Number(input.value) !== quantity) input.value = quantity;
            assignedByLine[line] += quantity;
            allocatedSubtotals[person] += quantity * lineData[line].price;
        });
        if(assignedByLine.some((quantity, index) => quantity !== lineData[index].quantity)) valid = false;
        if(allocatedSubtotals.some(value => value <= 0)) valid = false;
        const amounts = allocatedSubtotals.map(subtotal => Math.round((subtotal + subtotal * gstPercentage / 100 - subtotal * discountRate) * 100) / 100);
        const subtotal = lineData.reduce((sum, line) => sum + line.price * line.quantity, 0);
        const exactTotal = Math.round((subtotal + subtotal * gstPercentage / 100 - discountBase) * 100) / 100;
        const adjustment = Math.round((exactTotal - amounts.reduce((sum, amount) => sum + amount, 0)) * 100) / 100;
        const firstUsed = allocatedSubtotals.findIndex(value => value > 0);
        if(firstUsed >= 0) amounts[firstUsed] = Math.round((amounts[firstUsed] + adjustment) * 100) / 100;
        amounts.forEach((amount, person) => {
            allocated[person] = amount;
            const totalLabel = win.document.querySelector(`.split-person-total[data-person="${person}"]`);
            if(totalLabel) totalLabel.textContent = `₹${amount.toFixed(2)}`;
            const paidCheckbox = win.document.querySelector(`.split-paid[data-person="${person}"]`);
            if(paidCheckbox) paidCheckbox.disabled = allocatedSubtotals[person] <= 0;
        });
        const grandLabel = win.document.getElementById("splitGrand");
        if(grandLabel) grandLabel.textContent = `₹${exactTotal.toFixed(2)}`;
        return {valid, amounts, allocatedSubtotals};
    };
    win.document.querySelectorAll(".split-qty").forEach(input => input.addEventListener("input", recalculate));
    recalculate();
    win.document.getElementById("saveSplit").addEventListener("click", () => {
        const result = recalculate();
        if(!result.valid){ win.alert("Assign every item quantity exactly once and give each person at least one item."); return; }
        const payments = Array.from(win.document.querySelectorAll(".split-paid:checked")).map(check => {
            const person = Number(check.dataset.person);
            return {person_number: person + 1, amount: result.amounts[person], payment_type: win.document.querySelector(`.split-method[data-person="${person}"]`).value};
        });
        const allocations = Array.from({length: people}, (_, person) => ({
            person_number: person + 1,
            amount: result.amounts[person],
            items: Array.from({length: lineData.length}, (_, lineIndex) => {
                const input = win.document.querySelector(`.split-qty[data-line="${lineIndex}"][data-person="${person}"]`);
                return {line_index: lineIndex, quantity: Number(input?.value || 0)};
            }).filter(entry => entry.quantity > 0)
        }));
        if(!win.opener || typeof win.opener.completeSplitOrder !== "function"){
            win.alert("The POS page is no longer available. Reopen the split bill.");
            return;
        }
        win.opener.completeSplitOrder({payments, details: {people: allocations}});
        win.close();
    });
}

//==========================================================
// BUTTON
//==========================================================

const splitBtn=

document.getElementById(

"splitBill"

);

if(splitBtn){

splitBtn.addEventListener(

"click",

splitBill

);

}

window.completeSplitOrder = splitOrder => checkout({splitOrder});

//==========================================================
// SHORTCUT
//==========================================================

document.addEventListener(

"keydown",

function(e){

if(e.ctrlKey && e.key==="l"){

e.preventDefault();

splitBill();

}

});
