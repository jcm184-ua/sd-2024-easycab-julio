# Información del diseño de la solución
## Jerarquía de archivos:
```
├── core
│   ├── central
│   │   ├── crearBBDD.sql
│   │   ├── database.db
│   │   └── EC_Central.py
│   ├── Dockerfile
│   └── zookeeper-kafka
│       └── compose.yml
├── customers
│   ├── Dockerfile
│   └── EC_Customer.py
├── shared
│   ├── gui.py
│   └── mapa.py
├── taxi
│   ├── digital-engine
│   │   └── EC_DE.py
│   ├── Dockerfile
│   └── sensors
│       └── EC_S.py
```
# CORE
## CENTRAL
- **Puerto de escucha utilizado:** 20100
- Conecta con KAFKA en el puerto 20000

## BASE DE DATOS
Basada en **SQLite**, fichero **database.db**.

Tablas que encontramos:

**taxis** (ejemplo de posible contenido)

|id|estado      |posX|posY|
|--|------------|----|----|
|1 |esperando   |1   |1   |
|2 |desconectado|    |    |
|3 |servicio    |7   |10  |
|4 |incidencia  |12  |3   |

## BROKER
Utilizamos zookeeper y kafka mediante docker.
- **Puerto de escucha utilizado:** 20000.

Topics que existen:
- CLIENTES
- MAPA
- MOVIMIENTOS_TAXIS
- ESTADOS_TAXIS

# TAXI
## DIGITAL ENGINE
- Conecta con EC_Central en el puerto 20100.
- Conecta con KAFKA en el puerto 20000.
- **Puerto de escucha utilizado:** (20200 +$id) Es decir, taxi 1 con sensor 1 en  el 20201, taxi 2 con el sensor 2 en el 20202, etc...
- Recibe id como parámetro.

## SENSORS
- Conecta con EC_DE en el puerto (20200 +$id).

# CUSTOMERS
- **Conecta con KAFKA en el puerto 20000.
- Recibe id como parámetro.

