const tableBoard = document.getElementById("tableBoard");
const tableSummary = document.getElementById("tableSummary");
const dialog = document.getElementById("tableDialog");
const form = document.getElementById("tableForm");
const reservationDialog = document.getElementById("reservationDialog");
const reservationForm = document.getElementById("reservationForm");
let tables = [];
let editingTable = null;
let reservingTable = null;
let toastTimer;

function notify(message, error = false){
    const toast = document.getElementById("tableToast");
    toast.textContent = message;
    toast.classList.toggle("error", error);
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 3000);
}

async function api(path, options = {}){
    const response = await fetch(path, {
        credentials: "same-origin",
        headers: {"Content-Type": "application/json", ...(options.headers || {})},
        ...options
    });
    if(response.status === 401){ location.assign("/login"); throw new Error("Your session expired."); }
    const result = await response.json().catch(() => ({}));
    if(!response.ok || result.success === false) throw new Error(result.message || `Request failed (${response.status})`);
    return result;
}

async function loadTables(){
    tableBoard.innerHTML = '<div class="loading">Loading tables…</div>';
    try{
        tables = await api("/tables");
        if(!Array.isArray(tables)) throw new Error("The table list response was invalid.");
        renderSummary();
        renderTables();
    }catch(error){
        tableBoard.innerHTML = "";
        const message = document.createElement("div");
        message.className = "empty";
        message.textContent = error.message;
        tableBoard.appendChild(message);
        notify(error.message, true);
    }
}

function renderSummary(){
    const states = ["Available", "Occupied", "Reserved", "Cleaning"];
    const counts = Object.fromEntries(states.map(status => [status, tables.filter(table => table.status === status).length]));
    tableSummary.innerHTML = states.map(status => `<article class="summary-card ${status.toLowerCase()}"><span>${status}</span><strong>${counts[status]}</strong></article>`).join("");
}

function renderTables(){
    const query = document.getElementById("tableSearch").value.trim().toLowerCase();
    const shown = tables.filter(table => String(table.table_name).toLowerCase().includes(query));
    tableBoard.replaceChildren();
    if(!shown.length){
        const empty = document.createElement("div");
        empty.className = "empty";
        empty.textContent = query ? "No tables match your search." : "No tables yet. Add your first table to start the floor plan.";
        tableBoard.appendChild(empty);
        return;
    }
    shown.forEach(table => {
        const card = document.createElement("article");
        card.className = "table-card";
        const top = document.createElement("div");
        top.className = "table-card-top";
        const info = document.createElement("div");
        const name = document.createElement("h3");
        name.textContent = table.table_name;
        const capacity = document.createElement("div");
        capacity.className = "capacity";
        capacity.textContent = `${Number(table.capacity || 0)} seats`;
        info.append(name, capacity);
        const status = document.createElement("span");
        status.className = `status-pill ${String(table.status || "Available").toLowerCase()}`;
        status.textContent = table.status || "Available";
        top.append(info, status);
        card.appendChild(top);
        if(table.status === "Reserved"){
            const booking = document.createElement("div");
            booking.className = "reservation-detail";
            const guest = document.createElement("strong");
            guest.textContent = table.reservation_name || "Guest reservation";
            const detail = document.createElement("span");
            const date = table.reserved_for ? new Date(table.reserved_for).toLocaleString([], {dateStyle:"medium", timeStyle:"short"}) : "Time not set";
            detail.textContent = `${Number(table.reservation_guests || 0)} guests · ${date}${table.reservation_phone ? ` · ${table.reservation_phone}` : ""}`;
            booking.append(guest, detail);
            if(table.reservation_notes){
                const notes = document.createElement("span");
                notes.textContent = table.reservation_notes;
                booking.appendChild(notes);
            }
            card.appendChild(booking);
        }
        const actions = document.createElement("div");
        actions.className = "table-actions";
        const addAction = (label, handler, primary = false) => {
            const button = document.createElement("button");
            button.type = "button";
            button.textContent = label;
            if(primary) button.className = "seat";
            button.addEventListener("click", handler);
            actions.appendChild(button);
        };
        if(table.status === "Available"){
            addAction("Seat guests", () => seatTable(table), true);
            addAction("Reserve", () => openReservation(table));
        }else if(table.status === "Occupied"){
            addAction("Send to cleaning", () => setStatus(table.id, "Cleaning"), true);
        }else if(table.status === "Reserved"){
            addAction("Seat guests", () => seatTable(table), true);
            addAction("Edit booking", () => openReservation(table));
            addAction("Cancel reserve", () => cancelReservation(table.id));
        }else{
            addAction("Cleaning complete", () => setStatus(table.id, "Available"), true);
        }
        addAction("Edit", () => openDialog(table));
        card.appendChild(actions);
        tableBoard.appendChild(card);
    });
}

