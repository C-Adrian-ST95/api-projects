from pydantic import BaseModel, Field, ConfigDict

class ProductoCrear(BaseModel):
    nombre: str = Field(min_length=2, max_length=120)
    precio: float = Field(gt=0)
    stock: int = Field(ge=0)

class ProductoParcial(BaseModel):
    nombre: str | None = Field(
        default=None,
        min_length=2,
        max_length=120
    )
    precio: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)

class ProductoSalida(ProductoCrear):
    id: int

    model_config = ConfigDict(from_attributes=True)

class ConsultaProductos(BaseModel):
    total: int
    limite: int
    desplazamiento: int 
    resultados: list[ProductoSalida]

class SalidaStock(BaseModel):
    cantidad: int= Field(gt=0)

class UsuarioCrear(BaseModel):
    username: str = Field(
        min_length=3,
        max_leangth=40,
        pattern=r"^[a-zA-Z0-9_]+$"
    )

    password: str = Field(
        min_length=12,
        max_length=128
    )

class UsuarioSalida(BaseModel):
    id: int
    username: str
    rol: str
    activo: bool

    model_config = ConfigDict(from_attributes=True)