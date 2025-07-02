import spacy
import re
import unicodedata
from difflib import SequenceMatcher
from app.db import collections, client

# Cargar modelo de spaCy
try:
    nlp = spacy.load("es_core_news_sm")
except OSError:
    print("⚠️  Modelo español no encontrado. Instalando...")
    import subprocess
    subprocess.run(["python", "-m", "spacy", "download", "es_core_news_sm"])
    nlp = spacy.load("es_core_news_sm")

def normalize_text(text):
    """Normaliza el texto removiendo acentos y caracteres especiales"""
    if not text:
        return ""
    
    # Convertir a minúsculas
    text = text.lower().strip()
    
    # Remover acentos
    text = unicodedata.normalize('NFD', text)
    text = ''.join([c for c in text if unicodedata.category(c) != 'Mn'])
    
    # Remover caracteres especiales pero mantener espacios
    text = re.sub(r'[^\w\s]', '', text)
    
    # Remover espacios extra
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_keywords(text):
    """Extrae palabras clave del texto usando spaCy"""
    doc = nlp(text)
    
    # Obtener lemmas sin stop words
    keywords = []
    for token in doc:
        if (not token.is_stop and 
            not token.is_punct and 
            not token.is_space and
            len(token.text) > 2):
            keywords.append(token.lemma_.lower())
    
    # También agregar palabras originales normalizadas
    original_words = normalize_text(text).split()
    keywords.extend([word for word in original_words if len(word) > 2])
    
    return list(set(keywords))  # Remover duplicados

