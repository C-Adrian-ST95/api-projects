from contextlib import asynccontextmanager
from typing import Annotated, Literal

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from database import engine, Base, obtener_sesion
from models import Producto, MovimientoStock, Usuario
from schemas import ProductoCrear, ProductoParcial, ProductoSalida, ConsultaProductos, SalidaStock, UsuarioCrear, UsuarioSalida
from auth import hashear_password,verificar_password,crear_access_token,usuario_actual,solo_admin
from InventarioAPI_WebMovil.frontend import montar_frontend


# Crear tablas iniciales 
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="API REST con persistencia de datos",
    version="2.0.0",
    lifespan=lifespan)

montar_frontend(app)

SesionDB = Annotated[Session, Depends(obtener_sesion)]

@app.get("/")
def inicio():
    return {
        "mensaje": "InventarioAPI con PostgreSQL",
        "version": "2.0.0"
    }

# GET: todos los productos
@app.get("/productos",  response_model=list[ProductoSalida], dependencies=[Depends(usuario_actual)])
def listar_productos(db: SesionDB):
    return db.scalars(
        select(Producto).order_by(Producto.id)
    ).all()

# GET: producto por ID
@app.get("/productos/{producto_id}", response_model=ProductoSalida, dependencies=[Depends(usuario_actual)])
def obtener_producto(producto_id: int, db: SesionDB):
    producto = db.get(Producto, producto_id)

    if producto is None:
        raise HTTPException(404, "Producto no encontrado")

    return producto


# POST: crear un producto
@app.post("/productos", status_code=201, response_model=ProductoSalida, dependencies=[Depends(solo_admin)])
def crear_producto(datos: ProductoCrear, db:SesionDB):
    nuevo = Producto(**datos.model_dump())

    db.add(nuevo)
    db.commit()
    db.refresh(nuevo)

    return nuevo 

# PUT: remplazar todos los campos editables
@app.put("/productos/{producto_id}", response_model=ProductoSalida, dependencies=[Depends(solo_admin)])
def reemplazar_producto(producto_id: int, datos: ProductoCrear, db: SesionDB):
    producto = db.get(Producto, producto_id)

    if producto is None:
        raise HTTPException(404, "Producto no encontrado")

    for campo, valor in datos.model_dump().items():
        setattr(producto, campo, valor)

    db.commit()
    db.refresh(producto)

    return producto

# PATCH: modificar solamente ciertos campos
@app.patch("/productos/{producto_id}", response_model=ProductoSalida, dependencies=[Depends(solo_admin)])
def modificar_producto(producto_id: int, datos: ProductoParcial, db: SesionDB):
    producto = db.get(Producto, producto_id)

    if producto is None:
        raise HTTPException(404, "Producto no encontrado")

    cambios = datos.model_drump(exclude_unset=True)

    if not cambios:
        raise HTTPException(400, "No se enviaron cambios")

    if any(valor is None for valor in cambios.values()):
        raise HTTPException(422, "No se permite null")

    for campo, valor in cambios.items():
        setattr(producto, campo, valor)

    db.comit()
    db.refresh(producto)

    return producto

# DELETE: eliminar producto
@app.delete("/productos/{productos_id}", status_code=204, dependencies=[Depends(solo_admin)])
def eliminar_producto(producto_id: int, db: SesionDB):
    producto = db.get(Producto, producto_id)

    if producto is None:
        raise HTTPException(404, "Producto no encontrado")

    db.delete(producto)
    db.commit()

