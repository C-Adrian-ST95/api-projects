'use strict';

// Esta aplicación utiliza rutas relativas: página y API comparten el mismo origen.
// El JWT vive solamente en memoria. Se descarta al cerrar o recargar la página.
let token = null;
let usuario = null;
let productos = [];
let productoActivo = null;
let tipoModal = 'producto';
let busy = false;

const $ = id => document.getElementById(id);
const moneda = new Intl.NumberFormat('es-PE', { style: 'currency', currency: 'PEN' });
const numero = new Intl.NumberFormat('es-PE');

function mensajeError(payload, estado) {
  if (typeof payload?.detail === 'string') return payload.detail;
  if (Array.isArray(payload?.detail)) return payload.detail.map(x => x.msg || 'Dato inválido').join('; ');
  return `La solicitud falló (HTTP ${estado}).`;
}

async function api(ruta, opciones = {}) {
  const headers = new Headers(opciones.headers || {});
  if (token) headers.set('Authorization', `Bearer ${token}`);
  let body = opciones.body;
  if (body !== undefined && !(body instanceof URLSearchParams) && !(body instanceof FormData) && typeof body !== 'string') {
    headers.set('Content-Type', 'application/json');
    body = JSON.stringify(body);
  }
  const respuesta = await fetch(ruta, { ...opciones, headers, body, cache: 'no-store' });
  const payload = respuesta.status === 204 ? null : await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    if (respuesta.status === 401 && ruta !== '/auth/token') cerrarSesion('Tu sesión venció o ya no es válida.');
    throw new Error(mensajeError(payload, respuesta.status));
  }
  return payload;
}

function mostrarAviso(texto, error = false) {
  const t = $('toast');
  t.textContent = texto;
  t.classList.toggle('error', error);
  t.hidden = false;
  clearTimeout(mostrarAviso.timeoutId);
  mostrarAviso.timeoutId = setTimeout(() => { t.hidden = true; }, 4300);
}

function cerrarSesion(aviso = '') {
  token = null;
  usuario = null;
  productos = [];
  $('app-screen').hidden = true;
  $('login-screen').hidden = false;
  $('modal-overlay').hidden = true;
  $('password').value = '';
  $('login-error').hidden = true;
  if (aviso) mostrarAviso(aviso, true);
}

async function iniciarSesion(evento) {
  evento.preventDefault();
  const boton = $('login-submit');
  const error = $('login-error');
  error.hidden = true;
  boton.disabled = true;
  boton.textContent = 'Comprobando credenciales…';
  try {
    const formulario = new URLSearchParams({
      username: $('username').value.trim(),
      password: $('password').value
    });
    const datos = await api('/auth/token', { method: 'POST', body: formulario });
    token = datos.access_token;
    usuario = await api('/auth/me');
    $('user-chip').textContent = `${usuario.username} · ${usuario.rol}`;
    $('new-product').hidden = usuario.rol !== 'admin';
    $('login-screen').hidden = true;
    $('app-screen').hidden = false;
    $('password').value = '';
    await cargarDatos();
  } catch (e) {
    if (!usuario) token = null;
    error.textContent = e.message || 'No se pudo iniciar sesión.';
    error.hidden = false;
  } finally {
    boton.disabled = false;
    boton.textContent = 'Entrar al inventario →';
  }
}

async function cargarDatos() {
  if (!token) return;
  $('refresh-button').disabled = true;
  $('items-status').textContent = 'Consultando productos…';
  try {
    const [lista, reporte] = await Promise.all([
      api('/productos'),
      api('/reportes/inventario')
    ]);
    if (!Array.isArray(lista)) throw new Error('La API no devolvió una lista de productos.');
    productos = lista;
    $('stat-total').textContent = numero.format(reporte.total_productos);
    $('stat-units').textContent = numero.format(reporte.unidades_disponibles);
    $('stat-price').textContent = reporte.precio_promedio === null ? '—' : moneda.format(reporte.precio_promedio);
    renderProductos();
  } catch (e) {
    $('items-status').textContent = 'No se pudieron cargar los datos.';
    mostrarAviso(e.message, true);
  } finally {
    $('refresh-button').disabled = false;
  }
}

