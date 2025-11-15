-- ===================================================
-- Script para crear base de datos de reportes
-- ===================================================

-- Crear el usuario si no existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'siesa_report_user') THEN
        CREATE USER siesa_report_user WITH PASSWORD '123456';
    END IF;
END
$$;

-- Crear la base de datos si no existe
SELECT 'CREATE DATABASE siesa_report_db OWNER siesa_report_user'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'siesa_report_db')\gexec

-- Conectar a la base de datos siesa_report_db
\c siesa_report_db

-- Otorgar permisos al usuario
GRANT ALL PRIVILEGES ON DATABASE siesa_report_db TO siesa_report_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO siesa_report_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO siesa_report_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO siesa_report_user;

-- ===================================================
-- Crear tablas de ejemplo
-- ===================================================

-- Tabla de Clientes
CREATE TABLE IF NOT EXISTS clientes (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    email VARCHAR(100),
    telefono VARCHAR(20),
    ciudad VARCHAR(100),
    pais VARCHAR(100) DEFAULT 'Colombia',
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Productos
CREATE TABLE IF NOT EXISTS productos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    categoria VARCHAR(100),
    precio_unitario NUMERIC(15, 2) NOT NULL,
    stock INTEGER DEFAULT 0,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Ventas
CREATE TABLE IF NOT EXISTS ventas (
    id SERIAL PRIMARY KEY,
    numero_factura VARCHAR(50) UNIQUE NOT NULL,
    cliente_id INTEGER REFERENCES clientes(id),
    fecha_venta TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    subtotal NUMERIC(15, 2) NOT NULL DEFAULT 0,
    impuesto NUMERIC(15, 2) NOT NULL DEFAULT 0,
    total NUMERIC(15, 2) NOT NULL DEFAULT 0,
    estado VARCHAR(50) DEFAULT 'completada',
    observaciones TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de Detalle de Ventas
CREATE TABLE IF NOT EXISTS detalle_ventas (
    id SERIAL PRIMARY KEY,
    venta_id INTEGER REFERENCES ventas(id) ON DELETE CASCADE,
    producto_id INTEGER REFERENCES productos(id),
    cantidad INTEGER NOT NULL,
    precio_unitario NUMERIC(15, 2) NOT NULL,
    subtotal NUMERIC(15, 2) NOT NULL,
    impuesto NUMERIC(15, 2) NOT NULL DEFAULT 0,
    total NUMERIC(15, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================================
-- Insertar datos de ejemplo
-- ===================================================

-- Insertar clientes de ejemplo
INSERT INTO clientes (codigo, nombre, email, telefono, ciudad, pais) VALUES
('CLI001', 'Empresa ABC S.A.S', 'contacto@empresaabc.com', '3001234567', 'Bogotá', 'Colombia'),
('CLI002', 'Comercial XYZ Ltda', 'ventas@comercialxyz.com', '3009876543', 'Medellín', 'Colombia'),
('CLI003', 'Distribuidora La 14', 'info@la14.com', '3015551234', 'Cali', 'Colombia'),
('CLI004', 'Supermercado El Ahorro', 'compras@elahorro.com', '3012223344', 'Barranquilla', 'Colombia'),
('CLI005', 'Inversiones del Norte', 'admin@delnorte.com', '3018889999', 'Cartagena', 'Colombia')
ON CONFLICT (codigo) DO NOTHING;

-- Insertar productos de ejemplo
INSERT INTO productos (codigo, nombre, descripcion, categoria, precio_unitario, stock) VALUES
('PROD001', 'Laptop Dell Inspiron 15', 'Laptop 15 pulgadas, 8GB RAM, 256GB SSD', 'Tecnología', 2500000.00, 15),
('PROD002', 'Mouse Inalámbrico Logitech', 'Mouse inalámbrico ergonómico', 'Accesorios', 85000.00, 50),
('PROD003', 'Teclado Mecánico RGB', 'Teclado mecánico con iluminación RGB', 'Accesorios', 250000.00, 30),
('PROD004', 'Monitor Samsung 24"', 'Monitor Full HD 24 pulgadas', 'Tecnología', 650000.00, 20),
('PROD005', 'Impresora HP LaserJet', 'Impresora láser monocromática', 'Tecnología', 1200000.00, 10),
('PROD006', 'Silla Ergonómica', 'Silla de oficina ergonómica', 'Muebles', 450000.00, 25),
('PROD007', 'Escritorio Ejecutivo', 'Escritorio de madera 1.60m x 0.80m', 'Muebles', 800000.00, 12),
('PROD008', 'Cable HDMI 2m', 'Cable HDMI 2.0 de 2 metros', 'Accesorios', 35000.00, 100),
('PROD009', 'Webcam Logitech HD', 'Webcam HD 1080p con micrófono', 'Accesorios', 180000.00, 40),
('PROD010', 'Audífonos Bluetooth', 'Audífonos inalámbricos con cancelación de ruido', 'Accesorios', 320000.00, 35)
ON CONFLICT (codigo) DO NOTHING;

-- Insertar ventas de ejemplo (últimos 3 meses)
INSERT INTO ventas (numero_factura, cliente_id, fecha_venta, subtotal, impuesto, total, estado) VALUES
('FAC-2024-001', 1, '2024-08-15 10:30:00', 2500000.00, 475000.00, 2975000.00, 'completada'),
('FAC-2024-002', 2, '2024-08-20 14:15:00', 900000.00, 171000.00, 1071000.00, 'completada'),
('FAC-2024-003', 3, '2024-09-05 11:20:00', 1650000.00, 313500.00, 1963500.00, 'completada'),
('FAC-2024-004', 1, '2024-09-10 16:45:00', 565000.00, 107350.00, 672350.00, 'completada'),
('FAC-2024-005', 4, '2024-09-18 09:30:00', 3300000.00, 627000.00, 3927000.00, 'completada'),
('FAC-2024-006', 2, '2024-10-02 13:00:00', 1450000.00, 275500.00, 1725500.00, 'completada'),
('FAC-2024-007', 5, '2024-10-08 10:15:00', 800000.00, 152000.00, 952000.00, 'completada'),
('FAC-2024-008', 3, '2024-10-15 15:30:00', 2150000.00, 408500.00, 2558500.00, 'completada'),
('FAC-2024-009', 1, '2024-10-22 11:45:00', 685000.00, 130150.00, 815150.00, 'completada'),
('FAC-2024-010', 4, '2024-11-03 14:20:00', 1900000.00, 361000.00, 2261000.00, 'completada'),
('FAC-2024-011', 2, '2024-11-08 09:00:00', 1200000.00, 228000.00, 1428000.00, 'completada'),
('FAC-2024-012', 5, '2024-11-12 16:10:00', 3500000.00, 665000.00, 4165000.00, 'completada')
ON CONFLICT (numero_factura) DO NOTHING;

-- Insertar detalles de ventas
INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, subtotal, impuesto, total) VALUES
-- FAC-2024-001
(1, 1, 1, 2500000.00, 2500000.00, 475000.00, 2975000.00),
-- FAC-2024-002
(2, 2, 2, 85000.00, 170000.00, 32300.00, 202300.00),
(2, 3, 2, 250000.00, 500000.00, 95000.00, 595000.00),
(2, 8, 3, 35000.00, 105000.00, 19950.00, 124950.00),
(2, 9, 1, 180000.00, 180000.00, 34200.00, 214200.00),
-- FAC-2024-003
(3, 4, 2, 650000.00, 1300000.00, 247000.00, 1547000.00),
(3, 8, 10, 35000.00, 350000.00, 66500.00, 416500.00),
-- FAC-2024-004
(4, 6, 1, 450000.00, 450000.00, 85500.00, 535500.00),
(4, 2, 1, 85000.00, 85000.00, 16150.00, 101150.00),
(4, 8, 1, 35000.00, 35000.00, 6650.00, 41650.00),
-- FAC-2024-005
(5, 1, 1, 2500000.00, 2500000.00, 475000.00, 2975000.00),
(5, 7, 1, 800000.00, 800000.00, 152000.00, 952000.00),
-- FAC-2024-006
(6, 5, 1, 1200000.00, 1200000.00, 228000.00, 1428000.00),
(6, 3, 1, 250000.00, 250000.00, 47500.00, 297500.00),
-- FAC-2024-007
(7, 7, 1, 800000.00, 800000.00, 152000.00, 952000.00),
-- FAC-2024-008
(8, 1, 1, 2500000.00, 2500000.00, 475000.00, 2975000.00),
(8, 10, 2, 320000.00, 640000.00, 121600.00, 761600.00),
-- FAC-2024-009
(9, 6, 1, 450000.00, 450000.00, 85500.00, 535500.00),
(9, 3, 1, 250000.00, 250000.00, 47500.00, 297500.00),
-- FAC-2024-010
(10, 4, 2, 650000.00, 1300000.00, 247000.00, 1547000.00),
(10, 9, 3, 180000.00, 540000.00, 102600.00, 642600.00),
(10, 8, 2, 35000.00, 70000.00, 13300.00, 83300.00),
-- FAC-2024-011
(11, 5, 1, 1200000.00, 1200000.00, 228000.00, 1428000.00),
-- FAC-2024-012
(12, 1, 1, 2500000.00, 2500000.00, 475000.00, 2975000.00),
(12, 4, 1, 650000.00, 650000.00, 123500.00, 773500.00),
(12, 10, 1, 320000.00, 320000.00, 60800.00, 380800.00),
(12, 8, 1, 35000.00, 35000.00, 6650.00, 41650.00)
ON CONFLICT DO NOTHING;

-- ===================================================
-- Crear índices para mejorar el rendimiento
-- ===================================================

CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_venta);
CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_detalle_venta ON detalle_ventas(venta_id);
CREATE INDEX IF NOT EXISTS idx_detalle_producto ON detalle_ventas(producto_id);
CREATE INDEX IF NOT EXISTS idx_clientes_ciudad ON clientes(ciudad);

-- ===================================================
-- Crear vista para reportes
-- ===================================================

CREATE OR REPLACE VIEW vista_ventas_detalladas AS
SELECT 
    v.id as venta_id,
    v.numero_factura,
    v.fecha_venta,
    v.estado,
    c.codigo as cliente_codigo,
    c.nombre as cliente_nombre,
    c.ciudad as cliente_ciudad,
    c.pais as cliente_pais,
    p.codigo as producto_codigo,
    p.nombre as producto_nombre,
    p.categoria as producto_categoria,
    dv.cantidad,
    dv.precio_unitario,
    dv.subtotal,
    dv.impuesto,
    dv.total,
    v.total as total_venta
FROM ventas v
INNER JOIN clientes c ON v.cliente_id = c.id
INNER JOIN detalle_ventas dv ON v.id = dv.venta_id
INNER JOIN productos p ON dv.producto_id = p.id
ORDER BY v.fecha_venta DESC;

-- ===================================================
-- Otorgar permisos finales al usuario
-- ===================================================

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO siesa_report_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO siesa_report_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO siesa_report_user;

-- Mostrar resumen
SELECT 'Base de datos configurada exitosamente!' as mensaje;
SELECT 'Tablas creadas:' as info;
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;
