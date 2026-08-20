/* ==========================================================
                    API
========================================================== */

const API = "http://127.0.0.1:5000";

/* ==========================================================
                    GLOBAL VARIABLES
========================================================== */

let products = [];

let categories = [];

let deleteProductId = null;

/* ==========================================================
                    DOM ELEMENTS
========================================================== */

const productTable =
document.getElementById("productTable");

const categoryFilter =
document.getElementById("categoryFilter");

const productCategory =
document.getElementById("productCategory");

const loadingScreen =
document.getElementById("loadingScreen");

const toast =
document.getElementById("toast");

/* ==========================================================
                    INIT
========================================================== */

document.addEventListener(

    "DOMContentLoaded",

    () => {

        initialize();

    }

);

async function initialize(){

    showLoading();

    await loadDashboard();

    await loadCategories();

    await loadProducts();

    hideLoading();

}

/* ==========================================================
                    DASHBOARD
========================================================== */

async function loadDashboard(){

    try{

        const response =

        await fetch(

            API + "/inventory/dashboard"

        );

        const result =

        await response.json();

        if(result.success){

            document

            .getElementById("totalProducts")

            .textContent =

            result.data.total_products;

            document

            .getElementById("totalCategories")

            .textContent =

            result.data.total_categories;

            document

            .getElementById("inventoryValue")

            .textContent =

            "₹"+

            Number(

                result.data.inventory_value

            ).toFixed(2);

            document

            .getElementById("lowStockCount")

            .textContent =

            result.data.low_stock;

        }

    }

    catch(error){

        console.error(error);

        showToast(

            "Unable To Load Dashboard",

            "error"

        );

    }

}

/* ==========================================================
                    LOAD CATEGORIES
========================================================== */

async function loadCategories(){

    try{

        const response =

        await fetch(

            API + "/inventory/categories"

        );

        const result =

        await response.json();

        if(result.success){

            categories = result.data;

            categoryFilter.innerHTML =

            `<option value="">All Categories</option>`;

            productCategory.innerHTML = "";

            categories.forEach(category=>{

                categoryFilter.innerHTML +=

                `

                <option value="${category.id}">

                    ${category.name}

                </option>

                `;

                productCategory.innerHTML +=

                `

                <option value="${category.id}">

                    ${category.name}

                </option>

                `;

            });

        }

    }

    catch(error){

        console.error(error);

    }

}

/* ==========================================================
                    LOADING
========================================================== */

function showLoading(){

    loadingScreen.style.display="flex";

}

function hideLoading(){

    loadingScreen.style.display="none";

}

/* ==========================================================
                    TOAST
========================================================== */

function showToast(

    message,

    type="success"

){

    toast.textContent = message;

    toast.className = "";

    toast.classList.add(type);

    toast.classList.add("show");

    setTimeout(()=>{

        toast.classList.remove("show");

    },3000);

}
/* ==========================================================
                    LOAD PRODUCTS
========================================================== */

async function loadProducts(){

    try{

        const response =

        await fetch(

            API + "/inventory/products"

        );

        const result =

        await response.json();

        if(result.success){

            products = result.data;

            renderProducts(products);

            renderLowStock();

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

            "Unable To Load Products",

            "error"

        );

    }

}

/* ==========================================================
                    RENDER PRODUCTS
========================================================== */