function botonAccion(texto, clase, handler) {
  const b = document.createElement('button');
  b.type = 'button';
  b.className = `small-btn ${clase || ''}`;
  b.textContent = texto;
  b.addEventListener('click', handler);
  return b;
}

function texto(tag, clase, contenido) {
  const el = document.createElement(tag);
  if (clase) el.className = clase;
  el.textContent = String(contenido);
  return el;
}

function renderProductos() {
  const busqueda = $('search-input').value.trim().toLocaleLowerCase('es');
  const orden = $('sort-select').value;
  const lista = productos.filter(p =>
    p.nombre.toLocaleLowerCase('es').includes(busqueda) || String(p.id).includes(busqueda)
  );
  lista.sort((a, b) => {
    if (orden === 'stock') return a.stock - b.stock || a.id - b.id;
    if (orden === 'precio') return b.precio - a.precio || a.id - b.id;
    return a.nombre.localeCompare(b.nombre, 'es') || a.id - b.id;
  });
  $('items-status').textContent = `${numero.format(lista.length)} de ${numero.format(productos.length)} productos`;
  const contenedor = $('product-list');
  contenedor.replaceChildren();
  if (!lista.length) {
    const vacio = texto('div', 'empty-state', '');
    vacio.append(texto('strong', '', 'No se encontraron productos'));
    vacio.append(texto('span', '', 'Prueba otra búsqueda o registra un producto.'));
    contenedor.append(vacio);
    return;
  }
  for (const p of lista) {
    const tarjeta = texto('article', 'product-card', '');
    const cabecera = texto('div', 'product-head', '');
    cabecera.append(texto('div', 'product-symbol', '▣'));
    const titulo = texto('div', 'product-title', '');
    titulo.append(texto('h3', '', p.nombre), texto('small', '', `Código #${p.id}`));
    cabecera.append(titulo);
    const claseStock = p.stock === 0 ? 'empty' : p.stock < 20 ? 'low' : '';
    cabecera.append(texto('span', `stock-pill ${claseStock}`, p.stock === 0 ? 'Agotado' : p.stock < 20 ? 'Stock bajo' : 'Disponible'));
    const valores = texto('div', 'product-values', '');
    const precio = texto('div', '', '');
    precio.append(texto('span', '', 'Precio unitario'), texto('strong', '', moneda.format(p.precio)));
    const stock = texto('div', '', '');
    stock.append(texto('span', '', 'Existencias'), texto('strong', '', numero.format(p.stock)));
    valores.append(precio, stock);
    tarjeta.append(cabecera, valores);
    if (usuario?.rol === 'admin') {
      const acciones = texto('div', 'product-actions', '');
      acciones.append(botonAccion('Editar', '', () => abrirProducto(p)));
      acciones.append(botonAccion('Registrar salida', '', () => abrirSalida(p)));
      acciones.append(botonAccion('Eliminar', 'danger', () => borrarProducto(p)));
      tarjeta.append(acciones);
    }
    contenedor.append(tarjeta);
  }
}

function cerrarModal() {
  if (busy) return;
  $('modal-overlay').hidden = true;
}

function abrirProducto(p = null) {
  if (usuario?.rol !== 'admin') return;
  productoActivo = p;
  tipoModal = 'producto';
  $('product-form').hidden = false;
  $('stock-form').hidden = true;
  $('modal-title').textContent = p ? `Editar producto #${p.id}` : 'Nuevo producto';
  $('product-name').value = p?.nombre ?? '';
  $('product-price').value = p?.precio ?? '';
  $('product-stock').value = p?.stock ?? '';
  $('product-error').hidden = true;
  $('modal-overlay').hidden = false;
  $('product-name').focus();
}

