from flask import Flask, render_template, request, redirect, url_for, flash, session  # Importa los módulos de Flask necesarios
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user  # Importa herramientas de Flask-Login
from werkzeug.security import check_password_hash, generate_password_hash  # Para manejar contraseñas encriptadas
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import OperationalError # Conector para la base de datos PostgreSQL
#import mysql.connector  # Conector para la base de datos MySQL


app = Flask(__name__)  # Crea la instancia principal de la aplicación Flask
app.secret_key = 'PERRITORICOCONCOLADERICOENUNENVACEDELITROFUMANDOUNPORRITO'  # Clave para sesiones
"""
def get_db():  # Función para conectarse a la base de datos MySQL
    
  
    NOTA PARA ARGEL: llenar con los datos encriptaddos de la base de datos
    y agreagr los nombres de las tablas (todo exacto) y los respectivos campos de las mismas

    Tablas: 
    TBL_CLIENTE = ID_cel,Nombre,Apellido,Apodo,Password,Dirreccion_c
    ,TBL_COLONIA = ID_colonia,Colonia
    ,TBL_DETALLE_PEDIDO = ID_detalle_pedido,Cantidad,Importe_p,N_pedido,ID_producto
    ,TBL_DIRECCION = ID_dirreccion,Num_casa,Calle,Cruzamientos,Referencia,Colonia_d
    ,TBL_ENTREGA = ID_pedido,Tipo_Entrega
    ,TBL_ESTADO = ID_estado,Tipo_Estado
    ,TBL_FECHA = ID_fecha,Dia,Mes,Anio
    ,TBL_PAGO = ID_pago,Tipo_pago
    ,TBL_PEDIDO = ID_Pedido,Cantidad,Importe_g,Fecha,Num_cel,Tipo_entrega,Tipo_solicitud,Tipo_pago,Tipo_estado
    ,TBL_PRODUCTOS = ID_producto,Nombre,Cantidad,Precio
    ,TBL_SOLUCITUD = ID_solicitud,Tipo_Solicitud
   
    # Para llenar un folio en vista de cliente GENERAR: un ID verificar que no existe en la BD, Cantidad total de productos generales, Importe total de la compra, Fecha de compra, Tipo de solicitud WEBB, Tipo de estado (Pendiente, Aceptado, cancelado, entregado), TOMAR DEL FRONT: Número de celular del cliente, Tipo de entrega (a domicilio o en tienda), Tipo de pago (efectivo o tarjeta), ID del productos, cantidad de productos
    try:
        return mysql.connector.connect(
            host="bmpkp5mzuoyegtdi1unp-mysql.services.clever-cloud.com",  # Host de la base de datos - bmpkp5mzuoyegtdi1unp-mysql.services.clever-cloud.com
            user="u1xl9tvffkdbmhpc",  # Usuario de la base de datos  -  u1xl9tvffkdbmhpc
            password="oTEH5DchNRefhZxe1DEC",  # Contraseña de la base de datos - oTEH5DchNRefhZxe1DEC 
            database="bmpkp5mzuoyegtdi1unp"  # Nombre de la base de datos  - bmpkp5mzuoyegtdi1unp
        )
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None
    except Exception as e:
        print(f"[get_db] Error inesperado: {e}")
        return None
"""

def get_db():
    try:
        return psycopg2.connect(
            host="localhost",       # Reemplaza con tu host
            user="postgres",             # Usuario de la base de datos
            password="04230045",      # Contraseña
            dbname="Frute7",     # Nombre de la base de datos
            port="5432"                    # Puerto por defecto de PostgreSQL
        )
    except OperationalError as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None
    except Exception as e:
        print(f"[get_db] Error inesperado: {e}")
        return None
login_manager = LoginManager(app)   # Inicializa el manejador de login
login_manager.login_view = 'Usuario'  # Página de inicio de sesión