function renderProducts(data){

    productTable.innerHTML = "";

    if(data.length===0){

        productTable.innerHTML =

        `

        <tr>

            <td colspan="7">

                <div class="empty-state">

                    <i class="fa-solid fa-box-open"></i>

                    <h3>No Products Found</h3>

                    <p>

                        Click Add Product to begin.

                    </p>

                </div>

            </td>

        </tr>

        `;

        return;

    }

    data.forEach(product=>{

        let status="available";

        let statusText="Available";

        if(product.stock<=0){

            status="out";

            statusText="Out of Stock";

        }

        else if(product.stock<=10){

            status="low";

            statusText="Low Stock";

        }

        productTable.innerHTML +=

        `

        <tr>

            <td>${product.barcode||"-"}</td>

            <td>

                <strong>

                    ${product.name}

                </strong>

            </td>

            <td>

                ${product.category_name}

            </td>

            <td>

                ₹${Number(product.price).toFixed(2)}

            </td>

            <td>

                ${product.stock}

            </td>

            <td>

                <span class="status ${status}">

                    ${statusText}

                </span>

            </td>

            <td>

                <button

                    class="action-btn edit-btn"

                    onclick="editProduct(${product.id})">

                    <i class="fa-solid fa-pen"></i>

                </button>

                <button

                    class="action-btn delete-btn"

                    onclick="deleteProduct(${product.id})">

                    <i class="fa-solid fa-trash"></i>

                </button>

                <button

                    class="action-btn barcode-btn"

                    onclick="generateBarcode('${product.barcode}','${product.name}')">

                    <i class="fa-solid fa-barcode"></i>

                </button>

            </td>

        </tr>

        `;

    });

}

/* ==========================================================
                    LOW STOCK TABLE
========================================================== */

function renderLowStock(){

    const table =

    document.getElementById(

        "lowStockTable"

    );

    table.innerHTML="";

    const lowProducts =

    products.filter(

        p=>p.stock<=10

    );

    if(lowProducts.length===0){

        table.innerHTML=

        `

        <tr>

            <td colspan="3"

                class="text-center">

                No Low Stock Products

            </td>

        </tr>

        `;

        return;

    }

    lowProducts.forEach(product=>{

        table.innerHTML +=

        `

        <tr>

            <td>

                ${product.name}

            </td>

            <td>

                ${product.stock}

            </td>

            <td>

                <span class="status low">

                    Low

                </span>

            </td>

        </tr>

        `;

    });

}

/* ==========================================================
                    REFRESH DATA
========================================================== */

async function refreshInventory(){

    showLoading();

    await loadDashboard();

    await loadProducts();

    hideLoading();

}
/* ==========================================================
                    PRODUCT MODAL
========================================================== */

const productModal =
document.getElementById("productModal");

const categoryModal =
document.getElementById("categoryModal");

const deleteModal =
document.getElementById("deleteModal");

/* ==========================================================
                    OPEN PRODUCT MODAL
========================================================== */
document.addEventListener("DOMContentLoaded", () => {

    const addProductBtn = document.getElementById("addProductBtn");

    if(addProductBtn){

        addProductBtn.onclick = () => {

            document.getElementById("productModalTitle").textContent = "Add Product";

            document.getElementById("productForm").reset();

            document.getElementById("productId").value = "";

            productModal.classList.add("active");

        };

    }

});
/* ==========================================================
                    CLOSE PRODUCT MODAL
========================================================== */

document
.getElementById("closeProductModal")
.onclick = () => {

    productModal.classList.remove("active");

};

/* ==========================================================
                    SAVE PRODUCT
========================================================== */

document
.getElementById("productForm")
.addEventListener(

"submit",

async function(e){

    e.preventDefault();

    const id =
    document
    .getElementById("productId")
    .value;

    const product = {

        name:
        document.getElementById("productName").value,

        category_id:
        document.getElementById("productCategory").value,

        barcode:
        document.getElementById("barcode").value,

        price:
        document.getElementById("price").value,

        stock:
        document.getElementById("stock").value

    };

    let url =
    API + "/inventory/products";

    let method = "POST";

    if(id){

        url += "/" + id;

        method = "PUT";

    }

    try{

        const response =
        await fetch(

            url,

            {

                method,

                headers:{

                    "Content-Type":
                    "application/json"

                },

                body:
                JSON.stringify(product)

            }

        );

        const result =
        await response.json();

        if(result.success){

            showToast(result.message);

            productModal.classList.remove("active");

            refreshInventory();

        }

        else{

            showToast(

                result.message,

                "error"

            );

        }

    }

    catch(error){

        console.log(error);

    }

}

);

/* ==========================================================
                    EDIT PRODUCT
========================================================== */

