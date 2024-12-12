import mysql.connector
import sys

import pymysql

def get_db_connection():
    try:
        if "pythonanywhere" in sys.argv:
            # Configuración para PythonAnywhere
            connection = pymysql.connect(
                host='daviddeisla7.mysql.pythonanywhere-services.com',
                user='daviddeisla7',
                password='Sevilla77.',
                database='to_do_list',  # Nombre de tu base de datos
                cursorclass=pymysql.cursors.DictCursor
            )
        else:
            # Configuración para XAMPP (local)
            connection = mysql.connector.connect(
                host="localhost",  # Usamos localhost en desarrollo local
                user="root",  # Usuario predeterminado de XAMPP
                password="",  # XAMPP no tiene contraseña por defecto
                database="to_do_list"  # Asegúrate de que la base de datos existe localmente
            )

        print("Conexión a la base de datos establecida.")
        return connection

    except mysql.connector.Error as err:
        print(f"Error al conectar a la base de datos: {err}")
        return None
    except Exception as e:
        print(f"Ha ocurrido un error inesperado: {e}")
        return None





