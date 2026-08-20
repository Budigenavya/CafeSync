/* ==========================================================
   CafeSync POS
   settings.js
   Part A
   Initialization & Load Settings
========================================================== */

// ======================================================
// API URL
// ======================================================

const API = "http://127.0.0.1:5000";

// ======================================================
// DOM ELEMENTS
// ======================================================

const loadingOverlay = document.getElementById("loadingOverlay");

// Business Information

const cafeName = document.getElementById("cafeName");
const ownerName = document.getElementById("ownerName");
const cafePhone = document.getElementById("cafePhone");
const cafeEmail = document.getElementById("cafeEmail");
const cafeWebsite = document.getElementById("cafeWebsite");
const gstNumber = document.getElementById("gstNumber");
const cafeAddress = document.getElementById("cafeAddress");

// Business Hours

const openingTime = document.getElementById("openingTime");
const closingTime = document.getElementById("closingTime");
const workingDays = document.getElementById("workingDays");

// Social Media

const facebookLink = document.getElementById("facebookLink");
const instagramLink = document.getElementById("instagramLink");
const twitterLink = document.getElementById("twitterLink");
const whatsappNumber = document.getElementById("whatsappNumber");

// ======================================================
// HELPER FUNCTIONS
// ======================================================

function showLoader() {

    if (loadingOverlay) {

        loadingOverlay.style.display = "flex";

    }

}

function hideLoader() {

    if (loadingOverlay) {

        loadingOverlay.style.display = "none";

    }

}

function showToast(message, color = "#28a745") {

    const toast = document.createElement("div");

    toast.className = "toast-message";

    toast.style.background = color;

    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {

        toast.classList.add("show");

    }, 100);

    setTimeout(() => {

        toast.remove();

    }, 3000);

}

// ======================================================
// API HELPERS
// ======================================================

async function getData(url) {

    try {

        const response = await fetch(API + url);

        if (!response.ok) {

            throw new Error("Network Error");

        }

        return await response.json();

    }

    catch (error) {

        console.error(error);

        return {};

    }

}

async function postData(url, data) {

    try {

        const response = await fetch(API + url, {

            method: "POST",

            headers: {

                "Content-Type": "application/json"

            },

            body: JSON.stringify(data)

        });

        return await response.json();

    }

    catch (error) {

        console.error(error);

        return {

            success: false

        };

    }

}

// ======================================================
// LOAD SETTINGS
// ======================================================

async function loadSettings() {

    showLoader();

    try {

        const settings = await getData("/settings");

        cafeName.value = settings.cafe_name || "";

        ownerName.value = settings.owner_name || "";

        cafePhone.value = settings.phone || "";

        cafeEmail.value = settings.email || "";

        cafeWebsite.value = settings.website || "";

        gstNumber.value = settings.gst_number || "";

        cafeAddress.value = settings.address || "";

        openingTime.value = settings.opening_time || "";

        closingTime.value = settings.closing_time || "";

        workingDays.value = settings.working_days || "";

        facebookLink.value = settings.facebook || "";

        instagramLink.value = settings.instagram || "";

        twitterLink.value = settings.twitter || "";

        whatsappNumber.value = settings.whatsapp || "";

    }

    catch (error) {

        console.error(error);

        showToast("Unable to load settings", "#dc3545");

    }

    hideLoader();

}

// ======================================================
// INITIALIZE
// ======================================================

document.addEventListener("DOMContentLoaded", () => {

    loadSettings();

});
/* ==========================================================
   CafeSync POS
   settings.js
   Part B
   Save • Reset • Search • Logo Upload
========================================================== */

// ======================================================
// DOM ELEMENTS
// ======================================================

const saveSettings =
document.getElementById("saveSettings");

const resetSettings =
document.getElementById("resetSettings");

const settingsSearch =
document.getElementById("settingsSearch");

const logoUpload =
document.getElementById("logoUpload");

const logoPreview =
document.getElementById("logoPreview");

// ======================================================
// SAVE SETTINGS
// ======================================================

