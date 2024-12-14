USE easycab;
DROP TABLE IF EXISTS taxis;
DROP TABLE IF EXISTS clientes;
DROP USER IF EXISTS 'ec_central'@'';
DROP USER IF EXISTS 'ec_registry'@'';

CREATE TABLE IF NOT EXISTS taxis (
    id VARCHAR(255) PRIMARY KEY,
    estado VARCHAR(255) NOT NULL default "desconectado" CHECK(estado = "desconectado" or estado = "esperando" or estado ="enCamino" or estado = "servicio"),
    sensores VARCHAR(255) NOT NULL default "KO" CHECK(sensores = "OK" or sensores = "KO"),
    posicion VARCHAR(255) NOT NULL default "0,0",
    cliente VARCHAR(255) default NULL CHECK(cliente IS NULL or cliente = "a" or cliente = "b" or cliente = "c" or cliente = "d" or cliente = "e" or cliente = "f"),
    destino VARCHAR(255) default NULL CHECK(destino IS NULL or destino = "A" or destino = "B" or destino = "C" or destino = "D" or destino = "E" or destino = "F"),
    token VARCHAR(255),
    IP VARCHAR(255)
);
CREATE TABLE IF NOT EXISTS clientes (
    id VARCHAR(255) PRIMARY KEY,
    posicion VARCHAR(255) NOT NULL default "0,0",
    IP VARCHAR(255)
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

CREATE USER 'ec_central'@'%' IDENTIFIED BY 'sd2024_central';
CREATE USER 'ec_registry'@'%' IDENTIFIED BY 'sd2024_registry';
GRANT ALL PRIVILEGES ON easycab.* TO 'ec_central'@'%';
GRANT ALL PRIVILEGES ON easycab.* TO 'ec_registry'@'%';
FLUSH PRIVILEGES;