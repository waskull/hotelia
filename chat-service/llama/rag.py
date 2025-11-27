import chromadb
import httpx
from django.conf import settings

OLLAMA_API = getattr(settings, "OLLAMA_API", "http://localhost:11434/api")
MODEL_NAME = getattr(settings, "MODEL_NAME", "no_model")
client = chromadb.PersistentClient(path="./chroma_store")
collection_docs = client.get_or_create_collection("hotel_docs")
collection_chat = client.get_or_create_collection("chat_history")

SYSTEM_PROMPT = (
    "Eres el asistente de reservas del sistema Hotelia. "
    "Usa solo la información provista en 'Context' para responder "
    "consultas sobre hoteles, habitaciones y políticas de reserva o pago. "
    "Si no puedes responder con la información disponible, indica que no puedes responder. "
)

ERROR_MESSAGE = "No pude generar la respuesta."

# === FUNCIONES DE EMBEDDING ===
def get_ollama_embedding(text: str):
    with httpx.Client(timeout=900.0) as client_http:
        resp = client_http.post(f"{OLLAMA_API}embeddings", json={
            "model": "nomic-embed-text",
            "prompt": text,
        })
        resp.raise_for_status()
        return resp.json()["embedding"]

def add_document(doc_id, text, metadata=None):
    emb = get_ollama_embedding(text)
    collection_docs.add(
        ids=[str(doc_id)],
        documents=[text],
        metadatas=[metadata or {}],
        embeddings=[emb],
    )

def query_documents(query, n_results=8):
    q_embed = get_ollama_embedding(query)
    results = collection_docs.query(query_embeddings=[q_embed], n_results=n_results)
    return results["documents"][0] if results["documents"] else []

def query_user_history(user_query, user_id, n_results=3):
    q_embed = get_ollama_embedding(user_query)
    results = collection_chat.query(
        query_embeddings=[q_embed],
        n_results=n_results,
        where={"user_id": user_id}
    )
    if results and results["documents"]:
        return results["documents"][0]
    return []

def store_user_interaction(user_id, user_query, bot_answer):
    chat_text = f"Usuario: {user_query}\nAsistente: {bot_answer}"
    emb = get_ollama_embedding(chat_text)
    collection_chat.add(
        ids=[f"chat_{user_id or 'anon'}_{hash(user_query)}"],
        documents=[chat_text],
        metadatas=[{"user_id": user_id}],
        embeddings=[emb],
    )

def generate_answer(query, full_context):
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Context:\n{full_context}\n\n"
        f"Pregunta del usuario: {query}\n\n"
        "Respuesta:"
    )
    
    with httpx.Client(timeout=1000.0) as client_http:
        try:
            print("haciendo peticion")
            resp = client_http.post(f"{OLLAMA_API}generate", json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False
            })
            if resp.status_code == 200:
                resp.raise_for_status()
                data = resp.json()
                return data.get("response", ERROR_MESSAGE)
            else: return ERROR_MESSAGE
        except httpx.RequestError as e:
            print(e)
            return ERROR_MESSAGE
        
def get_user_history(user_id: str, limit: int = 10):
    results = collection_chat.get(where={"user_id": user_id})
    docs = results.get("documents", [])

    history = []
    for doc in docs[-limit:]:
        parts = doc.split("\nAsistente:")
        if len(parts) == 2:
            query = parts[0].replace("Usuario:", "").strip()
            answer = parts[1].strip()
            history.append({"query": query, "answer": answer})
    return list(reversed(history))  # devuelve en orden cronológico

def search_user_history(user_id: str, search: str, n_results: int = 5):
    results = collection_chat.get(where={"user_id": user_id})
    docs = results.get("documents", [])
    filtered = [doc for doc in docs if search.lower() in doc.lower()]
    filtered = filtered[-n_results:]

    history = []
    for doc in docs:
        parts = doc.split("\nAsistente:")
        if len(parts) == 2:
            query = parts[0].replace("Usuario:", "").strip()
            answer = parts[1].strip()
            history.append({"query": query, "answer": answer})
    return history

def handle_chat_query(query: str, user_id: str = "anon"):
    docs = query_documents(query)
    context = "\n".join(docs) if docs else "Sin contexto de documentos."
    user_history = query_user_history(query, user_id)
    context += "\n\nHistorial relevante:\n"
    if user_history:
        context += "\n".join(user_history)
    else: context += "\nSin historial previo relevante.\n"
    answer = generate_answer(query, context)
    if answer != ERROR_MESSAGE: store_user_interaction(user_id, query, answer)
    return answer
