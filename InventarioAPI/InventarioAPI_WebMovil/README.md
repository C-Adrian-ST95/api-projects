# InventarioAPI · Web móvil (Clase 6)

Web app adaptable a celular, tablet y computadora. No necesita instalar React, Node.js ni crear una APK.

## Requisitos

- Proyecto `D:\APIs\InventarioAPI` de las clases anteriores.
- FastAPI, PostgreSQL y autenticación funcionando (`/auth/token`, `/auth/me`).
- Endpoints: `GET /productos`, `GET /reportes/inventario`, `POST/PATCH/DELETE /productos`, `POST /productos/{id}/salidas`.
- Una cuenta de prueba `lector` y, para editar, una cuenta `admin`.

## Integrar sin borrar nada

1. Descomprime este ZIP y copia las carpetas/archivos siguientes a `D:\APIs\InventarioAPI`:

   - `web/` (la carpeta completa)
   - `frontend.py`

2. Abre tu `main_db.py`. Inmediatamente **después** de la creación de la instancia `app = FastAPI(...)` (fuera de sus paréntesis y antes o después de los endpoints), agrega:

   ```python
   from frontend import montar_frontend
   montar_frontend(app)
   ```

3. Ejecuta desde `D:\APIs\InventarioAPI`:

   ```powershell
   ..\.venv\Scripts\python.exe -m uvicorn main_db:app --reload --host 127.0.0.1 --port 8000
   ```

4. Prueba la página: `http://127.0.0.1:8000/app/`

## Desde el celular en la misma red Wi-Fi

1. Detén Uvicorn y vuelve a iniciarlo permitiendo conexiones de la red local:

   ```powershell
   ..\.venv\Scripts\python.exe -m uvicorn main_db:app --reload --host 0.0.0.0 --port 8000
   ```

2. En otra terminal ejecuta `ipconfig` y encuentra la **Dirección IPv4** de la red Wi-Fi/Ethernet activa, por ejemplo `192.168.1.25`. **Es un ejemplo, no la IP real de tu PC.**
3. Conecta el celular a la misma red Wi-Fi, abre `http://TU-IP:8000/app/` (ejemplo `http://192.168.1.25:8000/app/`).
4. Si Windows pregunta, autoriza **solo redes privadas de confianza** para el ejecutable Python. No apagues el firewall ni abras puertos del router.

**Seguridad:** por Wi-Fi con HTTP, las credenciales viajan sin protección TLS. Utiliza **cuentas y datos de prueba, una red privada confiable y nunca contraseñas reutilizadas**. Para usarlo realmente, conviene HTTPS; la sección siguiente ofrece una opción privada más segura.

## Fuera de casa, mediante HTTPS (dispositivos autorizados)

Instala y conecta Tailscale en la PC y los dispositivos que quieras autorizar. Conserva Uvicorn en `127.0.0.1` si solo usarás este método y ejecuta en la PC:

```powershell
tailscale serve --bg 8000
```

Tailscale puede pedirte habilitar certificados HTTPS. Consulta la URL que muestra con:

```powershell
tailscale serve status
```

Abre esa URL terminada en `/app/` en el celular que tenga Tailscale autorizado. No es un enlace público para todo internet: **solo funciona dentro de tu red privada de Tailscale**. Para una página de acceso público se necesita otra estrategia y reforzar controles de seguridad.

Documentación: https://tailscale.com/docs/features/tailscale-serve y https://fastapi.tiangolo.com/tutorial/static-files/

## Nota técnica

- El frontend y API tienen el mismo origen: no necesitas CORS.
- El JWT se guarda **solo en memoria JavaScript**: al recargar se cierra sesión.
- Esta app no publica secretos ni contraseñas en el código.
- Los nombres de productos se insertan en el DOM usando `textContent` para evitar interpretar HTML de datos.
- Si un producto tiene movimientos en `movimientos_stock`, puede que PostgreSQL impida borrarlo por la clave foránea. Es correcto: después enseñaremos baja lógica / archivado.
- `--reload` es para desarrollo. No es despliegue de producción.
- El servidor y PostgreSQL deben permanecer encendidos para acceder.

## Prueba rápida

1. Inicia sesión como `lector`: debe poder consultar, sin botones de edición.
2. Inicia sesión como `admin`: crea, edita, registra salida y verifica las estadísticas.
3. Revisa PostgreSQL: `SELECT * FROM productos ORDER BY id;`.
4. Abre la página desde el teléfono.
