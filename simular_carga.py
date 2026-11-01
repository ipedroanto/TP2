import requests
import time
import random

# CONFIGURACIÓN
# Apunta al backend FastAPI local o a tu puerto configurado en Docker (http://localhost:8000)
API_URL = "http://localhost:8000/analizar-reseña"

# Muestra de reseñas de prueba con diversidad de puntuaciones y categorías
DATASET_RESEÑAS = [
    {
        "cliente": "Carlos Mendoza",
        "correo": "carlos.mendoza@example.com",
        "puntuacion": 5,
        "comentario": "Excelente atención al cliente. El producto llegó antes de lo esperado y en perfectas condiciones.",
        "categoria": "Envío"
    },
    {
        "cliente": "Mariana Silva",
        "correo": "mariana.silva@example.com",
        "puntuacion": 1,
        "comentario": "El paquete llegó aplastado y roto. La atención telefónica fue pésima y no me dan solución.",
        "categoria": "Envío"
    },
    {
        "cliente": "Esteban Quito",
        "correo": "esteban.quito@example.com",
        "puntuacion": 4,
        "comentario": "Muy buen producto en relación precio-calidad. Cumple con las especificaciones.",
        "categoria": "Producto"
    },
    {
        "cliente": "Lucía Fernández",
        "correo": "lucia.f@example.com",
        "puntuacion": 2,
        "comentario": "El precio es desmedido para la baja calidad del material. No lo recomiendo.",
        "categoria": "Precio"
    },
    {
        "cliente": "Gonzalo Pérez",
        "correo": "gonzalo.perez@example.com",
        "puntuacion": 5,
        "comentario": "Increíble soporte técnico. Me ayudaron a configurar el equipo en 10 minutos.",
        "categoria": "Atención"
    },
    {
        "cliente": "Sofía Rossi",
        "correo": "sofia.rossi@example.com",
        "puntuacion": 3,
        "comentario": "El servicio es aceptable, pero la entrega demoró dos días más de lo prometido.",
        "categoria": "Envío"
    },
    {
        "cliente": "Martín Benítez",
        "correo": "martin.b@example.com",
        "puntuacion": 1,
        "comentario": "Me cobraron dos veces la factura y nadie me responde los correos. Exijo devolución.",
        "categoria": "Precio"
    },
    {
        "cliente": "Valeria Gómez",
        "correo": "valeria.gomez@example.com",
        "puntuacion": 4,
        "comentario": "Buena calidad general, el empaque podría mejorar pero el producto funciona muy bien.",
        "categoria": "Producto"
    }
]

def simular_carga_masiva(intervalo_segundos=1.5):
    print("=" * 70)
    print("🚀 INICIANDO SIMULACIÓN DE CARGA MASIVA DE RESEÑAS DE CLIENTES")
    print(f"🎯 Destino: {API_URL}")
    print(f"⏱️  Intervalo entre envíos: {intervalo_segundos} segundos")
    print("=" * 70 + "\n")

    exitosos = 0
    alertas = 0

    for i, resena in enumerate(DATASET_RESEÑAS, 1):
        print(f"➡️ [{i}/{len(DATASET_RESEÑAS)}] Enviando reseña de '{resena['cliente']}' ({resena['puntuacion']} ⭐)...")
        
        try:
            response = requests.post(API_URL, json=resena, timeout=5)
            
            if response.status_code == 201:
                data = response.json()
                exitosos += 1
                es_alerta = data.get("alerta_critica", False)
                
                if es_alerta:
                    alertas += 1
                    print(f"   🚨 ALERTA CRÍTICA REGISTRADA (Puntuación: {data['puntuacion']} <= 2) | ID DB: {data['id']}")
                else:
                    print(f"   ✅ Registrado con éxito | ID DB: {data['id']} | Estado: {data['estado_gestion']}")
            elif response.status_code == 422:
                print(f"   ❌ ERROR DE VALIDACIÓN PYDANTIC (422): {response.json()}")
            else:
                print(f"   ⚠️ Respuesta inesperada ({response.status_code}): {response.text}")

        except requests.exceptions.RequestException as e:
            print(f"   ❌ Fallo de conexión con la API: {e}")

        time.sleep(intervalo_segundos)

    print("\n" + "=" * 70)
    print("📊 RESUMEN DE LA SIMULACIÓN")
    print(f"✔️ Total procesadas: {exitosos}/{len(DATASET_RESEÑAS)}")
    print(f"🚨 Alertas críticas activadas: {alertas}")
    print("=" * 70)
    print("💡 Abre tu dashboard de Streamlit (http://localhost:8501) para ver las métricas actualizadas.")

if __name__ == "__main__":
    simular_carga_masiva(intervalo_segundos=1.5)