saveSettings?.addEventListener("click", async () => {

    const data = {

        cafe_name: cafeName.value,

        owner_name: ownerName.value,

        phone: cafePhone.value,

        email: cafeEmail.value,

        website: cafeWebsite.value,

        gst_number: gstNumber.value,

        address: cafeAddress.value,

        opening_time: openingTime.value,

        closing_time: closingTime.value,

        working_days: workingDays.value,

        facebook: facebookLink.value,

        instagram: instagramLink.value,

        twitter: twitterLink.value,

        whatsapp: whatsappNumber.value

    };

    showLoader();

    try {

        const result =
        await postData("/settings/save", data);

        if(result.success){

            showToast(
                "Settings Saved Successfully"
            );

        }

        else{

            showToast(
                result.message || "Save Failed",
                "#dc3545"
            );

        }

    }

    catch(error){

        console.error(error);

        showToast(
            "Unable to save settings",
            "#dc3545"
        );

    }

    hideLoader();

});

// ======================================================
// RESET SETTINGS
// ======================================================

resetSettings?.addEventListener("click", () => {

    const ok = confirm(
        "Reset all settings to the last saved values?"
    );

    if(!ok){

        return;

    }

    loadSettings();

    showToast("Settings Reset");

});

// ======================================================
// SEARCH SETTINGS
// ======================================================

settingsSearch?.addEventListener("keyup", function(){

    const keyword =
    this.value.toLowerCase();

    document
        .querySelectorAll(".card")
        .forEach(card => {

        const text =
        card.innerText.toLowerCase();

        if(text.includes(keyword)){

            card.style.display = "";

        }

        else{

            card.style.display = "none";

        }

    });

});

// ======================================================
// LOGO PREVIEW
// ======================================================

logoUpload?.addEventListener("change", function(){

    const file =
    this.files[0];

    if(!file){

        return;

    }

    const reader =
    new FileReader();

    reader.onload = function(e){

        logoPreview.src =
        e.target.result;

    };

    reader.readAsDataURL(file);

    showToast("Logo Preview Updated");

});

// ======================================================
// REFRESH SETTINGS
// ======================================================

const refreshSettings =
document.getElementById("refreshSettings");

refreshSettings?.addEventListener("click", ()=>{

    loadSettings();

    showToast("Settings Refreshed");

});
/* ==========================================================
   CafeSync POS
   settings.js
   Part C
   Password • Backup • Restore • Cache
========================================================== */

// ======================================================
// DOM ELEMENTS
// ======================================================

const currentPassword =
document.getElementById("currentPassword");

const newPassword =
document.getElementById("newPassword");

const confirmPassword =
document.getElementById("confirmPassword");

const backupDatabase =
document.getElementById("backupDatabase");

const restoreDatabase =
document.getElementById("restoreDatabase");

const restoreFile =
document.getElementById("restoreFile");

const clearCache =
document.getElementById("clearCache");

// ======================================================
// CHANGE PASSWORD
// ======================================================

async function changePassword(){

    if(newPassword.value !== confirmPassword.value){

        showToast(
            "Passwords do not match",
            "#dc3545"
        );

        return;

    }

    if(newPassword.value.length < 6){

        showToast(
            "Password must be at least 6 characters",
            "#dc3545"
        );

        return;

    }

    showLoader();

    try{

        const result = await postData(
            "/settings/change-password",
            {
                current_password: currentPassword.value,
                new_password: newPassword.value
            }
        );

        if(result.success){

            showToast("Password Changed Successfully");

            currentPassword.value = "";
            newPassword.value = "";
            confirmPassword.value = "";

        }else{

            showToast(
                result.message || "Password Change Failed",
                "#dc3545"
            );

        }

    }catch(error){

        console.error(error);

        showToast(
            "Unable to change password",
            "#dc3545"
        );

    }

    hideLoader();

}

// Trigger password change when Enter is pressed

confirmPassword?.addEventListener("keydown",function(e){

    if(e.key==="Enter"){

        changePassword();

    }

});

// ======================================================
// BACKUP DATABASE
// ======================================================

backupDatabase?.addEventListener("click",()=>{

    window.open(
        API + "/settings/backup",
        "_blank"
    );

});

// ======================================================
// RESTORE DATABASE
// ======================================================

restoreDatabase?.addEventListener("click",()=>{

    restoreFile.click();

});

