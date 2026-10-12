(function () {
  const api = "";
  let ingredients = [];
  let recipeLines = [];
  const $ = id => document.getElementById(id);
  const escapeHtml = value => String(value ?? "").replace(/[&<>\"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  async function call(url, options = {}) {
    const response = await fetch(api + url, {credentials: "same-origin", ...options, headers: {"Content-Type":"application/json", ...(options.headers || {})}});
    const body = await response.json();
    if (!response.ok || body.success === false) throw new Error(body.message || "Request failed");
    return body;
  }
  function fillIngredientSelect(id) {
    const select = $(id);
    const current = select.value;
    select.replaceChildren(new Option("Choose ingredient", ""));
    ingredients.filter(item => item.active).forEach(item => select.add(new Option(`${item.name} (${item.unit})`, item.id)));
    if ([...select.options].some(option => option.value === current)) select.value = current;
  }
  function renderIngredients() {
    const table = $("ingredientTable");
    table.replaceChildren();
    if (!ingredients.length) {
      table.innerHTML = '<tr><td colspan="5">No ingredients yet. Add ingredients above to start recipe tracking.</td></tr>';
      return;
    }
    ingredients.forEach(item => {
      const low = Number(item.current_stock) <= Number(item.low_stock_threshold);
      const row = document.createElement("tr");
      row.innerHTML = `<td>${escapeHtml(item.name)} <small>${escapeHtml(item.unit)}</small></td><td>${Number(item.current_stock).toFixed(3).replace(/\.?0+$/, "")}</td><td>${Number(item.low_stock_threshold).toFixed(3).replace(/\.?0+$/, "")}</td><td>₹${Number(item.unit_cost).toFixed(2)}</td><td><span class="status ${low ? "low" : "available"}">${low ? "Low" : "In stock"}</span></td>`;
      table.appendChild(row);
    });
  }
  async function loadIngredients() {
    try {
      const result = await call("/inventory/ingredients");
      ingredients = result.data || [];
      renderIngredients();
      ["movementIngredient", "receiptIngredient", "recipeIngredient"].forEach(fillIngredientSelect);
      await loadMovements();
    } catch (error) { $("ingredientTable").innerHTML = `<tr><td colspan="5">${escapeHtml(error.message)}</td></tr>`; }
  }
  async function loadMovements() {
    const table = $("ingredientMovementTable");
    try {
      const result = await call("/inventory/movements");
      table.replaceChildren();
      if (!result.data.length) { table.innerHTML = '<tr><td colspan="6">No ingredient movements recorded.</td></tr>'; return; }
      result.data.forEach(movement => {
        const row = document.createElement("tr");
        row.innerHTML = `<td>${escapeHtml(movement.created_at)}</td><td>${escapeHtml(movement.ingredient_name)}</td><td>${escapeHtml(movement.movement_type)}</td><td>${Number(movement.quantity_change) > 0 ? "+" : ""}${Number(movement.quantity_change)} ${escapeHtml(movement.unit)}</td><td>${escapeHtml(movement.reference || movement.notes || "—")}</td><td>${escapeHtml(movement.actor || "—")}</td>`;
        table.appendChild(row);
      });
    } catch (error) { table.innerHTML = `<tr><td colspan="6">${escapeHtml(error.message)}</td></tr>`; }
  }
  async function loadProductsIntoRecipe() {
    try {
      const result = await call("/inventory/products");
      const select = $("recipeProduct");
      select.replaceChildren(new Option("Choose menu item", ""));
      (result.data || []).forEach(product => select.add(new Option(product.name, product.id)));
    } catch (error) { console.error("Could not load recipe menu items", error); }
  }
  function renderRecipeLines() {
    const list = $("recipeLines");
    list.replaceChildren();
    recipeLines.forEach((line, index) => {
      const ingredient = ingredients.find(item => Number(item.id) === Number(line.ingredient_id));
      const row = document.createElement("div");
      row.className = "recipe-line";
      row.innerHTML = `<span>${escapeHtml(ingredient?.name || "Ingredient")} · ${Number(line.quantity)} ${escapeHtml(ingredient?.unit || "")}</span><button type="button" aria-label="Remove ingredient">Remove</button>`;
      row.querySelector("button").addEventListener("click", () => { recipeLines.splice(index, 1); renderRecipeLines(); });
      list.appendChild(row);
    });
    const estimated = recipeLines.reduce((sum, line) => {
      const ingredient = ingredients.find(item => Number(item.id) === Number(line.ingredient_id));
      return sum + Number(line.quantity) * Number(ingredient?.unit_cost || 0);
    }, 0);
    $("recipeCostEstimate").textContent = `Estimated ingredient cost: ₹${estimated.toFixed(2)} per serving`;
  }
  async function loadRecipe() {
    const productId = $("recipeProduct").value;
    recipeLines = [];
    if (!productId) { renderRecipeLines(); return; }
    try {
      const result = await call(`/inventory/products/${productId}/recipe`);
      recipeLines = (result.data?.items || []).map(item => ({ingredient_id: item.ingredient_id, quantity: Number(item.quantity)}));
      renderRecipeLines();
    } catch (error) { toast(error.message, "error"); }
  }
  function toast(message, type) {
    if (typeof showToast === "function") showToast(message, type);
    else window.alert(message);
  }
  $("ingredientForm").addEventListener("submit", async event => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    try { await call("/inventory/ingredients", {method:"POST", body:JSON.stringify(data)}); event.currentTarget.reset(); event.currentTarget.elements.unit.value = "g"; await loadIngredients(); toast("Ingredient added."); }
    catch (error) { toast(error.message, "error"); }
  });
  $("movementForm").addEventListener("submit", async event => {
    event.preventDefault();
    const id = $("movementIngredient").value;
    const type = $("movementType").value;
    let quantity = Number($("movementQuantity").value);
    if (type === "Waste") quantity *= -1;
    try { await call(`/inventory/ingredients/${id}/movement`, {method:"POST", body:JSON.stringify({type, quantity_change:quantity, notes:$("movementNotes").value})}); event.currentTarget.reset(); await loadIngredients(); toast("Stock movement saved."); }
    catch (error) { toast(error.message, "error"); }
  });
  $("receiptForm").addEventListener("submit", async event => {
    event.preventDefault();
    const item = {ingredient_id:Number($("receiptIngredient").value), quantity:Number($("receiptQuantity").value), unit_cost:Number($("receiptCost").value)};
    try {
      let supplierId = null;
      const supplierName = $("receiptSupplier").value.trim();
      if (supplierName) supplierId = (await call("/inventory/suppliers", {method:"POST", body:JSON.stringify({name:supplierName})})).data.id;
      await call("/inventory/receipts", {method:"POST", body:JSON.stringify({items:[item], reference:$("receiptReference").value, supplier_id:supplierId})});
      event.currentTarget.reset(); $("receiptCost").value = "0"; await loadIngredients(); toast("Purchase received and stock updated.");
    }
    catch (error) { toast(error.message, "error"); }
  });
  $("recipeProduct").addEventListener("change", loadRecipe);
  $("addRecipeLine").addEventListener("click", () => {
    const ingredientId = Number($("recipeIngredient").value);
    const quantity = Number($("recipeQuantity").value);
    if (!$("recipeProduct").value || !ingredientId || !Number.isFinite(quantity) || quantity <= 0) { toast("Choose a menu item and ingredient, then enter a quantity.", "error"); return; }
    if (recipeLines.some(line => Number(line.ingredient_id) === ingredientId)) { toast("That ingredient is already in the recipe.", "error"); return; }
    recipeLines.push({ingredient_id:ingredientId, quantity}); $("recipeQuantity").value = ""; renderRecipeLines();
  });
  $("recipeForm").addEventListener("submit", async event => {
    event.preventDefault();
    const productId = $("recipeProduct").value;
    if (!productId) return;
    try { await call(`/inventory/products/${productId}/recipe`, {method:"PUT", body:JSON.stringify({items:recipeLines})}); toast("Recipe saved. Future bills will use its ingredients."); }
    catch (error) { toast(error.message, "error"); }
  });
  loadIngredients();
  loadProductsIntoRecipe();
})();
