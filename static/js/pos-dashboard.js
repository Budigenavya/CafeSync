const $ = (id) => document.getElementById(id);
const money = (n) => new Intl.NumberFormat('en-IN', {style:'currency',currency:'INR',maximumFractionDigits:0}).format(Number(n)||0);
const safe = (value) => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const dateLabel = (value) => { if (!value) return '—'; const d = new Date(String(value).replace(' ','T')); return Number.isNaN(d.getTime()) ? safe(value) : d.toLocaleTimeString('en-IN',{hour:'numeric',minute:'2-digit'}); };

async function getJson(url) { const r = await fetch(url,{credentials:'same-origin',headers:{Accept:'application/json'}}); if (!r.ok) throw new Error(`${url}: ${r.status}`); return r.json(); }

function localBusinessDate() {
  return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
}

function drawSalesStatistics(data) {
  $('statsSales').textContent=money(data.sales);
  $('statsOrderCount').textContent=`${data.successful_orders||0} successful orders`;
  $('statsOrders').textContent=data.total_orders||0;
  $('cancelledCount').textContent=data.audit?.cancelled||0;
  $('discountedCount').textContent=data.audit?.discounted_bills||0;
  const payments=Object.entries(data.payment_methods||{}).sort((a,b)=>b[1]-a[1]);
  $('paymentBreakdown').innerHTML=payments.length?payments.map(([name,amount],i)=>`<div class="payment-line"><span><i class="payment-dot payment-dot-${i%4}"></i>${safe(name)}</span><b>${money(amount)} <small>${data.sales?Math.round(amount/data.sales*100):0}%</small></b></div>`).join(''):'<div class="stats-empty">No paid payments recorded.</div>';
  const bars=data.hourly||[], max=Math.max(1,...bars.map(b=>(Number(b['Dine In'])||0)+(Number(b.Parcel)||0)+(Number(b.Delivery)||0)));
  $('channelChart').innerHTML=bars.length?bars.map(b=>{const dine=Number(b['Dine In'])||0,parcel=Number(b.Parcel)||0,delivery=Number(b.Delivery)||0,total=dine+parcel+delivery;return `<div class="channel-bar-slot" title="${safe(b.label)} · ${money(total)}"><div class="channel-bar-stack"><i class="stack-delivery" style="height:${delivery/max*100}%"></i><i class="stack-parcel" style="height:${parcel/max*100}%"></i><i class="stack-dine" style="height:${dine/max*100}%"></i></div><span>${safe(b.label.split('–')[0])}</span></div>`}).join(''):'<div class="stats-empty">No paid sales for this date.</div>';
  const channels=data.channels||{};
  $('channelCards').innerHTML=['Dine In','Parcel','Delivery'].map((name,i)=>{const channel=channels[name]||{};return `<article class="panel channel-card"><span class="channel-card-icon channel-color-${i}"><i class="fa-solid ${['fa-utensils','fa-bag-shopping','fa-motorcycle'][i]}"></i></span><div><b>${name}</b><small>${channel.orders||0} orders</small></div><strong>${money(channel.sales)}</strong></article>`}).join('');
  const items=data.top_items||[];
  $('topItems').innerHTML=items.length?items.map((item,i)=>`<div class="top-item-row"><span class="item-rank">${i+1}</span><span class="top-item-name">${safe(item.name)}<small>${safe(item.quantity)} sold</small></span><b>${money(item.sales)}</b></div>`).join(''):'<div class="stats-empty">No paid items for this date.</div>';
}

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
    const orderStatus = o.order_status || o.status || 'Pending';
    const status = String(orderStatus).toLowerCase();
    const payment = String(o.payment_method||'Unpaid');
    return `<tr><td class="order-id">#${safe(o.id)}</td><td>${dateLabel(o.created_at)}</td><td class="pay-method">${safe(payment)}</td><td><span class="status ${safe(status)}">${safe(orderStatus)}</span></td><td class="align-right">${money(o.total)}</td></tr>`;
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

const syncTimes = {pos: null, orders: null};
function setSyncState(id, ok, timestamp) {
  const chip = $(id);
  if (ok) syncTimes[id === 'posSync' ? 'pos' : 'orders'] = timestamp || Date.now();
  const last = syncTimes[id === 'posSync' ? 'pos' : 'orders'];
  chip.classList.toggle('sync-error', !ok);
  chip.classList.toggle('sync-ok', ok);
  const label = chip.querySelector('span');
  const ago = last ? Math.floor((Date.now() - last) / 60000) : null;
  const ageLabel = ago === null ? '' : ago < 1 ? 'just now' : `${ago} min ago`;
  label.textContent = ok
    ? `${id === 'posSync' ? 'POS' : 'Orders'} synced ${ageLabel}`
    : last ? `${id === 'posSync' ? 'POS' : 'Orders'} sync delayed · ${ageLabel}` : `${id === 'posSync' ? 'POS' : 'Orders'} sync failed`;
  const icon = chip.querySelector('i');
  icon.className = `fa-solid ${ok ? 'fa-circle-check' : 'fa-triangle-exclamation'}`;
}

async function refreshDashboard() {
  $('refreshBtn').classList.add('busy');
  const [summary, recent, trend, kitchen, stock, tables] = await Promise.allSettled([
    getJson('/dashboard/overview'), getJson('/dashboard/recent-orders'), getJson('/dashboard/sales-trend'),
    getJson('/dashboard/kitchen'), getJson('/dashboard/low-stock'), getJson('/tables')
  ]);
  const statsDate=$('salesDate').value||localBusinessDate();
  let statsOk = false;
  try { drawSalesStatistics(await getJson(`/dashboard/sales-statistics?date=${encodeURIComponent(statsDate)}`)); statsOk = true; }
  catch(error) { $('paymentBreakdown').innerHTML='<span class="muted">Sales statistics could not be loaded.</span>'; $('channelChart').innerHTML='<div class="stats-empty">Could not load chart data.</div>'; }
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
  setSyncState('posSync', summary.status==='fulfilled' && statsOk);
  setSyncState('ordersSync', recent.status==='fulfilled' && kitchen.status==='fulfilled');
  $('updatedAt').textContent=`Updated ${new Date().toLocaleTimeString('en-IN',{hour:'numeric',minute:'2-digit'})}`;
  $('refreshBtn').classList.remove('busy');
}

const now=new Date(); $('todayDate').textContent=now.toLocaleDateString('en-IN',{weekday:'short',day:'numeric',month:'short',year:'numeric'});
$('salesDate').value=localBusinessDate();
$('salesDate').addEventListener('change',()=>refreshDashboard());
$('refreshBtn').addEventListener('click',refreshDashboard);
$('menuToggle').addEventListener('click',()=>{$('sidebar').classList.add('open');$('mobileScrim').classList.add('show');});
$('mobileScrim').addEventListener('click',()=>{$('sidebar').classList.remove('open');$('mobileScrim').classList.remove('show');});
$('logoutBtn').addEventListener('click',async e=>{e.preventDefault();try{await fetch('/logout',{method:'POST',credentials:'same-origin'});}finally{location.href='/login';}});
document.addEventListener('keydown',e=>{if(e.key==='F2'){e.preventDefault();location.href='/billing';}});
refreshDashboard();
setInterval(refreshDashboard,60000);