class User(UserMixin): # Clase para usuario logueado
    def __init__(self, id, nombre, apellido, apodo, password, rol, direccion):
        self.id = id  # ID del usuario
        self.nombre = nombre  # Nombre del usuario
        self.apellido = apellido  # Apellido del usuario
        self.apodo = apodo  # Apodo del usuario
        self.rol = rol #rol del usuario actual (Usuario "U", Admin "A", SuperAdmin "S")
        self.direccion = direccion  # Apodo del usuario

    def __repr__(self):
        return f'<User {self.apodo}>' # Representación del objeto usuario

@login_manager.user_loader
def load_user(user_id): # Función para tomar al usuario desde la base de datos por su ID
    try:
        conn = get_db() # Conecta a la base de datos
        if conn is None:
            return None  # No se pudo conectar = no hay usuario cargado


        cursor = conn.cursor(cursor_factory=RealDictCursor) # Activamos el diccionario para recibir los valores como un diccionario y no por [0], [1]
        cursor.execute("""
                    SELECT 
                        c.ID_cel, c.Nombre, c.Apellido, c.Apodo, c.Password, c.Tipo,
                        d.Num_casa, d.Calle, d.Cruzamientos, d.Referencia,
                        col.Colonia
                    FROM TBL_CLIENTE c
                    INNER JOIN TBL_DIRECCION d ON c.Dirreccion_c = d.ID_dirreccion
                    INNER JOIN TBL_COLONIA col ON d.Colonia_d = col.ID_colonia
                    WHERE c.ID_cel = %s
                    """, 
                    (user_id,)) # Busca el usuario por su ID
        user_data = cursor.fetchone() # Almacenamos el Usuario encontrado
        cursor.close() # Cerrar ursor
        conn.close() # IMPORTANTE!!!! Siempre cerrar la conexion con la base de datos

        if user_data:
            return User(
                id=user_data['id_cel'],
                nombre=user_data['nombre'],
                apellido=user_data['apellido'],
                apodo=user_data['apodo'],
                password=user_data['password'],
                rol=user_data['tipo'],
                direccion= F"#{user_data['num_casa']} C.{user_data['calle']} X{user_data['cruzamientos']} col.{user_data['colonia']}"
            )
    except Exception as e:
        print(f"[load_user] Error: {e}") 
    return None # Si no se encuentra, devuelve None

# Página principal
@app.route('/')
def home():  # Ruta principal
    return render_template('index.html')  # Muestra la plantilla de inicio

# Inicio de sesión
@app.route('/Usuario', methods=['GET', 'POST'])
def Usuario():  # Ruta para el inicio de sesión del usuario
    errores = {}  # Diccionario para guardar mensajes de error

    if request.method == "POST": # Verificar el envio del formulario
        Number = request.form.get("number", "").strip()  # Obtener el número del formulario
        Password = request.form.get("password", "").strip() # Obtener contraseña del formulario

        # Validaciones
        if not Number: # Verificar la existencia del dato 
            errores["number"] = "El número es requerido"
        elif not Number.isdigit() or len(Number) != 10: # Unicamente digitos y Unicamente de 10 caracteres
            errores["number"] = "Número de teléfono inválido"

        if not Password: # Verificar la existencia de la contraseña
            errores["password"] = "La contraseña es requerida"

        if not errores: 
            conn = get_db() # Conecta a la base de datos
            if conn is None:
                flash("No se pudo conectar a la base de datos. Inténtalo más tarde.", "error")
                return render_template("index.html")
            cursor = conn.cursor(cursor_factory=RealDictCursor) # Activamos el diccionario para recibir los valores como un diccionario y no por [0], [1]
            cursor.execute("""
                    SELECT 
                        c.ID_cel, c.Nombre, c.Apellido, c.Apodo, c.Password, c.Tipo,
                        d.Num_casa, d.Calle, d.Cruzamientos, d.Referencia,
                        col.Colonia
                    FROM TBL_CLIENTE c
                    INNER JOIN TBL_DIRECCION d ON c.Dirreccion_c = d.ID_dirreccion
                    INNER JOIN TBL_COLONIA col ON d.Colonia_d = col.ID_colonia
                    WHERE c.ID_cel = %s
                    """, 
                    (Number,)) # Obtenemos los datos del Cliente por su número
            user_data = cursor.fetchone() # Almacenamos el Usuario encontrado
            cursor.close() # Cerrar ursor
            conn.close() # IMPORTANTE!!!! Siempre cerrar la conexion con la base de datos

            if user_data: # Usuario encontrado
                stored_password = user_data.get("password", "")  # Almacenamos la contraseña del cliente que fue tomada de la BD
                
                if check_password_hash(stored_password, Password):  # Comparamos la contraseña de la BD con la del formulario
                    user = User(
                        id=user_data['id_cel'],
                        nombre=user_data['nombre'],
                        apellido=user_data['apellido'],
                        apodo=user_data['apodo'],
                        password=user_data['password'],
                        rol=user_data['tipo'],
                        direccion= F"#{user_data['num_casa']} C.{user_data['calle']} X{user_data['cruzamientos']} col.{user_data['colonia']}"
                    )
                    login_user(user)  # Iniciar sesión con Flask-Login
                    if user.rol == 'u':
                        return redirect(url_for("Pedidos")) #Redirigir a compras.
                    else:
                        return redirect(url_for("admin_inicio"))
                else:
                    errores["password"] = "Contraseña incorrecta"
            else:
                errores["number"] = "Número no encontrado" # No está registrado en la BD o no fue encontrado

    return render_template('log_in_usuario.html', errores=errores) # Muestra el login con errores si hay

