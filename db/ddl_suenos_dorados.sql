
CREATE TABLE categorias (
	id_categoria SERIAL NOT NULL, 
	nombre_categoria VARCHAR(80) NOT NULL, 
	descripcion_categoria TEXT, 
	slug VARCHAR(100) NOT NULL, 
	PRIMARY KEY (id_categoria), 
	UNIQUE (slug)
);


CREATE TABLE colores (
	id_color SERIAL NOT NULL, 
	nombre_color VARCHAR(60) NOT NULL, 
	codigo_hex VARCHAR(7), 
	PRIMARY KEY (id_color)
);


CREATE TABLE estado_envio (
	id_estado_envio SERIAL NOT NULL, 
	descripcion_estado VARCHAR(60) NOT NULL, 
	PRIMARY KEY (id_estado_envio)
);


CREATE TABLE estado_pedido (
	id_estado_pedido SERIAL NOT NULL, 
	descripcion_estado VARCHAR(60) NOT NULL, 
	PRIMARY KEY (id_estado_pedido)
);


CREATE TABLE medidas (
	id_medida SERIAL NOT NULL, 
	nombre_medida VARCHAR(50) NOT NULL, 
	ancho_cm NUMERIC(6, 2), 
	largo_cm NUMERIC(6, 2), 
	descripcion VARCHAR(100), 
	PRIMARY KEY (id_medida)
);


CREATE TABLE respuesta_bold (
	id_respuesta SERIAL NOT NULL, 
	transaction_id VARCHAR(100) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	payment_method VARCHAR(50), 
	amount NUMERIC(12, 2) NOT NULL, 
	timestamp_bold TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	raw_response TEXT, 
	PRIMARY KEY (id_respuesta), 
	UNIQUE (transaction_id)
);


CREATE TABLE roles (
	id_rol SERIAL NOT NULL, 
	descripcion_rol VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id_rol)
);


CREATE TABLE colecciones (
	id_coleccion SERIAL NOT NULL, 
	id_categoria INTEGER NOT NULL, 
	nombre_coleccion VARCHAR(100) NOT NULL, 
	descripcion_coleccion TEXT, 
	estado BOOLEAN NOT NULL, 
	PRIMARY KEY (id_coleccion), 
	FOREIGN KEY(id_categoria) REFERENCES categorias (id_categoria) ON DELETE RESTRICT ON UPDATE CASCADE
);


CREATE TABLE usuarios (
	id_usuario SERIAL NOT NULL, 
	id_rol INTEGER NOT NULL, 
	nombre_usuario VARCHAR(80) NOT NULL, 
	apellido_usuario VARCHAR(80) NOT NULL, 
	correo_electronico VARCHAR(120) NOT NULL, 
	telefono VARCHAR(20), 
	contrasena_hash VARCHAR(255) NOT NULL, 
	fecha_registro TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	estado BOOLEAN NOT NULL, 
	PRIMARY KEY (id_usuario), 
	FOREIGN KEY(id_rol) REFERENCES roles (id_rol) ON DELETE RESTRICT ON UPDATE CASCADE, 
	UNIQUE (correo_electronico)
);


CREATE TABLE direcciones (
	id_direccion SERIAL NOT NULL, 
	id_usuario INTEGER NOT NULL, 
	descripcion_direccion VARCHAR(200) NOT NULL, 
	descripcion_barrio VARCHAR(100), 
	descripcion_municipio VARCHAR(100) NOT NULL, 
	descripcion_departamento VARCHAR(100) NOT NULL, 
	es_principal BOOLEAN NOT NULL, 
	PRIMARY KEY (id_direccion), 
	FOREIGN KEY(id_usuario) REFERENCES usuarios (id_usuario) ON DELETE CASCADE ON UPDATE CASCADE
);


