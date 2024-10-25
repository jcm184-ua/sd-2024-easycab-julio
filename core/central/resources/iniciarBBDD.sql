DROP TABLE taxis;
DROP TABLE clientes;

CREATE TABLE IF NOT EXISTS taxis (
    id TEXT PRIMARY KEY,
    estado TEXT NOT NULL default "desconectado" CHECK(estado = "desconectado" or estado = "esperando" or estado = "servicio"),
    sensores TEXT NOT NULL default "KO" CHECK(sensores = "OK" or sensores = "KO"),
    posicion TEXT NOT NULL default ["-,-"],
    cliente TEXT default NULL CHECK(cliente IS NULL or cliente = "a" or cliente = "b" or cliente = "c" or cliente = "d" or cliente = "e" or cliente = "f"),
    destino TEXT default NULL CHECK(destino IS NULL or destino = "A" or destino = "B" or destino = "C" or destino = "D" or destino = "E" or destino = "F")
);

CREATE TABLE IF NOT EXISTS clientes (
    id TEXT PRIMARY KEY,
    posicion TEXT NOT NULL default ["-,-"]
);

INSERT INTO taxis (id) VALUES (1);
INSERT INTO taxis (id) VALUES (2);
INSERT INTO taxis (id) VALUES (3);
INSERT INTO taxis (id) VALUES (5);
INSERT INTO taxis (id) VALUES (6);
INSERT INTO taxis (id) VALUES (7);
INSERT INTO taxis (id) VALUES (8);
INSERT INTO taxis (id) VALUES (9);
INSERT INTO taxis (id) VALUES (10);

INSERT INTO clientes (id) VALUES ("a");
INSERT INTO clientes (id) VALUES ("b");
INSERT INTO clientes (id) VALUES ("c");
INSERT INTO clientes (id) VALUES ("d");
INSERT INTO clientes (id) VALUES ("e");
INSERT INTO clientes (id) VALUES ("f");