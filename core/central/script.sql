DROP TABLE taxis;
DROP TABLE clientes;

CREATE TABLE IF NOT EXISTS taxis (
    id TEXT PRIMARY KEY,
    estado TEXT NOT NULL default "desconectado" CHECK(estado = "desconectado" or estado = "esperando" or estado = "servicio" or estado = "incidencia"),
  	posicion TEXT NOT NULL default ["-,-"],
    destino TEXT NOT NULL default ["-,-"]
);

CREATE TABLE IF NOT EXISTS clientes (
    id TEXT PRIMARY KEY,
    estado TEXT NOT NULL default "desconectado" CHECK(estado = "desconectado" or estado = "esperando" or estado = "montado"),
    destino TEXT NOT NULL default ["-,-"],
    posicion TEXT NOT NULL default ["-,-"]
);

INSERT INTO taxis (id, estado) VALUES (1, "esperando");
INSERT INTO taxis (id) VALUES (2);
INSERT INTO taxis (id) VALUES (3);
INSERT INTO taxis (id) VALUES (4);

INSERT INTO clientes (id) VALUES ("a");
INSERT INTO clientes (id) VALUES ("b");
INSERT INTO clientes (id) VALUES ("c");
INSERT INTO clientes (id) VALUES ("d");