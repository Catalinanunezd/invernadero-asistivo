"""
PROYECTO: Invernadero Asistivo Ciberfísico
ARCHIVO: app.py
PROPÓSITO: Servidor API Flask conectado a MySQL en XAMPP.
           Sirve la interfaz web y procesa los pictogramas en tiempo real.
LENGUAJE: Python 3
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import pymysql

app = Flask(__name__, template_folder='templates')
CORS(app)

# Configuración de conexión a la base de datos de XAMPP
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '', # Vacío por defecto en XAMPP
    'database': 'invernadero_asistivo',
    'port': 3306,
    'cursorclass': pymysql.cursors.DictCursor
}

def obtener_conexion():
    return pymysql.connect(**DB_CONFIG)

# Umbrales agronómicos base (ajustables según necesidad)
UMBRAL_HUMEDAD_RIEGO = 40.0   # Menos de 40%: activar alerta de riego
TEMP_TIERRA_FRIO     = 15.0   # Menos de 15°C: sustrato frío
TEMP_TIERRA_CALOR    = 26.0   # Más de 26°C: sustrato caliente
TEMP_AIRE_FRIO       = 15.0   # Menos de 15°C en aire
TEMP_AIRE_CALOR      = 28.0   # Más de 28°C en aire
UMBRAL_CO_MQ7        = 10.0   # Límite seguro de CO
UMBRAL_CO2_SCD30     = 1200.0 # Límite seguro de CO2

@app.route('/api/suelo', methods=['POST'])
def registrar_suelo():
    """Recibe mediciones de Cajón 1 o Cajón 2"""
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "Formato JSON inválido"}), 400

    id_cajon = datos.get('id_cajon')
    hum_azul = datos.get('humedad_azul')
    hum_morado = datos.get('humedad_morado')
    temp_sustrato = datos.get('temp_sustrato')

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """INSERT INTO lecturas_suelo 
                     (id_cajon, humedad_azul, humedad_morado, temp_sustrato) 
                     VALUES (%s, %s, %s, %s)"""
            cursor.execute(sql, (id_cajon, hum_azul, hum_morado, temp_sustrato))
        conexion.commit()
    finally:
        conexion.close()

    return jsonify({"mensaje": f"Lectura de Cajón {id_cajon} registrada"}), 201

@app.route('/api/aire', methods=['POST'])
def registrar_aire():
    """Recibe mediciones de aire (Adelante o Atrás)"""
    datos = request.get_json()
    if not datos:
        return jsonify({"error": "Formato JSON inválido"}), 400

    ubicacion = datos.get('ubicacion')
    temp_amb = datos.get('temp_ambiente')
    hum_amb = datos.get('humedad_ambiente')
    co_mq7 = datos.get('co_mq7')
    co2_scd30 = datos.get('co2_scd30', None)

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """INSERT INTO lecturas_aire 
                     (ubicacion, temp_ambiente, humedad_ambiente, co_mq7, co2_scd30) 
                     VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(sql, (ubicacion, temp_amb, hum_amb, co_mq7, co2_scd30))
        conexion.commit()
    finally:
        conexion.close()

    return jsonify({"mensaje": f"Lectura de Aire ({ubicacion}) registrada"}), 201

@app.route('/api/estado_actual', methods=['GET'])
def obtener_estado_actual():
    """Retorna la última medición de cada sector y evalúa los 4 pictogramas"""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM lecturas_suelo WHERE id_cajon = 1 ORDER BY id DESC LIMIT 1")
            cajon1 = cursor.fetchone() or {"humedad_azul": 55.0, "humedad_morado": 55.0, "temp_sustrato": 20.0}

            cursor.execute("SELECT * FROM lecturas_suelo WHERE id_cajon = 2 ORDER BY id DESC LIMIT 1")
            cajon2 = cursor.fetchone() or {"humedad_azul": 55.0, "humedad_morado": 55.0, "temp_sustrato": 20.0}

            cursor.execute("SELECT * FROM lecturas_aire WHERE ubicacion = 'adelante' ORDER BY id DESC LIMIT 1")
            aire_adelante = cursor.fetchone() or {"temp_ambiente": 22.0, "humedad_ambiente": 60.0, "co_mq7": 2.0}

            cursor.execute("SELECT * FROM lecturas_aire WHERE ubicacion = 'atras' ORDER BY id DESC LIMIT 1")
            aire_atras = cursor.fetchone() or {"temp_ambiente": 22.0, "humedad_ambiente": 60.0, "co_mq7": 2.0, "co2_scd30": 600.0}

        # Evaluación lógica de los 4 pictogramas (Verde = False, Rojo = True)
        
        # 1. Pictograma Riego por zonas
        c1_azul_alerta = cajon1["humedad_azul"] < UMBRAL_HUMEDAD_RIEGO
        c1_morado_alerta = cajon1["humedad_morado"] < UMBRAL_HUMEDAD_RIEGO
        c2_azul_alerta = cajon2["humedad_azul"] < UMBRAL_HUMEDAD_RIEGO
        c2_morado_alerta = cajon2["humedad_morado"] < UMBRAL_HUMEDAD_RIEGO

        # 2. Pictograma Temperatura de Sustrato (por cajón)
        c1_tierra_alerta = (cajon1["temp_sustrato"] < TEMP_TIERRA_FRIO) or (cajon1["temp_sustrato"] > TEMP_TIERRA_CALOR)
        c2_tierra_alerta = (cajon2["temp_sustrato"] < TEMP_TIERRA_FRIO) or (cajon2["temp_sustrato"] > TEMP_TIERRA_CALOR)

        # 3. Pictograma Temperatura de Aire
        temp_aire_promedio = round((aire_adelante["temp_ambiente"] + aire_atras["temp_ambiente"]) / 2.0, 1)
        aire_temp_alerta = (temp_aire_promedio < TEMP_AIRE_FRIO) or (temp_aire_promedio > TEMP_AIRE_CALOR)

        # 4. Pictograma Ventilación y Gases (Evaluación conjunta OR)
        gases_alerta = (
            aire_adelante["co_mq7"] > UMBRAL_CO_MQ7 or
            aire_atras["co_mq7"] > UMBRAL_CO_MQ7 or
            (aire_atras.get("co2_scd30") is not None and aire_atras["co2_scd30"] > UMBRAL_CO2_SCD30)
        )

        respuesta = {
            "cajon1": {
                "humedad_azul": cajon1["humedad_azul"],
                "alerta_azul": c1_azul_alerta,
                "humedad_morado": cajon1["humedad_morado"],
                "alerta_morado": c1_morado_alerta,
                "temp_sustrato": cajon1["temp_sustrato"],
                "alerta_sustrato": c1_tierra_alerta
            },
            "cajon2": {
                "humedad_azul": cajon2["humedad_azul"],
                "alerta_azul": c2_azul_alerta,
                "humedad_morado": cajon2["humedad_morado"],
                "alerta_morado": c2_morado_alerta,
                "temp_sustrato": cajon2["temp_sustrato"],
                "alerta_sustrato": c2_tierra_alerta
            },
            "aire": {
                "adelante": aire_adelante,
                "atras": aire_atras,
                "temp_promedio": temp_aire_promedio,
                "alerta_temperatura_aire": aire_temp_alerta,
                "alerta_ventilacion_gases": gases_alerta
            }
        }
    finally:
        conexion.close()

    return jsonify(respuesta)

@app.route('/')
def pagina_principal():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)