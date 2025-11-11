import httpx
from django.core.management.base import BaseCommand
from django.conf import settings
from llama.rag_llamacpp import add_document
from llama.rag import add_document as ollama_add_document
from llama.rag_gemini import add_document as gemini_add_document

HOTELS_API = f"{settings.HOTELS_SERVICE_URL}hotels/"
ROOMS_API = f"{settings.HOTELS_SERVICE_URL}rooms/"


class Command(BaseCommand):
    help = "Ingesta documentos desde los microservicios de hoteles y habitaciones."

    def add_arguments(self, parser):
        parser.add_argument(
            "--engine",
            type=str,
            choices=["ollama", "llama", "gemini"],
            default="llama",
            help="Motor para generar embeddings (ollama, llama o Gemini).",
        )

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando proceso de ingesta...")
        engine = kwargs["engine"]
        self.stdout.write(self.style.WARNING(f"Usando motor: {engine}"))
        total_docs = 0
        headers = {
            "Content-Type": "application/json",
            "X-Hotel-Gateway-Token": settings.HOTELS_GATEWAY_TOKEN
        }
        # Cliente httpx
        client = httpx.Client(timeout=10.0, headers=headers)

        # Habitaciones
        try:
            self.stdout.write("Obteniendo datos de hoteles...")
            hotel_response = client.get(HOTELS_API)
            hotel_response.raise_for_status()
            hotels = hotel_response.json()

            for hotel in hotels:
                id = hotel.get("id", "unknown")
                name = hotel.get("name", "Hotel sin nombre")
                desc = hotel.get("description", "")
                stars = hotel.get("star_rating", 1)
                city = hotel.get("city", "")
                payment_policy = hotel.get("payment_policy", "")
                reservation_policy = hotel.get("reservation_policy", "")
                email = hotel.get("email", "Hotel sin correo")
                phone = hotel.get("phone", "Hotel sin telefono")
                services = hotel.get("services", "")
                text = (
                    f"Hotel: {name}. "
                    f"Descripción: {desc}. "
                    f"Estrellas: Hotel de {stars} estrellas. "
                    f"Servicios: {services}. "
                    f"Correo: {email}. "
                    f"Telefono: {phone}. "
                    f"Ciudad: {city}. "
                    f"Política de pago: {payment_policy}. "
                    f"Política de reservaciones: {reservation_policy}."
                )
                print(text)

                if engine == "ollama":
                    ollama_add_document(
                        doc_id=f"hotel_{id}",
                        text=text,
                        metadata={"source": "hotel", "id": id},
                    )
                elif engine == "gemini":
                    gemini_add_document(
                        doc_id=f"hotel_{id}",
                        text=text,
                        metadata={"source": "hotel", "id": id},
                    )
                else:
                    add_document(
                        doc_id=f"hotel_{id}",
                        text=text,
                        metadata={"source": "hotel", "id": id},
                    )
                total_docs += 1

            self.stdout.write(
                f"{len(hotels)} hoteles ingresados correctamente.")
        except Exception as e:
            self.stderr.write(f"Error al obtener hoteles: {e}")

        # Habitaciones
        try:
            self.stdout.write("Obteniendo datos de habitaciones...")
            rooms_response = client.get(ROOMS_API)
            rooms_response.raise_for_status()
            rooms = rooms_response.json()

            for room in rooms:
                hotel = room.get("hotel")
                print(hotel)
                id = room.get("id", "unknown")
                number = room.get("room_number", "Sin número")
                hotel_name = str(room.get("hotel_name", "Hotel sin nombre"))
                room_type = room.get("room_type", "")
                price = room.get("price_per_night", "")
                capacity = room.get("capacity", "")
                text = (
                    f"Habitación {number} del hotel {hotel_name}. "
                    f"Tipo de habitación: {room_type}. "
                    f"Capacidad: {capacity}. "
                    f"Precio por noche: {price}$."
                )
                print(text)
                add_document(
                    doc_id=f"room_{id}",
                    text=text,
                    metadata={"source": "room", "id": id}
                )
                total_docs += 1

            self.stdout.write(
                f"{len(rooms)} habitaciones ingresadas correctamente.")
        except Exception as e:
            self.stderr.write(f"Error al obtener habitaciones: {e}")

        client.close()
        self.stdout.write(self.style.SUCCESS(
            f"Ingesta completada. Total documentos: {total_docs}"))
