from pydantic_settings import BaseSettings
import json
import os


class KafkaSettings(BaseSettings):
    kafka_bootstrap_servers: str = "localhost:9092"
    orders_topic: str = "orders"
    
    class Config:
        env_prefix = "KAFKA_"


kafka_settings = KafkaSettings()

# region agent log
# Hypothesis A: Check if KAFKA_BOOTSTRAP_SERVERS env var is set correctly
with open(r'c:\Users\User\Desktop\BIM_Dil\Python\pride\1st task\OrderService\.cursor\debug.log', 'a') as f:
    f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"A","location":"kafka/config.py:17","message":"KafkaSettings initialized","data":{"kafka_bootstrap_servers":kafka_settings.kafka_bootstrap_servers,"orders_topic":kafka_settings.orders_topic,"env_var":os.getenv("KAFKA_BOOTSTRAP_SERVERS")},"timestamp":int(__import__('time').time()*1000)})+'\n')
# endregion