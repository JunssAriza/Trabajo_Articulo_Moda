const API_BASE_URL = "http://127.0.0.1:8000";
const PRENDAS_URL = `${API_BASE_URL}/prendas`;

const productGrid = document.querySelector("#product-grid");
const searchInput = document.querySelector("#search-input");
const statusFilter = document.querySelector("#status-filter");
const notice = document.querySelector("#notice");
const dialog = document.querySelector("#item-dialog");
const form = document.querySelector("#item-form");
const formError = document.querySelector("#form-error");
const saveButton = document.querySelector("#save-item-button");
const items = [];
let editingId = null;

document.querySelector("#today-label").textContent = new Intl.DateTimeFormat("es-CO", {
  day: "numeric",
  month: "long",
  year: "numeric",
}).format(new Date());

function getId(item) {
  return item._id ?? item.id;
}

function formatPrice(price) {
  return new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  }).format(price);
}

function showNotice(message) {
  notice.textContent = message;
  notice.hidden = false;
}

function clearNotice() {
  notice.textContent = "";
  notice.hidden = true;
}

async function request(url, options = {}) {
  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new Error(
      `No se pudo conectar con la API en ${API_BASE_URL}. Comprueba que el backend esté iniciado.`,
    );
  }

  const body = await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body?.detail;
    const message = Array.isArray(detail)
      ? detail.map((error) => error.msg).join(" ")
      : detail || `La solicitud falló (HTTP ${response.status}).`;
    throw new Error(message);
  }
  return body;
}

function updateConnection(connected) {
  const dot = document.querySelector("#connection-dot");
  dot.classList.toggle("connected", connected);
  dot.classList.toggle("failed", !connected);
  document.querySelector("#connection-label").textContent = connected
    ? "API conectada"
    : "API no disponible";
}

function updateStats() {
  const available = items.filter((item) => item.en_exhibicion).length;
  document.querySelector("#total-count").textContent = items.length;
  document.querySelector("#available-count").textContent = available;
  document.querySelector("#unavailable-count").textContent = items.length - available;
}

function createActionButton(label, symbol, className, onClick) {
  const button = document.createElement("button");
  button.className = `icon-button ${className}`;
  button.type = "button";
  button.setAttribute("aria-label", label);
  button.title = label;
  button.textContent = symbol;
  button.addEventListener("click", onClick);
  return button;
}

function createProductCard(item) {
  const card = document.createElement("article");
  card.className = "product-card";

  const art = document.createElement("div");
  art.className = "product-art";
  art.setAttribute("aria-hidden", "true");
  const garment = document.createElement("span");
  garment.className = "garment";
  garment.textContent = "✳";
  art.append(garment);

  if (item.image_url) {
    const image = document.createElement("img");
    image.className = "product-image";
    image.src = item.image_url;
    image.alt = item.prenda;
    image.addEventListener("error", () => image.remove(), { once: true });
    art.append(image);
  }

  const status = document.createElement("span");
  status.className = `product-status${item.en_exhibicion ? "" : " unavailable"}`;
  status.textContent = item.en_exhibicion ? "En exhibición" : "Fuera de exhibición";
  art.append(status);

  const details = document.createElement("div");
  details.className = "product-details";
  const titleRow = document.createElement("div");
  titleRow.className = "product-title-row";
  const name = document.createElement("h3");
  name.className = "product-name";
  name.textContent = item.prenda;
  titleRow.append(name);

  const size = document.createElement("p");
  size.className = "product-size";
  size.textContent = `Talla ${item.talla}`;

  const footer = document.createElement("div");
  footer.className = "product-footer";
  const price = document.createElement("p");
  price.className = "product-price";
  price.textContent = formatPrice(item.precio);

  const actions = document.createElement("div");
  actions.className = "product-actions";
  actions.append(
    createActionButton("Editar prenda", "✎", "edit-button", () => openDialog(item)),
    createActionButton("Eliminar prenda", "⌫", "delete-button", () => deleteItem(item)),
  );
  footer.append(price, actions);
  details.append(titleRow, size, footer);
  card.append(art, details);
  return card;
}

