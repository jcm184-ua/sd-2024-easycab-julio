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