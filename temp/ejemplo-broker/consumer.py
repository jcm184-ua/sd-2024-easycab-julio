from kafka import KafkaConsumer 
consumer=KafkaConsumer('PLAYERS',bootstrap_servers='localhost:20000',auto_offset_reset='earliest')

for message in consumer:
    print(message)
