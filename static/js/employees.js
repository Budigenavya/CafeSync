/* ==========================================================
   CafeSync POS
   employees.js
   Part A
   Initialization & Employee Loading
========================================================== */

// ======================================================
// API URL
// ======================================================

const API = "http://127.0.0.1:5000";

// ======================================================
// DOM ELEMENTS
// ======================================================

// Statistics
const totalEmployees = document.getElementById("totalEmployees");
const presentToday = document.getElementById("presentToday");
const onShift = document.getElementById("onShift");
const monthlyPayroll = document.getElementById("monthlyPayroll");

// Table
const employeeTable = document.getElementById("employeeTable");

// Search & Filters
const employeeSearch = document.getElementById("employeeSearch");
const departmentFilter = document.getElementById("departmentFilter");
const statusFilter = document.getElementById("statusFilter");
const filterEmployees = document.getElementById("filterEmployees");

// Loading
const loadingOverlay = document.getElementById("loadingOverlay");

// ======================================================
// GLOBAL DATA
// ======================================================

let employees = [];
let filteredEmployees = [];

// ======================================================
// LOADING
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

    } catch (err) {

        console.error(err);

        return [];

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

    } catch (err) {

        console.error(err);

        return {
            success: false
        };

    }

}

// ======================================================
// LOAD DASHBOARD STATS
// ======================================================

async function loadEmployeeStats() {

    showLoader();

    try {

        const stats = await getData("/employees/dashboard");

        totalEmployees.textContent = stats.total_employees || 0;
        presentToday.textContent = stats.present_today || 0;
        onShift.textContent = stats.on_shift || 0;
        monthlyPayroll.textContent =
            "₹" + (stats.monthly_payroll || 0);

    } catch (err) {

        console.error(err);

    }

    hideLoader();

}

// ======================================================
// LOAD EMPLOYEES
// ======================================================

async function loadEmployees() {

    showLoader();

    try {

        employees =
            await getData("/employees");

        filteredEmployees = [...employees];

        renderEmployeeTable(filteredEmployees);

    } catch (err) {

        console.error(err);

    }

    hideLoader();

}

// ======================================================
// RENDER TABLE
// ======================================================

function renderEmployeeTable(data) {

    if (!data.length) {

        employeeTable.innerHTML = `

            <tr>

                <td colspan="9">

                    No Employees Found

                </td>

            </tr>

        `;

        return;

    }

    let html = "";

    data.forEach(emp => {

        html += `

        <tr>

            <td>${emp.id}</td>

            <td>

                <img src="${emp.photo || '/static/images/default-user.png'}"
                     class="table-avatar">

            </td>

            <td>${emp.name}</td>

            <td>${emp.role}</td>

            <td>${emp.phone}</td>

            <td>${emp.email}</td>

            <td>

                <span class="badge ${emp.status.toLowerCase()}">

                    ${emp.status}

                </span>

            </td>

            <td>${emp.shift}</td>

            <td>

                <button
                    class="edit-btn"
                    onclick="editEmployee(${emp.id})">

                    <i class="fa-solid fa-pen"></i>

                </button>

                <button
                    class="delete-btn"
                    onclick="deleteEmployee(${emp.id})">

                    <i class="fa-solid fa-trash"></i>

                </button>

                <button
                    class="view-btn"
                    onclick="viewEmployee(${emp.id})">

                    <i class="fa-solid fa-eye"></i>

                </button>

            </td>

        </tr>

        `;

    });

    employeeTable.innerHTML = html;

}

// ======================================================
// TOAST
// ======================================================

function showToast(message, color = "green") {

    const toast = document.createElement("div");

    toast.className = "toast-message";

    toast.style.background = color;

    toast.innerHTML = message;

    document.body.appendChild(toast);

    setTimeout(() => {

        toast.classList.add("show");

    }, 100);

    setTimeout(() => {

        toast.remove();

    }, 3000);

}

// ======================================================
// INITIALIZE
// ======================================================

