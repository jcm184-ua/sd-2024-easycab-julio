# Información del diseño de la solución

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
