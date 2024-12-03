# Información del diseño de la solución

## Guía de despliegue:
Estando en el directorio raíz:

### Construcción de los contenedores
- docker build -f core/central/Dockerfile -t ec_central .
- docker build -f customers/Dockerfile -t ec_customer .
- docker build -f taxis/digital-engine/Dockerfile -t ec_de .
- docker build -f taxis/sensors/Dockerfile -t ec_sensor .

alternativamente:

- docker build -f core/central/Dockerfile -t ec_central . && docker build -f customers/Dockerfile -t ec_customer . && docker build -f taxis/digital-engine/Dockerfile -t ec_de . && docker build -f taxis/sensors/Dockerfile -t ec_sensor .

### Arranque de la solución
- docker compose -f core/database/compose.yml up
- docker compose -f core/broker/compose.yml up
- docker run --network host ec_central
- docker run --network host ec_de
- docker run --network host ec_sensor
- docker run --network host ec_customer

## Jerarquía de archivos:

```
├── core
│   ├── central
│   │   ├── crearBBDD.sql
│   │   ├── database.db
│   │   ├── EC_Central.py
│   │   └── Dockerfile
│   └── zookeeper-kafka
│       └── compose.yml
├── customers
│   ├── Dockerfile
│   └── EC_Customer.py
├── shared
│   ├── gui.py
│   └── mapa.py
└── taxi
    ├── digital-engine
    │   └── EC_DE.py
    ├── Dockerfile
    └── sensors
        └── EC_S.py
```

# CORE

## CENTRAL

- **Puerto de escucha utilizado:** 20100
- Conecta con KAFKA en el puerto 20000

## BASE DE DATOS

Basada en **SQLite**, fichero **database.db**.

Tablas que encontramos:

**taxis** (ejemplo de posible contenido)

| id  | estado       | destino | posicion |
| --- | ------------ | ------- | -------- |
| a   | desconectado | "-,-"   | "-,-"    |
| b   | desconectado | "-,-"   | "-,-"    |
| c   | desconectado | "-,-"   | "-,-"    |
| d   | desconectado | "-,-"   | "-,-"    |

**clientes** (ejemplo de posible contenido)

| id  | estado       | posicion | destino |
| --- | ------------ | -------- | ------- |
| 1   | esperando    | "-,-"    | "-,-"   |
| 2   | desconectado | "-,-"    | "-,-"   |
| 3   | desconectado | "-,-"    | "-,-"   |
| 4   | desconectado | "-,-"    | "-,-"   |

## BROKER

Utilizamos zookeeper y kafka mediante docker.

- **Puerto de escucha utilizado:** 20000.

Topics que existen:

- CLIENTES
- MAPA
- MOVIMIENTOS_TAXIS (necesario?)
- ESTADOS_TAXIS

# TAXI

## DIGITAL ENGINE

- Conecta con EC_Central en el puerto 20100.
- Conecta con KAFKA en el puerto 20000.
- **Puerto de escucha utilizado:** (20200 +$id) Es decir, taxi 1 con sensor 1 en el 20201, taxi 2 con el sensor 2 en el 20202, etc...
- Recibe id como parámetro.

Cuando se conecta a la central, una vez autenticado, la central le mandará el estado del mapa
en el momento de su conexión a través del broker.

Quedará a la espera de las solicitudes de servicio, información de posición, y actualizaciones
del mapa a través del broker.

## SENSORS

- Conecta con EC_DE en el puerto (20200 +$id).

# CUSTOMERS

- Conecta con KAFKA en el puerto 20000.
- Recibe id como parámetro.

La comunicación con Central sera parecido a:

EC_Customer publica en CLIENTES:

- "[EC_DE1->C][A]" (Solicito servicio a A)

EC_Engine responde con:

- "[EC_C->EC_DE1][OK]"
- "[EC_C->EC_DE1][KO]"

Más adelante, EC_Engine comunica el fin del servicio con:

- "[EC_C->EC_DE1][EXITO]"
- "[EC_C->EC_DE1][FRACASO]"
