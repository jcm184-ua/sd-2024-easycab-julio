import time
from kafka import KafkaProducer

producer= KafkaProducer(bootstrap_servers='127.0.0.1:20000')

text = "[EC_DE1->C][A]"
producer.send('CLIENTES',text.encode('utf-8'))
time.sleep(2)

''' for _ in range(10):
    name=fake.name()
    print(name)
    producer.send('CLIENTES',name.encode('utf-8'))
    print(name)
    time.sleep(0.001)
print ('***THE END***')
time.sleep(2) '''

""" EC_Customer publica en CLIENTES: "[C1_E][A]" (Solicito servicio a A)
EC_Engine responde con:
"[E_C1][OK]"
"[E_C1][KO]"
Más adelante, EC_Engine comunica el fin del servicio con:
"[E_C1][EXITO]"
"[E_C1][FRACASO]" """

