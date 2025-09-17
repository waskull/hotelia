import subprocess
import os
import time
import platform

# Define la ruta base de tu proyecto
base_dir = os.path.dirname(os.path.abspath(__file__))

# Define los microservicios a iniciar
microservices = [
    {'name': 'api-gateway', 'port': 8000},
    {'name': 'auth-service', 'port': 8001},
    {'name': 'hotels-service', 'port': 8002},
    {'name': 'reservations-service', 'port': 8003},
    {'name': 'notifications-service', 'port': 8004},
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

def start_services():
    """Inicia todos los microservicios definidos."""
    print("Iniciando microservicios...")
    python_executable = get_python_executable()

    if not os.path.exists(python_executable):
        print(f"❌ Error: El ejecutable de Python del entorno virtual no se encontró en '{python_executable}'.")
        return

    for service in microservices:
        service_path = os.path.join(base_dir, service['name'])
        
        if not os.path.isdir(service_path):
            print(f"❌ Error: El directorio '{service['name']}' no existe en {base_dir}")
            continue

        # Usa la ruta completa del ejecutable de Python del venv
        command = [
            python_executable, 'manage.py', 'runserver', f'0.0.0.0:{service["port"]}'
        ]
        
        if platform.system() == 'Windows':
            kwargs = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
        else:
            kwargs = {'preexec_fn': os.setsid}

        try:
            process = subprocess.Popen(
                command,
                cwd=service_path,
                **kwargs
            )
            processes.append(process)
            print(f"✔️ Microservicio '{service['name']}' iniciado en el puerto {service['port']}. PID: {process.pid}")
            time.sleep(2)
        except FileNotFoundError:
            print(f"❌ Error: El comando o manage.py no se encontró. Asegúrate de que el entorno virtual esté completo y las dependencias instaladas.")
        except Exception as e:
            print(f"❌ Error al iniciar el microservicio '{service['name']}': {e}")

def stop_services():
    """Detiene todos los procesos de los microservicios."""
    print("\nDeteniendo microservicios...")
    for process in processes:
        try:
            if platform.system() == 'Windows':
                subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], check=True)
            else:
                os.killpg(os.getpgid(process.pid), subprocess.signal.SIGTERM)
            print(f"Proceso con PID {process.pid} terminado.")
        except Exception as e:
            print(f"Error al terminar el proceso {process.pid}: {e}")
    processes.clear()
    print("Todos los microservicios han sido detenidos.")

if __name__ == "__main__":    
    start_services()

    print("\nTodos los microservicios están en ejecución. Presiona Ctrl+C para detenerlos.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSeñal de interrupción recibida. Deteniendo los servicios...")
        stop_services()

        print("Saliendo del script.")