document.addEventListener("DOMContentLoaded", () => {

    loadEmployeeStats();

    loadEmployees();

});
/* ==========================================================
   CafeSync POS
   employees.js
   Part B
   Employee CRUD Operations
========================================================== */

// ======================================================
// MODAL ELEMENTS
// ======================================================

const employeeModal =
document.getElementById("employeeModal");

const employeeModalTitle =
document.getElementById("employeeModalTitle");

const addEmployeeBtn =
document.getElementById("addEmployeeBtn");

const closeEmployeeModal =
document.getElementById("closeEmployeeModal");

const cancelEmployeeBtn =
document.getElementById("cancelEmployeeBtn");

const saveEmployeeBtn =
document.getElementById("saveEmployeeBtn");

// Form Fields

const employeeId =
document.getElementById("employeeId");

const employeeName =
document.getElementById("employeeName");

const employeeEmail =
document.getElementById("employeeEmail");

const employeePhone =
document.getElementById("employeePhone");

const employeeAddress =
document.getElementById("employeeAddress");

const employeeRole =
document.getElementById("employeeRole");

const employeeShift =
document.getElementById("employeeShift");

const joiningDate =
document.getElementById("joiningDate");

const employeeDOB =
document.getElementById("employeeDOB");

const employeeSalary =
document.getElementById("employeeSalary");

const employeeStatus =
document.getElementById("employeeStatus");

// Employee Details Panel

const employeeDetails =
document.getElementById("employeeDetails");

// ======================================================
// MODAL FUNCTIONS
// ======================================================

function openEmployeeModal(){

    employeeModal.style.display = "flex";

}

function closeModal(){

    employeeModal.style.display = "none";

    clearEmployeeForm();

}

// ======================================================
// CLEAR FORM
// ======================================================

function clearEmployeeForm(){

    employeeId.value = "";

    employeeName.value = "";

    employeeEmail.value = "";

    employeePhone.value = "";

    employeeAddress.value = "";

    employeeRole.value = "";

    employeeShift.value = "Morning";

    joiningDate.value = "";

    employeeDOB.value = "";

    employeeSalary.value = "";

    employeeStatus.value = "Active";

}

// ======================================================
// ADD EMPLOYEE
// ======================================================

addEmployeeBtn?.addEventListener("click",()=>{

    employeeModalTitle.innerHTML =
    "Add Employee";

    clearEmployeeForm();

    openEmployeeModal();

});

// ======================================================
// SAVE EMPLOYEE
// ======================================================

saveEmployeeBtn?.addEventListener("click",

async ()=>{

    const data = {

        id: employeeId.value,

        name: employeeName.value,

        email: employeeEmail.value,

        phone: employeePhone.value,

        address: employeeAddress.value,

        role: employeeRole.value,

        shift: employeeShift.value,

        joining_date: joiningDate.value,

        dob: employeeDOB.value,

        salary: employeeSalary.value,

        status: employeeStatus.value

    };

    showLoader();

    try{

        const result =
        await postData("/employees/save",data);

        if(result.success){

            showToast("Employee Saved");

            closeModal();

            loadEmployees();

            loadEmployeeStats();

        }

        else{

            showToast("Save Failed","red");

        }

    }

    catch(error){

        console.error(error);

    }

    hideLoader();

});

// ======================================================
// EDIT EMPLOYEE
// ======================================================

async function editEmployee(id){

    showLoader();

    try{

        const emp =
        await getData("/employees/" + id);

        employeeModalTitle.innerHTML =
        "Edit Employee";

        employeeId.value = emp.id;

        employeeName.value = emp.name;

        employeeEmail.value = emp.email;

        employeePhone.value = emp.phone;

        employeeAddress.value = emp.address;

        employeeRole.value = emp.role;

        employeeShift.value = emp.shift;

        joiningDate.value =
        emp.joining_date;

        employeeDOB.value =
        emp.dob;

        employeeSalary.value =
        emp.salary;

        employeeStatus.value =
        emp.status;

        openEmployeeModal();

    }

    catch(error){

        console.error(error);

    }

    hideLoader();

}

