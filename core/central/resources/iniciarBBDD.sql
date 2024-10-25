DROP TABLE taxis;
DROP TABLE clientes;

CREATE TABLE IF NOT EXISTS taxis (
    id TEXT PRIMARY KEY,
    estado TEXT NOT NULL default "desconectado" CHECK(estado = "desconectado" or estado = "esperando" or estado = "servicio"),
    sensores TEXT NOT NULL default "KO" CHECK(sensores = "OK" or sensores = "KO"),
    posicion TEXT NOT NULL,
    cliente TEXT default NULL CHECK(cliente IS NULL or cliente = "a" or cliente = "b" or cliente = "c" or cliente = "d" or cliente = "e" or cliente = "f"),
    destino TEXT default NULL CHECK(destino IS NULL or destino = "A" or destino = "B" or destino = "C" or destino = "D" or destino = "E" or destino = "F")
);

CREATE TABLE IF NOT EXISTS clientes (
    id TEXT PRIMARY KEY,
    posicion TEXT NOT NULL default ["-,-"]
);

INSERT INTO taxis (id, posicion) VALUES (1, "1,1");
INSERT INTO taxis (id, posicion) VALUES (2, "1,2");
INSERT INTO taxis (id, posicion) VALUES (3, "1,3");
INSERT INTO taxis (id, posicion) VALUES (4, "1,4");
INSERT INTO taxis (id, posicion) VALUES (5, "1,5");
INSERT INTO taxis (id, posicion) VALUES (6, "1,6");

INSERT INTO clientes (id, posicion) VALUES ("a", "15,17");
INSERT INTO clientes (id, posicion) VALUES ("b", "6,12");
INSERT INTO clientes (id, posicion) VALUES ("c", "18,15");
INSERT INTO clientes (id, posicion) VALUES ("d", "3,5");
INSERT INTO clientes (id, posicion) VALUES ("e", "7,8");
INSERT INTO clientes (id, posicion) VALUES ("f", " 13, 14");