"""
Módulo de Base de Datos (database.py)
Gestiona la conexión asíncrona a MongoDB utilizando Motor.
"""

from decouple import config
from motor.motor_asyncio import AsyncIOMotorClient

# Carga la URL y nombre de la base de datos desde el archivo .env
MONGODB_URL = config('MONGODB_URL', default='mongodb://localhost:27017')
DATABASE_NAME = config('DATABASE_NAME', default='articulos_moda')

# Cliente asíncrono de MongoDB
client = AsyncIOMotorClient(MONGODB_URL)

# Referencia a la base de datos relacional/documental
database = client[DATABASE_NAME]

# Colección de prendas en MongoDB
coleccion_prendas = database['prendas']

async def verificar_conexion():
    """Función de comprobación de estado de la conexión al iniciar la API."""
    try:
        await client.admin.command('ping')
        print(f"Conexión a MongoDB exitosa - Base de Datos: {DATABASE_NAME}")
    except Exception as e:
        print(f"Error al conectar a MongoDB: {e}")
        raise