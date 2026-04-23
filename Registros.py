from Conector import Conector
usuarios = [
    {"user": "m_app", "password": "fruteria7"}, # 0
    {"user": "m_app", "password": "fruteria7"}, # 1
    {"user": "m_crud", "password": "Usuario7"}, # 2
    {"user": "f_lectura", "password": "LecturaFru"} # 3
]
#hacer un for que inserte 100 registros en la base de datos
#registrar numero de celular (funcion random para generar numeros de 10 digitos), nombre, apellido, apodo y el numero 1.

try:
    con = Conector(usuarios[0]["user"],usuarios[0]["password"])
    conn = con.conectar()
    cursor = conn.cursor()
    i=4687
    while i < 32999:
        numero_celular = str(i).zfill(10)  # Genera un número de celular de 10 dígitos
        nombre = f"Nombre{i}"
        apellido = f"Apellido{i}"
        apodo = f"Apodo{i}"
        cursor.execute("""
            INSERT INTO tbl_cliente (id_cel, nombre, apellido, apodo, dirreccion_c)
            VALUES (%s, %s, %s, %s, %s)
            """, (numero_celular, nombre, apellido, apodo, 1))
        conn.commit()
        i += 1
    con.cerrar()   
except Exception as e:
        print(f"[load_user] Error: {e}") 