async function setStatus(id, status){
    try{
        await api(`/tables/${id}/status`, {method: "PUT", body: JSON.stringify({status})});
        notify(`Table updated to ${status.toLowerCase()}.`);
        await loadTables();
    }catch(error){ notify(error.message, true); }
}

async function seatTable(table){
    try{
        await api(`/tables/${table.id}/status`, {method:"PUT", body:JSON.stringify({status:"Occupied"})});
        location.assign(`/billing?table_id=${encodeURIComponent(table.id)}`);
    }catch(error){notify(error.message, true);}
}

function openReservation(table){
    reservingTable = table;
    reservationForm.reset();
    document.getElementById("reservationTitle").textContent = `Reserve ${table.table_name}`;
    document.getElementById("reservationGuests").max = Number(table.capacity || 4);
    document.getElementById("reservationGuests").value = table.reservation_guests || 2;
    document.getElementById("reservationName").value = table.reservation_name || "";
    document.getElementById("reservationPhone").value = table.reservation_phone || "";
    document.getElementById("reservationNotes").value = table.reservation_notes || "";
    const local = new Date(Date.now() + 60 * 60 * 1000);
    local.setMinutes(Math.ceil(local.getMinutes() / 15) * 15, 0, 0);
    const offset = local.getTimezoneOffset();
    document.getElementById("reservedFor").value = new Date(local.getTime() - offset * 60000).toISOString().slice(0, 16);
    if(table.reserved_for) document.getElementById("reservedFor").value = table.reserved_for.slice(0, 16);
    reservationDialog.hidden = false;
    document.getElementById("reservationName").focus();
}

function closeReservation(){reservationDialog.hidden = true; reservationForm.reset(); reservingTable = null;}

async function cancelReservation(id){
    try{
        await api(`/tables/${id}/cancel-reservation`, {method:"PUT", body:JSON.stringify({})});
        notify("Reservation cancelled.");
        await loadTables();
    }catch(error){notify(error.message, true);}
}

reservationForm.addEventListener("submit", async event => {
    event.preventDefault();
    if(!reservingTable) return;
    const payload = {
        name: document.getElementById("reservationName").value.trim(),
        phone: document.getElementById("reservationPhone").value.trim(),
        guests: Number(document.getElementById("reservationGuests").value),
        reserved_for: document.getElementById("reservedFor").value,
        notes: document.getElementById("reservationNotes").value.trim()
    };
    try{
        await api(`/tables/${reservingTable.id}/reserve`, {method:"PUT", body:JSON.stringify(payload)});
        closeReservation();
        notify("Reservation saved.");
        await loadTables();
    }catch(error){notify(error.message, true);}
});

function openDialog(table = null){
    editingTable = table;
    document.getElementById("tableDialogTitle").textContent = table ? "Edit table" : "Add a table";
    document.getElementById("tableName").value = table?.table_name || "";
    document.getElementById("tableCapacity").value = table?.capacity || 4;
    dialog.hidden = false;
    document.getElementById("tableName").focus();
}

function closeDialog(){dialog.hidden = true; form.reset(); editingTable = null;}

form.addEventListener("submit", async event => {
    event.preventDefault();
    const payload = {
        table_name: document.getElementById("tableName").value.trim(),
        capacity: Number(document.getElementById("tableCapacity").value)
    };
    try{
        await api(editingTable ? `/tables/${editingTable.id}` : "/tables", {
            method: editingTable ? "PUT" : "POST", body: JSON.stringify(payload)
        });
        closeDialog();
        notify(editingTable ? "Table details updated." : "Table added.");
        await loadTables();
    }catch(error){ notify(error.message, true); }
});

document.getElementById("addTable").addEventListener("click", () => openDialog());
document.getElementById("closeTableDialog").addEventListener("click", closeDialog);
document.getElementById("closeReservationDialog").addEventListener("click", closeReservation);
document.getElementById("refreshTables").addEventListener("click", loadTables);
document.getElementById("tableSearch").addEventListener("input", renderTables);
dialog.addEventListener("click", event => {if(event.target === dialog) closeDialog();});
reservationDialog.addEventListener("click", event => {if(event.target === reservationDialog) closeReservation();});
loadTables();
setInterval(loadTables, 20000);
