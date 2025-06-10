from flask import Flask, render_template, request, redirect, url_for, make_response
import psycopg2
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)

# Configuración de la base de datos PostgreSQL en Aiven
DATABASE_URL = "postgres://avnadmin:AVNS_pdsDJhAU_gTzfuGRc-n@pg-396fdbe9-gaaa.f.aivencloud.com:12081/defaultdb?sslmode=require"

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

def init_db():
    with app.app_context():
        conn = get_db_connection()
        cur = conn.cursor()

        # Tabla de clientes
        cur.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                nit TEXT NOT NULL
            )
        ''')

        # Tabla de productos
        cur.execute('''
            CREATE TABLE IF NOT EXISTS productos (
                id SERIAL PRIMARY KEY,
                nombre TEXT NOT NULL,
                tipo TEXT NOT NULL,
                codigo TEXT NOT NULL,
                precio_unitario REAL NOT NULL
            )
        ''')

        # Tabla de ventas
        cur.execute('''
            CREATE TABLE IF NOT EXISTS ventas (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER NOT NULL,
                producto_id INTEGER NOT NULL,
                cantidad INTEGER NOT NULL,
                monto_total REAL NOT NULL,
                fecha_venta DATE NOT NULL,
                FOREIGN KEY (cliente_id) REFERENCES clientes (id),
                FOREIGN KEY (producto_id) REFERENCES productos (id)
            )
        ''')

        conn.commit()
        cur.close()

@app.route('/')
def index():
    return redirect(url_for('ventas'))

# Rutas para clientes
@app.route('/clientes', methods=['GET', 'POST'])
def clientes():
    if request.method == 'POST':
        nombre = request.form['nombre']
        nit = request.form['nit']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO clientes (nombre, nit) VALUES (%s, %s)', (nombre, nit))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('clientes'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM clientes')
    clientes = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('clientes.html', clientes=clientes)

@app.route('/editar_cliente/<int:id>', methods=['GET', 'POST'])
def editar_cliente(id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        nombre = request.form['nombre']
        nit = request.form['nit']

        cur.execute('UPDATE clientes SET nombre = %s, nit = %s WHERE id = %s', (nombre, nit, id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('clientes'))

    cur.execute('SELECT * FROM clientes WHERE id = %s', (id,))
    cliente = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('editar_cliente.html', cliente=cliente)

@app.route('/borrar_cliente/<int:id>')
def borrar_cliente(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM clientes WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('clientes'))

# Rutas para productos
@app.route('/productos', methods=['GET', 'POST'])
def productos():
    if request.method == 'POST':
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        codigo = request.form['codigo']
        precio_unitario = float(request.form['precio_unitario'])

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO productos (nombre, tipo, codigo, precio_unitario) VALUES (%s, %s, %s, %s)',
                    (nombre, tipo, codigo, precio_unitario))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('productos'))

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM productos')
    productos = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('productos.html', productos=productos)

@app.route('/editar_producto/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    conn = get_db_connection()
    cur = conn.cursor()

    if request.method == 'POST':
        nombre = request.form['nombre']
        tipo = request.form['tipo']
        codigo = request.form['codigo']
        precio_unitario = float(request.form['precio_unitario'])

        cur.execute('UPDATE productos SET nombre = %s, tipo = %s, codigo = %s, precio_unitario = %s WHERE id = %s',
                    (nombre, tipo, codigo, precio_unitario, id))
        conn.commit()
        cur.close()
        conn.close()
        return redirect(url_for('productos'))

    cur.execute('SELECT * FROM productos WHERE id = %s', (id,))
    producto = cur.fetchone()
    cur.close()
    conn.close()
    return render_template('editar_producto.html', producto=producto)

@app.route('/borrar_producto/<int:id>')
def borrar_producto(id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM productos WHERE id = %s', (id,))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for('productos'))

# Rutas para ventas
@app.route('/ventas', methods=['GET', 'POST'])
def ventas():
    conn = get_db_connection()
    cur = conn.cursor()

    # Verificar si hay clientes y productos
    cur.execute('SELECT COUNT(*) FROM clientes')
    num_clientes = cur.fetchone()[0]
    cur.execute('SELECT COUNT(*) FROM productos')
    num_productos = cur.fetchone()[0]

    if request.method == 'POST':
        if 'add_producto' in request.form:
            # Redirigir a la página de productos
            return redirect(url_for('productos'))
        else:
            # Registrar una venta
            cliente_id = int(request.form['cliente_id'])
            producto_id = int(request.form['producto_id'])
            cantidad = int(request.form['cantidad'])
            monto_total = float(request.form['monto_total'])
            fecha_venta = request.form['fecha_venta']

            cur.execute('INSERT INTO ventas (cliente_id, producto_id, cantidad, monto_total, fecha_venta) VALUES (%s, %s, %s, %s, %s)',
                        (cliente_id, producto_id, cantidad, monto_total, fecha_venta))
            conn.commit()
            return redirect(url_for('ventas'))

    # Obtener datos para mostrar en la página
    cur.execute('SELECT * FROM clientes')
    clientes = cur.fetchall()
    cur.execute('SELECT * FROM productos')
    productos = cur.fetchall()

    # Filtro por nombre o NIT del cliente
    filtro = request.args.get('filtro', '').strip()
    if filtro:
        cur.execute('''
            SELECT ventas.id, clientes.nombre, productos.nombre, ventas.cantidad, ventas.monto_total, ventas.fecha_venta
            FROM ventas
            JOIN clientes ON ventas.cliente_id = clientes.id
            JOIN productos ON ventas.producto_id = productos.id
            WHERE clientes.nombre ILIKE %s OR clientes.nit ILIKE %s
            ORDER BY ventas.fecha_venta DESC
        ''', (f'%{filtro}%', f'%{filtro}%'))
    else:
        cur.execute('''
            SELECT ventas.id, clientes.nombre, productos.nombre, ventas.cantidad, ventas.monto_total, ventas.fecha_venta
            FROM ventas
            JOIN clientes ON ventas.cliente_id = clientes.id
            JOIN productos ON ventas.producto_id = productos.id
            ORDER BY ventas.fecha_venta DESC
        ''')

    ventas = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('ventas.html', clientes=clientes, productos=productos, ventas=ventas, num_clientes=num_clientes, num_productos=num_productos, filtro=filtro)

@app.route('/download_pdf', methods=['GET', 'POST'])
def download_pdf():
    if request.method == 'POST':
        fecha_inicio = request.form['fecha_inicio']
        fecha_fin = request.form['fecha_fin']

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('''
            SELECT ventas.id, clientes.nombre, productos.nombre, ventas.cantidad, ventas.monto_total, ventas.fecha_venta
            FROM ventas
            JOIN clientes ON ventas.cliente_id = clientes.id
            JOIN productos ON ventas.producto_id = productos.id
            WHERE ventas.fecha_venta BETWEEN %s AND %s
            ORDER BY ventas.fecha_venta DESC
        ''', (fecha_inicio, fecha_fin))
        ventas = cur.fetchall()
        cur.close()
        conn.close()

        # Crear un PDF
        buffer = io.BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.drawString(100, 750, f"Historial de Ventas ({fecha_inicio} a {fecha_fin})")

        y = 700
        for venta in ventas:
            pdf.drawString(100, y, f"Cliente: {venta[1]}")
            pdf.drawString(100, y - 20, f"Producto: {venta[2]}")
            pdf.drawString(100, y - 40, f"Cantidad: {venta[3]}")
            pdf.drawString(100, y - 60, f"Monto Total: {venta[4]} Bs.")
            pdf.drawString(100, y - 80, f"Fecha de Venta: {venta[5]}")
            pdf.drawAlignedString(100, y, f"<br>")
            y -= 100

        pdf.save()
        buffer.seek(0)

        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=historial_ventas_{fecha_inicio}_a_{fecha_fin}.pdf'
        return response

    return render_template('descargar_pdf.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)