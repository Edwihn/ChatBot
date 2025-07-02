import os
from pymongo import MongoClient
import os
from urllib.parse import quote_plus

# RECOMENDADO: usa variable de entorno
MONGO_URI = os.getenv("MONGO_URI")

# OPCIONAL: fallback si no hay variable de entorno
if not MONGO_URI:
    USERNAME = "edjoel05"
    PASSWORD = "1234"  # O usa os.getenv("MONGO_PASSWORD")
    escaped_password = quote_plus(PASSWORD)
    CLUSTER_HOST = "server1.jns05ba.mongodb.net"

    MONGO_URI = f"mongodb+srv://{USERNAME}:{escaped_password}@{CLUSTER_HOST}/chatbot?retryWrites=true&w=majority"

DB_NAME = "chatbot"

try:
    client = MongoClient(
        MONGO_URI,
        serverSelectionTimeoutMS=5000,  # Timeout de 5 segundos
        connectTimeoutMS=10000,         # Timeout de conexión
        maxPoolSize=50,                 # Pool de conexiones
        retryWrites=True               # Reintentar escrituras
    )
    
    db = client[DB_NAME]
    
    # Obtener referencias a las colecciones
    collections = {
        'recomendaciones': db['recomendaciones'],
        'metricas': db['metricas'],
        'sobre': db['sobre']
    }
    
except Exception as e:
    exit(1)