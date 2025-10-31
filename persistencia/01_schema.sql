-- Crear tabla de propiedades para MySQL
CREATE TABLE IF NOT EXISTS propiedades (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(255) NOT NULL,
    descripcion TEXT,
    tipo VARCHAR(50) NOT NULL,
    precio DECIMAL(12,2) NOT NULL,
    habitaciones INT DEFAULT 0,
    banos DECIMAL(2,1) DEFAULT 0.0,
    area_m2 DECIMAL(8,2) DEFAULT 0.00,
    ubicacion VARCHAR(255),
    fecha_publicacion DATE,
    imagen_url VARCHAR(512)
);