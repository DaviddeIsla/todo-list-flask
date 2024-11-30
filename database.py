import mysql.connector

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",  # El usuario predeterminado de XAMPP
            password="",  # XAMPP no usa contraseña para root por defecto
            database="to_do_list"  # Usa el nuevo nombre de la base de datos sin espacios
        )
        print("Conexión a la base de datos establecida.")
        return connection
    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None

