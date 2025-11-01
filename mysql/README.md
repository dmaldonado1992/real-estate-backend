# MySQL Standalone Container

Contenedor MySQL independiente para el proyecto de propiedades.

## Ubicación
```
C:\Users\Daniel Maldonado\Documents\vue\backend\mysql\
```

## Estructura
```
backend/
├── mysql/
│   ├── docker-compose.yml
│   └── README.md
└── persistencia/              ← Scripts SQL compartidos
    ├── 01_schema.sql
    └── 02_seed_data.sql
```

## Uso

### Iniciar el contenedor
```powershell
cd "C:\Users\Daniel Maldonado\Documents\vue\backend\mysql"
docker-compose up -d
```

### Detener el contenedor
```powershell
docker-compose down
```

### Ver logs
```powershell
docker-compose logs -f
```

### Acceder a MySQL
```powershell
docker exec -it mySql mysql -uroot -prootpassword propiedades_db
```

### Reiniciar
```powershell
docker-compose restart
```

### Eliminar todo (incluyendo datos)
```powershell
docker-compose down -v
```

## Configuración

**Nombre del contenedor:** `mySql`  
**Puerto:** `3306`  
**Base de datos:** `propiedades_db`  
**Usuario root:** `root`  
**Contraseña root:** `rootpassword`  
**Usuario app:** `propiedades_user`  
**Contraseña app:** `propiedades_pass`

## Conexión desde aplicaciones

```
Host: localhost
Puerto: 3306
Database: propiedades_db
Usuario: root
Contraseña: rootpassword
```

## Scripts de inicialización

Los scripts en `../persistencia/` se ejecutan automáticamente cuando el contenedor se crea por primera vez:
- `01_schema.sql` - Crea la tabla `propiedades`
- `02_seed_data.sql` - Inserta 16 propiedades de ejemplo
