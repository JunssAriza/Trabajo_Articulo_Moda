"""
Módulo de Modelos de Datos (models.py)
Define esquemas Pydantic y adaptadores para ObjectId de MongoDB.
Caso de estudio: Boutique de Moda "Estilo Urbano" (colección: prendas).
"""

from datetime import datetime  # noqa: I001
from typing import Annotated
from urllib.parse import urlsplit

from bson import ObjectId
from pydantic import AliasChoices, AfterValidator, BaseModel, ConfigDict, Field
from pydantic_core import core_schema


class _ObjectIdPydanticAnnotation:
    """Adaptador para validar y serializar ObjectId de MongoDB en Pydantic v2"""

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        def validate(v):
            if isinstance(v, ObjectId):
                return str(v)
            if isinstance(v, str) and ObjectId.is_valid(v):
                return v
            raise ValueError("ID inválido de MongoDB (ObjectId)")

        return core_schema.json_or_python_schema(
            json_schema=core_schema.str_schema(),
            python_schema=core_schema.no_info_plain_validator_function(validate),
            serialization=core_schema.to_string_ser_schema(),
        )


# Tipo de dato reutilizable para Pydantic
PyObjectId = Annotated[str, _ObjectIdPydanticAnnotation]


def _validate_image_url(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()
    if not value:
        return None

    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("La imagen debe ser una URL pública HTTP o HTTPS.")

    return value


ImagenUrl = Annotated[
    str | None,
    Field(
        max_length=2048,
        description="URL pública HTTP/HTTPS de la imagen; no se almacena el archivo.",
    ),
    AfterValidator(_validate_image_url),
]


class ArticuloModaBase(BaseModel):
    prenda: str = Field(
        ...,
        min_length=2,
        max_length=150,
        description="Nombre o tipo de prenda de vestir",
        examples=["Chaqueta Oversize Urbana"],
    )
    talla: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Talla de la prenda (ej. XS, S, M, L, XL o numérica)",
        examples=["M"],
    )
    precio: float = Field(
        ...,
        gt=0,
        description="Precio unitario de la prenda",
        examples=[129000.0],
    )
    en_exhibicion: bool = Field(
        default=True,
        description="Indica si la prenda se encuentra actualmente en exhibición",
    )
    imagen_url: ImagenUrl = Field(
        default=None,
        validation_alias=AliasChoices("imagen_url", "image_url"),
    )


class ArticuloModaCreate(ArticuloModaBase):
    """Modelo utilizado para recibir solicitudes POST de creación"""


class ArticuloModaUpdate(BaseModel):
    """Modelo para solicitudes PUT/PATCH (campos opcionales para edición)"""

    prenda: str | None = Field(None, min_length=2, max_length=150)
    talla: str | None = Field(None, min_length=1, max_length=20)
    precio: float | None = Field(None, gt=0)
    en_exhibicion: bool | None = None
    imagen_url: ImagenUrl | None = Field(
        default=None,
        validation_alias=AliasChoices("imagen_url", "image_url"),
    )


class ArticuloModa(ArticuloModaBase):
    """Modelo completo de respuesta que incluye el ID de MongoDB y la fecha de registro"""

    id: PyObjectId = Field(
        alias="_id",
        description="Identificador único ObjectId de MongoDB",
    )
    fecha_creacion: datetime = Field(
        default_factory=datetime.now,
        description="Fecha de registro en la colección 'prendas'",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "_id": "654321789abcdef012345678",
                "prenda": "Chaqueta Oversize Urbana",
                "talla": "M",
                "precio": 129000.0,
                "en_exhibicion": True,
                "imagen_url": "https://ejemplo.com/chaqueta-oversize.jpg",
                "fecha_creacion": "2026-11-20T10:48:00",
            }
        },
    )