# Cerrar sesión
@app.route('/logout')
@login_required
def logout():  # Ruta para cerrar sesión
    logout_user()  # Cierra la sesión
    return redirect(url_for("Usuario"))  # Redirige al login

@app.route("/Usuario/Pedir")
@login_required
def Pedidos():  # Ruta que muestra los pedidos del cliente
    """
    NOTA PARA ARMANDO:
    el current_user enviara un diccionario al cual vas a poder acceder desde HTML con los siguientes comandos:
    Comando          | Resultado
    Usuario.id       | Numero del cliente 
    Usuario.nombre   | Nombre del cliente
    Usuario.apellido | Apellido del cliente
    Usuario.apodo    | Apodo del Cliente
    Usuario.direccion| Direccion del Cliente
    Usuario.rol      | Rol en la base de datos
    Producto.ID_producto | ID del Producto
    Producto.Nombre  | Nombre del Producto
    Producto.Cantidad| Cantidad existente de Producto
    Producto.Precio  | Precio unitario de Producto
    """
    try:
        conn = get_db() # Conecta a la base de datos
        if conn is None:
            return None  # No se pudo conectar = no hay usuario cargado
        
        cursor = conn.cursor(cursor_factory=RealDictCursor) # Activamos el diccionario para recibir los valores como un diccionario y no por [0], [1]
        cursor.execute("SELECT * FROM TBL_PRODUCTOS") # Busca los productos existentes
        Productos = cursor.fetchall() # Almacenamos todos los productos
        cursor.close() # Cerrar ursor
        conn.close() # IMPORTANTE!!!! Siempre cerrar la conexion con la base de datos

        return render_template("pedidos_clientes.html", Usuario=current_user, Productos = Productos)  #Envia los datos del usuario loggeado y los productos existentes
    except Exception as e:
        print(f"[load_user] Error: {e}") 
    return render_template("pedidos_clientes.html", Usuario=current_user, Productos = Productos)  #Envia los datos del usuario loggeado y los productos existentes # Si no se encuentra, devuelve None

@app.route("/Enviar/Pedido",methods=['POST'])
@login_required
def EnviarPedido():
    pos = 0
    productos = request.form.getlist('productos[]')#Lista de productos seleccionados por el usuario
    cantidades = request.form.getlist('cantidades[]')
    metodo_entrega = request.form['metodoEntrega']
    metodo_pago = request.form['metodoPago']


    lista_final = []

    for id_producto in productos:
        cantidad = int(cantidades[pos]) #Tomamos el valor y lo convertimos en int
        producto = obtener_producto_por_id(id_producto) # lo enviamos a la funcion para buscarlo en la BD y obtener el precio
        precio = producto['precio'] if producto else 0 

        lista_final.append({
            'id': id_producto,
            'cantidad': cantidad,
            'subtotal': cantidad * precio
        })
        

    guardar_pedido_en_db(lista_final, current_user.id, "WEB" ,metodo_pago, metodo_entrega)
    
    return redirect(url_for('Pedidos'))  

