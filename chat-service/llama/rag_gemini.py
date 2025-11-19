import httpx
import chromadb
from uuid import uuid4
from django.conf import settings
import re

# Configuración de Google Gemini
GOOGLE_API_KEY = getattr(settings, "GOOGLE_API_KEY", None)
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta"

ERROR_MESSAGE = "No pude generar la respuesta."

# Cliente ChromaDB persistente
client = chromadb.PersistentClient(path="./chroma_store")
docs_collection = client.get_or_create_collection("gemini_hotel_docs")
history_collection = client.get_or_create_collection("gemini_chat_history")

SYSTEM_PROMPT = (
    "Eres el asistente de reservas del sistema Hotelia. "
    "Usa solo la información provista en 'CONTEXT' para responder "
    "consultas sobre hoteles, habitaciones y políticas de reserva o pago. "
    "Si no puedes responder con la información disponible, indica que no puedes responder."
)


def get_gemini_embedding(text: str):
    url = f"{GEMINI_API_BASE}/models/gemini-embedding-001:embedContent?key={GOOGLE_API_KEY}"
    response = httpx.post(
        url,
        json={
            "content": {
                "parts": [{"text": text}]
            },
            "output_dimensionality": 768
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("embedding", {}).get("values", [])


def add_document(doc_id, text, metadata=None):
    try:
        existing = docs_collection.get(ids=[str(doc_id)])
        if existing and existing.get("ids"):
            print(f"Documento '{doc_id}' ya existe. Se omite la ingesta.")
            return

        emb = get_gemini_embedding(text)
        docs_collection.add(
            ids=[str(doc_id)],
            documents=[text],
            metadatas=[metadata or {}],
            embeddings=[emb],
        )
        print(f"Documento '{doc_id}' agregado correctamente.")

    except Exception as e:
        print(f"Error al agregar documento '{doc_id}': {e}")


def query_documents(query: str, n_results=23):
    q_embed = get_gemini_embedding(query)
    results = docs_collection.query(
        query_embeddings=[q_embed], n_results=n_results)
    return results["documents"][0] if results["documents"] else []


def store_user_interaction(user_id: str, query: str, answer: str):
    combined_text = f"Usuario: {query}\nAsistente: {answer}"
    embedding = get_gemini_embedding(combined_text)
    print("Almacenando: ",combined_text, "user: ",user_id)
    history_collection.add(
        ids=[f"{user_id}-{uuid4()}"],
        documents=[combined_text],
        metadatas={"user_id": user_id},
        embeddings=[embedding],
    )


def gemini_get_user_history(user_id: str, limit: int = 10):
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
        parts = doc.split("\nAsistente:")
        if len(parts) == 2:
            query = parts[0].replace("Usuario:", "").strip()
            answer = parts[1].strip()
            history.append({"query": query, "answer": answer})
        else:
            history.append({"query": doc.strip(), "answer": ""})
    return list(reversed(history))


def search_user_history_gemini(user_id: str, search: str, n_results: int = 5):
    q_embed = get_gemini_embedding(search)
    results = history_collection.query(
        query_embeddings=[q_embed], n_results=n_results, where={
            "user_id": user_id}
    )
    docs_nested = results.get("documents", [])
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


def generate_answer_gemini(query: str, context: str, temperature: float = 0.8):
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"=== CONTEXT ===\n{context}\n\n"
        f"=== PREGUNTA DEL USUARIO ===\n{query}\n\n"
        "=== INSTRUCCIÓN ===\n"
        "Responde solo con información del contexto. Sé claro y conciso."
    )
    url = f"{GEMINI_API_BASE}/models/gemini-2.0-flash-lite:generateContent?key={GOOGLE_API_KEY}"
    try:
        print("contexto: ", prompt)
        response = httpx.post(url, json={
            "contents": [
                {
                    "role": "user",
                    "parts": [{
                        "text": prompt}]
                }
            ]
        },
            timeout=120
        )
        response.raise_for_status()
        data = response.json()

        # Gemini responde con un formato anidado
        candidates = data.get("candidates", [])
        if not candidates:
            return ERROR_MESSAGE

        text = candidates[0].get("content", {}).get(
            "parts", [{}])[0].get("text", "")
        return clean_response(text)

    except Exception as e:
        print(f"Error en generate_answer_gemini: {e}")
        return ERROR_MESSAGE


def handle_chat_query_gemini(query: str, user_id: str):
    docs = query_documents(query)
    context = "\n".join(docs) if docs else "Sin contexto de documentos."
    user_history = search_user_history_gemini(user_id=user_id, search=query)
    context += "\n\nHistorial relevante:\n"
    if user_history:
        formatted_history = [
            f"Usuario: {item['query']}\nAsistente: {item['answer']}"
            for item in user_history
            if isinstance(item, dict)
        ]
        context += "\n".join(formatted_history)
    else:
        context += "\nSin historial previo relevante.\n"

    try:
        answer = generate_answer_gemini(query, context)
        print("Respuesta:", answer)
        if answer != ERROR_MESSAGE:
            pass
            store_user_interaction(user_id, query, answer)
        return answer
    except Exception as e:
        print(e)
        return ERROR_MESSAGE


def clean_response(text: str) -> str:
    text = re.sub(r"```+", "", text)
    text = text.strip()
    if text.startswith("Asistente:"):
        text = text.replace("Asistente:", "").strip()
    return text
