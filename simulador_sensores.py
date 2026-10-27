"""
PROYECTO: Invernadero Asistivo Ciberfísico
ARCHIVO: simulador_sensores.py
PROPÓSITO: Generar telemetría en tiempo real con alertas programadas y espaciadas,
           incluyendo el escenario de Frío + Gases para validar el temporizador
           y la pausa térmica (Opción 2) en la interfaz web.
LENGUAJE: Python 3
"""

import time
import random
import requests

# Endpoints locales de Flask
URL_SUELO = "http://localhost:5000/api/suelo"
URL_AIRE  = "http://localhost:5000/api/aire"

# -------------------------------------------------------------
# CONFIGURACIÓN DEL TIEMPO DE CADA ALERTA (EN SEGUNDOS)
# -------------------------------------------------------------
# Puedes ajustar este valor: 60 = 1 minuto por fase, 120 = 2 minutos, etc.
SEGUNDOS_POR_ESCENARIO = 60 

print("=======================================================", flush=True)
print("🚀 SIMULADOR DE TELEMETRÍA CON ESCENARIOS TEMPORIZADOS", flush=True)
print(f"   Cada estado durará aproximadamente {SEGUNDOS_POR_ESCENARIO} segundos.", flush=True)
print("   Enviando datos cada 3 segundos a http://localhost:5000", flush=True)
print("   (Presiona Ctrl + C en esta terminal para detenerlo)", flush=True)
print("=======================================================\n", flush=True)

tiempo_inicio = time.time()

def oscilar(base, margen):
    """Agrega una pequeña variación decimal para que el número cambie en cada ciclo"""
    return round(base + random.uniform(-margen, margen), 1)