CREATE TABLE productos (
	id_producto SERIAL NOT NULL, 
	id_categoria INTEGER NOT NULL, 
	id_coleccion INTEGER, 
	nombre_producto VARCHAR(150) NOT NULL, 
	descripcion_producto TEXT, 
	slug VARCHAR(180) NOT NULL, 
	estado_producto BOOLEAN NOT NULL, 
	fecha_creacion TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id_producto), 
	FOREIGN KEY(id_categoria) REFERENCES categorias (id_categoria) ON DELETE RESTRICT ON UPDATE CASCADE, 
	FOREIGN KEY(id_coleccion) REFERENCES colecciones (id_coleccion) ON DELETE SET NULL ON UPDATE CASCADE, 
	UNIQUE (slug)
);


CREATE TABLE descuentos (
	id SERIAL NOT NULL, 
	id_producto INTEGER, 
	codigo VARCHAR(40) NOT NULL, 
	porcentaje_descuento NUMERIC(5, 2) NOT NULL, 
	fecha_inicio DATE NOT NULL, 
	fecha_fin DATE NOT NULL, 
	is_active BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_descuentos_codigo UNIQUE (codigo), 
	CONSTRAINT ck_descuentos_porcentaje_rango CHECK (porcentaje_descuento >= 0 AND porcentaje_descuento <= 100), 
	CONSTRAINT ck_descuentos_fechas_validas CHECK (fecha_fin >= fecha_inicio), 
	FOREIGN KEY(id_producto) REFERENCES productos (id_producto) ON DELETE SET NULL ON UPDATE CASCADE
);


CREATE TABLE imagenes_producto (
	id_imagen SERIAL NOT NULL, 
	id_producto INTEGER NOT NULL, 
	id_color INTEGER, 
	url_imagen VARCHAR(500) NOT NULL, 
	orden INTEGER NOT NULL, 
	es_principal BOOLEAN NOT NULL, 
	PRIMARY KEY (id_imagen), 
	FOREIGN KEY(id_producto) REFERENCES productos (id_producto) ON DELETE CASCADE ON UPDATE CASCADE, 
	FOREIGN KEY(id_color) REFERENCES colores (id_color) ON DELETE SET NULL ON UPDATE CASCADE
);


CREATE TABLE pedidos (
	id_pedido SERIAL NOT NULL, 
	id_usuario INTEGER NOT NULL, 
	id_direccion INTEGER NOT NULL, 
	id_estado_pedido INTEGER NOT NULL, 
	fecha_pedido TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	subtotal NUMERIC(12, 2) NOT NULL, 
	descuento NUMERIC(12, 2) NOT NULL, 
	costo_envio NUMERIC(12, 2) NOT NULL, 
	total NUMERIC(12, 2) NOT NULL, 
	PRIMARY KEY (id_pedido), 
	FOREIGN KEY(id_usuario) REFERENCES usuarios (id_usuario) ON DELETE RESTRICT ON UPDATE CASCADE, 
	FOREIGN KEY(id_direccion) REFERENCES direcciones (id_direccion) ON DELETE RESTRICT ON UPDATE CASCADE, 
	FOREIGN KEY(id_estado_pedido) REFERENCES estado_pedido (id_estado_pedido) ON DELETE RESTRICT ON UPDATE CASCADE
);


CREATE TABLE variantes_producto (
	id_variante SERIAL NOT NULL, 
	id_producto INTEGER NOT NULL, 
	id_medida INTEGER NOT NULL, 
	id_color INTEGER NOT NULL, 
	sku VARCHAR(60) NOT NULL, 
	precio NUMERIC(12, 2) NOT NULL, 
	referencia VARCHAR(100) NOT NULL, 
	stock INTEGER NOT NULL, 
	estado BOOLEAN NOT NULL, 
	PRIMARY KEY (id_variante), 
	CONSTRAINT uq_variantes_combinacion UNIQUE (id_producto, id_medida, id_color, referencia), 
	FOREIGN KEY(id_producto) REFERENCES productos (id_producto) ON DELETE CASCADE ON UPDATE CASCADE, 
	FOREIGN KEY(id_medida) REFERENCES medidas (id_medida) ON DELETE RESTRICT ON UPDATE CASCADE, 
	FOREIGN KEY(id_color) REFERENCES colores (id_color) ON DELETE RESTRICT ON UPDATE CASCADE, 
	UNIQUE (sku)
);


