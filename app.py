from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
from flask_mail import Mail, Message
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import re
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'mi_secreto'  # Cambia esta clave por una clave segura

# Configuración de Flask-Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["20 per minute"]  # Límite predeterminado: 20 solicitudes por minuto
)

# Configuración de la base de datos
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'to_do_list',
    'charset': 'utf8mb4'
}

# Configuración de correo (Flask-Mail)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'tu_email@gmail.com'  # Cambiar por tu email
app.config['MAIL_PASSWORD'] = 'tu_contraseña_email'  # Cambiar por tu contraseña
mail = Mail(app)

# Función para crear conexión con la base de datos
def create_connection():
    try:
        conn = mysql.connector.connect(**db_config)
        return conn
    except Error as e:
        print(f"Error de conexión: {e}")
        return None

# Ruta de registro
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        usuario = request.form['usuario']
        correo = request.form['correo']
        contraseña = request.form['contraseña']
        confirm_contraseña = request.form['confirm_contraseña']
        
        if not re.match(r'^[a-zA-Z0-9]+$', usuario):
            flash("El nombre de usuario solo puede contener letras y números.", "danger")
        elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', correo):
            flash("Introduce un correo electrónico válido.", "danger")
        elif contraseña != confirm_contraseña:
            flash("Las contraseñas no coinciden.", "danger")
        else:
            conn = create_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    # Almacena la contraseña en texto plano
                    cursor.execute("INSERT INTO users (usuario, correo, contraseña) VALUES (%s, %s, %s)", 
                                   (usuario, correo, contraseña))
                    conn.commit()
                    flash("Usuario registrado exitosamente.", "success")
                    return redirect(url_for('login'))
                except Error as e:
                    flash(f"Error al registrar el usuario: {e}", "danger")
                finally:
                    cursor.close()
                    conn.close()
    return render_template('register.html')

# Ruta de inicio de sesión con límite de solicitudes
@limiter.limit("5 per minute")
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form.get('usuario')
        contraseña = request.form.get('contraseña')

        if not usuario or not contraseña:
            flash("Por favor, ingresa tanto el nombre de usuario como la contraseña.", "danger")
            return render_template('login.html')

        conn = create_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE usuario = %s", (usuario,))
            user = cursor.fetchone()
            cursor.close()
            conn.close()

            # Comparar la contraseña en texto plano (sin usar bcrypt)
            if user and contraseña == user['contraseña']:
                session['user_id'] = user['id']
                session['usuario'] = user['usuario']
                flash("Inicio de sesión exitoso.", "success")
                return redirect(url_for('todo_list'))
            else:
                flash("Usuario o contraseña incorrectos.", "danger")

    return render_template('login.html')

# Ruta para el To-Do List
@app.route('/todo_list', methods=['GET', 'POST'])
def todo_list():
    if 'user_id' not in session:
        flash("Inicia sesión para acceder al To-Do List", "warning")
        return redirect(url_for('login'))

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Agregar una tarea
    if request.method == 'POST':
        description = request.form.get('description')
        priority = request.form.get('priority')
        due_datetime = request.form.get('due_datetime')  # Tomamos el valor de due_datetime
        status = 'Pendiente'  # Cuando se agrega una nueva tarea, se establece como 'Pendiente'

        if description and priority and due_datetime:
            try:
                cursor.execute("INSERT INTO tasks (user_id, description, priority, status, due_datetime) VALUES (%s, %s, %s, %s, %s)",
                               (session['user_id'], description, priority, status, due_datetime))
                conn.commit()
                flash("Tarea añadida exitosamente.", "success")
            except Error as e:
                flash(f"Error al agregar la tarea: {e}", "danger")
        else:
            flash("Por favor, completa todos los campos.", "warning")

    # Obtener tareas
    cursor.execute(""" 
        SELECT * FROM tasks 
        WHERE user_id = %s 
        ORDER BY FIELD(status, 'Pendiente', 'En Progreso', 'Completada', 'No Hechas') DESC
    """, (session['user_id'],))
    tasks = cursor.fetchall()

    # Formatear las fechas
    for task in tasks:
        if task['due_datetime']:
            task['due_datetime'] = task['due_datetime'].strftime('%Y-%m-%d %H:%M:%S')

    cursor.close()
    conn.close()

    return render_template('todo_list.html', tasks=tasks)

# Ruta para actualizar la prioridad de una tarea
@app.route('/update_priority/<int:task_id>', methods=['GET', 'POST'])
def update_priority(task_id):
    if 'user_id' not in session:
        flash("Inicia sesión para acceder a las tareas", "warning")
        return redirect(url_for('login'))

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    # Obtener la tarea por su id
    cursor.execute("SELECT * FROM tasks WHERE id = %s AND user_id = %s", (task_id, session['user_id']))
    task = cursor.fetchone()

    if not task:
        flash("Tarea no encontrada.", "danger")
        return redirect(url_for('todo_list'))

    if request.method == 'POST':
        # Obtener nueva prioridad
        new_priority = request.form.get('priority')

        if new_priority:
            try:
                # Actualizar la prioridad en la base de datos
                cursor.execute("UPDATE tasks SET priority = %s WHERE id = %s", (new_priority, task_id))
                conn.commit()
                flash("Prioridad actualizada exitosamente.", "success")
                return redirect(url_for('todo_list'))
            except Error as e:
                flash(f"Error al actualizar la prioridad: {e}", "danger")

    cursor.close()
    conn.close()

    return render_template('prioridad.html', task=task)

# Ruta para actualizar el estado de una tarea
@app.route('/update_status/<int:task_id>', methods=['POST'])
def update_status(task_id):
    if 'user_id' not in session:
        flash("Inicia sesión para modificar el estado de las tareas", "warning")
        return redirect(url_for('login'))

    new_status = request.form.get('new_status')  # Leer el nuevo estado desde el formulario

    if not new_status:
        flash("Selecciona un estado válido.", "danger")
        return redirect(url_for('todo_list'))

    conn = create_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE tasks SET status = %s WHERE id = %s AND user_id = %s", 
                           (new_status, task_id, session['user_id']))
            conn.commit()
            flash("Estado de la tarea actualizado exitosamente.", "success")
        except Error as e:
            flash(f"Error al actualizar el estado: {e}", "danger")
        finally:
            cursor.close()
            conn.close()

    return redirect(url_for('todo_list'))

@app.route('/delete_task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM tasks WHERE id = %s AND user_id = %s
    """, (task_id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()

    flash("Tarea eliminada exitosamente.", "success")
    return redirect(url_for('todo_list'))

# Ruta para cerrar sesión
@app.route('/logout')
def logout():
    session.clear()
    flash("Sesión cerrada", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)