// ======================================================
// DELETE EMPLOYEE
// ======================================================

async function deleteEmployee(id){

    const confirmDelete =
    confirm("Delete this employee?");

    if(!confirmDelete){

        return;

    }

    showLoader();

    try{

        const result =
        await postData(

        "/employees/delete",

        {

            id:id

        });

        if(result.success){

            showToast(

            "Employee Deleted"

            );

            loadEmployees();

            loadEmployeeStats();

        }

        else{

            showToast(

            "Delete Failed",

            "red"

            );

        }

    }

    catch(error){

        console.error(error);

    }

    hideLoader();

}

// ======================================================
// VIEW EMPLOYEE
// ======================================================

async function viewEmployee(id){

    try{

        const emp =
        await getData("/employees/" + id);

        employeeDetails.innerHTML =

        `

        <div class="employee-profile">

            <img
            src="${emp.photo}"

            class="profile-image">

            <h2>

                ${emp.name}

            </h2>

            <p>

                ${emp.role}

            </p>

            <hr>

            <p>

                <strong>Email:</strong>

                ${emp.email}

            </p>

            <p>

                <strong>Phone:</strong>

                ${emp.phone}

            </p>

            <p>

                <strong>Salary:</strong>

                ₹${emp.salary}

            </p>

            <p>

                <strong>Status:</strong>

                ${emp.status}

            </p>

            <p>

                <strong>Shift:</strong>

                ${emp.shift}

            </p>

        </div>

        `;

    }

    catch(error){

        console.error(error);

    }

}

// ======================================================
// CLOSE EVENTS
// ======================================================

closeEmployeeModal?.addEventListener(

"click",

closeModal

);

cancelEmployeeBtn?.addEventListener(

"click",

closeModal

);

window.addEventListener("click",

function(event){

    if(event.target === employeeModal){

        closeModal();

    }

});
/* ==========================================================
   CafeSync POS
   employees.js
   Part C
   Attendance • Shift • Payroll • Performance
==========================================================*/

// ======================================================
// DOM ELEMENTS
// ======================================================

const attendanceTable =
document.getElementById("attendanceTable");

const shiftTable =
document.getElementById("shiftTable");

const announcementList =
document.getElementById("announcementList");

// Payroll

const totalPayroll =
document.getElementById("totalPayroll");

const averageSalary =
document.getElementById("averageSalary");

const newEmployees =
document.getElementById("newEmployees");

// Performance

const bestEmployee =
document.getElementById("bestEmployee");

const attendanceRate =
document.getElementById("attendanceRate");

const employeeRating =
document.getElementById("employeeRating");

// ======================================================
// LOAD ATTENDANCE
// ======================================================

async function loadAttendance(){

    try{

        const data =
        await getData("/employees/attendance");

        if(!data.length){

            attendanceTable.innerHTML =

            `<tr>

                <td colspan="4">

                    No Attendance Found

                </td>

            </tr>`;

            return;

        }

        let html="";

        data.forEach(emp=>{

            html +=

            `<tr>

                <td>${emp.name}</td>

                <td>${emp.check_in}</td>

                <td>${emp.check_out}</td>

                <td>

                    <span class="badge ${emp.status.toLowerCase()}">

                        ${emp.status}

                    </span>

                </td>

            </tr>`;

        });

        attendanceTable.innerHTML = html;

    }

    catch(error){

        console.error(error);

    }

}

// ======================================================
// LOAD SHIFTS
// ======================================================

async function loadShifts(){

    try{

        const shifts =
        await getData("/employees/shifts");

        if(!shifts.length){

            shiftTable.innerHTML =

            `<tr>

                <td colspan="4">

                    No Shift Data

                </td>

            </tr>`;

            return;

        }

        let html="";

        shifts.forEach(emp=>{

            html +=

            `<tr>

                <td>${emp.name}</td>

                <td>${emp.shift}</td>

                <td>${emp.start}</td>

                <td>${emp.end}</td>

            </tr>`;

        });

        shiftTable.innerHTML = html;

    }

    catch(error){

        console.error(error);

    }

}

