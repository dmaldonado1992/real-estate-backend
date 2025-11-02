# 🔧 Instalador Backend + MySQL

Este script instala y configura automáticamente el backend FastAPI con su propia instancia de MySQL.

## 🚀 Uso

```bash
# Desde la carpeta backend
install-backend.bat
```

## 📋 Lo que hace

1. **Lee el Dockerfile del backend** automáticamente
2. **Configura MySQL** en puerto 3308 (para evitar conflictos)
3. **Construye la imagen** del backend con todas las dependencias
4. **Inicia los contenedores** con hot-reload activado
5. **Inicializa la base de datos** automáticamente
6. **Expone documentación** de la API

## 🌐 Servicios

- **Backend API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **MySQL**: localhost:3308

## 📊 Base de Datos

- **Host**: localhost:3308
- **Usuario**: backend_user
- **Contraseña**: backend_pass
- **Base de datos**: backend_db

## 🛠️ Comandos útiles

```bash
# Ver logs
docker logs -f backend-app
docker logs -f backend-mysql

# Acceder a MySQL
docker exec -it backend-mysql mysql -u backend_user -p backend_db

# Detener
docker stop backend-app backend-mysql

# Eliminar
docker rm backend-app backend-mysql
docker network rm backend-network
```

## 💡 Características

- ✅ Hot reload activado
- ✅ Base de datos auto-inicializada
- ✅ API documentación en /docs
- ✅ Red aislada para el backend
- ✅ Puerto MySQL único (3308)
- ✅ Lee configuración del Dockerfile automáticamente