function editProduct(id){

    const product =

    products.find(

        p => p.id == id

    );

    if(!product) return;

    document
    .getElementById("productModalTitle")
    .textContent = "Edit Product";

    document
    .getElementById("productId")
    .value = product.id;

    document
    .getElementById("productName")
    .value = product.name;

    document
    .getElementById("productCategory")
    .value = product.category_id;

    document
    .getElementById("barcode")
    .value = product.barcode;

    document
    .getElementById("price")
    .value = product.price;

    document
    .getElementById("stock")
    .value = product.stock;

    productModal.classList.add("active");

}

/* ==========================================================
                    DELETE PRODUCT
========================================================== */

function deleteProduct(id){

    deleteProductId = id;

    deleteModal.classList.add("active");

}

/* ==========================================================
                    CONFIRM DELETE
========================================================== */

document
.getElementById("confirmDelete")
.onclick = async () => {

    try{

        const response =
        await fetch(

            API +
            "/inventory/products/" +
            deleteProductId,

            {

                method:"DELETE"

            }

        );

        const result =
        await response.json();

        if(result.success){

            showToast(result.message);

            refreshInventory();

        }

        else{

            showToast(

                result.message,

                "error"

            );

        }

    }

    catch(error){

        console.log(error);

    }

    deleteModal.classList.remove("active");

};

/* ==========================================================
                    CANCEL DELETE
========================================================== */

document
.getElementById("cancelDelete")
.onclick = () => {

    deleteModal.classList.remove("active");

};

/* ==========================================================
                    CATEGORY MODAL
========================================================== */

const addCategoryBtn = document.getElementById("addCategoryBtn");
const closeCategoryModal = document.getElementById("closeCategoryModal");


if(addCategoryBtn){

    addCategoryBtn.onclick = () => {

        if(categoryModal){
            categoryModal.classList.add("active");
        }

    };

}


if(closeCategoryModal){

    closeCategoryModal.onclick = () => {

        if(categoryModal){
            categoryModal.classList.remove("active");
        }

    };

}

/* ==========================================================
                    SAVE CATEGORY
========================================================== */

document
.getElementById("categoryForm")
.addEventListener(

"submit",

async function(e){

    e.preventDefault();

    const category = {

        name:

        document
        .getElementById("categoryName")
        .value

    };

    try{

        const response =
        await fetch(

            API +
            "/inventory/categories",

            {

                method:"POST",

                headers:{

                    "Content-Type":
                    "application/json"

                },

                body:
                JSON.stringify(category)

            }

        );

        const result =
        await response.json();

        if(result.success){

            showToast(result.message);

            categoryModal.classList.remove("active");

            loadCategories();

        }

        else{

            showToast(

                result.message,

                "error"

            );

        }

    }

    catch(error){

        console.log(error);

    }

}

);
/* ==========================================================
                    SEARCH PRODUCT
========================================================== */

document
.getElementById("searchProduct")
.addEventListener("keyup", filterProducts);

document
.getElementById("searchBtn")
.addEventListener("click", filterProducts);

/* ==========================================================
                    FILTERS
========================================================== */

document
.getElementById("categoryFilter")
.addEventListener("change", filterProducts);

document
.getElementById("stockFilter")
.addEventListener("change", filterProducts);

function filterProducts(){

    const keyword =
    document
    .getElementById("searchProduct")
    .value
    .toLowerCase();

    const category =
    document
    .getElementById("categoryFilter")
    .value;

    const stock =
    document
    .getElementById("stockFilter")
    .value;

    let filtered = [...products];

    if(keyword){

        filtered = filtered.filter(product =>

            product.name
            .toLowerCase()
            .includes(keyword)

            ||

            (product.barcode || "")
            .toLowerCase()
            .includes(keyword)

        );

    }

    if(category){

        filtered = filtered.filter(product =>

            String(product.category_id) === category

        );

    }

    if(stock==="low"){

        filtered = filtered.filter(product =>

            product.stock>0 && product.stock<=10

        );

    }

    if(stock==="available"){

        filtered = filtered.filter(product =>

            product.stock>10

        );

    }

    renderProducts(filtered);

}

/* ==========================================================
                    RESET FILTER
========================================================== */