restoreFile?.addEventListener("change",

async function(){

    if(this.files.length===0){

        return;

    }

    const formData = new FormData();

    formData.append(
        "file",
        this.files[0]
    );

    showLoader();

    try{

        const response = await fetch(
            API + "/settings/restore",
            {
                method:"POST",
                body:formData
            }
        );

        const result = await response.json();

        if(result.success){

            showToast("Database Restored");

        }else{

            showToast(
                result.message || "Restore Failed",
                "#dc3545"
            );

        }

    }catch(error){

        console.error(error);

        showToast(
            "Restore Error",
            "#dc3545"
        );

    }

    hideLoader();

});

// ======================================================
// CLEAR CACHE
// ======================================================

clearCache?.addEventListener("click",()=>{

    const ok = confirm(
        "Clear local application cache?"
    );

    if(!ok){

        return;

    }

    localStorage.clear();

    sessionStorage.clear();

    showToast("Cache Cleared");

});
/* ==========================================================
   CafeSync POS
   settings.js
   Part D
   Theme • Language • Notifications • Billing Settings
========================================================== */

// ======================================================
// DOM ELEMENTS
// ======================================================

// Theme

const theme =
document.getElementById("theme");

const language =
document.getElementById("language");

// Notifications

const lowStockAlert =
document.getElementById("lowStockAlert");

const dailySalesReport =
document.getElementById("dailySalesReport");

const employeeNotifications =
document.getElementById("employeeNotifications");

// Billing

const gstPercentage =
document.getElementById("gstPercentage");

const serviceCharge =
document.getElementById("serviceCharge");

const currency =
document.getElementById("currency");

const decimalPlaces =
document.getElementById("decimalPlaces");

const defaultDiscount =
document.getElementById("defaultDiscount");

const maximumDiscount =
document.getElementById("maximumDiscount");

const allowManualDiscount =
document.getElementById("allowManualDiscount");

const receiptHeader =
document.getElementById("receiptHeader");

const receiptFooter =
document.getElementById("receiptFooter");

const showLogoOnReceipt =
document.getElementById("showLogoOnReceipt");

const showGSTOnReceipt =
document.getElementById("showGSTOnReceipt");

// ======================================================
// APPLY THEME
// ======================================================

function applyTheme(selectedTheme){

    document.body.classList.remove(
        "light-theme",
        "dark-theme"
    );

    if(selectedTheme === "dark"){

        document.body.classList.add("dark-theme");

    }

    else if(selectedTheme === "light"){

        document.body.classList.add("light-theme");

    }

    localStorage.setItem(
        "cafesync_theme",
        selectedTheme
    );

}

theme?.addEventListener("change",function(){

    applyTheme(this.value);

    showToast("Theme Updated");

});

// ======================================================
// LANGUAGE
// ======================================================

language?.addEventListener("change",function(){

    localStorage.setItem(
        "cafesync_language",
        this.value
    );

    showToast(
        "Language preference saved"
    );

});

// ======================================================
// SAVE LOCAL PREFERENCES
// ======================================================

function savePreferences(){

    const preferences = {

        theme: theme?.value,

        language: language?.value,

        low_stock_alert:
            lowStockAlert?.checked,

        daily_sales_report:
            dailySalesReport?.checked,

        employee_notifications:
            employeeNotifications?.checked,

        gst_percentage:
            gstPercentage?.value,

        service_charge:
            serviceCharge?.value,

        currency:
            currency?.value,

        decimal_places:
            decimalPlaces?.value,

        default_discount:
            defaultDiscount?.value,

        maximum_discount:
            maximumDiscount?.value,

        allow_manual_discount:
            allowManualDiscount?.checked,

        receipt_header:
            receiptHeader?.value,

        receipt_footer:
            receiptFooter?.value,

        show_logo:
            showLogoOnReceipt?.checked,

        show_gst:
            showGSTOnReceipt?.checked

    };

    localStorage.setItem(

        "cafesync_preferences",

        JSON.stringify(preferences)

    );

}

// ======================================================
// AUTO SAVE PREFERENCES
// ======================================================

[
theme,
language,
lowStockAlert,
dailySalesReport,
employeeNotifications,
gstPercentage,
serviceCharge,
currency,
decimalPlaces,
defaultDiscount,
maximumDiscount,
allowManualDiscount,
receiptHeader,
receiptFooter,
showLogoOnReceipt,
showGSTOnReceipt

].forEach(control=>{

    control?.addEventListener(

        "change",

        savePreferences

    );

});