CREATE TABLE detalle_pedido (
	id_detalle_pedido SERIAL NOT NULL, 
	id_pedido INTEGER NOT NULL, 
	id_variante INTEGER NOT NULL, 
	cantidad INTEGER NOT NULL, 
	precio_unitario NUMERIC(12, 2) NOT NULL, 
	PRIMARY KEY (id_detalle_pedido), 
	FOREIGN KEY(id_pedido) REFERENCES pedidos (id_pedido) ON DELETE CASCADE ON UPDATE CASCADE, 
	FOREIGN KEY(id_variante) REFERENCES variantes_producto (id_variante) ON DELETE RESTRICT ON UPDATE CASCADE
);


CREATE TABLE envio (
	id_envio SERIAL NOT NULL, 
	id_pedido INTEGER NOT NULL, 
	id_estado_envio INTEGER NOT NULL, 
	numero_guia VARCHAR(100), 
	transportadora VARCHAR(80), 
	fecha_envio TIMESTAMP WITHOUT TIME ZONE, 
	fecha_entrega_estimada TIMESTAMP WITHOUT TIME ZONE, 
	fecha_entrega_real TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id_envio), 
	UNIQUE (id_pedido), 
	FOREIGN KEY(id_pedido) REFERENCES pedidos (id_pedido) ON DELETE RESTRICT ON UPDATE CASCADE, 
	FOREIGN KEY(id_estado_envio) REFERENCES estado_envio (id_estado_envio) ON DELETE RESTRICT ON UPDATE CASCADE, 
	UNIQUE (numero_guia)
);


CREATE TABLE movimientos_inventario (
	id_movimiento SERIAL NOT NULL, 
	id_variante INTEGER NOT NULL, 
	tipo_movimiento VARCHAR(20) NOT NULL, 
	cantidad INTEGER NOT NULL, 
	stock_anterior INTEGER NOT NULL, 
	stock_nuevo INTEGER NOT NULL, 
	referencia_documento VARCHAR(100), 
	observacion TEXT, 
	fecha_movimiento TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id_movimiento), 
	FOREIGN KEY(id_variante) REFERENCES variantes_producto (id_variante) ON DELETE RESTRICT ON UPDATE CASCADE
);


CREATE TABLE pagos (
	id_pago SERIAL NOT NULL, 
	id_pedido INTEGER NOT NULL, 
	id_respuesta_bold INTEGER, 
	monto NUMERIC(12, 2) NOT NULL, 
	fecha_pago TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	metodo_pago VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id_pago), 
	UNIQUE (id_pedido), 
	FOREIGN KEY(id_pedido) REFERENCES pedidos (id_pedido) ON DELETE RESTRICT ON UPDATE CASCADE, 
	FOREIGN KEY(id_respuesta_bold) REFERENCES respuesta_bold (id_respuesta) ON DELETE SET NULL ON UPDATE CASCADE
);

CREATE INDEX ix_usuarios_id_rol_estado ON usuarios (id_rol, estado);

CREATE INDEX ix_productos_categoria_estado ON productos (id_categoria, estado_producto);

CREATE INDEX ix_productos_coleccion_estado ON productos (id_coleccion, estado_producto);

CREATE INDEX ix_descuentos_codigo_activo ON descuentos (codigo, is_active);

CREATE INDEX ix_descuentos_producto_activo ON descuentos (id_producto, is_active);

CREATE INDEX ix_pedidos_estado_fecha ON pedidos (id_estado_pedido, fecha_pedido);

CREATE INDEX ix_pedidos_usuario_fecha ON pedidos (id_usuario, fecha_pedido);

CREATE INDEX ix_variantes_estado_stock ON variantes_producto (estado, stock);

CREATE INDEX ix_variantes_producto_estado ON variantes_producto (id_producto, estado);

-- ============================================================
--  INSERCIÓN DE DATOS INICIALES
-- ============================================================

INSERT INTO roles (descripcion_rol) VALUES ('Administrador');
INSERT INTO roles (descripcion_rol) VALUES ('Cliente');

