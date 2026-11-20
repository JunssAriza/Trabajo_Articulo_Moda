"""
Módulo Principal de la Aplicación (main.py)
Instancia FastAPI, gestiona CORS, conexión asíncrona y expone el CRUD con Motor.
Caso de estudio: Boutique de Moda "Estilo Urbano" (colección: prendas).
"""

from datetime import datetime, timedelta  # noqa: I001

from bson import ObjectId
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware

from database import coleccion_prendas, verificar_conexion
from models import ArticuloModa, ArticuloModaCreate, ArticuloModaUpdate

# Instancia principal de FastAPI
app = FastAPI(
    title='API Boutique de Moda "Estilo Urbano" - SENA ADSO',
    description="API RESTful asíncrona con FastAPI y MongoDB (FARM Stack) para gestión de prendas.",
    version="1.0.0",
)

# Configuración de CORS para permitir conexión con clientes Frontend (React, Angular, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Evento de inicio del servidor
@app.on_event("startup")
async def startup_db_client():
    await verificar_conexion()


# ================================================
# ENDPOINTS RESTful ASÍNCRONOS - COLECCIÓN "PRENDAS"
# ================================================


@app.get("/", tags=["Raíz"])
async def root():
    return {
        "mensaje": 'Bienvenido a la API de Boutique de Moda "Estilo Urbano" (SENA ADSO)',
        "coleccion": "prendas",
        "documentacion": "/docs",
    }


@app.post(
    "/prendas",
    response_model=ArticuloModa,
    status_code=status.HTTP_201_CREATED,
    tags=["Prendas"],
    summary="Registrar una nueva prenda en MongoDB",
)
async def create_prenda(prenda_in: ArticuloModaCreate):
    """
    Guarda una prenda de forma asíncrona en la colección 'prendas' de MongoDB:
    - Asigna la fecha de creación actual.
    - Evita duplicados exactos de prenda y talla (lanza HTTP 400 Bad Request).
    """
    # 1. Validar que no exista otra prenda idéntica (mismo nombre de prenda y talla)
    prenda_existente = await coleccion_prendas.find_one(
        {"prenda": prenda_in.prenda, "talla": prenda_in.talla}
    )
    if prenda_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe la prenda '{prenda_in.prenda}' en talla '{prenda_in.talla}'.",
        )

    # 2. Preparar el diccionario del documento
    nueva_prenda = prenda_in.model_dump()
    nueva_prenda["fecha_creacion"] = datetime.now()

    # 3. Insertar asíncronamente en MongoDB
    resultado = await coleccion_prendas.insert_one(nueva_prenda)

    # 4. Recuperar el documento recién creado por su _id ObjectId
    prenda_creada = await coleccion_prendas.find_one({"_id": resultado.inserted_id})
    return prenda_creada


@app.get(
    "/prendas",
    response_model=list[ArticuloModa],
    status_code=status.HTTP_200_OK,
    tags=["Prendas"],
    summary="Listar prendas (Colección / Filtros de tarjetas)",
)
async def get_prendas(
    en_exhibicion: bool | None = Query(
        default=None,
        description="Filtrar por estado de exhibición (true = En Exhibición, false = Sin Stock / fuera de exhibición)",
    ),
    sin_stock: bool = Query(
        default=False,
        description="Si es true, muestra prendas con en_exhibicion=False (Sin Stock)",
    ),
    nueva_prenda: bool = Query(
        default=False,
        description="Si es true, filtra prendas registradas en los últimos 7 días (Nueva Prenda)",
    ),
    talla: str | None = Query(
        default=None,
        description="Filtrar opcionalmente por talla (ej. S, M, L, XL)",
    ),
):
    """
    Recupera asíncronamente los documentos de la colección 'prendas' con soporte
    para filtros de catálogo/tarjetas: Colección completa, En Exhibición, Sin Stock y Nueva Prenda.
    """
    filtro: dict = {}

    if sin_stock:
        filtro["en_exhibicion"] = False
    elif en_exhibicion is not None:
        filtro["en_exhibicion"] = en_exhibicion

    if nueva_prenda:
        hace_una_semana = datetime.now() - timedelta(days=7)
        filtro["fecha_creacion"] = {"$gte": hace_una_semana}

    if talla:
        filtro["talla"] = talla

    prendas = []
    cursor = coleccion_prendas.find(filtro)
    async for documento in cursor:
        prendas.append(documento)
    return prendas


@app.get(
    "/prendas/{id}",
    response_model=ArticuloModa,
    status_code=status.HTTP_200_OK,
    tags=["Prendas"],
    summary="Buscar prenda por ObjectId",
)
async def get_prenda_por_id(id: str):
    """Busca una prenda específica por su ObjectId de MongoDB."""
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es válido.",
        )

    prenda = await coleccion_prendas.find_one({"_id": ObjectId(id)})
    if prenda:
        return prenda

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No se encontró ninguna prenda con el ID '{id}'.",
    )


@app.put(
    "/prendas/{id}",
    response_model=ArticuloModa,
    status_code=status.HTTP_200_OK,
    tags=["Prendas"],
    summary="Actualizar datos o estado de una prenda",
)
async def update_prenda(id: str, prenda_update: ArticuloModaUpdate):
    """Actualiza los campos de un documento en MongoDB por su _id."""
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId válido.",
        )

    datos_a_actualizar = prenda_update.model_dump(exclude_unset=True)

    if len(datos_a_actualizar) >= 1:
        resultado_actualizacion = await coleccion_prendas.update_one(
            {"_id": ObjectId(id)},
            {"$set": datos_a_actualizar},
        )

        if (
            resultado_actualizacion.modified_count == 1
            or resultado_actualizacion.matched_count == 1
        ):
            prenda_modificada = await coleccion_prendas.find_one({"_id": ObjectId(id)})
            return prenda_modificada

    prenda_existente = await coleccion_prendas.find_one({"_id": ObjectId(id)})
    if prenda_existente:
        return prenda_existente

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No es posible actualizar. La prenda con ID '{id}' no existe.",
    )


@app.delete(
    "/prendas/{id}",
    status_code=status.HTTP_200_OK,
    tags=["Prendas"],
    summary="Eliminar prenda de MongoDB",
)
async def delete_prenda(id: str):
    """Elimina permanentemente un documento de MongoDB por su ObjectId."""
    if not ObjectId.is_valid(id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El formato del ID '{id}' no es un ObjectId válido.",
        )

    resultado_eliminacion = await coleccion_prendas.delete_one({"_id": ObjectId(id)})

    if resultado_eliminacion.deleted_count == 1:
        return {"mensaje": f"Prenda con ID '{id}' eliminada exitosamente de MongoDB."}

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"No es posible eliminar. La prenda con ID '{id}' no existe en la base de datos.",
    )