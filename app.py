"""
    NOTA PARA ARGEL: llenar con los datos encriptaddos de la base de datos
    y agreagr los nombres de las tablas (todo exacto) y los respectivos campos de las mismas

    Tablas: 
    tbl_estado = id_estado, estado
    tbl_fecha = id_fecha, dia, mes, anio
    tbl_pedido = id_pedido, cantidad, importe_g, fecha, num_cel, tipo_pago, tipo_estado, id_corte
    tbl_producto = id_producto, nombre, cantidad, precio
    tbl_detalle_pedido = id_detalle_pedido, cantidad, importe_p, n_pedido, id_producto
    tbl_direccion = id_direccion, num_casa, calle, cruzamientos, referencia, colonia_d
    tbl_colonia = id_colonia, colonia
    tbl_corte = id_corte, fecha, total_ventas, total_gastos, total_final
    tbl_gasto = id_gasto, descripcion
    tbl_pago = id_pago, tipo_pago
    tbl_cliente = id_cel, nombre, apellido, apodo, direccion_c
    tbl_gasto_d = id_gasto_d, monto, id_gasto, id_corte, fecha
"""
import pyotp
import time
import uuid
import base64
import qrcode
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, Response  # Importa los módulos de Flask necesarios
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user  # Importa herramientas de Flask-Login
from werkzeug.security import check_password_hash, generate_password_hash  # Para manejar contraseñas encriptadas
from psycopg2.extras import RealDictCursor
from Conector import Conector
from datetime import datetime
from psycopg2 import (
    OperationalError, IntegrityError, ProgrammingError, 
    InternalError, DatabaseError, DataError, InterfaceError
)
import psycopg2
from decimal import Decimal #lo puse por el bien de la trama Att:Argel PD:lo uso en la linea 720
from waitress import serve
import re
usuarios = [
    {"user": "m_app", "password": "fruteria7"}, # 0
    {"user": "m_app", "password": "fruteria7"}, # 1
    {"user": "m_crud", "password": "Usuario7"}, # 2
    {"user": "f_lectura", "password": "LecturaFru"} # 3
]
 
app = Flask(__name__)  # Crea la instancia principal de la aplicación Flask
app.secret_key = 'PERRITORICOCONCOLADERICOENUNENVACEDELITROFUMANDOUNPORRITO'  # Clave para sesiones
login_manager = LoginManager(app)   # Inicializa el manejador de login
login_manager.login_view = 'Usuario'  # Página de inicio de sesión

class User(UserMixin):
    def __init__(self,id,usuario,password,f2p,tipo, estado):
        self.id = id
        self.usuario = usuario
        self.password = password
        self.f2p = f2p
        self.tipo = tipo
        self.estado = estado


@login_manager.user_loader
def load_user(user_id):
    try:
        con = Conector(usuarios[3]["user"],usuarios[3]["password"])
        conn = con.conectar()
        if conn is None:
            flash("No se pudo conectar a la base de datos. Inténtalo más tarde.", "error")
            logout()
            return redirect(url_for('Usuario'))
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM tbl_usuario WHERE id = %s", (user_id,))
        data_user = cursor.fetchone()
        cursor.close()
        conn.close()
        con.cerrar()
        if data_user:
            return  User(
                        id=data_user['id'],
                        usuario=data_user['usuario'],
                        password=data_user['password'],
                        f2p=data_user['key_f2p'],
                        tipo=data_user['tipo'],
                        estado=data_user['estado'],
                    )
    except OperationalError as e:
        print(f"[load_user] Error: {e}")     
    except Exception as e:
        print(f"[load_user] Error: {e}") 
    return None # Si no se encuentra, devuelve None

# Página principal
@app.route('/')
def home():  # Ruta principal
    return redirect(url_for('Usuario'))  # Muestra la plantilla de inici

# Inicio de sesión
@app.route('/Usuario', methods=['GET', 'POST'])
def Usuario():  # Ruta para el inicio de sesión del usuario
    errores = []  # array para guardar mensajes de error
    cursor = None
    conn = None
    con = None

    if request.method == "POST": # Verificar el envio del formulario
        usuario = request.form.get("usuario", "").strip()  # Obtener el número del formulario
        Password = request.form.get("password", "").strip() # Obtener contraseña del formulario
    

        # Validaciones
        if not usuario: # Verificar la existencia del dato 
            flash("El Usuario es requerido", "error")

        if not Password: # Verificar la existencia de la contraseña
            flash("La contraseña es requerida", "error")
            
        if not errores: 
            con = Conector(usuarios[0]["user"],usuarios[0]["password"])
            conn = con.conectar()
            if conn is None:
                session['login'] = "Error al conectar"
            else:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT * FROM tbl_usuario WHERE usuario = %s", (usuario,))
                data_user = cursor.fetchone()
                conn.commit()
            if data_user:
                
                if data_user.get("estado_d") == False:
                    errores.append("Usuario desactivado, contacte al administrador")
                elif data_user["estado"] is None:
                    stored_password = data_user.get("password", "")  # Almacenamos la contraseña del cliente que fue tomada de la BD
                    if check_password_hash(stored_password, Password):

                        secret_2fa = data_user.get("key_f2p","")
                        totp = pyotp.TOTP(secret_2fa)
                        codigo_2fa = request.form.get('codigo_2fa')
                        print(codigo_2fa)
                        print(totp.verify(codigo_2fa))
                        print("Código actual TOTP esperado:", totp.now())
                        
                        if not codigo_2fa or not totp.verify(codigo_2fa):
                            errores.append("Codigo de verificación incorrecto")
                        else:
                            session_token = str(uuid.uuid4())
                            session['expiry_time'] = datetime.utcnow().timestamp()
                            session['session_token'] = session_token
                            session['usuario'] = data_user["usuario"]
                            session.permanent = True
                            cursor.execute("UPDATE tbl_usuario SET estado = %s WHERE usuario = %s", (session_token, data_user["usuario"]))
                            conn.commit()
                            user = User(
                                id=data_user['id'],
                                usuario=data_user['usuario'],
                                password=data_user['password'],
                                f2p=data_user['key_f2p'],
                                tipo=data_user['tipo'],
                                estado=session_token,
                            )
                            login_user(user)
                            cursor.close()
                            conn.close()
                            con.cerrar()
                            return redirect(url_for("admin_inicio"))
                    else:
                        errores.append("Usuario o contraseña incorrectos")
                else:
                    errores.append("Usuario con una sesion activa")
            else:
                errores.append("Usuario o contraseña incorrectos")  
    if cursor is not None:
        cursor.close()
    if conn is not None:
        conn.close()
    if con is not None:
        con.cerrar()
    return render_template('log_in_usuario.html',errores=errores) # Muestra el login con errores si hay

