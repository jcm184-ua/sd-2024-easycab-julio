import time
from kafka import KafkaProducer
from faker import Faker

fake= Faker()
producer= KafkaProducer(bootstrap_servers='127.0.0.1:20000')
for _ in range(10):
    name=fake.name()
    producer.send('PLAYERS',name.encode('utf-8'))
    print(name)
    time.sleep(0.001)
print ('***THE END***')
time.sleep(2)