function abrirSalida(p) {
  if (usuario?.rol !== 'admin') return;
  productoActivo = p;
  tipoModal = 'salida';
  $('product-form').hidden = true;
  $('stock-form').hidden = false;
  $('modal-title').textContent = 'Registrar salida';
  $('stock-details').textContent = `${p.nombre} · Stock disponible: ${numero.format(p.stock)}`;
  $('stock-quantity').value = '';
  $('stock-quantity').max = String(p.stock);
  $('stock-error').hidden = true;
  $('modal-overlay').hidden = false;
  $('stock-quantity').focus();
}

async function guardarProducto(e) {
  e.preventDefault();
  if (busy) return;
  const nombre = $('product-name').value.trim();
  const precio = Number($('product-price').value);
  const stock = Number($('product-stock').value);
  const error = $('product-error');
  error.hidden = true;
  if (nombre.length < 2 || !Number.isFinite(precio) || precio <= 0 || !Number.isInteger(stock) || stock < 0) {
    error.textContent = 'Revisa el nombre, el precio y el stock.';
    error.hidden = false;
    return;
  }
  busy = true;
  $('product-save').disabled = true;
  try {
    const ruta = productoActivo ? `/productos/${productoActivo.id}` : '/productos';
    await api(ruta, {
      method: productoActivo ? 'PATCH' : 'POST',
      body: { nombre, precio, stock }
    });
    mostrarAviso(productoActivo ? 'Producto actualizado correctamente.' : 'Producto creado correctamente.');
    busy = false;
    cerrarModal();
    await cargarDatos();
  } catch (ex) {
    error.textContent = ex.message;
    error.hidden = false;
  } finally {
    busy = false;
    $('product-save').disabled = false;
  }
}

async function guardarSalida(e) {
  e.preventDefault();
  if (busy || !productoActivo) return;
  const cantidad = Number($('stock-quantity').value);
  const error = $('stock-error');
  error.hidden = true;
  if (!Number.isInteger(cantidad) || cantidad < 1 || cantidad > productoActivo.stock) {
    error.textContent = 'Ingresa una cantidad entera dentro del stock disponible.';
    error.hidden = false;
    return;
  }
  busy = true;
  $('stock-save').disabled = true;
  try {
    await api(`/productos/${productoActivo.id}/salidas`, { method: 'POST', body: { cantidad } });
    busy = false;
    cerrarModal();
    mostrarAviso(`Salida de ${cantidad} unidades registrada.`);
    await cargarDatos();
  } catch (ex) {
    error.textContent = ex.message;
    error.hidden = false;
  } finally {
    busy = false;
    $('stock-save').disabled = false;
  }
}

async function borrarProducto(p) {
  if (usuario?.rol !== 'admin') return;
  // En PostgreSQL, una clave foránea puede impedir borrar productos con movimientos.
  if (!window.confirm(`¿Eliminar "${p.nombre}" (ID ${p.id})? Esta acción no se puede deshacer.`)) return;
  try {
    await api(`/productos/${p.id}`, { method: 'DELETE' });
    mostrarAviso('Producto eliminado.');
    await cargarDatos();
  } catch (e) {
    mostrarAviso(e.message + ' Si tiene movimientos históricos, conserva el producto o implementa una baja lógica.', true);
  }
}

$('login-form').addEventListener('submit', iniciarSesion);
$('logout-button').addEventListener('click', () => cerrarSesion());
$('refresh-button').addEventListener('click', cargarDatos);
$('new-product').addEventListener('click', () => abrirProducto());
$('search-input').addEventListener('input', renderProductos);
$('sort-select').addEventListener('change', renderProductos);
$('product-form').addEventListener('submit', guardarProducto);
$('stock-form').addEventListener('submit', guardarSalida);
$('modal-close').addEventListener('click', cerrarModal);
$('product-cancel').addEventListener('click', cerrarModal);
$('stock-cancel').addEventListener('click', cerrarModal);
$('modal-overlay').addEventListener('click', e => { if (e.target === $('modal-overlay')) cerrarModal(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') cerrarModal(); });