# Cerrar sesión
@app.route('/logout')
@login_required
def logout():  # Ruta para cerrar sesión
    con = Conector(usuarios[0]["user"],usuarios[0]["password"])
    conn = con.conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("UPDATE tbl_usuario SET estado = %s WHERE usuario = %s", (None, current_user.usuario))
    conn.commit()
    session.pop('session_token', None)
    logout_user()  # Cierra la sesión 
    cursor.close()
    conn.close()
    con.cerrar()
    return redirect(url_for('Usuario'))  # Redirige al login

@app.before_request
def check_session_expiry():
    last_active = session.get('expiry_time')
    if last_active:
        elapsed = datetime.utcnow().timestamp() - last_active
        max_idle = 1800  # segundos para caducar la sesión
        if elapsed > max_idle:
            automatic_logout()
            return 
    else:
        # Si no hay registro de actividad, marca ahora como actividad
        session['last_active'] = datetime.utcnow().timestamp()

    # Si la sesión sigue activa, actualiza el tiempo de última actividad
    session['last_active'] = datetime.utcnow().timestamp()

def automatic_logout():
    # Borrar estado en la BD
    usuario = session.get('usuario', None)
    print('estamos en outo_logout : ', usuario) 
    if usuario:
        con = Conector(usuarios[0]["user"], usuarios[0]["password"])
        conn = con.conectar()
        if conn is None:
            con.cerrar()
            print("no se establecio conexcion con la base de datos")
            return
        else:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("UPDATE tbl_usuario SET estado = %s WHERE usuario = %s", (None, usuario))
            conn.commit()
            session.clear()
            logout_user()  # Flask-Login 
               
    cursor.close()
    conn.close()
    con.cerrar()
    return redirect(url_for('Usuario'))  # Redirige al login

def verificar_sesion(usuario):
 
   
    con = Conector(usuarios[3]["user"],usuarios[3]["password"])
    conn = con.conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT estado FROM tbl_usuario WHERE usuario=%s",(usuario))
    token_bd = cursor.fetchone()
    session_token = session.get('session_token')
    if session_token != token_bd:
        logout()
    cursor.close()
    conn.close()
    con.cerrar()
    return render_template("log_in_usuario.html")  # Redirige al login
    
def obtener_producto_por_id(id_producto):
   
    con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
    conn = con.conectar()
    if not conn:
        return None
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM tbl_productos WHERE id_producto = %s", (id_producto,))
    producto = cursor.fetchone()
    cursor.close()
    conn.close()

    return producto

def guardar_pedido_en_db(lista_productos, num_cel ,metodo_pago):

    if int(current_user.tipo) not in [0, 1, 2]:
        flash("No tienes permisos para crear pedidos", "pedido_error")
        return False

    try:    
        con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
        conn = con.conectar()
        if not conn:
            flash("Error al conectar con la base de datos", "pedido_error")
            return
        cursor = conn.cursor()
        inicio = time.time()
        #Considerar su estado segun el metodo de pago
        if metodo_pago == "P1":
            estado = "E1"
        else:
            estado = "E3"

        # FLUJO DE PASOS PARA AÑADIR A LA BD EL PEDIDO
        # 1. Insertar un nuevo pedido en TBL_PEDIDOS
        total = sum(item['subtotal'] for item in lista_productos)
        cantidad_total = sum(item['cantidad'] for item in lista_productos)