// ======================================================
// LOAD LOCAL PREFERENCES
// ======================================================

function loadPreferences(){

    const saved =

    localStorage.getItem(

        "cafesync_preferences"

    );

    if(!saved){

        return;

    }

    const pref = JSON.parse(saved);

    if(theme) theme.value = pref.theme || "light";

    if(language) language.value = pref.language || "en";

    if(lowStockAlert)
        lowStockAlert.checked =
        pref.low_stock_alert ?? true;

    if(dailySalesReport)
        dailySalesReport.checked =
        pref.daily_sales_report ?? true;

    if(employeeNotifications)
        employeeNotifications.checked =
        pref.employee_notifications ?? false;

    if(gstPercentage)
        gstPercentage.value =
        pref.gst_percentage || "";

    if(serviceCharge)
        serviceCharge.value =
        pref.service_charge || "";

    if(currency)
        currency.value =
        pref.currency || "INR";

    if(decimalPlaces)
        decimalPlaces.value =
        pref.decimal_places || "2";

    if(defaultDiscount)
        defaultDiscount.value =
        pref.default_discount || "";

    if(maximumDiscount)
        maximumDiscount.value =
        pref.maximum_discount || "";

    if(allowManualDiscount)
        allowManualDiscount.checked =
        pref.allow_manual_discount ?? false;

    if(receiptHeader)
        receiptHeader.value =
        pref.receipt_header || "";

    if(receiptFooter)
        receiptFooter.value =
        pref.receipt_footer || "";

    if(showLogoOnReceipt)
        showLogoOnReceipt.checked =
        pref.show_logo ?? false;

    if(showGSTOnReceipt)
        showGSTOnReceipt.checked =
        pref.show_gst ?? true;

    applyTheme(theme.value);

}

// ======================================================
// INITIALIZE LOCAL SETTINGS
// ======================================================

document.addEventListener(

    "DOMContentLoaded",

    ()=>{

        loadPreferences();

    }

);
/* ==========================================================
   CafeSync POS
   settings.js
   Part E
   Final Initialization & Utilities
========================================================== */

// ======================================================
// KEYBOARD SHORTCUTS
// ======================================================

document.addEventListener("keydown", function (e) {

    // Ctrl + S = Save Settings
    if (e.ctrlKey && e.key.toLowerCase() === "s") {

        e.preventDefault();

        saveSettings?.click();

    }

    // Ctrl + R = Reload Settings
    if (e.ctrlKey && e.key.toLowerCase() === "r") {

        e.preventDefault();

        loadSettings();

        loadPreferences();

        showToast("Settings Reloaded");

    }

    // ESC = Close Loading Overlay (if visible)

    if (e.key === "Escape") {

        hideLoader();

    }

});

// ======================================================
// AUTO REFRESH SETTINGS
// ======================================================

// Refresh every 10 minutes

setInterval(() => {

    loadSettings();

}, 600000);

// ======================================================
// FORM VALIDATION
// ======================================================

function validateSettings() {

    if (cafeName.value.trim() === "") {

        showToast(
            "Cafe Name is required",
            "#dc3545"
        );

        cafeName.focus();

        return false;

    }

    if (cafeEmail.value &&
        !cafeEmail.value.includes("@")) {

        showToast(
            "Enter a valid email address",
            "#dc3545"
        );

        cafeEmail.focus();

        return false;

    }

    return true;

}

// ======================================================
// OVERRIDE SAVE BUTTON
// ======================================================

saveSettings?.addEventListener("click", function (e) {

    if (!validateSettings()) {

        e.preventDefault();

        return;

    }

});

// ======================================================
// BEFORE LEAVING PAGE
// ======================================================

window.addEventListener("beforeunload", function (e) {

    // Optional warning if you implement dirty-form tracking
    // e.preventDefault();
    // e.returnValue = "";

});

// ======================================================
// APPLICATION INITIALIZATION
// ======================================================

document.addEventListener("DOMContentLoaded", () => {

    // Load server-side settings
    loadSettings();

    // Load local preferences
    loadPreferences();

    console.log("===================================");

    console.log(" CafeSync Settings Module Loaded ");

    console.log("===================================");

});