import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import OperationalError # Conector para la base de datos PostgreSQL

class Conector:
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.coneccion = None

    def conectar(self):
        try:
            self.coneccion = psycopg2.connect(
                host="localhost",       # Reemplaza con tu host
                user= self.user,             # Usuario de la base de datos
                password= self.password,      # Contraseña
                dbname="Fru7",     # Nombre de la base de datos
                port="5432",                    # Puerto por defecto de PostgreSQL
                options='-c client_encoding=utf8'
            )
            return self.coneccion
        except psycopg2.Error as error:
            print("USUARIO O CONTRASEÑA INCORRECTOS", error)
            return None
        except Exception as e:
            print(f"Error desconocido: {e}")
            return None
    
    def cerrar(self):
        if self.coneccion:
            try:
                self.coneccion.close()
            except Exception as e:
                print("Error cerrando conexión:", e)
            finally:
                self.coneccion = None
