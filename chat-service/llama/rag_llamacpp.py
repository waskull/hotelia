import httpx
import chromadb
from uuid import uuid4
from django.conf import settings
import re

# URL base de tu servidor llama.cpp
LLAMACPP_API = getattr(settings, "LLAMACPP_API", "http://localhost:8080/")
LLAMACPP_API_EMBEDDINGS = getattr(
    settings, "LLAMACPP_API_EMBEDDINGS", "http://localhost:8085/")

ERROR_MESSAGE = "No pude generar la respuesta."
# Cliente ChromaDB persistente
client = chromadb.PersistentClient(path="./chroma_store")
docs_collection = client.get_or_create_collection("hotel_docs")
history_collection = client.get_or_create_collection("chat_history")

SYSTEM_PROMPT = (
    "Eres el asistente de reservas del sistema Hotelia. "
    "Usa solo la información provista en 'CONTEXT' para responder "
    "consultas sobre hoteles, habitaciones y políticas de reserva o pago. "
    "Si no puedes responder con la información disponible, indica que no puedes responder."
)


def add_document(doc_id, text, metadata=None):
    try:
        # Verificar si el documento ya existe
        existing = docs_collection.get(ids=[str(doc_id)])
        if existing and existing.get("ids"):
            print(f"Documento '{doc_id}' ya existe. Se omite la ingesta.")
            return

        # Generar embedding
        emb = get_llamacpp_embedding(text)

        # Agregar a ChromaDB
        docs_collection.add(
            ids=[str(doc_id)],
            documents=[text],
            metadatas=[metadata or {}],
            embeddings=[emb],
        )

        print(f"Documento '{doc_id}' agregado correctamente.")

    except Exception as e:
        print(f"Error al agregar documento '{doc_id}': {e}")


def get_llamacpp_embedding(text: str):
    if not isinstance(text, str):
        text = str(text)
    with httpx.Client(timeout=900.0) as client_http:
        response = client_http.post(
            f"{LLAMACPP_API_EMBEDDINGS}embeddings",
            json={"content": text}
        )
        response.raise_for_status()
        data = response.json()
        if isinstance(data, dict) and "embedding" in data:
            return data.get("embedding", [])

    # Si la respuesta es una lista
        if isinstance(data, list):
            first = data[0]
            if "embedding" in first:
                # Puede venir como lista dentro de lista
                embedding = first["embedding"]
                return embedding[0] if isinstance(embedding[0], list) else embedding

        raise ValueError(
            f"Formato inesperado en la respuesta de embeddings: {data}")


def query_documents(query: str, n_results=6):
    q_embed = get_llamacpp_embedding(query)
    results = docs_collection.query(
        query_embeddings=[q_embed], n_results=n_results)
    return results["documents"][0] if results["documents"] else []


def store_user_interaction(user_id: str, query: str, answer: str):
    print("Almacenando en ChromaDB")
    combined_text = f"Usuario: {query}\nAsistente: {answer}"
    embedding = get_llamacpp_embedding(combined_text)
    history_collection.add(
        ids=[f"{user_id}-{uuid4()}"],
        documents=[combined_text],
        metadatas={"user_id": user_id},
        embeddings=[embedding],
    )


def get_user_history(user_id: str, limit: int = 10):
    try:
        results = history_collection.get(where={"user_id": user_id})
    except Exception as e:
        print(f"Error al obtener historial del usuario {user_id}: {e}")
        return []

    docs = results.get("documents", []) if isinstance(results, dict) else []

    history = []
    for doc in docs[-limit:]:
        if not isinstance(doc, str):
            continue

        # Formato esperado: "Usuario: <pregunta>\nAsistente: <respuesta>"
        parts = doc.split("\nAsistente:")
        if len(parts) == 2:
            query = parts[0].replace("Usuario:", "").strip()
            answer = parts[1].strip()
            history.append({
                "query": query,
                "answer": answer
            })
        else:
            # Si no coincide el formato, guarda el texto completo como referencia
            history.append({
                "query": doc.strip(),
                "answer": ""
            })

    # Devuelve el historial más antiguo primero (orden cronológico)
    return list(reversed(history))


def search_user_history(user_id: str, search: str, n_results: int = 5):
    q_embed = get_llamacpp_embedding(search)
    results = history_collection.query(
        query_embeddings=[q_embed],
        n_results=n_results,
        where={"user_id": user_id},
    )
    docs_nested = results.get("documents", [])

    # Aplanar lista de listas
    docs = [d for sublist in docs_nested for d in sublist] if docs_nested else []

    history = []
    for doc in docs:
        if not isinstance(doc, str):
            doc = str(doc)

        parts = doc.split("\nAsistente:")
        if len(parts) == 2:
            query = parts[0].replace("Usuario:", "").strip()
            answer = parts[1].strip()
            history.append({"query": query, "answer": answer})
    return history


def generate_answer_llamacpp(query: str, context: str, n_predict: int = 512, temperature: float = 0.8):
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"=== CONTEXT ===\n{context}\n\n"
        f"=== PREGUNTA DEL USUARIO ===\n{query}\n\n"
        "=== INSTRUCCIÓN ===\n"
        "Responde solo con información del contexto. Sé claro y conciso.\n"
    )
    print("contexto: ", context)

    with httpx.Client(timeout=900.0) as client_http:
        try:
            response = client_http.post(
                f"{LLAMACPP_API}completion",
                json={
                    "prompt": prompt,
                    "n_predict": n_predict,
                    "temperature": temperature,
                    "stream": False,
                    "stop": ["Usuario:", "Pregunta:"],
                },
            )
            response.raise_for_status()
            data = response.json()

            return data.get("content", ERROR_MESSAGE)
        except httpx.RequestError as e:
            print("error:", e)
            return ERROR_MESSAGE


def handle_chat_query_llamacpp(query: str, user_id: str = "anon"):
    docs = query_documents(query)
    context = "\n".join(docs) if docs else "Sin contexto de documentos."
    user_history = search_user_history(user_id=user_id, search=query)
    context += "\n\nHistorial relevante:\n"
    if user_history:
        # Convertir diccionarios a texto
        formatted_history = [
            f"Usuario: {item['query']}\nAsistente: {item['answer']}"
            for item in user_history
            if isinstance(item, dict)
        ]
        context += "\n".join(formatted_history)
    else:
        context += "\nSin historial previo relevante.\n"
    try:
        answer = generate_answer_llamacpp(query, context)
        answer = clean_response(answer)
        print("Respuesta:", answer)
        if answer != ERROR_MESSAGE:
            store_user_interaction(user_id, query, answer)
        return answer
    except Exception as e:
        print(e)
        return ERROR_MESSAGE


def clean_response(text: str) -> str:
    # Elimina los bloques de código Markdown
    text = re.sub(r"```+", "", text)
    # Quita espacios al inicio y fin de línea
    text = text.strip()

    if text.startswith("=== RESPUESTA ===\n"):
        text = text.replace("=== RESPUESTA ===\n", "")
    if text.startswith("Asistente: "):
        text = text.replace("Asistente: ", "").strip()

    return text