#cambio sql procedural
        sql_insert_pedido = """
        INSERT INTO tbl_pedido (cantidad, importe_g, fecha, num_cel, tipo_pago, tipo_estado)
            VALUES (%s, %s, CURRENT_DATE, %s, %s, %s) RETURNING id_pedido
         """
        cursor.execute(sql_insert_pedido, (
            cantidad_total,
            total,
            num_cel, # Cel del cliente
            metodo_pago,      # según TBL_PAGO
            estado ))
        final = time.time()
        print(f'Los segundos son { final-inicio:.7f} en PEDIDOS con un DISPARADOR')
        # 2. Obtener el ID del nuevo pedido
        id_pedido = cursor.fetchone() # ← 🔹 ESTE ES EL ID REAL DEL PEDIDO INSERTADO

        # 3. Insertar cada producto en TBL_DETALLE_PEDIDOS
        for producto in lista_productos:
            cursor.execute("""
                INSERT INTO tbl_detalle_pedido (cantidad, importe_p, n_pedido, id_producto)
                VALUES (%s, %s, %s, %s)
            """, (
                producto['cantidad'],
                producto['subtotal'],
                id_pedido,
                producto['id']
            ))
            DescontarInventario(producto['id'],producto['cantidad'])

        conn.commit()
        flash("Pedido creado exitosamente", "pedido_success")
    except OperationalError as e:
        if conn:
            conn.rollback()
        flash(f"Error operacional: problemas con la conexión o recursos. {e}", "pedido_error")
    except IntegrityError as e:
        if conn:
            conn.rollback()
        flash(f"Error de integridad: violación de restricciones o claves duplicadas. {e}", "pedido_error")
    except ProgrammingError as e:
        if conn:
            conn.rollback()
        flash(f"Error de programación: problemas con la sintaxis o consulta SQL. {e}", "pedido_error")
    except InternalError as e:
        if conn:
            conn.rollback()
        flash(f"Error interno en la base de datos. {e}", "pedido_error")
    except DatabaseError as e:
        if conn:
            conn.rollback()
        flash(f"Error general de base de datos. {e}", "pedido_error")
    except DataError as e:
        if conn:
            conn.rollback()
        flash(f"Error de datos: problemas con el formato o tipo de datos. {e}", "pedido_error")
    except InterfaceError as e:
        if conn:
            conn.rollback()
        flash(f"Error de interfaz: problemas con el driver de la base de datos. {e}", "pedido_error")
    except TimeoutError as e:
        if conn:
            conn.rollback()
        flash(f"Error de tiempo de espera: la operación tardó demasiado. {e}", "pedido_error")
    except ValueError as e:
        if conn:
            conn.rollback()
        flash(f"Error de valor: datos inválidos en los cálculos. {e}", "pedido_error")
    except KeyError as e:
        if conn:
            conn.rollback()
        flash(f"Error de clave: falta información requerida en los datos. {e}", "pedido_error")
    except TypeError as e:
        if conn:
            conn.rollback()
        flash(f"Error de tipo: operación con tipos de datos incorrectos. {e}", "pedido_error")
    except AttributeError as e:
        if conn:
            conn.rollback()
        flash(f"Error de atributo: acceso a atributo inexistente. {e}", "pedido_error")
    except Exception as e:
        if conn:
            conn.rollback()
        flash(f"Error inesperado al crear el pedido: {str(e)}", "pedido_error")            
    finally:
        cursor.close()
        conn.close()
    
        
def DescontarInventario(Id, Cantidad):
    errores = [] # Diccionario para guardar mensajes de error
    con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
    conn = con.conectar()
    if not conn:
        errores['errores'].append("No se pudo establecer conexión con la base de datos.")
        return False, errores

    try:
#cambio sql procedural
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        inicio = time.time()
        cursor.execute("CALL procedure_descontar(%s, %s)", (Id, Cantidad))
        final = time.time()
        print(f'Los segundos son { final-inicio:.7f} en DESCONTAR INVENTARIO Con un proceso almacenado/FUNCION')
        conn.commit()
        return True

    except OperationalError as e:
            errores['errores'].append(f"Error operacional: problemas con la conexión o recursos. {e}" ) 
    except IntegrityError as e:
            errores['errores'].append(f"Error de integridad: violación de restricciones o claves duplicadas. {e}")
    except ProgrammingError as e:
            errores['errores'].append(f"Error de programación: problemas con la sintaxis o consulta SQL. {e}")
    except InternalError as e:
            errores['errores'].append(f"Error interno en la base de datos. {e}")
    except DatabaseError as e:
            errores['errores'].append(f"Error general de base de datos. {e}")
    except Exception as e:
            errores['errores'].append(f"Error inesperado: {e}")   
            conn.rollback()
            return False, errores

    finally:
        conn.close()

