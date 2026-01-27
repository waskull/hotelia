# Hotelia — Plataforma de Reserva de Habitaciones.

**Hotelia** es una plataforma modular basada en **microservicios** que gestiona reservas de habitaciones en hoteles.

Cuenta además con un **chatbot inteligente (RAG)** integrado en el microservicio `chat-service`, el cual utiliza **ChromaDB** para recuperación de conocimiento y soporta modelos locales y externos mediante **Ollama**, **llama.cpp** y **Gemini**.

Visita la api demo en: 👉 [Hotelia](https://hotelia-production.up.railway.app/api/) - [Mirror](https://hotelia.onrender.com/api/)
Visita la documentación en: 👉 [Hotelia Docs](https://hotelia-production.up.railway.app/api/docs/) - [Hotelia Docs Mirror](https://hotelia.onrender.com/api/docs/)

---

## 🏨 Características principales de Hotelia

- 🔑 **Autenticación JWT** gracias a SimpleJWT.
- 🧿 **Sistema de reserva** solo registrate y reserva tu habitación.
- 📩 **Notificaciones por correo** cuando tu reserva es realizada recibiras una notificación por correo electronico.
- 🧾 **API RESTful** con Django REST Framework.
- 💾 **Persistencia** en SQLite (metadatos).

---



## 🚀 Características principales del Chatbot

- 🔍 **Búsqueda semántica** con embeddings.
- 🧠 **Generación aumentada** con contexto recuperado desde ChromaDB.
- ⚡ **Ejecución local** del modelo LLM (ej. Gemma 3 1B, Llama 3.2 1B, Gemma 3 4B, etc.) mediante `llama.cpp` u `Ollama`.
- 🧾 **API RESTful** con Django REST Framework.
- 💾 **Persistencia** con ChromaDB (vectores).
- 🧱 Arquitectura modular y extensible (puedes cambiar el modelo o el vector store fácilmente).

---

## 🧩 Arquitectura general

```text
                                            ┌──────────────────────┐
                                            │      Cliente Web     │
                                            └──────────┬───────────┘
                                                       │
                                           (Todas las peticiones HTTP)
                                                       │
                                            ┌──────────▼───────────┐
                                            │     API Gateway      │
                                            └──────────┬───────────┘
           ┌─────────────────────┼─────────────────────┼──────────────────────┼─────────────────────┐
           │                     │                     │                      │                     │
   ┌───────▼───────┐     ┌───────▼────────┐    ┌───────▼────────┐     ┌───────▼───────┐     ┌───────▼───────┐
   │ Auth Service  │     │  Hotels Service│    │  Reservations  │     │ Notifications │     │ Chat Service  │
   │ (JWT, tokens) │     │  (Hoteles)     │    │  Service       │     │ Service       │     │ (RAG Chatbot) │
   └───────────────┘     └────────────────┘    └────────────────┘     └───────────────┘     └───────────────┘
