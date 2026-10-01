const $ = (id) => document.getElementById(id);
const money = (n) => new Intl.NumberFormat('en-IN', {style:'currency',currency:'INR',maximumFractionDigits:0}).format(Number(n)||0);
const safe = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dateLabel = (value) => { if (!value) return '—'; const d = new Date(String(value).replace(' ','T')); return Number.isNaN(d.getTime()) ? safe(value) : d.toLocaleTimeString('en-IN',{hour:'numeric',minute:'2-digit'}); };

async function getJson(url) { const r = await fetch(url,{credentials:'same-origin',headers:{Accept:'application/json'}}); if (!r.ok) throw new Error(`${url}: ${r.status}`); return r.json(); }

function drawSales(days) {
  const rows = [...(days || [])].reverse();
  const vals = rows.map(d => Number(d.revenue)||0);
  const max = Math.max(1,...vals);
  $('axisTop').textContent = Math.round(max).toLocaleString('en-IN');
  $('axisMid').textContent = Math.round(max/2).toLocaleString('en-IN');
  $('salesBars').innerHTML = rows.length ? rows.map((d,i) => {
    const label = new Date(`${d.sales_date}T12:00:00`).toLocaleDateString('en-IN',{weekday:'short'});
    const height = Math.max(4, vals[i]/max*100);
    const today = i===rows.length-1;
    return `<div class="bar-slot" title="${safe(label)} · ${money(vals[i])}"><div class="bar${today?' today':''}" style="height:${height}%"></div><span>${safe(label)}</span></div>`;
  }).join('') : '<div class="empty-stock">Sales will appear here once orders are paid.</div>';
}

function drawOrders(orders) {
  const host = $('recentOrders');
  if (!orders?.length) { host.innerHTML='<tr><td colspan="5" class="loading-row">No orders yet. Start with a new order.</td></tr>'; return; }
  host.innerHTML = orders.slice(0,6).map(o => {
    const status = String(o.order_status||'Pending').toLowerCase();
    const payment = String(o.payment_method||'Unpaid');
    return `<tr><td class="order-id">#${safe(o.id)}</td><td>${dateLabel(o.created_at)}</td><td class="pay-method">${safe(payment)}</td><td><span class="status ${safe(status)}">${safe(o.order_status||'Pending')}</span></td><td class="align-right">${money(o.total)}</td></tr>`;
  }).join('');
}

function drawStock(items) {
  $('lowStockCount').textContent = items.length;
  $('stockDot').style.display = items.length ? 'block' : 'none';
  const host = $('stockList');
  host.innerHTML = items.length ? items.slice(0,4).map(x => `<div class="stock-row"><span class="stock-icon"><i class="fa-solid fa-triangle-exclamation"></i></span><span class="stock-name">${safe(x.name)}<small>Minimum ${safe(x.min_stock)} ${safe(x.unit||'units')}</small></span><span class="stock-level">${safe(x.stock)} left</span></div>`).join('') : '<div class="empty-stock"><i class="fa-solid fa-circle-check"></i> Everything is stocked up.</div>';
}

function drawTables(tables) {
  const busy = tables.filter(t=>String(t.status).toLowerCase()!=='available').length;
  $('occupiedTables').textContent=busy; $('freeTables').textContent=tables.length-busy;
  $('tableGrid').innerHTML=tables.length ? tables.slice(0,12).map(t=>`<div class="table-chip${String(t.status).toLowerCase()==='available'?'':' busy'}" title="${safe(t.status)} · ${safe(t.capacity||'')} seats">${safe(t.table_name||`T${t.id}`)}</div>`).join('') : '<span class="muted">No tables configured</span>';
}

async function refreshDashboard() {
  $('refreshBtn').classList.add('busy');
  const [summary, recent, trend, kitchen, stock, tables] = await Promise.allSettled([
    getJson('/dashboard/overview'), getJson('/dashboard/recent-orders'), getJson('/dashboard/sales-trend'),
    getJson('/dashboard/kitchen'), getJson('/dashboard/low-stock'), getJson('/tables')
  ]);
  if (summary.status==='fulfilled') {
    const s=summary.value;
    $('todaySales').textContent=money(s.today_sales); $('todayOrders').textContent=s.today_orders||0; $('avgOrder').textContent=money(s.average_order);
  }
  if (recent.status==='fulfilled') drawOrders(recent.value.recent_orders||[]);
  if (trend.status==='fulfilled') drawSales(trend.value);
  if (kitchen.status==='fulfilled') {
    const k=kitchen.value, active=(Number(k.pending)||0)+(Number(k.preparing)||0);
    $('kitchenCount').textContent=active; $('pendingCount').textContent=k.pending||0;
    $('preparingCount').textContent=k.preparing||0; $('readyCount').textContent=k.ready||0;
    $('kitchenReady').textContent=`${k.ready||0} ready`; $('navPending').textContent=active;
  }
  if (stock.status==='fulfilled') drawStock(stock.value);
  if (tables.status==='fulfilled') drawTables(tables.value);
  $('updatedAt').textContent=`Updated ${new Date().toLocaleTimeString('en-IN',{hour:'numeric',minute:'2-digit'})}`;
  $('refreshBtn').classList.remove('busy');
}

const now=new Date(); $('todayDate').textContent=now.toLocaleDateString('en-IN',{weekday:'short',day:'numeric',month:'short',year:'numeric'});
$('refreshBtn').addEventListener('click',refreshDashboard);
$('menuToggle').addEventListener('click',()=>{$('sidebar').classList.add('open');$('mobileScrim').classList.add('show');});
$('mobileScrim').addEventListener('click',()=>{$('sidebar').classList.remove('open');$('mobileScrim').classList.remove('show');});
$('logoutBtn').addEventListener('click',async e=>{e.preventDefault();try{await fetch('/logout',{method:'POST',credentials:'same-origin'});}finally{location.href='/login';}});
document.addEventListener('keydown',e=>{if(e.key==='F2'){e.preventDefault();location.href='/billing';}});
refreshDashboard();
setInterval(refreshDashboard,60000);