def BuscarClientePorID(telefono):
    errores = {}  # Diccionario para guardar mensajes de error
    try:
        con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
        conn = con.conectar()
        if conn is None:
            return False  # Si no hay conexión, asumimos que no se puede buscar
        
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
                    SELECT 
                        c.id_cel, c.nombre, c.apellido, c.apodo,
                        d.num_casa, d.calle, d.cruzamientos, d.referencia,
                        col.colonia
                    FROM tbl_cliente c
                    INNER JOIN tbl_direccion d ON c.dirreccion_c = d.id_dirreccion
                    INNER JOIN tbl_colonia col ON d.colonia_d = col.id_colonia
                    WHERE c.id_cel = %s
                    """, 
                    (telefono,)) # Busca el usuario por su ID
        resultado = cursor.fetchone()

        if resultado is None:
            return None
        
        resultado = {
                    'id': resultado['id_cel'],
                    'nombre': resultado['nombre'],
                    'apellido': resultado['apellido'],
                    'apodo': resultado['apodo'],
                    'direccion': f"#{resultado['num_casa']} C.{resultado['calle']} X{resultado['cruzamientos']} col.{resultado['colonia']}"
                }   

        cursor.close()
        conn.close()

        return resultado 

    except OperationalError as e:
            errores['errores'].append(f"Error operacional: problemas con la conexión o recursos. {e}" ) 
    except IntegrityError as e:
            errores['errores'].append(f"Error de integridad: violación de restricciones o claves duplicadas. {e}")
    except ProgrammingError as e:
            errores['errores'].append(f"Error de programación: problemas con la sintaxis o consulta SQL. {e}")
    except InternalError as e:
            errores['errores'].append(f"Error interno en la base de datos. {e}")
    except DatabaseError as e:
            errores['errores'].append(f"Error general de base de datos. {e}")
    except Exception as e:
            errores['errores'].append(f"Error inesperado: {e}")   
            return False


def GuardarCliente(telefono, nombre, apellido, apodo):
    try:
        # Validaciones básicas
        if not telefono or not nombre:
            return {"error": "Teléfono y nombre son obligatorios"}
        
        con = Conector(usuarios[int(current_user.tipo)]["user"], usuarios[int(current_user.tipo)]["password"])
        conn = con.conectar()
        if conn is None:
            return {"error": "No se pudo conectar a la base de datos"}
        
        cursor = conn.cursor()
        
        # Verificar si el teléfono ya existe
        cursor.execute("SELECT id_cel FROM tbl_cliente WHERE id_cel = %s", (telefono,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return {"error": "El teléfono ya está registrado"}
        
        # Insertar nuevo cliente
        cursor.execute(
            "INSERT INTO tbl_cliente (id_cel, nombre, apellido, apodo, direccion_c) VALUES (%s, %s, %s, %s, %s)",
            (telefono, nombre, apellido, apodo, 1)
        )
        conn.commit()
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.IntegrityError as e:
        # Manejar errores de integridad (duplicados, FK violadas, etc.)
        if conn:
            conn.rollback()
            cursor.close()
            conn.close()
        return {"error": "Error de integridad en la base de datos"}
        
    except psycopg2.Error as e:
        # Manejar otros errores de PostgreSQL
        if conn:
            conn.rollback()
            cursor.close()
            conn.close()
        return {"error": f"Error de base de datos: {str(e)}"}
        
    except Exception as e:
        # Manejar cualquier otro error
        if conn:
            conn.rollback()
            if 'cursor' in locals(): cursor.close()
            if 'conn' in locals(): conn.close()
        return {"error": f"Error inesperado: {str(e)}"}

# Admin Panel Prueba
@app.route('/admin')
@login_required
def admin_inicio():
    tipoadmin = int(current_user.tipo)
    return render_template("admin.html", current_user=current_user, tipoadmin=tipoadmin, modo="inicio")

@app.route('/admin/alta', methods=['GET', 'POST'])
@login_required
def alta():  
    modo = 'alta'
    con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
    conn = con.conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT id, usuario, tipo FROM tbl_usuario WHERE tipo <> '0' AND estado_d = TRUE ORDER BY tipo ASC")
    usuarios_data = cursor.fetchall()
    tipoadmin = int(current_user.tipo)
#FORMULARIO
    if request.method == 'POST' and request.form.get("usuario") and request.form.get("password") and request.form.get("identificador") and request.form.get("tipo") and not request.form.get("usuario_mod") and not request.form.get("usuario_del"):
        id_nuevo = request.form.get("identificador")
        usuario_nuevo = request.form.get("usuario")
        password_nuevo = request.form.get("password")
        tipo_nuevo = request.form.get("tipo")
        errores = []

        if not re.match(r"^\d{10}$", id_nuevo):
            errores.append("Ingresa un número telefónico válido.")
        else:
            cursor.execute("SELECT 1 FROM tbl_usuario WHERE id = %s", (int(id_nuevo),))
            if cursor.fetchone():
                errores.append("El identificador ya existe. Debe ser único.")

        if len(usuario_nuevo) < 4:
            errores.append("El usuario debe tener como mínimo 4 caracteres.")

        if len(password_nuevo) < 8:
            errores.append("La contraseña debe tener mínimo 8 caracteres.")
        if not re.search(r"[A-Z]", password_nuevo):
            errores.append("La contraseña debe contener al menos una mayúscula.")

        if tipo_nuevo not in ['1', '2', '3']:
            errores.append("Debes seleccionar el tipo de usuario.")

        if errores:
            for mensaje in errores:
                flash(mensaje, "alta_error")
            cursor.close()
            conn.close()
            return redirect(url_for('alta'))

        hashed_password = generate_password_hash(password_nuevo)
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        uri = totp.provisioning_uri(name=usuario_nuevo, issuer_name="ElAmigo 7")

        img = qrcode.make(uri)
        buf = BytesIO()
        img.save(buf)
        img_b64 = base64.b64encode(buf.getvalue()).decode('utf-8')

        try:
            cursor.execute("INSERT INTO tbl_usuario (id, usuario, password, key_f2p , tipo) VALUES (%s, %s, %s, %s, %s)",
                           (int(id_nuevo), usuario_nuevo, hashed_password, secret, tipo_nuevo))
            conn.commit()
            flash("Usuario creado correctamente.", "alta_success")
        except Exception as e:
            conn.rollback()
            flash("Error al crear el usuario: " + str(e), "alta_error")        
        cursor.close()
        conn.close()
        return render_template('admin.html', current_user=current_user,tipoadmin=tipoadmin ,modo=modo, usuarios=usuarios_data, img_b64=img_b64, secret=secret)
 #TABLA
    if request.method == 'POST' and request.form.get("usuario_mod"):
        usuario = request.form.get("usuario_mod")
        nuevo_tipo = request.form.get("nuevo_tipo")
        nueva_contrasena = request.form.get("nueva_contrasena")

        
        if nuevo_tipo in ['1', '2', '3']:
            cursor.execute("SELECT password FROM tbl_usuario WHERE usuario = %s AND estado_d = TRUE", (usuario,))
            resultado = cursor.fetchone()
            current_hash = resultado["password"] if resultado else None

            if nueva_contrasena and current_hash:
                if check_password_hash(current_hash, nueva_contrasena):
                    flash("La nueva contraseña es igual a la actual", "tabla_info")
                else:
                    hashed_nueva = generate_password_hash(nueva_contrasena)
                    cursor.execute("UPDATE tbl_usuario SET password = %s, tipo = %s WHERE usuario = %s AND tipo <> '0' AND estado_d = TRUE", (hashed_nueva, nuevo_tipo, usuario))
                    conn.commit()
                    flash("Contraseña actualizada correctamente", "tabla_success")
            else:
                cursor.execute("UPDATE tbl_usuario SET tipo = %s WHERE usuario = %s AND tipo <> '0' AND estado_d = TRUE", (nuevo_tipo, usuario))
                conn.commit()
                flash("Tipo actualizado correctamente", "tabla_info")
#ELIMIANR USUARIO
    if request.method == 'POST' and request.form.get("usuario_del"):
        usuario = request.form.get("usuario_del")
        cursor.execute("UPDATE tbl_usuario SET estado_d = FALSE WHERE usuario = %s AND tipo IN ('1', '2', '3')", (usuario,))
        conn.commit()
        flash(f"Usuario eliminado correctamente: {usuario}", "tabla_success")
    cursor.close()
    conn.close()
    return render_template('admin.html', current_user=current_user,tipoadmin=tipoadmin ,modo=modo, usuarios=usuarios_data, img_b64=None, secret=None)

@app.route('/admin/corte', methods=['GET', 'POST']) 
@login_required
def corte():
    con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
    conn = con.conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    tipoadmin = int(current_user.tipo)
    try:
        cursor.execute("""
            SELECT SUM(importe_g) AS venta_total
            FROM tbl_pedido
            WHERE fecha = CURRENT_DATE;
        """)
        resultado = cursor.fetchone()
        VentaDelDia = resultado["venta_total"] if resultado else 0

        cursor.execute("""
            SELECT SUM(monto) AS gasto_total
            FROM tbl_gasto_d
            WHERE fecha = CURRENT_DATE;
        """)
        resultado = cursor.fetchone()
        GastosDelDia = resultado["gasto_total"] if resultado else 0

        cursor.execute("""
            SELECT
            (SELECT COALESCE(SUM(importe_g),0) FROM tbl_pedido WHERE fecha = CURRENT_DATE) -
            (SELECT COALESCE(SUM(monto),0) FROM tbl_gasto_d WHERE fecha = CURRENT_DATE) AS total_final;
        """)
        resultado = cursor.fetchone()
        Total = resultado["total_final"] if resultado else 0

        if request.method == "POST":
            cursor.execute("""
                SELECT id_corte 
                FROM tbl_corte 
                WHERE fecha = CURRENT_DATE;
            """)
            existe = cursor.fetchone() is not None
            if not existe:
                cursor.execute("""
                    INSERT INTO tbl_corte (fecha, total_ventas, total_gastos, total_final)
                    VALUES (CURRENT_DATE, %s, %s, %s) RETURNING id_corte;
                    """, (VentaDelDia, GastosDelDia, Total))
                id_corte = cursor.fetchone()["id_corte"]

                cursor.execute("""
                    UPDATE tbl_gasto_d
                    SET id_corte = %s
                    WHERE fecha = CURRENT_DATE;
                    """, (id_corte,))
            else:
                    # 👇 Actualiza el corte existente del día
                cursor.execute("""
                    UPDATE tbl_corte
                    SET total_ventas = %s,
                        total_gastos = %s,
                        total_final  = %s
                    WHERE fecha = CURRENT_DATE
                    RETURNING id_corte;
                """, (VentaDelDia, GastosDelDia, Total))
                id_corte = cursor.fetchone()["id_corte"]

                cursor.execute("""
                    UPDATE tbl_gasto_d
                    SET id_corte = %s
                    WHERE fecha = CURRENT_DATE;
                """, (id_corte,))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print("Error al guardar corte:", e)  # Ver en consola/terminal
        VentaDelDia = 0 
        GastosDelDia = 0 
        Total = 0
    return render_template("admin.html", modo="corte",  current_user=current_user,tipoadmin=tipoadmin ,VentaDelDia=VentaDelDia, GastosDelDia=GastosDelDia, Total=Total, Error="")


@app.route('/admin/gasto', methods=['GET', 'POST'])
@login_required
def gasto():
    tipoadmin = int(current_user.tipo)
    gastos_detalle = []
    gastos = []
    con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
    conn = con.conectar()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    if request.method == "POST":    
        Proveedor = request.form.get("nombre_proveedor")
        if Proveedor and Proveedor.strip():
            Proveedor = Proveedor.strip().lower().capitalize()
            cursor.execute("INSERT INTO tbl_gasto (descripcion) VALUES (%s) ON CONFLICT (descripcion) DO NOTHING RETURNING id_gasto",(Proveedor.strip(),))
            nuevo = cursor.fetchone()
            conn.commit()
            if nuevo:
                flash("Proveedor Registrado Correctamente", "success")
            else:
                flash("El Proveedor ya existe", "warning")
        Proveedor_corte = request.form.get("descripcion_corte")
        monto = request.form.get("monto")
        if monto and Proveedor_corte:
            cursor.execute("INSERT INTO tbl_gasto_d (monto, id_gasto) VALUES (%s,%s)",(monto,int(Proveedor_corte),))
            conn.commit()
        
    cursor.execute("""
                    SELECT 
                        d.monto,
                        d.fecha,
                        g.descripcion
                    FROM 
                        tbl_gasto_d AS d
                    JOIN 
                        tbl_gasto AS g 
                        ON d.id_gasto = g.id_gasto;
                    """)
    gastos_detalle = cursor.fetchall()
    cursor.execute("SELECT * FROM tbl_gasto")
    gastos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("admin.html", modo="gasto", current_user=current_user,tipoadmin=tipoadmin ,gastos = gastos, gastos_detalle=gastos_detalle)


# ver pedidos 
@app.route('/admin/pedidos', methods=['GET', 'POST'])
@login_required
def ver_pedidos():
    try:
        con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
        conn = con.conectar()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        modo = 'pedidos'
        detalles = None
        tipoadmin = int(current_user.tipo)
        if request.method == 'POST':
            action = request.form.get('action')
            try: 
                if action == 'eliminar':
                    pedido_id = request.form.get('id_pedido')
                    cursor.execute("UPDATE TBL_PEDIDO SET Tipo_estado = %s WHERE ID_Pedido = %s", ('E4', pedido_id))
                    conn.commit()
                    flash("Pedido eliminado correctamente", "success")
                elif action == 'detalles':
                    pedido_id = request.form.get('id_pedido')
                    cursor.execute("""
                                SELECT
                                    dp.Cantidad,
                                    dp.Importe_p,
                                    p.Nombre
                                FROM TBL_DETALLE_PEDIDO dp
                                INNER JOIN TBL_PRODUCTOS p ON dp.ID_producto = p.ID_producto
                                WHERE dp.N_pedido = %s
                                ORDER BY p.Nombre;""", (pedido_id,))
                    detalles = cursor.fetchall()
                    modo = 'detalles'
                elif action == 'editar':
                    pedido_id = request.form.get('id_pedido')
                    cantidad = request.form.get('cantidad')
                    importe = request.form.get('importe')
                    fecha = request.form.get('fecha')
                    num_cel = request.form.get('num_cel')
                    tipo_pago = request.form.get('tipo_pago')
                    tipo_estado = request.form.get('tipo_estado')

                    cursor.execute("""
                        UPDATE TBL_PEDIDO
                        SET Cantidad = %s, Importe_g = %s, Fecha = %s, Num_cel = %s, Tipo_pago = %s, Tipo_estado = %s
                        WHERE ID_Pedido = %s
                    """, (cantidad, importe, fecha, num_cel, tipo_pago, tipo_estado, pedido_id))
                    conn.commit()
                    flash("Pedido actualizado correctamente", "success")
            except Exception as e:
                conn.rollback()
                if "permission denied" in str(e).lower() or "insufficient privilege" in str(e).lower():
                    flash("No tienes permisos suficientes en la base de datos para realizar esta acción", "error")
                elif "violates foreign key constraint" in str(e).lower():
                    flash("No se puede realizar la acción debido a restricciones de integridad referencial", "error")
                elif "cannot access local variable 'action' where it is not associated with a value" in str(e).lower():
                    print("epico")
                else:
                    flash(f"Error en la operación: {str(e)} permisos insuficientes", "error")
   
        Numero = request.args.get('buscar_cel')
        Filtro = request.args.get('tipo_estado')
        if Numero and not Filtro:
            cursor.execute("SELECT * FROM TBL_PEDIDO WHERE Tipo_estado != 'E4' AND Num_cel = %s",(Numero,))
        elif Filtro and not Numero:
            cursor.execute("SELECT * FROM TBL_PEDIDO WHERE Tipo_estado = %s",(Filtro,))
        elif Filtro and Numero:
            cursor.execute("SELECT * FROM TBL_PEDIDO WHERE Tipo_estado = %s AND Num_cel = %s",(Filtro,Numero,))
        else:
            cursor.execute("SELECT * FROM TBL_PEDIDO WHERE Tipo_estado != 'E4'")
        pedidos = cursor.fetchall()

        conn.close()

    except Exception as e:
        # Capturar errores de conexión o consultas generales
        flash(f"Error de conexión a la base de datos: {str(e)}", "error")
        # Asignar valores por defecto para que el template funcione
        modo = 'pedidos'
        pedidos = []
        detalles = None
        tipoadmin = int(current_user.tipo)

    return render_template('admin.html', modo=modo, tipoadmin=tipoadmin, pedidos=pedidos, detalles=detalles)

#  Vista de clientes
@app.route('/admin/clientes', methods=['GET', 'POST'])
@login_required
def ver_clientes():

    try:
        con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
        conn = con.conectar()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        tipoadmin = int(current_user.tipo)
        Numero = request.args.get('buscar_cel')

        # 🔹 1. Cargar colonias
        cursor.execute("SELECT * FROM tbl_colonia")
        colonias = cursor.fetchall()

        # 🔹 2. Cargar direcciones existentes (para el select del nuevo cliente)
        cursor.execute("""
            SELECT 
                d.id_dirreccion, d.num_casa, d.calle, d.cruzamientos, col.colonia
            FROM tbl_direccion d
            INNER JOIN tbl_colonia col ON d.colonia_d = col.id_colonia
            ORDER BY d.num_casa DESC;
        """)
        direcciones = cursor.fetchall()

        # 🔹 3. Buscar clientes (si hay número, filtra; si no, lista todos)
        if Numero:
            cursor.execute("""
                SELECT 
                    c.id_cel, c.nombre, c.apellido, c.apodo,
                    d.num_casa, d.calle, d.cruzamientos, d.referencia,
                    col.colonia
                FROM tbl_cliente c
                INNER JOIN tbl_direccion d ON c.dirreccion_c = d.id_dirreccion
                INNER JOIN tbl_colonia col ON d.colonia_d = col.id_colonia
                WHERE c.id_cel = %s
                ORDER BY c.nombre
            """, (Numero,))
        else:
            cursor.execute("""
                SELECT 
                    c.id_cel, c.nombre, c.apellido, c.apodo,
                    d.num_casa, d.calle, d.cruzamientos, d.referencia,
                    col.colonia
                FROM tbl_cliente c
                INNER JOIN tbl_direccion d ON c.dirreccion_c = d.id_dirreccion
                INNER JOIN tbl_colonia col ON d.colonia_d = col.id_colonia
                ORDER BY c.nombre 
            """)

        Uclientes = cursor.fetchall()

        # 🔹 4. Convertir los clientes a formato limpio para el template
        clientes = []
        for cliente in Uclientes:
            user = {
                'id': cliente['id_cel'],
                'nombre': cliente['nombre'],
                'apellido': cliente['apellido'],
                'apodo': cliente['apodo'],
                'direccion': f"#{cliente['num_casa']} C.{cliente['calle']} X{cliente['cruzamientos']} col.{cliente['colonia']}",
                'referencia': cliente["referencia"]
            }
            clientes.append(user)

        # 🔹 5. Si se envía un formulario para cambiar apodo
        if request.method == "POST":
            apodo = request.form.get("Apodo")
            Id = request.form.get("id_original")
            cursor.execute("UPDATE tbl_cliente SET apodo = %s WHERE id_cel = %s", (apodo, Id))
            conn.commit()
    except Exception as e:
            print("pepe", e)
    finally:        
        conn.close()

    # 🔹 6. Render con direcciones incluidas
    return render_template('admin.html', modo='clientes', tipoadmin=tipoadmin ,clientes=clientes, colonias=colonias, direcciones=direcciones)

#  Vista de clientes
@app.route('/admin/direccion', methods=['GET', 'POST'])
@login_required
def editar_direccion():
    print(request.form)
    try:
        con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
        conn = con.conectar()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        id_cliente = request.form.get('id_cliente')
        num_casa = request.form.get('Num_casa')
        calle = request.form.get('Calle')
        cruzamientos = request.form.get('Cruzamientos')
        referencia = request.form.get('Referencia')
        colonia = request.form.get('Colonia')
        cursor.execute("INSERT INTO tbl_direccion (num_casa, calle, cruzamientos, referencia, colonia_d) VALUES(%s,%s,%s,%s,%s) RETURNING id_dirreccion",(num_casa,calle,cruzamientos,referencia,colonia))
        id_direccion = cursor.fetchone()['id_dirreccion']
        cursor.execute("UPDATE tbl_cliente SET dirreccion_c = %s WHERE id_cel = %s", (id_direccion, id_cliente))
        conn.commit()
    except Exception as e:
        print("pepe", e)
    finally:
            if conn:
                conn.close()
    return redirect(url_for('ver_clientes'))




#  Vista de clientes
@app.route('/admin/agregarCliente', methods=['GET', 'POST'])
@login_required
def crear_cliente():
    if request.method == "POST":
        Numero = request.form.get("nuevo_celular") #admin
        Apodo = request.form.get("nuevo_apodo") 
        Apellido = request.form.get("nuevo_apellido") #admin
        Nombre = request.form.get("nuevo_nombre") #admin
        DireccionID = request.form.get("direccion_existente") #admin
        try:
            con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
            conn = con.conectar()
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            "tbl_cliente = id_cel, nombre, apellido, apodo, direccion_c"
            inicio = time.time()
            cursor.execute("CALL agregar_cliente(%s, %s, %s, %s, %s);",  (Numero, Nombre, Apellido, Apodo, DireccionID)) 
            final = time.time()
            print(f'Los segundos son { final-inicio:.7f} en CREAR CLIENTE con un proceso almacenado')
            conn.commit()
            flash("Cliente creado correctamente", "success")
        except Exception as e:
            flash(f"No se pudo agregar el cliente: {str(e)}", "danger")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()

    return redirect(url_for('ver_clientes'))

#  Vista de clientes
@app.route('/admin/eliminarProducto', methods=['GET', 'POST'])
@login_required
def eliminar_producto():
    try:   
        con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
        conn = con.conectar()
        cursor = conn.cursor(cursor_factory=RealDictCursor) 
        if request.method == "POST":
            Id = request.form.get("id_producto")
            inicio = time.time()
            cursor.execute("CALL eliminar_producto(%s);", (Id,))
            final = time.time()
            print(f'Los segundos son { final-inicio:.7f} en ELIMINAR PRODUCTO con un proceso almacenado')
            conn.commit()
            flash("Producto eliminado correctamente", "succes")
    except Exception as e:
        print("pepe", e)
    finally:        
        conn.close()
    return redirect(url_for("ver_inventario"))

#  Vista de inventario
@app.route('/admin/inventario', methods=['GET', 'POST'])
@login_required
def ver_inventario():
    try:    
        con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
        conn = con.conectar()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        tipoadmin = int(current_user.tipo)
        ID = request.args.get('buscar_id')
        if ID :
            cursor.execute("SELECT * FROM tbl_productos WHERE id_producto = %s AND estado = true", (ID,))
        else:
            cursor.execute("SELECT * FROM tbl_productos WHERE estado = true")#cambie la846 y esta
        productos = cursor.fetchall()
    except Exception as e:
        print("pepe", e)
    finally:        
        conn.close()
    return render_template('admin.html', modo='inventario', tipoadmin=tipoadmin , productos=productos)

#  Agregar Productos
@app.route('/admin/agregarProducto', methods=['GET', 'POST'])
@login_required
def agregar_producto():
    try:
        con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
        conn = con.conectar()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        Id_producto = request.form.get("id_producto")
        Nombre = request.form.get("nombre")
        Cantidad = request.form.get("cantidad")
        Precio = request.form.get("precio")
        inicio = time.time()
        cursor.execute( "CALL agregar_producto(%s, %s, %s, %s);",  (Id_producto, Nombre, Cantidad, Precio))
        final = time.time()
        print(f'Los segundos son { final-inicio:.7f} en CREAR PRODUCTO con un proceso almacenado')
        conn.commit()
        flash("Producto agregado correctamente", "success")

    except Exception as e:
        conn.rollback()
        flash(f"Producto NO agregado, posible existencia del mismo ID: {str(e)}", "danger")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("ver_inventario"))

# Vista de inventario
@app.route('/admin/inventario_UP', methods=['GET', 'POST'])
@login_required
def inventario_up():
    if request.method == 'POST':
        try:    
            con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
            conn = con.conectar()
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # Obtener datos del formulario de manera segura
            Cantidad = request.form.get('cantidad')
            Precio = request.form.get('precio')
            id_producto = request.form.get('id_producto')

            # Validación básica (puedes expandir esto según tus necesidades)
            if not Cantidad or not Precio or not id_producto:
                return "Faltan datos necesarios"

            inicio = time.time()
           # Ejecutar la actualización
            cursor.execute("CALL actualizar_producto(%s, %s, %s);",  (id_producto, Cantidad, Precio))
            final = time.time()
            print(f'Los segundos son { final-inicio:.7f} en actualizar producto con un proceso almacenado')
            
            conn.commit()
            flash("Producto actualizado correctamente", "success")
            return redirect(url_for("ver_inventario"))
        except Exception as e:
            conn.rollback()
            return f"Error al actualizar el producto: {e}"
        finally:
            conn.close()
    else:
        return "Método no permitido"


@app.route('/admin/hacer/pedido', methods=['GET', 'POST'])
@login_required
def PedidoSuc():
    try:    
        con = Conector(usuarios[int(current_user.tipo)]["user"],usuarios[int(current_user.tipo)]["password"])
        conn = con.conectar()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM TBL_PRODUCTOS WHERE estado = true")
        productos = cursor.fetchall()
        tipoadmin = int(current_user.tipo)
        cursor.close()
        conn.close()

    except Exception as e:
        print("pepe", e)
    finally:    
        conn.close()
    
    if request.method == "POST":
        pos = 0
        telefono = request.form.get('telefono')
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        apodo = request.form['apodo']
        productos = request.form.getlist('productos[]')#Lista de productos seleccionados por el usuario
        cantidades = request.form.getlist('cantidades[]')
        metodo_pago = 'P2'
        
        lista_final = []
        for id_producto in productos:
            cantidad = Decimal(cantidades[pos]) #Tomamos el valor y lo convertimos en int
            producto = obtener_producto_por_id(id_producto) # lo enviamos a la funcion para buscarlo en la BD y obtener el precio
                
            precio = Decimal(producto.get('precio') or producto.get('Precio', 0))#corregi esto solo aumente el decimal


            lista_final.append({
                'id': id_producto,
                'cantidad': cantidad,
                'subtotal': cantidad * precio
            })
            pos+=1

        cliente = BuscarClientePorID(telefono)

        

        if cliente is None:
            if GuardarCliente(telefono, nombre, apellido, apodo):
                guardar_pedido_en_db(lista_final, telefono, metodo_pago)
        else:
            print(cliente)
            guardar_pedido_en_db(lista_final, cliente['id'],metodo_pago)
        return redirect(url_for('PedidoSuc'))    

    return render_template('admin.html', modo='hacerpedido', tipoadmin=tipoadmin ,productos=productos )


@app.route('/buscar_cliente/<telefono>', methods=['GET'])
@login_required
def buscar_cliente_ajax(telefono):
    cliente = BuscarClientePorID(telefono)
    if cliente:
        # Si existe, responde los datos con JSON
        return jsonify({
            "exists": True,
            "nombre": cliente['nombre'],
            "apellido": cliente['apellido'],
            "apodo": cliente.get('apodo', "")
        })
    else:
        # No existe
        return jsonify({"exists": False})

if __name__ == '__main__':
    serve(app,host="0.0.0.0", port=5001, threads=10)
    #app.run(debug=True,chost="0.0.0.0", port=5000)
    