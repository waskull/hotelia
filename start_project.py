import subprocess
import os
import time
import platform
import sys
import signal  # Importamos signal para manejar la señal de terminación de forma más robusta

# Define la ruta base de tu proyecto
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define los microservicios a iniciar
# NOTA: Asegúrate de que 'app_module' apunte a la ruta de tu aplicación ASGI (ej: 'project_name.asgi:application')
microservices = [
    {'name': 'api-gateway', 'port': 8000, 'app_module': 'core.asgi:application'},
    {'name': 'auth-service', 'port': 8001,
        'app_module': 'auth_service.asgi:application'},
    {'name': 'hotels-service', 'port': 8002,
        'app_module': 'hotels_service.asgi:application'},
    {'name': 'reservations-service', 'port': 8003,
        'app_module': 'reservations_service.asgi:application'},
    {'name': 'notifications-service', 'port': 8004,
        'app_module': 'notifications_service.asgi:application'},
]


# Lista para almacenar los procesos de los microservicios
processes = []


def get_python_executable():
    """Retorna la ruta del ejecutable de Python del entorno virtual."""
    venv_path = os.path.join(base_dir, 'venv')
    if platform.system() == 'Windows':
        return os.path.join(venv_path, 'Scripts', 'python.exe')
    else:
        return os.path.join(venv_path, 'bin', 'python')


def get_uvicorn_executable():
    """Retorna la ruta del ejecutable de uvicorn del entorno virtual."""
    venv_path = os.path.join(base_dir, 'venv')
    if platform.system() == 'Windows':
        # En Windows, los ejecutables suelen estar en Scripts
        return os.path.join(venv_path, 'Scripts', 'uvicorn.exe')
    else:
        # En Linux/macOS, los ejecutables suelen estar en bin
        return os.path.join(venv_path, 'bin', 'uvicorn')


def start_services():
    """Inicia todos los microservicios definidos usando Uvicorn."""
    print("Iniciando microservicios con Uvicorn...")

    use_uvicorn = input(
        "¿Deseas usar Uvicorn para iniciar los microservicios? (s/n): ").lower().strip()
    if use_uvicorn != 's':
        print("No iniciaremos los microservicios con Uvicorn.")
    else:
        print("Iniciando microservicios con Uvicorn...")

    uvicorn_executable = get_uvicorn_executable()
    python_executable = get_python_executable()

    if not os.path.exists(uvicorn_executable):
        print(
            f"❌ Error: El ejecutable de Uvicorn no se encontró en '{uvicorn_executable}'.")
        print("Asegúrate de haber instalado uvicorn en tu entorno virtual (pip install uvicorn).")
        return

    for service in microservices:
        service_path = os.path.join(base_dir, service['name'])

        if not os.path.isdir(service_path):
            print(
                f"❌ Error: El directorio '{service['name']}' no existe en {base_dir}")
            continue

        # El comando de Uvicorn: uvicorn <app_module> --host 0.0.0.0 --port <port>
        # Nota: <app_module> debe ser la ruta a tu aplicación ASGI (ej: api_gateway.asgi:application)

        if use_uvicorn == 's':
            command = [
                uvicorn_executable, service['app_module'], '--host', '0.0.0.0', '--port', str(
                    service['port']), '--reload'
            ]
        else:
            command = [
                python_executable, 'manage.py', 'runserver', f'0.0.0.0:{service["port"]}'
            ]

        # Configuración para que los procesos se puedan terminar correctamente
        if platform.system() == 'Windows':
            # Usa CREATE_NEW_PROCESS_GROUP en Windows para asegurar el manejo de la terminación
            kwargs = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
        else:
            # Usa os.setsid en Linux/macOS para crear un nuevo grupo de procesos
            kwargs = {'preexec_fn': os.setsid}

        try:
            # Iniciamos el proceso de Uvicorn
            process = subprocess.Popen(
                command,
                cwd=service_path,  # Ejecutamos el comando desde la carpeta del microservicio
                **kwargs,
                # Puedes redirigir stdout y stderr a un archivo o a /dev/null si quieres un output más limpio
                # stdout=subprocess.PIPE,
                # stderr=subprocess.PIPE
            )
            processes.append(process)
            print(
                f"✔️ Microservicio '{service['name']}' iniciado con Uvicorn en http://0.0.0.0:{service['port']}. PID: {process.pid}")
            # Damos un pequeño tiempo para que el servidor se inicialice
            time.sleep(1)
        except FileNotFoundError:
            print(f"❌ Error: El ejecutable de uvicorn no se encontró. Asegúrate de que el entorno virtual esté activo y uvicorn instalado.")
        except Exception as e:
            print(
                f"❌ Error al iniciar el microservicio '{service['name']}': {e}")


def stop_services():
    """Detiene todos los procesos de los microservicios."""
    print("\nDeteniendo microservicios...")
    for service_process in processes:
        try:
            pid = service_process.pid
            if platform.system() == 'Windows':
                # Terminación forzada del árbol de procesos en Windows
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(pid)],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                # Envía SIGTERM al grupo de procesos para terminar uvicorn y sus subprocesos (si los hay)
                try:
                    pgid = os.getpgid(pid)
                    os.killpg(pgid, signal.SIGTERM)
                except ProcessLookupError:
                    # Si el proceso ya terminó, continuamos
                    pass
            print(f"Proceso con PID {pid} terminado.")
        except Exception as e:
            print(
                f"Error al intentar terminar el proceso {service_process.pid}: {e}")

    # Limpiar la lista de procesos después de detenerlos
    processes.clear()
    print("Todos los microservicios han sido detenidos.")


if __name__ == "__main__":
    # Validar que los módulos de aplicación estén definidos
    for service in microservices:
        if 'app_module' not in service:
            print("❌ Error de configuración: 'app_module' no está definido para un servicio. Revisa la lista 'microservices'.")
            sys.exit(1)

    start_services()

    print("\nTodos los microservicios están en ejecución. Presiona Ctrl+C para detenerlos. 🛑")
    try:
        # Bucle principal para mantener el script en ejecución
        while True:
            time.sleep(1)
            # También puedes añadir una verificación de estado de los procesos aquí si es necesario
    except KeyboardInterrupt:
        print("\nSeñal de interrupción recibida. Deteniendo los servicios...")
        stop_services()
        print("Saliendo del script. 👋")
