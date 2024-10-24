import time
from kafka import KafkaProducer

producer= KafkaProducer(bootstrap_servers='127.0.0.1:20000')

#text = "[EC_DE1->C][A]"
while True:
    text = "[EC_DigitalEngine-1->EC_Central][(1,2)]"
    producer.send('CLIENTES',text.encode('utf-8'))
    time.sleep(1)
    text = "[EC_DigitalEngine-1->EC_Central][(2,3)]"
    producer.send('TAXIS',text.encode('utf-8'))
    time.sleep(1)
    text = "[EC_DigitalEngine-1->EC_Central][(2,4)]"
    producer.send('TAXIS',text.encode('utf-8'))
    time.sleep(1)
    text = "[EC_DigitalEngine-1->EC_Central][(2,5)]"
    producer.send('TAXIS',text.encode('utf-8'))
    time.sleep(5)

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

