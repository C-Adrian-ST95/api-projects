from sqlalchemy import String, Float, Integer, CheckConstraint, ForeignKey, DateTime, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from database import Base
from datetime import datetime



class Producto(Base):
    __tablename__ = "productos"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    nombre: Mapped[str] = mapped_column(
        String(120), nullable=False
    )

    precio: Mapped[float] = mapped_column(
        Float, nullable=False
    )

    stock: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "precio > 0", name= "precio_positivo"
        ),
        CheckConstraint(
            "stock >= 0",
            name="stock_no_negativo"
        ),
    )

class MovimientoStock(Base):
    __tablename__ = "movimientos_stock"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )
    producto_id: Mapped[int] = mapped_column(
        ForeignKey("productos.id"),
        nullable=False
    )
    tipo: Mapped[str] = mapped_column(
        String(10), nullable=False
    )

    cantidad: Mapped[int] = mapped_column(
        Integer, nullable=False
    )

    fecha: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            cantidad >= 0, name="cantidad_movimiento_positivo"
        ),
    )

class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    username: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    rol: Mapped[str] = mapped_column(
        String(20), 
        nullable=False
    )

    activo: Mapped[bool] = mapped_column(
        Boolean, 
        nullable=False, 
        default=True
    )

    __table_args__ = (
        CheckConstraint(
            "rol IN ('lector', 'admin')",
            name="rol_usuario_valido"
        ),
    )