while True:
    segundos_transcurridos = int(time.time() - tiempo_inicio)
    
    # Ahora rotamos entre 6 fases (0 a 5)
    fase = (segundos_transcurridos // SEGUNDOS_POR_ESCENARIO) % 6
    segundos_en_fase = segundos_transcurridos % SEGUNDOS_POR_ESCENARIO

    # ---------------------------------------------------------
    # DEFINICIÓN DE LOS ESCENARIOS POR FASE
    # ---------------------------------------------------------
    if fase == 0:
        # FASE 0: Todo normal y óptimo (Todos los pictogramas en Verde)
        c1_azul   = oscilar(55.0, 1.2)
        c1_morado = oscilar(52.0, 1.0)
        c1_tierra = oscilar(20.0, 0.4)
        temp_aire = oscilar(22.5, 0.5)
        co_aire   = oscilar(2.2, 0.3)
        co2_aire  = oscilar(600.0, 20.0)
        mensaje_fase = "🟢 ESTADO 0: Todo Óptimo (4 pictogramas en Verde)"

    elif fase == 1:
        # FASE 1: Alerta de RIEGO (Humedad < 40%)
        c1_azul   = oscilar(31.5, 0.8)  # Dispara regadera en rojo
        c1_morado = oscilar(50.0, 1.0)
        c1_tierra = oscilar(20.5, 0.3)
        temp_aire = oscilar(23.0, 0.5)
        co_aire   = oscilar(2.0, 0.2)
        co2_aire  = oscilar(620.0, 15.0)
        mensaje_fase = "🔴 ALERTA 1: ¡Riego requerido en Zona Azul del Cajón 1!"

    elif fase == 2:
        # FASE 2: Alerta de VENTILACIÓN EN TEMPLADO (CO2 > 1200 ppm, sin frío)
        c1_azul   = oscilar(53.0, 1.0)
        c1_morado = oscilar(51.0, 1.0)
        c1_tierra = oscilar(20.0, 0.3)
        temp_aire = oscilar(24.0, 0.6)
        co_aire   = oscilar(3.5, 0.4)
        co2_aire  = oscilar(1380.0, 30.0) # > 1200 activa ventana en rojo
        mensaje_fase = "🔴 ALERTA 2: ¡Ventilación por Gases en clima normal (Sin temporizador)!"

    elif fase == 3:
        # FASE 3: Alerta de TEMPERATURA AMBIENTE (Calor en el aire > 28°C)
        c1_azul   = oscilar(48.0, 1.0)
        c1_morado = oscilar(49.0, 1.0)
        c1_tierra = oscilar(22.0, 0.4)
        temp_aire = oscilar(31.5, 0.7)  # > 28°C activa termómetro en rojo
        co_aire   = oscilar(2.4, 0.3)
        co2_aire  = oscilar(700.0, 20.0)
        mensaje_fase = "🔴 ALERTA 3: ¡Temperatura Ambiental alta en el invernadero!"

    elif fase == 4:
        # FASE 4: CASO ESPECIAL OPCIÓN 2 -> AMBIENTE FRÍO (< 15°C) + GASES (> 1200 ppm)
        # Activa la cuenta regresiva de 5 minutos y la posterior pausa térmica de 3 minutos
        c1_azul   = oscilar(50.0, 1.0)
        c1_morado = oscilar(51.0, 1.0)
        c1_tierra = oscilar(18.0, 0.4)
        temp_aire = oscilar(11.8, 0.5)  # < 15°C: Frío ambiental
        co_aire   = oscilar(12.5, 0.6)  # > 10 ppm: CO alto
        co2_aire  = oscilar(1350.0, 25.0) # > 1200 ppm: CO2 alto
        mensaje_fase = "⏱️ ALERTA 4 (OPCIÓN 2): ¡Frío (11.8°C) + Gases! Activa temporizador de ventilación"

    elif fase == 5:
        # FASE 5: ALERTA DOBLE (Riego en Cajón 2 Morado + Tierra Caliente en Cajón 1)
        c1_azul   = oscilar(50.0, 1.0)
        c1_morado = oscilar(52.0, 1.0)
        c1_tierra = oscilar(28.5, 0.5)  # > 26°C activa temperatura de tierra en rojo
        temp_aire = oscilar(24.5, 0.4)
        co_aire   = oscilar(2.1, 0.2)
        co2_aire  = oscilar(650.0, 15.0)
        c2_morado_doble = oscilar(33.0, 0.8) # < 40% activa riego en Cajón 2
        mensaje_fase = "🔴🔴 ALERTA 5: Doble Alerta (Riego Cajón 2 + Tierra Caliente Cajón 1)"

    # Variables para Cajón 2 (se mantienen estables salvo en la fase 5)
    c2_azul_val   = oscilar(54.0, 1.0)
    c2_morado_val = c2_morado_doble if fase == 5 else oscilar(51.0, 1.0)
    c2_tierra_val = oscilar(20.2, 0.3)

    # ---------------------------------------------------------
    # PAQUETES JSON PARA FLASK Y MYSQL
    # ---------------------------------------------------------
    payload_cajon1 = {
        "id_cajon": 1,
        "humedad_azul": c1_azul,
        "humedad_morado": c1_morado,
        "temp_sustrato": c1_tierra
    }

    payload_cajon2 = {
        "id_cajon": 2,
        "humedad_azul": c2_azul_val,
        "humedad_morado": c2_morado_val,
        "temp_sustrato": c2_tierra_val
    }

    payload_aire_ade = {
        "ubicacion": "adelante",
        "temp_ambiente": temp_aire,
        "humedad_ambiente": oscilar(56.0, 1.5),
        "co_mq7": co_aire
    }

    payload_aire_atr = {
        "ubicacion": "atras",
        "temp_ambiente": temp_aire,
        "humedad_ambiente": oscilar(55.0, 1.5),
        "co_mq7": co_aire,
        "co2_scd30": co2_aire
    }

    # Transmisión HTTP
    try:
        requests.post(URL_SUELO, json=payload_cajon1, timeout=2)
        requests.post(URL_SUELO, json=payload_cajon2, timeout=2)
        requests.post(URL_AIRE, json=payload_aire_ade, timeout=2)
        requests.post(URL_AIRE, json=payload_aire_atr, timeout=2)

        print(f"[{segundos_en_fase}s / {SEGUNDOS_POR_ESCENARIO}s] {mensaje_fase}", flush=True)
        print(f"   -> C1: Azul={c1_azul}% | Morado={c1_morado}% | Tierra={c1_tierra}°C", flush=True)
        print(f"   -> Aire: Temp={temp_aire}°C | CO={co_aire} ppm | CO2={co2_aire} ppm", flush=True)
        print("----------------------------------------------------------------", flush=True)

    except requests.exceptions.ConnectionError:
        print("⚠️ AVISO: Servidor app.py desconectado. ¿Está corriendo en la otra terminal?", flush=True)
    except Exception as err:
        print(f"⚠️ Error al enviar: {err}", flush=True)

    time.sleep(3)