function renderItems() {
  const query = searchInput.value.trim().toLocaleLowerCase("es");
  const filter = statusFilter.value;
  const visibleItems = items.filter((item) => {
    const matchesText = `${item.prenda} ${item.talla}`.toLocaleLowerCase("es").includes(query);
    const matchesStatus =
      filter === "all" ||
      (filter === "available" && item.en_exhibicion) ||
      (filter === "unavailable" && !item.en_exhibicion);
    return matchesText && matchesStatus;
  });

  productGrid.replaceChildren();
  document.querySelector("#result-count").textContent =
    `${visibleItems.length} ${visibleItems.length === 1 ? "prenda" : "prendas"}`;

  if (visibleItems.length === 0) {
    const emptyState = document.createElement("div");
    emptyState.className = "empty-state";
    const title = document.createElement("strong");
    const message = document.createElement("p");
    if (items.length === 0) {
      title.textContent = "Tu colección empieza aquí";
      message.textContent = "Agrega la primera prenda para verla en tu inventario.";
    } else {
      title.textContent = "No encontramos prendas";
      message.textContent = "Prueba con otra búsqueda o cambia el filtro.";
    }
    emptyState.append(title, message);
    productGrid.append(emptyState);
    return;
  }

  productGrid.append(...visibleItems.map(createProductCard));
}

async function loadItems() {
  productGrid.replaceChildren();
  const loading = document.createElement("div");
  loading.className = "loading-state";
  loading.textContent = "Cargando tu colección…";
  productGrid.append(loading);

  try {
    const result = await request(PRENDAS_URL);
    items.splice(0, items.length, ...result);
    updateConnection(true);
    clearNotice();
    updateStats();
    renderItems();
  } catch (error) {
    updateConnection(false);
    updateStats();
    showNotice(error.message);
    renderItems();
  }
}

function openDialog(item = null) {
  editingId = item ? getId(item) : null;
  form.reset();
  form.elements.en_exhibicion.checked = true;
  formError.hidden = true;
  formError.textContent = "";
  document.querySelector("#dialog-title").textContent = item ? "Editar prenda" : "Agregar prenda";
  saveButton.textContent = item ? "Guardar cambios" : "Guardar prenda";

  if (item) {
    form.elements.prenda.value = item.prenda;
    form.elements.talla.value = item.talla;
    form.elements.precio.value = item.precio;
    form.elements.en_exhibicion.checked = item.en_exhibicion;
    form.elements.image_url.value = item.image_url ?? "";
  }
  dialog.showModal();
  form.elements.prenda.focus();
}

function closeDialog() {
  dialog.close();
}

async function saveItem(event) {
  event.preventDefault();
  formError.hidden = true;
  saveButton.disabled = true;

  const formData = new FormData(form);
  const item = {
    prenda: formData.get("prenda").trim(),
    talla: formData.get("talla").trim(),
    precio: Number(formData.get("precio")),
    en_exhibicion: formData.has("en_exhibicion"),
    image_url: formData.get("image_url").trim() || null,
  };
  const url = editingId ? `${PRENDAS_URL}/${encodeURIComponent(editingId)}` : PRENDAS_URL;

  try {
    await request(url, { method: editingId ? "PUT" : "POST", body: JSON.stringify(item) });
    closeDialog();
    await loadItems();
  } catch (error) {
    formError.textContent = error.message;
    formError.hidden = false;
  } finally {
    saveButton.disabled = false;
  }
}

async function deleteItem(item) {
  if (!window.confirm(`¿Eliminar "${item.prenda}" de tu inventario?`)) return;
  try {
    await request(`${PRENDAS_URL}/${encodeURIComponent(getId(item))}`, { method: "DELETE" });
    await loadItems();
  } catch (error) {
    showNotice(`No se pudo eliminar la prenda. ${error.message}`);
  }
}

document.querySelector("#add-item-button").addEventListener("click", () => openDialog());
document.querySelector("#close-dialog-button").addEventListener("click", closeDialog);
document.querySelector("#cancel-dialog-button").addEventListener("click", closeDialog);
form.addEventListener("submit", saveItem);
searchInput.addEventListener("input", renderItems);
statusFilter.addEventListener("change", renderItems);

loadItems();