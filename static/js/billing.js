/*==========================================================
                CafeSync POS
                billing.js
                PART 1
==========================================================*/

//==========================================================
// API
//==========================================================

const API = "http://127.0.0.1:5000";

//==========================================================
// GLOBAL VARIABLES
//==========================================================

let products = [];

let categories = [];

let cart = [];

let selectedCategory = "All";

let paymentMethod = "Cash";

let gstPercentage = 5;

let currentOrder = null;

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

    await loadCategories();

    await loadProducts();

    updateTotals();

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

                <div class="stock">

                    Stock : ${product.stock}

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

                addToCart(product);

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

function addToCart(product){

    const existing=cart.find(item=>item.id===product.id);

    if(existing){

        existing.quantity++;

    }

    else{

        cart.push({

            id:product.id,

            name:product.name,

            price:Number(product.price),

            image:product.image,

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

                </div>

            </div>

            <div class="cart-right">

                <div class="quantity">

                    <button
                        onclick="decreaseQuantity(${item.id})">

                        -

                    </button>

                    <span>

                        ${item.quantity}

                    </span>

                    <button
                        onclick="increaseQuantity(${item.id})">

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
                    onclick="removeItem(${item.id})">

                    <i class="fas fa-trash"></i>

                </button>

            </div>

        `;

        cartItems.appendChild(cartCard);

    });

}

//==========================================================
// INCREASE QUANTITY
//==========================================================

function increaseQuantity(id){

    const item = cart.find(p => p.id === id);

    if(!item) return;

    item.quantity++;

    renderCart();

    updateTotals();

}

//==========================================================
// DECREASE QUANTITY
//==========================================================

function decreaseQuantity(id){

    const item = cart.find(p => p.id === id);

    if(!item) return;

    item.quantity--;

    if(item.quantity <= 0){

        cart = cart.filter(p => p.id !== id);

    }

    renderCart();

    updateTotals();

}

//==========================================================
// REMOVE ITEM
//==========================================================

function removeItem(id){

    cart = cart.filter(item => item.id !== id);

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

    const discount =
        Number(discountInput?.value || 0);

    const gst =
        subtotal * gstPercentage / 100;

    const grandTotal =
        subtotal + gst - discount;

    document.getElementById("subtotal").innerHTML =
        "₹" + subtotal.toFixed(2);

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
.querySelectorAll(".payment-btn")
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

async function checkout(){

    if(cart.length===0){

        showToast(
            "Cart is Empty",
            "error"
        );

        return;

    }

    let subtotal=0;

    cart.forEach(item=>{

        subtotal+=
        item.price*item.quantity;

    });

    const discount=
    Number(
        document
        .getElementById("discount")
        .value
    );

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

        customer:
        document.getElementById("customerName").value

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

            showToast(
                "Bill Saved Successfully"
            );

            cart=[];

            renderCart();

            updateTotals();

        }

        else{

            showToast(

                data.message,

                "error"

            );

        }

    }

    catch(err){

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

holdBtn.addEventListener("click",()=>{

    if(cart.length===0){

        showToast(

            "Nothing to Hold",

            "warning"

        );

        return;

    }

    currentOrder=[...cart];

    showToast(

        "Order Held"

    );

});

}

//==========================================================
// PRINT BILL
//==========================================================

const printBtn=
document.getElementById("printBtn");

if(printBtn){

printBtn.addEventListener("click",()=>{

    window.print();

});

}

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

	// 5% GST
	const gstValue = subtotalValue * 0.05;

	// No discount for now
	const discountValue = 0;

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

    	    order_type:
        	tableId
            	? "Dine In"
            	: "Take Away",

    	    subtotal: subtotalValue,

    	    gst: gstValue,

    	    discount: discountValue,

    	    total: grandTotalValue,

    	    payment_method: "Pending",

    	    items: cart.map(item => ({

        	product_id: item.id,

        	quantity: Number(item.quantity),

        	price: Number(item.price)

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

            }

            else {

                showToast(
                    result.message ||
                    "Unable to send order",
                    "error"
                );

            }

        }

        catch (error) {

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

        addToCart(product);

        showToast(

            product.name+" Added"

        );

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

if(customerInput){

customerInput.addEventListener(

"keyup",

async function(){

    if(this.value.length<3)

        return;

    try{

        const response=

        await fetch(

        API+

        "/customers/search?name="+

        this.value

        );

        if(!response.ok)

            return;

        const data=

        await response.json();

        console.log(data);

    }

    catch(err){

        console.log(err);

    }

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

function generateReceiptHTML(){

    let itemsHTML="";

    let subtotal=0;

    cart.forEach(item=>{

        subtotal+=item.price*item.quantity;

        itemsHTML+=`

        <tr>

            <td>${item.name}</td>

            <td>${item.quantity}</td>

            <td>₹${item.price.toFixed(2)}</td>

            <td>₹${(item.price*item.quantity).toFixed(2)}</td>

        </tr>

        `;

    });

    const discount=
    Number(document.getElementById("discount").value||0);

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

            <p>GST : ₹${gst.toFixed(2)}</p>

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

    printBtn.onclick=printReceipt;

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

function holdCurrentOrder(){

    if(cart.length===0){

        showToast(

            "Cart Empty",

            "warning"

        );

        return;

    }

    let orders=

    JSON.parse(

        localStorage.getItem(

        "held_orders"

        ) || "[]"

    );

    const order={

        id:Date.now(),

        customer:

        document.getElementById(

        "customerName"

        ).value,

        table:

        document.getElementById(

        "tableNo"

        ).value,

        payment:paymentMethod,

        cart:[...cart],

        date:new Date()

        .toLocaleString()

    };

    orders.push(order);

    localStorage.setItem(

        "held_orders",

        JSON.stringify(orders)

    );

    cart=[];

    renderCart();

    updateTotals();

    showToast(

        "Order Held"

    );

    loadHeldOrders();

}

//==========================================================
// LOAD HOLD ORDERS
//==========================================================

function loadHeldOrders(){

    const container=

    document.getElementById(

    "heldOrders"

    );

    if(!container)

        return;

    container.innerHTML="";

    const orders=

    JSON.parse(

        localStorage.getItem(

        "held_orders"

        ) || "[]"

    );

    orders.forEach(order=>{

        const card=

        document.createElement("div");

        card.className="hold-card";

        card.innerHTML=`

        <h4>

        Table :

        ${order.table}

        </h4>

        <p>

        ${order.customer||"Walk-in"}

        </p>

        <small>

        ${order.date}

        </small>

        <button

        onclick="resumeOrder(${order.id})">

        Resume

        </button>

        `;

        container.appendChild(card);

    });

}

//==========================================================
// RESUME ORDER
//==========================================================

function resumeOrder(id){

    let orders=

    JSON.parse(

        localStorage.getItem(

        "held_orders"

        ) || "[]"

    );

    const order=

    orders.find(

        o=>o.id===id

    );

    if(!order)

        return;

    cart=order.cart;

    document.getElementById(

    "customerName"

    ).value=

    order.customer;

    document.getElementById(

    "tableNo"

    ).value=

    order.table;

    renderCart();

    updateTotals();

    orders=

    orders.filter(

        o=>o.id!==id

    );

    localStorage.setItem(

        "held_orders",

        JSON.stringify(orders)

    );

    loadHeldOrders();

}

//==========================================================
// DELETE HOLD ORDER
//==========================================================

function deleteHeldOrder(id){

    let orders=

    JSON.parse(

        localStorage.getItem(

        "held_orders"

        ) || "[]"

    );

    orders=

    orders.filter(

        o=>o.id!==id

    );

    localStorage.setItem(

        "held_orders",

        JSON.stringify(orders)

    );

    loadHeldOrders();

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

    if(!people || people<1){

        return;

    }

    let subtotal=0;

    cart.forEach(item=>{

        subtotal+=item.price*item.quantity;

    });

    const discount=
    Number(

        document.getElementById(

        "discount"

        ).value || 0

    );

    const gst=

    subtotal*gstPercentage/100;

    const grand=

    subtotal+gst-discount;

    const perPerson=

    grand/people;

    showSplitBill(

        people,

        perPerson,

        grand

    );

}

//==========================================================
// SHOW SPLIT BILL
//==========================================================

function showSplitBill(

people,

perPerson,

total

){

    let html="";

    html+=`

    <h2>

    Split Bill

    </h2>

    <hr>

    `;

    for(let i=1;i<=people;i++){

        html+=`

        <div
        style="
        padding:12px;
        margin:10px 0;
        border:1px solid #ddd;
        border-radius:8px;">

            <b>

            Person ${i}

            </b>

            <br><br>

            Amount :

            ₹${perPerson.toFixed(2)}

        </div>

        `;

    }

    html+=`

    <hr>

    <h3>

    Total :

    ₹${total.toFixed(2)}

    </h3>

    `;

    const win=

    window.open(

    "",

    "_blank",

    "width=450,height=700"

    );

    win.document.write(`

    <html>

    <head>

    <title>

    Split Bill

    </title>

    <style>

    body{

    font-family:Arial;

    padding:25px;

    }

    </style>

    </head>

    <body>

    ${html}

    </body>

    </html>

    `);

    win.document.close();

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