// ======================================================
// PAYROLL
// ======================================================

async function loadPayroll(){

    try{

        const payroll =
        await getData("/employees/payroll");

        totalPayroll.textContent =
        "₹" + (payroll.total_payroll || 0);

        averageSalary.textContent =
        "₹" + (payroll.average_salary || 0);

        newEmployees.textContent =
        payroll.new_employees || 0;

    }

    catch(error){

        console.error(error);

    }

}

// ======================================================
// PERFORMANCE
// ======================================================

async function loadPerformance(){

    try{

        const perf =
        await getData("/employees/performance");

        bestEmployee.textContent =
        perf.best_employee || "-";

        attendanceRate.textContent =
        (perf.attendance_rate || 0) + "%";

        employeeRating.textContent =
        perf.average_rating || "0.0";

    }

    catch(error){

        console.error(error);

    }

}

// ======================================================
// ANNOUNCEMENTS
// ======================================================

async function loadAnnouncements(){

    try{

        const notices =
        await getData("/employees/announcements");

        if(!notices.length){

            announcementList.innerHTML =

            "<p>No announcements available.</p>";

            return;

        }

        let html="";

        notices.forEach(item=>{

            html +=

            `<div class="announcement-item">

                <h4>${item.title}</h4>

                <p>${item.message}</p>

                <small>${item.date}</small>

            </div>`;

        });

        announcementList.innerHTML = html;

    }

    catch(error){

        console.error(error);

    }

}

// ======================================================
// REFRESH EMPLOYEE DATA
// ======================================================

function refreshEmployeeModule(){

    loadAttendance();

    loadShifts();

    loadPayroll();

    loadPerformance();

    loadAnnouncements();

}

// ======================================================
// INITIALIZE
// ======================================================

document.addEventListener(

"DOMContentLoaded",

()=>{

    refreshEmployeeModule();

});
/* ==========================================================
   CafeSync POS
   employees.js
   Part D
   Search • Filters • Photo Upload • Refresh
========================================================== */

// ======================================================
// SEARCH EMPLOYEES
// ======================================================

function searchEmployees(keyword){

    keyword = keyword.toLowerCase();

    filteredEmployees = employees.filter(emp => {

        return (
            emp.name.toLowerCase().includes(keyword) ||
            emp.role.toLowerCase().includes(keyword) ||
            emp.phone.toLowerCase().includes(keyword) ||
            emp.email.toLowerCase().includes(keyword)
        );

    });

    renderEmployeeTable(filteredEmployees);

}

employeeSearch?.addEventListener("keyup", function(){

    searchEmployees(this.value);

});

// ======================================================
// FILTER EMPLOYEES
// ======================================================

function applyFilters(){

    const department = departmentFilter.value;
    const status = statusFilter.value;

    filteredEmployees = employees.filter(emp => {

        const deptMatch =
            !department || emp.role === department;

        const statusMatch =
            !status || emp.status === status;

        return deptMatch && statusMatch;

    });

    renderEmployeeTable(filteredEmployees);

}

filterEmployees?.addEventListener("click", applyFilters);

// ======================================================
// PHOTO UPLOAD PREVIEW
// ======================================================

const employeePhoto =
document.getElementById("employeePhoto");

employeePhoto?.addEventListener("change", function(){

    const file = this.files[0];

    if(!file) return;

    showToast("Photo selected successfully");

});

// ======================================================
// REFRESH BUTTON
// ======================================================

const refreshEmployees =
document.getElementById("refreshEmployees");

refreshEmployees?.addEventListener("click", ()=>{

    loadEmployeeStats();

    loadEmployees();

    refreshEmployeeModule();

    showToast("Employee data refreshed");

});

// ======================================================
// ESC KEY CLOSE MODAL
// ======================================================

