from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Crear aplicación
app = FastAPI(title="InventarioAPI", description="Mi primera API REST", version="1.0.0")

# Modelo parra validar nuevos productos
class ProductoCrear(BaseModel):
    nombre: str = Field(min_length=2)
    precio: float = Field(gt=0)
    stock: int = Field(ge=0)

# Modelo para modificar campos individuales. 
class ProductoParcial(BaseModel):
    nombre: str | None = Field(default=None, min_length=2)
    precio: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)

# Base temporal de productos
productos = [
    {
        "id": 1,
        "nombre": "Cemento Portland",
        "precio": 32.50,
        "stock": 120
    },
    {
        "id": 2, 
        "nombre": "Acero corrugado",
        "precio": 28.00,
        "stock": 80
    }
]

#Endpoit principal
@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a InventarioAPI"}

#Consultar todos los productos
@app.get("/productos")
def lista_productos():
    return productos

# Consultar un producto por ID
@app.get("/productos/{producto_id}")
def obtener_productos(producto_id: int):
    for producto in productos:
        if producto["id"] == producto_id:
            return producto
    raise HTTPException(status_code=404, detail="Producto no encontrado")

# Registrar un nuevo producto 
@app.post("/productos", status_code=201)
def crear_producto(producto: ProductoCrear):
    nuevo_id = max(
        (p["id"] for p in productos), default=0
    ) + 1

    nuevo_productos = {
        "id": nuevo_id,
        **producto.model_dump()
    }

    productos.append(nuevo_productos)
    return nuevo_productos

# reemplazar registro 
@app.put("/productos/{producto_id}")
def reemplazar_producto(producto_id: int, datos: ProductoCrear):
    for indice, producto in enumerate(productos):
        if producto["id"] == producto_id:

            producto[indice] = {
                "id" : producto_id,
                **datos.model_dump()
            }

            return productos[indice]
    
    raise HTTPException(status_code=404, detail="Producto no encontrado")

# Modificar registro.
@app.patch("/productos/{producto_id}")
def modificar_producto(producto_id: int, datos: ProductoParcial):
    cambios = datos.model_dump(exclude_unset=True)

    if not cambios: 
        raise HTTPException(
            status_code=400, detail="Debes enviar almenos un campo"
        )

    if any(valor is None for valor in cambios.values()):
        raise HTTPException(
            status_code=422, detail="No se permiten campos con valor null"
        )

    for producto in productos:
        if producto["id"] == producto_id:
            producto.update(cambios)
            return producto

    raise HTTPException(
        status_code=404, detail="Producto no encontrado"
    )

# Eliminar registro. 
@app.delete("/productos/{producto_id}", status_code=204)
def eliminar_producto(producto_id: int):

    for indice, producto in enumerate(productos):
        if producto["id"] == producto_id:
            productos.pop(indice)
            return

    raise HTTPException(
        status_code=404, detail="Producto no encontrada"
    )