INSERT INTO estado_pedido (descripcion_estado) VALUES 
('Pendiente'), ('Pagado'), ('En preparación'), ('Despachado'), ('Entregado'), ('Cancelado'), ('Reembolsado');

INSERT INTO estado_envio (descripcion_estado) VALUES 
('Pendiente despacho'), ('En tránsito'), ('En ciudad destino'), ('Entregado'), ('Novedad'), ('Devuelto');

-- Script generado desde INVENTARIO PARA PAG.csv
-- Ejecutar en la base de datos suenos_dorados.
BEGIN;

-- Categorias
INSERT INTO categorias (nombre_categoria, descripcion_categoria, slug) VALUES ('Edredones', 'Productos de edredones', 'edredones') ON CONFLICT (slug) DO UPDATE SET nombre_categoria = EXCLUDED.nombre_categoria, descripcion_categoria = EXCLUDED.descripcion_categoria;
INSERT INTO categorias (nombre_categoria, descripcion_categoria, slug) VALUES ('Sábanas', 'Productos de sábanas', 'sabanas') ON CONFLICT (slug) DO UPDATE SET nombre_categoria = EXCLUDED.nombre_categoria, descripcion_categoria = EXCLUDED.descripcion_categoria;

-- Color por defecto para inventario sin color especifico
INSERT INTO colores (nombre_color, codigo_hex) SELECT 'Sin especificar', NULL WHERE NOT EXISTS (SELECT 1 FROM colores WHERE nombre_color = 'Sin especificar');

-- Medidas
INSERT INTO medidas (nombre_medida, ancho_cm, largo_cm, descripcion) SELECT '100x190', 100.0, 190.0, 'Medida 100x190' WHERE NOT EXISTS (SELECT 1 FROM medidas WHERE ancho_cm = 100.0 AND largo_cm = 190.0);
INSERT INTO medidas (nombre_medida, ancho_cm, largo_cm, descripcion) SELECT '120x190', 120.0, 190.0, 'Medida 120x190' WHERE NOT EXISTS (SELECT 1 FROM medidas WHERE ancho_cm = 120.0 AND largo_cm = 190.0);
INSERT INTO medidas (nombre_medida, ancho_cm, largo_cm, descripcion) SELECT '140x190', 140.0, 190.0, 'Medida 140x190' WHERE NOT EXISTS (SELECT 1 FROM medidas WHERE ancho_cm = 140.0 AND largo_cm = 190.0);
INSERT INTO medidas (nombre_medida, ancho_cm, largo_cm, descripcion) SELECT '160x190', 160.0, 190.0, 'Medida 160x190' WHERE NOT EXISTS (SELECT 1 FROM medidas WHERE ancho_cm = 160.0 AND largo_cm = 190.0);
INSERT INTO medidas (nombre_medida, ancho_cm, largo_cm, descripcion) SELECT '200x200', 200.0, 200.0, 'Medida 200x200' WHERE NOT EXISTS (SELECT 1 FROM medidas WHERE ancho_cm = 200.0 AND largo_cm = 200.0);