document
.getElementById("resetBtn")
.addEventListener("click",()=>{

    document
    .getElementById("searchProduct")
    .value="";

    document
    .getElementById("categoryFilter")
    .value="";

    document
    .getElementById("stockFilter")
    .value="";

    renderProducts(products);

});

/* ==========================================================
                    BARCODE
========================================================== */

const barcodeModal =
document.getElementById("barcodeModal");

function generateBarcode(barcode,name){

    barcodeModal.classList.add("active");

    JsBarcode(

        "#barcodePreview",

        barcode || "000000000",

        {

            format:"CODE128",

            displayValue:true,

            fontSize:18,

            width:2,

            height:70

        }

    );

}

document
.getElementById("closeBarcodeModal")
.onclick=()=>{

    barcodeModal.classList.remove("active");

};

/* ==========================================================
                    PRINT BARCODE
========================================================== */

document
.getElementById("printBarcode")
.onclick=()=>{

    const printWindow = window.open();

    printWindow.document.write(

        document
        .querySelector(".barcode-area")
        .innerHTML

    );

    printWindow.print();

    printWindow.close();

};

/* ==========================================================
                    EXPORT EXCEL
========================================================== */

document
.getElementById("exportExcel")
.onclick=()=>{

    window.location.href=

    API+

    "/inventory/export/excel";

};

/* ==========================================================
                    EXPORT PDF
========================================================== */

document
.getElementById("exportPDF")
.onclick=()=>{

    window.location.href=

    API+

    "/inventory/export/pdf";

};
/* ==========================================================
                    DARK MODE
========================================================== */

const darkBtn =
document.getElementById("darkModeBtn");

darkBtn.addEventListener("click",()=>{

    document.body.classList.toggle("dark");

    localStorage.setItem(

        "inventoryTheme",

        document.body.classList.contains("dark")

    );

});

if(localStorage.getItem("inventoryTheme")==="true"){

    document.body.classList.add("dark");

}

/* ==========================================================
                    CLOSE MODALS
========================================================== */

window.onclick=function(event){

    if(event.target===productModal){

        productModal.classList.remove("active");

    }

    if(event.target===categoryModal){

        categoryModal.classList.remove("active");

    }

    if(event.target===barcodeModal){

        barcodeModal.classList.remove("active");

    }

    if(event.target===deleteModal){

        deleteModal.classList.remove("active");

    }

};

/* ==========================================================
                    KEYBOARD SHORTCUTS
========================================================== */

document.addEventListener(

    "keydown",

    function(e){

        // ESC closes all modals

        if(e.key==="Escape"){

            productModal.classList.remove("active");

            categoryModal.classList.remove("active");

            barcodeModal.classList.remove("active");

            deleteModal.classList.remove("active");

        }

        // Ctrl + N = Add Product

        if(e.ctrlKey && e.key==="n"){

            e.preventDefault();

            document
            .getElementById("addProductBtn")
            .click();

        }

    }

);

/* ==========================================================
                    AUTO REFRESH
========================================================== */

// Refresh inventory every 60 seconds

setInterval(()=>{

    refreshInventory();

},60000);

/* ==========================================================
                    HELPERS
========================================================== */

function formatCurrency(value){

    return "₹"+

    Number(value).toFixed(2);

}

function clearProductForm(){

    document

    .getElementById("productForm")

    .reset();

    document

    .getElementById("productId")

    .value="";

}

function clearCategoryForm(){

    document

    .getElementById("categoryForm")

    .reset();

}

/* ==========================================================
                    AFTER SAVE
========================================================== */

async function reloadEverything(){

    showLoading();

    await loadDashboard();

    await loadCategories();

    await loadProducts();

    hideLoading();

}

/* ==========================================================
                    WINDOW LOAD
========================================================== */

window.addEventListener(

    "load",

    ()=>{

        hideLoading();

    }

);

/* ==========================================================
                    DEBUG MODE
========================================================== */

console.log(

    "CafeSync Inventory Loaded Successfully"

);

/* ==========================================================
                    END OF FILE
========================================================== */