@app.get("/consultas/productos", response_model=ConsultaProductos,dependencies=[Depends(usuario_actual)])
def consultar_productos(
    db: SesionDB,
    q: str | None = Query(default=None, min_length=2),
    stock_min: int | None = Query(default=None, ge=0),
    precio_min: float | None = Query(default=None, ge=0),
    limite: int = Query(default=10, ge=1, le=100),
    desplazamiento: int = Query(default=0, ge=0),
    orden: Literal["id", "nombre", "precio", "stock"] = "id",
    sentido: Literal["asc", "desc"] = "asc"
):
    filtros = []

    # Filtrar por nombre
    if q is not None: 
        if not q.strip():
            raise HTTPException(
                status_code=400,
                detail="La busqueda no puede estar vacia"
            )
        filtros.append(Producto.nombre.ilike(f"%{q.strip()}%"))

    # Filtrar por stock minimo
    if stock_min is not None:
        filtros.append(Producto.stock >= stock_min)

    # Filtrar por precio minimo
    if precio_min is not None:
        filtros.append(Producto.precio >= precio_min)

    # Contar todos los registros que cumple el filtro
    total = db.scalar(
        select(func.count()).select_from(Producto).where(*filtros))
    

    # Seleccionar la columna de ordenación permitida
    columnas = {
        "id": Producto.id,
        "nombre": Producto.nombre,
        "precio": Producto.precio,
        "stock": Producto.stock
    }

    columna = columnas[orden]

    orden_sql = (
        columna.desc()
        if sentido == "desc"
        else columna.asc()
    )

    # construir la consulta pagina
    consulta = (
        select(Producto).where(*filtros).order_by(orden_sql)
    )

    resultados = db.scalars(consulta).all()

    return {
        "total": total,
        "limite": limite,
        "desplazamiento": desplazamiento,
        "resultados": resultados
    }

# Estadistica mediante SQL
@app.get("/reportes/inventario", dependencies=[Depends(usuario_actual)])
def reporte_inventario(db: SesionDB):

    consulta = select(
        func.count(Producto.id).label("total"),
        func.coalesce(func.sum(Producto.stock), 0).label("unidades"),
        func.avg(Producto.precio).label("promedio")
    )

    resultado = db.execute(consulta).one()

    return {
        "total_productos": resultado.total,
        "unidades_disponibles": resultado.unidades,
        "precio_promedio": (
            round(float(resultado.promedio),2)
            if resultado.promedio is not None 
            else None)
    }


@app.post(
    "/productos/{producto_id}/salidas",
    status_code=201,
    dependencies=[Depends(solo_admin)]
)
def registrar_salida(
    producto_id: int,
    datos: SalidaStock,
    db: SesionDB
):
    try:
        producto = db.scalar(
            select(Producto)
            .where(Producto.id == producto_id)
            .with_for_update()
        )

        if producto is None:
            raise HTTPException(
                404, "Producto no encontrado"
            )

        if producto.stock < datos.cantidad:
            raise HTTPException(
                409, "Stock insuficiente"
            )

        producto.stock -= datos.cantidad

        movimiento = MovimientoStock(
            producto_id=producto_id,
            tipo="SALIDA",
            cantidad=datos.cantidad
        )

        db.add(movimiento)
        db.flush()

        respuesta = {
            "movimiento_id": movimiento.id,
            "producto_id": producto_id,
            "cantidad": datos.cantidad,
            "stock_restante": producto.stock
        }

        db.commit()
        return respuesta

    except Exception:
        db.rollback()
        raise


# iniciar de sesión
@app.post("/auth/registro", status_code=201, response_model=UsuarioSalida)
def registrar_usuario(datos: UsuarioCrear, db: SesionDB):
    nuevo = Usuario(
        username=datos.username,
        password_hash=hashear_password(datos.password),
        rol="lector",
        activo=True
    )

    db.add(nuevo)

    try: 
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409,detail="El usuario ya existe")

    db.refresh(nuevo)

    return nuevo

# Consultar el Usuario autenticado
@app.post("/auth/token")
def iniciar_sesion(formulario: Annotated[OAuth2PasswordRequestForm, Depends()], db: SesionDB):
    usuario = db.scalar(
        select(Usuario).where(Usuario.username == formulario.username)
    )
    if (
        usuario is None or not usuario.activo
        or not verificar_password(
            formulario.password,usuario.password_hash
        ) 
    ):
        raise HTTPException(
            status_code=401, detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token= crear_access_token(usuario.id)

    return {"access_token": token, "token_type": "bearer"}

# Consultar el usuario autenticado
@app.get("/auth/me", response_model=UsuarioSalida)
def consultar_mi_usuario(
    usuario: Annotated[Usuario, Depends(usuario_actual)]
):
    return usuario