-- Productos
INSERT INTO productos (id_categoria, id_coleccion, nombre_producto, descripcion_producto, slug, estado_producto) SELECT c.id_categoria, NULL, 'EDREDON KIRA', 'Producto importado desde inventario: EDREDON KIRA', 'edredon-kira', TRUE FROM categorias c WHERE c.slug = 'edredones' ON CONFLICT (slug) DO UPDATE SET nombre_producto = EXCLUDED.nombre_producto, descripcion_producto = EXCLUDED.descripcion_producto, estado_producto = EXCLUDED.estado_producto;
INSERT INTO productos (id_categoria, id_coleccion, nombre_producto, descripcion_producto, slug, estado_producto) SELECT c.id_categoria, NULL, 'EDREDON NORDICO', 'Producto importado desde inventario: EDREDON NORDICO', 'edredon-nordico', TRUE FROM categorias c WHERE c.slug = 'edredones' ON CONFLICT (slug) DO UPDATE SET nombre_producto = EXCLUDED.nombre_producto, descripcion_producto = EXCLUDED.descripcion_producto, estado_producto = EXCLUDED.estado_producto;
INSERT INTO productos (id_categoria, id_coleccion, nombre_producto, descripcion_producto, slug, estado_producto) SELECT c.id_categoria, NULL, 'EDREDON PRIMAVERA', 'Producto importado desde inventario: EDREDON PRIMAVERA', 'edredon-primavera', TRUE FROM categorias c WHERE c.slug = 'edredones' ON CONFLICT (slug) DO UPDATE SET nombre_producto = EXCLUDED.nombre_producto, descripcion_producto = EXCLUDED.descripcion_producto, estado_producto = EXCLUDED.estado_producto;
INSERT INTO productos (id_categoria, id_coleccion, nombre_producto, descripcion_producto, slug, estado_producto) SELECT c.id_categoria, NULL, 'IMPERMEABLE', 'Producto importado desde inventario: IMPERMEABLE', 'impermeable', TRUE FROM categorias c WHERE c.slug = 'sabanas' ON CONFLICT (slug) DO UPDATE SET nombre_producto = EXCLUDED.nombre_producto, descripcion_producto = EXCLUDED.descripcion_producto, estado_producto = EXCLUDED.estado_producto;
INSERT INTO productos (id_categoria, id_coleccion, nombre_producto, descripcion_producto, slug, estado_producto) SELECT c.id_categoria, NULL, 'SABANA 188 HILOS', 'Producto importado desde inventario: SABANA 188 HILOS', 'sabana-188-hilos', TRUE FROM categorias c WHERE c.slug = 'sabanas' ON CONFLICT (slug) DO UPDATE SET nombre_producto = EXCLUDED.nombre_producto, descripcion_producto = EXCLUDED.descripcion_producto, estado_producto = EXCLUDED.estado_producto;
INSERT INTO productos (id_categoria, id_coleccion, nombre_producto, descripcion_producto, slug, estado_producto) SELECT c.id_categoria, NULL, 'SABANA TRÚLU', 'Producto importado desde inventario: SABANA TRÚLU', 'sabana-trulu', TRUE FROM categorias c WHERE c.slug = 'sabanas' ON CONFLICT (slug) DO UPDATE SET nombre_producto = EXCLUDED.nombre_producto, descripcion_producto = EXCLUDED.descripcion_producto, estado_producto = EXCLUDED.estado_producto;
INSERT INTO productos (id_categoria, id_coleccion, nombre_producto, descripcion_producto, slug, estado_producto) SELECT c.id_categoria, NULL, 'SABANA UNICOLOR', 'Producto importado desde inventario: SABANA UNICOLOR', 'sabana-unicolor', TRUE FROM categorias c WHERE c.slug = 'sabanas' ON CONFLICT (slug) DO UPDATE SET nombre_producto = EXCLUDED.nombre_producto, descripcion_producto = EXCLUDED.descripcion_producto, estado_producto = EXCLUDED.estado_producto;