def search_mongodb(user_keywords, category):
    """Busca en MongoDB usando diferentes estrategias MEJORADAS"""
    
    try:
        # Mapear categorías a nombres de colecciones
        collection_name = category.lower()
        if collection_name not in ['recomendaciones', 'metricas', 'sobre']:
            print(f"⚠️  Categoría '{category}' no válida")
            return []
        
        collection = collections[collection_name]
        print(f"🔍 Buscando en colección: {collection_name}")
        print(f"🔑 Keywords del usuario: {user_keywords}")
        
        results = []
        
        # ESTRATEGIA 1 MEJORADA: Buscar por palabras clave con regex (más flexible)
        for keyword in user_keywords:
            # Normalizar keyword para búsqueda
            normalized_keyword = normalize_text(keyword)
            
            # Crear múltiples variantes de búsqueda
            search_variants = [
                keyword,  # Original
                normalized_keyword,  # Normalizada
                keyword.lower(),  # Minúscula
            ]
            
            # Construir query más flexible
            or_conditions = []
            
            # Para arrays de palabras clave
            for variant in search_variants:
                or_conditions.extend([
                    # Búsqueda exacta en array
                    {"palabras_clave": {"$in": [variant]}},
                    # Búsqueda con regex en array (coincidencia parcial)
                    {"palabras_clave": {"$elemMatch": {"$regex": re.escape(variant), "$options": "i"}}},
                    # Si palabras_clave es string
                    {"palabras_clave": {"$regex": re.escape(variant), "$options": "i"}}
                ])
            
            query = {"$or": or_conditions}
            docs = list(collection.find(query))
            
            for doc in docs:
                if not any(str(existing.get('_id')) == str(doc.get('_id')) for existing in results):
                    doc['score'] = 3  # Puntuación alta para coincidencia en palabras clave
                    doc['match_type'] = f'keyword_match_{keyword}'
                    results.append(doc)
            
            print(f"   Keyword '{keyword}' - Resultados en palabras_clave: {len(docs)}")
        
        # ESTRATEGIA 2 MEJORADA: Buscar en el texto de la pregunta
        for keyword in user_keywords:
            normalized_keyword = normalize_text(keyword)
            
            # Buscar tanto keyword original como normalizada
            query = {
                "$or": [
                    {"pregunta": {"$regex": re.escape(keyword), "$options": "i"}},
                    {"pregunta": {"$regex": re.escape(normalized_keyword), "$options": "i"}}
                ]
            }
            docs = list(collection.find(query))
            for doc in docs:
                if not any(str(existing.get('_id')) == str(doc.get('_id')) for existing in results):
                    doc['score'] = 2  # Puntuación media
                    doc['match_type'] = f'question_match_{keyword}'
                    results.append(doc)
            print(f"   Keyword '{keyword}' - En preguntas: {len(docs)}")
        
        # ESTRATEGIA 3 MEJORADA: Buscar en el texto de la respuesta
        for keyword in user_keywords:
            normalized_keyword = normalize_text(keyword)
            
            query = {
                "$or": [
                    {"respuesta": {"$regex": re.escape(keyword), "$options": "i"}},
                    {"respuesta": {"$regex": re.escape(normalized_keyword), "$options": "i"}}
                ]
            }
            docs = list(collection.find(query))
            for doc in docs:
                if not any(str(existing.get('_id')) == str(doc.get('_id')) for existing in results):
                    doc['score'] = 1  # Puntuación baja
                    doc['match_type'] = f'answer_match_{keyword}'
                    results.append(doc)
            print(f"   Keyword '{keyword}' - En respuestas: {len(docs)}")
        
        # ESTRATEGIA 4 NUEVA: Búsqueda por fragmentos de palabras
        if not results:
            print("🔍 Intentando búsqueda por fragmentos...")
            for keyword in user_keywords:
                if len(keyword) > 4:  # Solo para palabras de más de 4 caracteres
                    # Buscar fragmentos de la palabra
                    fragment = keyword[:4]  # Primeros 4 caracteres
                    
                    query = {
                        "$or": [
                            {"palabras_clave": {"$elemMatch": {"$regex": f".*{re.escape(fragment)}.*", "$options": "i"}}},
                            {"palabras_clave": {"$regex": f".*{re.escape(fragment)}.*", "$options": "i"}},
                            {"pregunta": {"$regex": f".*{re.escape(fragment)}.*", "$options": "i"}}
                        ]
                    }
                    
                    docs = list(collection.find(query))
                    for doc in docs:
                        if not any(str(existing.get('_id')) == str(doc.get('_id')) for existing in results):
                            doc['score'] = 0.8
                            doc['match_type'] = f'fragment_match_{fragment}'
                            results.append(doc)
                    print(f"   Fragmento '{fragment}': {len(docs)} resultados")
        
        # ESTRATEGIA 5: Búsqueda muy amplia si aún no hay resultados
        if not results and len(user_keywords) > 0:
            print("🔍 Búsqueda muy amplia...")
            # Crear una sola query con todas las keywords
            all_conditions = []
            
            for keyword in user_keywords:
                normalized_keyword = normalize_text(keyword)
                all_conditions.extend([
                    {"palabras_clave": {"$elemMatch": {"$regex": f".*{re.escape(keyword)}.*", "$options": "i"}}},
                    {"palabras_clave": {"$regex": f".*{re.escape(keyword)}.*", "$options": "i"}},
                    {"pregunta": {"$regex": f".*{re.escape(keyword)}.*", "$options": "i"}},
                    {"respuesta": {"$regex": f".*{re.escape(keyword)}.*", "$options": "i"}},
                    {"palabras_clave": {"$elemMatch": {"$regex": f".*{re.escape(normalized_keyword)}.*", "$options": "i"}}},
                    {"palabras_clave": {"$regex": f".*{re.escape(normalized_keyword)}.*", "$options": "i"}},
                    {"pregunta": {"$regex": f".*{re.escape(normalized_keyword)}.*", "$options": "i"}},
                    {"respuesta": {"$regex": f".*{re.escape(normalized_keyword)}.*", "$options": "i"}}
                ])
            
            if all_conditions:
                query = {"$or": all_conditions}
                docs = list(collection.find(query).limit(10))  # Limitar resultados
                for doc in docs:
                    doc['score'] = 0.5
                    doc['match_type'] = 'broad_search'
                    results.append(doc)
                print(f"   Búsqueda amplia: {len(docs)} resultados")
        
        # Debugging: Mostrar qué se encontró
        print(f"\n📊 RESUMEN DE BÚSQUEDA:")
        match_types = {}
        for result in results:
            match_type = result.get('match_type', 'unknown')
            match_types[match_type] = match_types.get(match_type, 0) + 1
        
        for match_type, count in match_types.items():
            print(f"   {match_type}: {count} resultados")
        
        # Remover duplicados reales basándose en _id
        unique_results = {}
        for result in results:
            try:
                doc_id = str(result.get('_id', ''))
                if doc_id and doc_id not in unique_results:
                    unique_results[doc_id] = result
                elif doc_id:
                    # Mantener el de mayor score
                    current_score = result.get('score', 0)
                    existing_score = unique_results[doc_id].get('score', 0)
                    if current_score > existing_score:
                        unique_results[doc_id] = result
            except Exception as e:
                print(f"⚠️  Error procesando resultado: {e}")
                continue
        
        # Ordenar por score descendente
        final_results = sorted(unique_results.values(), 
                             key=lambda x: x.get('score', 0), 
                             reverse=True)
        
        print(f"✅ Total resultados únicos: {len(final_results)}")
        
        # Debug: mostrar estructura de los primeros resultados
        for i, result in enumerate(final_results[:3], 1):
            print(f"\n🔍 Resultado #{i} (Score: {result.get('score', 0)}):")
            print(f"   ID: {result.get('_id')}")
            print(f"   Match type: {result.get('match_type', 'N/A')}")
            print(f"   Pregunta: {result.get('pregunta', 'N/A')[:80]}...")
            keywords = result.get('palabras_clave', [])
            if isinstance(keywords, list):
                print(f"   Keywords (array): {keywords[:5]}...")
            else:
                print(f"   Keywords (string): {str(keywords)[:80]}...")
        
        return final_results[:5]  # Retornar los 5 mejores
        
    except Exception as e:
        print(f"❌ Error en búsqueda MongoDB: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return []

def calculate_similarity_score(user_message, db_entry):
    """Calcula score de similitud entre mensaje del usuario y entrada de BD"""
    try:
        # Combinar pregunta y palabras clave para comparación
        palabras_clave = db_entry.get('palabras_clave', [])
        if isinstance(palabras_clave, list):
            palabras_str = ' '.join(palabras_clave)
        else:
            palabras_str = str(palabras_clave) if palabras_clave else ''
            
        db_text = f"{db_entry.get('pregunta', '')} {palabras_str}"
        
        # Usar spaCy para similitud semántica
        user_doc = nlp(user_message)
        db_doc = nlp(db_text)
        
        semantic_similarity = user_doc.similarity(db_doc)
        
        # Calcular similitud léxica como backup
        lexical_similarity = SequenceMatcher(None, 
                                           normalize_text(user_message), 
                                           normalize_text(db_text)).ratio()
        
        # Combinar ambas similitudes
        final_score = (semantic_similarity * 0.7) + (lexical_similarity * 0.3)
        
        return final_score
        
    except Exception as e:
        print(f"Error calculando similitud: {e}")
        return 0

def process_user_input(user_message, category):
    """Función principal para procesar input del usuario con MongoDB"""
    
    if not user_message or not user_message.strip():
        return "Por favor, escribe un mensaje válido."
    
    if not category:
        return "Por favor, selecciona una categoría válida."
    
    print(f"\n🔍 PROCESANDO CONSULTA")
    print(f"📝 Mensaje: '{user_message}'")
    print(f"📂 Categoría: '{category}'")
    
    # 1. Normalizar y extraer keywords
    normalized_message = normalize_text(user_message)
    user_keywords = extract_keywords(user_message)
    
    print(f"🔑 Keywords extraídas: {user_keywords}")
    print(f"📝 Mensaje normalizado: '{normalized_message}'")
    
    if not user_keywords:
        # Si no hay keywords, usar palabras del mensaje normalizado
        user_keywords = [word for word in normalized_message.split() if len(word) > 2]
        print(f"🔄 Keywords de respaldo: {user_keywords}")
    
    if not user_keywords:
        return "No pude entender tu mensaje. ¿Podrías reformularlo de otra manera?"
    
    # 2. Buscar en MongoDB
    search_results = search_mongodb(user_keywords, category)
    
    if not search_results:
        print("❌ No se encontraron resultados")
        return get_default_response(category)
    
    # 3. Calcular similitudes y elegir mejor respuesta
    best_match = None
    best_score = 0
    
    for result in search_results:
        similarity_score = calculate_similarity_score(user_message, result)
        db_score = result.get('score', 0)
        
        # Combinar score de BD con similitud semántica
        final_score = (db_score * 0.4) + (similarity_score * 0.6)
        
        print(f"📊 Resultado: Score BD={db_score}, Similitud={similarity_score:.3f}, Final={final_score:.3f}")
        print(f"   Pregunta: {result.get('pregunta', 'N/A')[:50]}...")
        print(f"   Match type: {result.get('match_type', 'N/A')}")
        
        if final_score > best_score:
            best_score = final_score
            best_match = result
    
    # Umbral más bajo para mayor flexibilidad
    if best_match and best_score > 0.2:  # Reducido de 0.3 a 0.2
        print(f"✅ Mejor coincidencia encontrada (score: {best_score:.3f})")
        return best_match.get('respuesta', 'Respuesta no disponible.')
    else:
        print(f"⚠️  Score muy bajo ({best_score:.3f}), usando respuesta por defecto")
        return get_default_response(category)

def get_default_response(category):
    """Respuestas por defecto según categoría"""
    default_responses = {
        "recomendaciones": "Lo siento, no tengo recomendaciones específicas para tu consulta. ¿Podrías ser más específico sobre qué tipo de recomendación necesitas?",
        "sobre": "No encontré información específica sobre ese tema. ¿Te gustaría conocer más sobre algún aspecto particular de WorldMatters o el medio ambiente?",
        "metricas": "No tengo métricas disponibles para esa consulta específica. ¿Podrías reformular tu pregunta o especificar qué tipo de datos te interesan?"
    }
    
    return default_responses.get(category.lower(), 
                               "Lo siento, no encontré información sobre tu consulta. ¿Podrías reformular tu pregunta?")

def test_mongodb_connection():
    """Prueba la conexión a MongoDB y muestra estadísticas MEJORADA"""
    try:
        print("🔍 PROBANDO CONEXIÓN A MONGODB ATLAS")
        
        # Probar conexión
        client.admin.command('ping')
        print("✅ Ping exitoso a MongoDB Atlas")
        
        collection_names = ['recomendaciones', 'metricas', 'sobre']
        
        for col_name in collection_names:
            try:
                collection = collections[col_name]
                count = collection.count_documents({})
                print(f"\n📊 Colección '{col_name}': {count} documentos")
                
                # Mostrar ejemplos y estructura
                if count > 0:
                    samples = list(collection.find({}).limit(3))
                    for i, sample in enumerate(samples, 1):
                        print(f"\n   📝 Ejemplo {i}:")
                        print(f"   ID: {sample.get('_id')}")
                        print(f"   Pregunta: {sample.get('pregunta', 'N/A')[:60]}...")
                        
                        keywords = sample.get('palabras_clave', [])
                        if isinstance(keywords, list):
                            print(f"   Keywords (array): {keywords[:5]}{'...' if len(keywords) > 5 else ''}")
                        else:
                            print(f"   Keywords (string): {str(keywords)[:60]}...")
                        
                        # Verificar estructura
                        print(f"   Tipo palabras_clave: {type(keywords)}")
                        print(f"   Campos disponibles: {list(sample.keys())}")
                        
            except Exception as e:
                print(f"❌ Error accediendo a colección '{col_name}': {e}")
        
        print("\n✅ Test de conexión completado")
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión a MongoDB Atlas: {e}")
        print("Verifica:")
        print("1. String de conexión correcto")
        print("2. Usuario y contraseña correctos") 
        print("3. Tu IP está en el whitelist de Atlas")
        print("4. El cluster está activo y disponible")
        return False

def debug_search(user_message, category):
    """Función de debugging para entender por qué no encuentra resultados"""
    print(f"\n🐛 MODO DEBUG ACTIVADO")
    print(f"📝 Mensaje original: '{user_message}'")
    print(f"📂 Categoría: '{category}'")
    
    # Extraer keywords paso a paso
    normalized = normalize_text(user_message)
    keywords = extract_keywords(user_message)
    
    print(f"🔄 Normalizado: '{normalized}'")
    print(f"🔑 Keywords extraídas: {keywords}")
    
    # Verificar qué hay en la BD
    collection = collections[category.lower()]
    
    # Mostrar algunos documentos de ejemplo
    print(f"\n📋 Primeros 3 documentos de '{category}':")
    samples = list(collection.find({}).limit(3))
    
    for i, doc in enumerate(samples, 1):
        print(f"\n   📄 Documento {i}:")
        print(f"   Pregunta: {doc.get('pregunta', 'N/A')}")
        keywords_db = doc.get('palabras_clave', [])
        if isinstance(keywords_db, list):
            print(f"   Keywords en BD: {keywords_db}")
        else:
            print(f"   Keywords en BD (string): {keywords_db}")
    
    # Intentar búsqueda manual con cada keyword
    print(f"\n🔍 Probando búsqueda manual:")
    for keyword in keywords:
        print(f"\n   Buscando: '{keyword}'")
        
        # Búsqueda exacta
        exact_query = {"palabras_clave": {"$in": [keyword]}}
        exact_results = list(collection.find(exact_query))
        print(f"   Exacta: {len(exact_results)} resultados")
        
        # Búsqueda con regex
        regex_query = {"palabras_clave": {"$regex": keyword, "$options": "i"}}
        regex_results = list(collection.find(regex_query))
        print(f"   Regex: {len(regex_results)} resultados")
        
        # Búsqueda en pregunta
        question_query = {"pregunta": {"$regex": keyword, "$options": "i"}}
        question_results = list(collection.find(question_query))
        print(f"   En pregunta: {len(question_results)} resultados")

# Función para cerrar la conexión (buena práctica)
def close_connection():
    """Cierra la conexión a MongoDB"""
    try:
        client.close()
        print("✅ Conexión a MongoDB cerrada correctamente")
    except Exception as e:
        print(f"⚠️  Error cerrando conexión: {e}")
