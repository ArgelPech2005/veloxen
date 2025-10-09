import mysql.connector
import time

def test_conexion_clever_cloud():
    try:
        # Inicio de tiempo para medir latencia de consulta
        start_total = time.time()

        # Conexión a Clever Cloud
        conn = mysql.connector.connect(
            host="bmpkp5mzuoyegtdi1unp-mysql.services.clever-cloud.com",
            user="u1xl9tvffkdbmhpc",
            password="oTEH5DchNRefhZxe1DEC",
            database="bmpkp5mzuoyegtdi1unp"
        )
        
        cursor = conn.cursor()

        # Inicio de tiempo para medir consulta
        start_query = time.time()

        cursor.execute("SELECT 1")
        resultado = cursor.fetchone()

        end_query = time.time()
        end_total = time.time()

        print(f"✔️ Resultado consulta: {resultado}")
        print(f"⏱️ Tiempo de la consulta SQL: {end_query - start_query:.4f} segundos")
        print(f"⏱️ Tiempo total conexión + consulta: {end_total - start_total:.4f} segundos")

        # Cierra conexiones
        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        print(f"❌ Error de conexión o consulta: {err}")