document.addEventListener("keydown", function(e){

    if(e.key === "Escape"){

        closeModal();

    }

});

// ======================================================
// CLICK OUTSIDE MODAL
// ======================================================

window.addEventListener("click", function(e){

    if(e.target === employeeModal){

        closeModal();

    }

});

// ======================================================
// SORT EMPLOYEES
// ======================================================

function sortEmployees(field){

    filteredEmployees.sort((a,b)=>{

        if(a[field] < b[field]) return -1;

        if(a[field] > b[field]) return 1;

        return 0;

    });

    renderEmployeeTable(filteredEmployees);

}

// ======================================================
// RESET FILTERS
// ======================================================

function resetFilters(){

    departmentFilter.value = "";

    statusFilter.value = "";

    employeeSearch.value = "";

    filteredEmployees = [...employees];

    renderEmployeeTable(filteredEmployees);

}

// ======================================================
// OPTIONAL AUTO REFRESH
// ======================================================

// Refresh employee data every 5 minutes

setInterval(()=>{

    loadEmployeeStats();

    loadEmployees();

},300000);

/* ==========================================================
   CafeSync POS
   employees.js
   Part E
   Export • Import • Print • Final Initialization
========================================================== */

// ======================================================
// DOM ELEMENTS
// ======================================================

const exportEmployeesExcel =
document.getElementById("exportEmployeesExcel");

const exportEmployeesPDF =
document.getElementById("exportEmployeesPDF");

const printEmployees =
document.getElementById("printEmployees");

const importEmployees =
document.getElementById("importEmployees");

const employeeImportFile =
document.getElementById("employeeImportFile");

// ======================================================
// EXPORT EXCEL
// ======================================================

exportEmployeesExcel?.addEventListener("click",()=>{

    window.open(
        API + "/employees/export/excel",
        "_blank"
    );

});

// ======================================================
// EXPORT PDF
// ======================================================

exportEmployeesPDF?.addEventListener("click",()=>{

    window.open(
        API + "/employees/export/pdf",
        "_blank"
    );

});

// ======================================================
// PRINT
// ======================================================

printEmployees?.addEventListener("click",()=>{

    window.print();

});

// ======================================================
// IMPORT
// ======================================================

importEmployees?.addEventListener("click",()=>{

    employeeImportFile.click();

});

employeeImportFile?.addEventListener("change",

async function(){

    if(this.files.length === 0){

        return;

    }

    const formData = new FormData();

    formData.append(
        "file",
        this.files[0]
    );

    showLoader();

    try{

        const response =
        await fetch(API + "/employees/import",{

            method:"POST",

            body:formData

        });

        const result =
        await response.json();

        if(result.success){

            showToast(
                "Employees Imported Successfully"
            );

            loadEmployees();

            loadEmployeeStats();

        }

        else{

            showToast(
                result.message || "Import Failed",
                "red"
            );

        }

    }

    catch(error){

        console.error(error);

        showToast(
            "Import Error",
            "red"
        );

    }

    hideLoader();

});

// ======================================================
// KEYBOARD SHORTCUTS
// ======================================================

document.addEventListener("keydown",(e)=>{

    // Ctrl + N = Add Employee

    if(e.ctrlKey && e.key.toLowerCase()==="n"){

        e.preventDefault();

        addEmployeeBtn.click();

    }

    // Ctrl + P = Print

    if(e.ctrlKey && e.key.toLowerCase()==="p"){

        e.preventDefault();

        window.print();

    }

    // Ctrl + R = Refresh

    if(e.ctrlKey && e.key.toLowerCase()==="r"){

        e.preventDefault();

        loadEmployeeStats();

        loadEmployees();

        refreshEmployeeModule();

        showToast("Employee data refreshed");

    }

});

// ======================================================
// FINAL INITIALIZATION
// ======================================================

document.addEventListener("DOMContentLoaded",()=>{

    loadEmployeeStats();

    loadEmployees();

    refreshEmployeeModule();

    console.log("CafeSync Employee Module Loaded");

});