def obtener_producto_por_id(id_producto):
    try:
        conn = get_db()
        if not conn:
            return None
    
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM TBL_PRODUCTOS WHERE ID_producto = %s", (id_producto,))
        producto = cursor.fetchone()
        cursor.close()
        conn.close()
        return producto
    except Exception as e:
        print(f"[load_user] Error: {e}") 
    return None  # Si no se encuentra, devuelve None

def guardar_pedido_en_db(lista_productos, num_cel, solicitud ,metodo_pago, metodo_entrega):
    conn = get_db()
    if not conn:
        return

    try:
        cursor = conn.cursor()

        # Paso 1: Obtener la fecha actual del servidor
        cursor.execute("SELECT CURDATE(), DAY(CURDATE()), MONTH(CURDATE()), YEAR(CURDATE())")
        fecha_actual, dia, mes, anio = cursor.fetchone()

        # Paso 2: Verificar si esa fecha ya existe como ID en TBL_FECHA
        sql_buscar = "SELECT ID_fecha FROM TBL_FECHA WHERE ID_fecha = %s"
        cursor.execute(sql_buscar, (fecha_actual,))
        existe = cursor.fetchone()

        # Paso 3: Si no existe, la insertamos
        if existe:
            print("La fecha ya existe con ID:", fecha_actual)
        else:
            sql_insertar_fecha = '''
                INSERT INTO TBL_FECHA (ID_fecha, Dia, Mes, Anio)
                VALUES (%s, %s, %s, %s)
            '''
            cursor.execute(sql_insertar_fecha, (fecha_actual, dia, mes, anio))
            conn.commit()
            print("Fecha insertada con ID:", fecha_actual)

        #Considerar su estado segun el metodo de pago
        if metodo_pago == "P1":
            estado = "E1"
        else:
            estado = "E3"

        if metodo_entrega == "DMC":
            total = 15 + total #Costo de domicilio

        # FLUJO DE PASOS PARA AÑADIR A LA BD EL PEDIDO
        # 1. Insertar un nuevo pedido en TBL_PEDIDOS
        total = sum(item['subtotal'] for item in lista_productos)
        cantidad_total = sum(item['cantidad'] for item in lista_productos)

        cursor.execute("""
            INSERT INTO TBL_PEDIDO (Cantidad, Importe_g, Fecha, Num_cel, Tipo_entrega, Tipo_solicitud, Tipo_pago, Tipo_estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            cantidad_total,
            total,
            fecha_actual, # Valor tomado del servidor de la BD
            num_cel, # Cel del cliente
            metodo_entrega,     # NECESITAS TOMAR ESTE VALOR DESDE EL HTML DE NANDO (PU o DMC)
            solicitud,        # lo hizo desde la APPWEB
            metodo_pago,      # según TBL_PAGO
            estado      # E1 = Aceptado y E3 = Pendiente (E2 = cancelado) segun el pedodo de pago (Si es efectivo será E1 sino será E3)
        ))

        # 2. Obtener el ID del nuevo pedido
        id_pedido = cursor.lastrowid

        # 3. Insertar cada producto en TBL_DETALLE_PEDIDOS
        for producto in lista_productos:
            cursor.execute("""
                INSERT INTO TBL_DETALLE_PEDIDO (Cantidad, Importe_p, N_pedido, ID_producto)
                VALUES (%s, %s, %s, %s)
            """, (
                producto['cantidad'],
                producto['subtotal'],
                id_pedido,
                producto['id']
            ))
            DescontarInventario(producto['id'],producto['cantidad'])

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print("Error al guardar pedido:", e)
        conn.rollback()
        conn.close()

def DescontarInventario(Id, Cantidad):
    conn = get_db()
    if not conn:
        print("No se pudo establecer conexión con la base de datos.")
        return False

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT Cantidad FROM TBL_PRODUCTOS WHERE ID_producto = %s", (Id,))
        producto = cursor.fetchone()

        if not producto:
            print(f"No se encontró el producto con ID {Id}")
            return False

        nueva_cantidad = max(producto["cantidad"] - Cantidad, 0)

        cursor.execute(
            "UPDATE TBL_PRODUCTOS SET Cantidad = %s WHERE ID_producto = %s",
            (nueva_cantidad, Id)
        )
        conn.commit()
        return True

    except Exception as e:
        print("Error al descontar inventario:", e)
        conn.rollback()
        return False

    finally:
        conn.close()




@app.route('/Invitado')
def invitado():
    try:
        conn = get_db() # Conecta a la base de datos
        if conn is None:
            return None  # No se pudo conectar = no hay usuario cargado
        
        cursor = conn.cursor(cursor_factory=RealDictCursor) # Activamos el diccionario para recibir los valores como un diccionario y no por [0], [1]
        cursor.execute("SELECT * FROM TBL_PRODUCTOS") # Busca los productos existentes
        Productos = cursor.fetchall() # Almacenamos todos los productos
        cursor.close() # Cerrar ursor
        conn.close() # IMPORTANTE!!!! Siempre cerrar la conexion con la base de datos
            
        return render_template('log_in_invitado.html',Productos = Productos)#Envia los datos del usuario loggeado y los productos existentes
    except Exception as e:
        print(f"[load_user] Error: {e}") 
    return render_template('log_in_invitado.html',Productos = Productos)


@app.route('/Enviar/Pedido/Invitado',methods=['POST'])
def EnviarPedidoInvitado():
    #Tomar los datos del invitados para generar el pedido.
    pos = 0
    telefono = request.form['telefono']
    nombre = request.form['nombre']
    apellido = request.form['apellido']
    apodo = request.form['apodo']
    productos = request.form.getlist('productos[]')#Lista de productos seleccionados por el usuario
    cantidades = request.form.getlist('cantidades[]')
    metodo_entrega = 'PU'
    metodo_pago = 'P2'
    
    lista_final = []
    for id_producto in productos:
        cantidad = int(cantidades[pos]) #Tomamos el valor y lo convertimos en int
        producto = obtener_producto_por_id(id_producto) # lo enviamos a la funcion para buscarlo en la BD y obtener el precio
        precio = producto['precio'] if producto else 0 

        lista_final.append({
            'id': id_producto,
            'cantidad': cantidad,
            'subtotal': cantidad * precio
        })
    
    if BuscarClientePorID(telefono):
        User = load_user(telefono)
        guardar_pedido_en_db(lista_final, User.id, "WEB" ,metodo_pago, metodo_entrega)
    else:
        if GuardarCliente(telefono, nombre, apellido, apodo):
            guardar_pedido_en_db(lista_final, telefono, "WEB" ,metodo_pago, metodo_entrega)
   
    return redirect(url_for('invitado'))  

def BuscarClientePorID(telefono):
    try:
        conn = get_db()  # Conexión a la base de datos
        if conn is None:
            return False  # Si no hay conexión, asumimos que no se puede buscar
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM TBL_CLIENTE WHERE ID_cel = %s", (telefono,))
        resultado = cursor.fetchone()

        cursor.close()
        conn.close()

        return True if resultado else False

    except Exception as e:
        print(f"[BuscarClientePorID] Error: {e}")
        return False


def GuardarCliente(telefono, nombre, apellido, apodo):
    try:
        conn = get_db() # Conecta a la base de datos
        if conn is None:
            return None  # No se pudo conectar = no hay usuario cargado
        
        cursor = conn.cursor() # Activamos el diccionario para recibir los valores como un diccionario y no por [0], [1]
        contra = generate_password_hash(str(nombre).capitalize())
        cursor.execute(
        "INSERT INTO TBL_CLIENTE (ID_cel, Nombre, Apellido, Apodo, Password) VALUES (%s, %s, %s, %s, %s)",
            (telefono, nombre, apellido, apodo, contra)
        )
        conn.commit()
        cursor.close()
        conn.close() # IMPORTANTE!!!! Siempre cerrar la conexion con la base de datos
        return True
    except Exception as e:
        print(f"[Invitado] Error: {e}")
        return False 

# Admin Panel Prueba
@app.route('/admin')
@login_required
def admin_inicio():
    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM TBL_PRODUCTOS")
    productos = cursor.fetchall()

    alertas_stock = []

    for producto in productos:
        cantidad = producto["cantidad"]
        mensaje = ""
        tipo = ""

        if cantidad == 0:
            tipo = "stock-empty"  # negro
            mensaje = f"◼️ SIN STOCK: {producto['nombre']} no tiene unidades disponibles."
        elif cantidad <= 5:
            tipo = "stock-danger"  # rojo
            mensaje = f"🔴 ADVERTENCIA: {producto['nombre']} está MUY cerca de agotarse (stock: {cantidad})"
        elif cantidad <= 10:
            tipo = "stock-warning"  # amarillo
            mensaje = f"🟡 CUIDADO: {producto['nombre']} está por agotarse (stock: {cantidad})"
        else:
            continue  # No mostrar productos con suficiente stock

        alertas_stock.append({
            "mensaje": mensaje,
            "tipo": tipo,
            "cantidad": cantidad
        })

    # Orden: verde arriba no se muestra, luego warning (10), danger (5), luego empty (0)
    prioridad = {"stock-warning": 2, "stock-danger": 1, "stock-empty": 0}
    alertas_stock.sort(key=lambda x: prioridad.get(x["tipo"], -1), reverse=True)

    return render_template("admin.html", modo="inicio", productos=productos, alertas_stock=alertas_stock)

# ver pedidos 
@app.route('/admin/pedidos', methods=['GET', 'POST'])
@login_required
def ver_pedidos():
    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    modo = 'pedidos'
    detalles = None
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'eliminar':
            pedido_id = request.form.get('id_pedido')
            cursor.execute("UPDATE TBL_PEDIDO SET Tipo_estado = %s WHERE ID_Pedido = %s", ('E4', pedido_id))
            db.commit()
        elif action == 'detalles':
            pedido_id = request.form.get('id_pedido')
            cursor.execute("""
                        SELECT
                            dp.Cantidad,
                            dp.Importe_p,
                            p.Nombre
                        FROM TBL_DETALLE_PEDIDO dp
                        INNER JOIN TBL_PRODUCTOS p ON dp.ID_producto = p.ID_producto
                        WHERE dp.N_pedido = %s""", (pedido_id,))
            detalles = cursor.fetchall()
            modo = 'detalles'
            db.commit()
        elif action == 'editar':
            pedido_id = request.form.get('id_pedido')
            cantidad = request.form.get('cantidad')
            importe = request.form.get('importe')
            fecha = request.form.get('fecha')
            num_cel = request.form.get('num_cel')
            tipo_entrega = request.form.get('tipo_entrega')
            tipo_solicitud = request.form.get('tipo_solicitud')
            tipo_pago = request.form.get('tipo_pago')
            tipo_estado = request.form.get('tipo_estado')

            cursor.execute("""
                UPDATE TBL_PEDIDO
                SET Cantidad = %s, Importe_g = %s, Fecha = %s, Num_cel = %s,
                    Tipo_entrega = %s, Tipo_solicitud = %s, Tipo_pago = %s, Tipo_estado = %s
                WHERE ID_Pedido = %s
            """, (cantidad, importe, fecha, num_cel, tipo_entrega, tipo_solicitud, tipo_pago, tipo_estado, pedido_id))
            db.commit()
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
    db.close()

    return render_template('admin.html', modo = modo, pedidos = pedidos, detalles = detalles)

#  Vista de clientes
@app.route('/admin/clientes', methods=['GET', 'POST'])
@login_required
def ver_clientes():
    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    Numero = request.args.get('buscar_cel')
    cursor.execute("SELECT * FROM tbl_colonia")
    colonias = cursor.fetchall()
    if Numero:
        cursor.execute("""
                        SELECT 
                            c.id_cel, c.nombre, c.apellido, c.apodo,
                            d.num_casa, d.calle, d.rruzamientos, d.referencia,
                            col.Colonia
                        FROM TBL_CLIENTE c
                        INNER JOIN TBL_DIRECCION d ON c.Dirreccion_c = d.ID_dirreccion
                        INNER JOIN TBL_COLONIA col ON d.Colonia_d = col.ID_colonia
                        WHERE c.Tipo = 'u' AND c.ID_cel = %s
                        """,(Numero,))
    else:
        cursor.execute("""
                        SELECT 
                            c.ID_cel, c.Nombre, c.Apellido, c.Apodo,
                            d.Num_casa, d.Calle, d.Cruzamientos, d.Referencia,
                            col.Colonia
                        FROM TBL_CLIENTE c
                        INNER JOIN TBL_DIRECCION d ON c.Dirreccion_c = d.ID_dirreccion
                        INNER JOIN TBL_COLONIA col ON d.Colonia_d = col.ID_colonia
                        WHERE c.Tipo = 'u'
                        """)
    Uclientes = cursor.fetchall()
    clientes = []
    for cliente in Uclientes:
        user = {
                'id':cliente['id_cel'],
                'nombre':cliente['nombre'],
                'apellido':cliente['apellido'],
                'apodo':cliente['apodo'],
                'direccion': F"#{cliente['num_casa']} C.{cliente['calle']} X{cliente['cruzamientos']} col.{cliente['colonia']}",
                'referencia':cliente["referencia"]
        }
        clientes.append(user)
    if request.method == "POST":
        apodo = request.form.get("Apodo")
        Id = request.form.get("id_original")
        cursor.execute("UPDATE TBL_CLIENTE SET Apodo = %s WHERE ID_cel = %s", (apodo, Id,))
        db.commit()
    db.close()
    return render_template('admin.html', modo='clientes', clientes=clientes, colonias = colonias)

#  Vista de clientes
@app.route('/admin/direccion', methods=['GET', 'POST'])
@login_required
def editar_direccion():
    print(request.form)
    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    id_cliente = request.form.get('id_cliente')
    num_casa = request.form.get('Num_casa')
    calle = request.form.get('Calle')
    cruzamientos = request.form.get('Cruzamientos')
    referencia = request.form.get('Referencia')
    colonia = request.form.get('Colonia')
    cursor.execute("INSERT INTO tbl_direccion (num_casa, calle, cruzamientos, referencia, colonia_d) VALUES(%s,%s,%s,%s,%s) RETURNING id_dirreccion",(num_casa,calle,cruzamientos,referencia,colonia))
    id_direccion = cursor.fetchone()['id_dirreccion']
    cursor.execute("UPDATE tbl_cliente SET dirreccion_c = %s WHERE id_cel = %s", (id_direccion, id_cliente))
    db.commit()
    db.close()
    return redirect(url_for('ver_clientes'))



#  Vista de clientes
@app.route('/admin/agregarCliente', methods=['GET', 'POST'])
@login_required
def crear_cliente():
    if request.method == "POST":
        Numero = request.form.get("nuevo_celular")
        Apodo = request.form.get("nuevo_apodo")
        Apellido = request.form.get("nuevo_apellido")
        Nombre = request.form.get("nuevo_nombre")
        GuardarCliente(Numero,Nombre,Apellido,Apodo)
    return redirect(url_for('ver_clientes'))

#  Vista de clientes
@app.route('/admin/eliminarProducto', methods=['GET', 'POST'])
@login_required
def eliminar_producto():
    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    if request.method == "POST":
        Id = request.form.get("id_producto")
        cursor.execute("DELETE FROM TBL_PRODUCTOS WHERE ID_producto = %s",(Id,))
        db.commit()
    db.close()
    return redirect(url_for("ver_inventario"))

#  Vista de inventario
@app.route('/admin/inventario', methods=['GET', 'POST'])
@login_required
def ver_inventario():
    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    ID = request.args.get('buscar_id')
    if ID :
        cursor.execute("SELECT * FROM tbl_productos WHERE id_producto = %s", (ID,))
    else:
        cursor.execute("SELECT * FROM tbl_productos")
    productos = cursor.fetchall()
    db.close()
    return render_template('admin.html', modo='inventario', productos=productos)

#  Agregar Productos
@app.route('/admin/agregarProducto', methods=['GET', 'POST'])
@login_required
def agregar_producto():
    try:
        db = get_db()
        cursor = db.cursor(cursor_factory=RealDictCursor)

        Id_producto = request.form.get("id_producto")
        Nombre = request.form.get("nombre")
        Cantidad = request.form.get("cantidad")
        Precio = request.form.get("precio")

        cursor.execute(
            "INSERT INTO TBL_PRODUCTOS (ID_producto,Nombre,Cantidad,Precio) VALUES (%s,%s,%s,%s)",
            (Id_producto, Nombre, Cantidad, Precio)
        )
        db.commit()
        flash("Producto agregado correctamente", "success")

    except Exception as e:
        db.rollback()
        flash(f"Producto NO agregado, posible existencia del mismo ID: {str(e)}", "danger")

    finally:
        cursor.close()
        db.close()

    return redirect(url_for("ver_inventario"))

# Vista de inventario
@app.route('/admin/inventario_UP', methods=['GET', 'POST'])
@login_required
def inventario_up():
    if request.method == 'POST':
        db = get_db()
        cursor = db.cursor(cursor_factory=RealDictCursor)
        
        # Obtener datos del formulario de manera segura
        Cantidad = request.form.get('cantidad')
        Precio = request.form.get('precio')
        id_producto = request.form.get('id_producto')

        # Validación básica (puedes expandir esto según tus necesidades)
        if not Cantidad or not Precio or not id_producto:
            return "Faltan datos necesarios"

        # Ejecutar la actualización
        try:
            cursor.execute(
                "UPDATE TBL_PRODUCTOS SET Cantidad = %s, Precio = %s WHERE ID_producto = %s",
                (Cantidad, Precio, id_producto)
            )
            db.commit()
            return redirect(url_for("ver_inventario"))
        except Exception as e:
            db.rollback()
            return f"Error al actualizar el producto: {e}"
        finally:
            db.close()
    else:
        return "Método no permitido"


@app.route('/admin/hacer/pedido', methods=['GET', 'POST'])
@login_required
def PedidoSuc():
    db = get_db()
    cursor = db.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM TBL_PRODUCTOS")
    productos = cursor.fetchall()
    db.close()
    if request.method == "POST":
        pos = 0
        telefono = request.form['telefono']
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        apodo = request.form['apodo']
        productos = request.form.getlist('productos[]')#Lista de productos seleccionados por el usuario
        cantidades = request.form.getlist('cantidades[]')
        metodo_entrega = 'PU'
        metodo_pago = 'P2'
        
        lista_final = []
        for id_producto in productos:
            cantidad = int(cantidades[pos]) #Tomamos el valor y lo convertimos en int
            producto = obtener_producto_por_id(id_producto) # lo enviamos a la funcion para buscarlo en la BD y obtener el precio
            precio = producto['precio'] if producto else 0 

            lista_final.append({
                'id': id_producto,
                'cantidad': cantidad,
                'subtotal': cantidad * precio
            })
        
        if BuscarClientePorID(telefono):
            User = load_user(telefono)
            guardar_pedido_en_db(lista_final, User.id, "SUC" ,metodo_pago, metodo_entrega)
        else:
            if GuardarCliente(telefono, nombre, apellido, apodo):
                guardar_pedido_en_db(lista_final, telefono, "SUC" ,metodo_pago, metodo_entrega)

    return render_template('admin.html', modo='hacerpedido', productos=productos)

if __name__ == '__main__':
    app.run(debug=True)