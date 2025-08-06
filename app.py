from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

# Usuario fijo
USUARIO = "Goku"
CLAVE = "zangetzu#90"

# Función para conexión con la base de datos
def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

# Crear tabla si no existe
def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS hwids (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hwid TEXT,
        cliente TEXT,
        estado TEXT,
        valido TEXT,
        dias_restantes INTEGER,
        fecha_activacion TEXT,
        fecha_expiracion TEXT
    )
    """)
    conn.commit()
init_db()

# Ruta de login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form["usuario"]
        clave = request.form["clave"]
        if usuario == USUARIO and clave == CLAVE:
            session["usuario"] = usuario
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Usuario o clave incorrectos")
    return render_template("login.html")

# Ruta de logout
@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect(url_for("login"))

# Decorador para requerir login
def login_requerido(f):
    def wrap(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    wrap.__name__ = f.__name__
    return wrap

# Dashboard
@app.route("/")
@login_requerido
def dashboard():
    conn = get_db()
    hwids = conn.execute("SELECT * FROM hwids").fetchall()
    total = len(hwids)
    activos = sum(1 for h in hwids if h["estado"] == "ACTIVE")
    validos = sum(1 for h in hwids if h["valido"] == "VÁLIDO")
    proximos = sum(1 for h in hwids if h["dias_restantes"] <= 3)
    return render_template("dashboard.html", hwids=hwids, total=total, activos=activos, validos=validos, proximos=proximos)

# Activar nuevo HWID
@app.route("/activar", methods=["GET", "POST"])
@login_requerido
def activar():
    if request.method == "POST":
        hwid = request.form["hwid"]
        cliente = request.form["cliente"]
        dias = int(request.form["dias"])
        fecha_activacion = datetime.now().strftime("%Y-%m-%d")
        fecha_expiracion = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")
        conn = get_db()
        conn.execute("""
        INSERT INTO hwids (hwid, cliente, estado, valido, dias_restantes, fecha_activacion, fecha_expiracion)
        VALUES (?, ?, 'ACTIVE', 'VÁLIDO', ?, ?, ?)
        """, (hwid, cliente, dias, fecha_activacion, fecha_expiracion))
        conn.commit()
        return redirect(url_for("dashboard"))
    return render_template("activar.html")

# Eliminar HWID
@app.route("/eliminar/<int:id>")
@login_requerido
def eliminar(id):
    conn = get_db()
    conn.execute("DELETE FROM hwids WHERE id = ?", (id,))
    conn.commit()
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True)