-- Variantes de producto
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'ZACK', 'EDREDON_PRIMAVERA_ZACK_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'YARA', 'EDREDON_PRIMAVERA_YARA_160X190', 145000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'YANI', 'EDREDON_PRIMAVERA_YANI_160X190', 145000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'VURU', 'EDREDON_PRIMAVERA_VURU_200X200', 155000.0, 2, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'VERDE JADE', 'SABANA_UNICOLOR_VERDE_JADE_140X190', 69900.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'sabana-unicolor' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'TING', 'EDREDON_PRIMAVERA_TING_160X190', 145000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'TIGE', 'EDREDON_PRIMAVERA_TIGE_140X190', 135000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'TIGE', 'EDREDON_PRIMAVERA_TIGE_160X190', 145000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'SINYA', 'EDREDON_PRIMAVERA_SINYA_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'SARIT', 'EDREDON_PRIMAVERA_SARIT_160X190', 145000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'SARIT', 'EDREDON_PRIMAVERA_SARIT_200X200', 155000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'ROZZ', 'EDREDON_PRIMAVERA_ROZZ_120X190', 129900.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 120.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'ROZZ', 'EDREDON_PRIMAVERA_ROZZ_200X200', 155000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'RENKLY', 'EDREDON_PRIMAVERA_RENKLY_140X190', 135000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'RANDER', 'EDREDON_PRIMAVERA_RANDER_120X190', 129900.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 120.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'RANDER', 'EDREDON_PRIMAVERA_RANDER_160X190', 145000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'RANDER', 'EDREDON_PRIMAVERA_RANDER_200X200', 155000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'PROTECTOR ANTIFLUIDO', 'IMPERMEABLE_PROTECTOR_ANTIFLUIDO_100X190', 51000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 100.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'impermeable' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'PROTECTOR ANTIFLUIDO', 'IMPERMEABLE_PROTECTOR_ANTIFLUIDO_120X190', 59000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 120.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'impermeable' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'PROTECTOR ANTIFLUIDO', 'IMPERMEABLE_PROTECTOR_ANTIFLUIDO_160X190', 73000.0, 3, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'impermeable' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'PROTECTOR ANTIFLUIDO', 'IMPERMEABLE_PROTECTOR_ANTIFLUIDO_200X200', 79000.0, 2, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'impermeable' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'PLATA', 'SABANA_188_HILOS_PLATA_200X200', 139000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'sabana-188-hilos' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'PAIN', 'EDREDON_PRIMAVERA_PAIN_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'NILO', 'EDREDON_PRIMAVERA_NILO_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'NEGRO-GRIS', 'EDREDON_KIRA_NEGRO_GRIS_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'NAELI', 'SABANA_TRULU_NAELI_200X200', 131000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'sabana-trulu' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'MORA EN LECHE-GRIS', 'EDREDON_KIRA_MORA_EN_LECHE_GRIS_140X190', 135000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'MITU', 'EDREDON_PRIMAVERA_MITU_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'MITU', 'EDREDON_PRIMAVERA_MITU_160X190', 145000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'MALID', 'EDREDON_PRIMAVERA_MALID_200X200', 155000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'LORY', 'EDREDON_PRIMAVERA_LORY_140X190', 135000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'HABANO', 'EDREDON_NORDICO_HABANO_140X190', 160000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-nordico' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'AZUL BEBE- BEIGE', 'EDREDON_KIRA_AZUL_BEBE_BEIGE_140X190', 135000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'CAQUI-BLANCO', 'EDREDON_KIRA_CAQUI_BLANCO_140X190', 135000.0, 3, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'LINO-HABANO', 'EDREDON_KIRA_LINO_HABANO_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'LAKAY', 'EDREDON_PRIMAVERA_LAKAY_140X190', 135000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'LAKAY', 'EDREDON_PRIMAVERA_LAKAY_200X200', 155000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'KIRMIN', 'EDREDON_PRIMAVERA_KIRMIN_140X190', 135000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'KIRMIN', 'EDREDON_PRIMAVERA_KIRMIN_160X190', 145000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'GULY', 'EDREDON_PRIMAVERA_GULY_160X190', 145000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'GLASSY', 'EDREDON_PRIMAVERA_GLASSY_200X200', 155000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'GARY', 'EDREDON_PRIMAVERA_GARY_200X200', 155000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'GANTU', 'EDREDON_PRIMAVERA_GANTU_160X190', 145000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'GANTU', 'EDREDON_PRIMAVERA_GANTU_200X200', 155000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'GADY', 'EDREDON_PRIMAVERA_GADY_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'FLORY', 'EDREDON_PRIMAVERA_FLORY_200X200', 155000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'CLAR', 'EDREDON_PRIMAVERA_CLAR_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'CIGLY', 'EDREDON_PRIMAVERA_CIGLY_140X190', 135000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'CHOCOLATE-HABANO', 'EDREDON_KIRA_CHOCOLATE_HABANO_100X190', 119000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 100.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'CHOCOLATE-HABANO', 'EDREDON_KIRA_CHOCOLATE_HABANO_200X200', 155000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BUDY', 'SABANA_TRULU_BUDY_200X200', 131000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'sabana-trulu' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BLUMET', 'SABANA_TRULU_BLUMET_120X190', 100000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 120.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'sabana-trulu' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BLOMY', 'EDREDON_PRIMAVERA_BLOMY_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BLOMY', 'EDREDON_PRIMAVERA_BLOMY_160X190', 145000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'MELYN', 'EDREDON_PRIMAVERA_MELYN_160X190', 145000.0, 2, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'ISIS', 'EDREDON_PRIMAVERA_ISIS_160X190', 145000.0, 2, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'WIRE', 'EDREDON_PRIMAVERA_WIRE_160X190', 145000.0, 2, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'STAR', 'EDREDON_PRIMAVERA_STAR_160X190', 145000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'YAIZ', 'EDREDON_PRIMAVERA_YAIZ_160X190', 145000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BLOMY', 'EDREDON_PRIMAVERA_BLOMY_200X200', 155000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BLANCO-PLATA', 'EDREDON_KIRA_BLANCO_PLATA_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BLANCO-PLATA', 'EDREDON_KIRA_BLANCO_PLATA_160X190', 145000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BLANCO-NEGRO', 'EDREDON_KIRA_BLANCO_NEGRO_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BLANCO-LILA', 'EDREDON_KIRA_BLANCO_LILA_160X190', 135000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 160.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BLANCO', 'EDREDON_KIRA_BLANCO_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BLANCA', 'SABANA_UNICOLOR_BLANCA_200X200', 80000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'sabana-unicolor' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BESK', 'EDREDON_PRIMAVERA_BESK_200X200', 155000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BEIGE-HABANO', 'EDREDON_KIRA_BEIGE_HABANO_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BALY', 'EDREDON_PRIMAVERA_BALY_140X190', 135000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'YOLET', 'EDREDON_PRIMAVERA_YOLET_140X190', 135000.0, 2, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'GROEN', 'EDREDON_PRIMAVERA_GROEN_140X190', 135000.0, 2, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'ISIS', 'EDREDON_PRIMAVERA_ISIS_140X190', 135000.0, 3, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'YAIZ', 'EDREDON_PRIMAVERA_YAIZ_140X190', 135000.0, 2, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'MELYN', 'EDREDON_PRIMAVERA_MELYN_140X190', 135000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'PINKY', 'EDREDON_PRIMAVERA_PINKY_140X190', 135000.0, 3, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'CHOCO', 'EDREDON_PRIMAVERA_CHOCO_140X190', 135000.0, 3, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'WIRE', 'EDREDON_PRIMAVERA_WIRE_140X190', 135000.0, 2, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'JADYS', 'EDREDON_PRIMAVERA_JADYS_140X190', 135000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'AZUL OSCURO-GRIS', 'EDREDON_KIRA_AZUL_OSCURO_GRIS_140X190', 135000.0, 0, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 140.0 AND m.largo_cm = 190.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-kira' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'ADONIS', 'SABANA_TRULU_ADONIS_200X200', 131000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'sabana-trulu' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'ABEN', 'EDREDON_PRIMAVERA_ABEN_200X200', 155000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'PALM', 'EDREDON_PRIMAVERA_PALM_200X200', 155000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'BLOOM', 'EDREDON_PRIMAVERA_BLOOM_200X200', 155000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'LYZ', 'EDREDON_PRIMAVERA_LYZ_200X200', 155000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;
INSERT INTO variantes_producto (id_producto, id_medida, id_color, referencia, sku, precio, stock, estado) SELECT p.id_producto, m.id_medida, c.id_color, 'MITSE', 'EDREDON_PRIMAVERA_MITSE_200X200', 155000.0, 1, TRUE FROM productos p JOIN medidas m ON m.ancho_cm = 200.0 AND m.largo_cm = 200.0 JOIN colores c ON c.nombre_color = 'Sin especificar' WHERE p.slug = 'edredon-primavera' ON CONFLICT (sku) DO UPDATE SET referencia = EXCLUDED.referencia, precio = EXCLUDED.precio, stock = EXCLUDED.stock, estado = EXCLUDED.estado;

COMMIT;

SHOW data_directory;

SELECT * FROM usuarios;