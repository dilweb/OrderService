import json
import logging
from typing import Dict, Any
from confluent_kafka import Producer
from confluent_kafka.admin import AdminClient
from confluent_kafka.cimpl import KafkaException

from orderservice.kafka.config import kafka_settings

logger = logging.getLogger(__name__)


class OrderProducer:
    """Kafka Producer для отправки заказов в топик orders"""
    
    def __init__(self):
        """Инициализация Producer с настройками из конфига"""
        # region agent log
        # Hypothesis B: Check Producer config at initialization
        import time
        with open(r'c:\Users\User\Desktop\BIM_Dil\Python\pride\1st task\OrderService\.cursor\debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"B","location":"kafka/producer.py:18","message":"Producer __init__ called","data":{"bootstrap_servers":kafka_settings.kafka_bootstrap_servers,"topic":kafka_settings.orders_topic},"timestamp":int(time.time()*1000)})+'\n')
        # endregion
        
        self.producer = Producer({
            'bootstrap.servers': kafka_settings.kafka_bootstrap_servers,
            'client.id': 'order-service-producer',
            # Ждём подтверждения от всех реплик (для надёжности)
            'acks': 'all',
            # Повторная отправка при ошибке
            'retries': 3,
            # Таймаут для повторных попыток
            'retry.backoff.ms': 100
        })
        self.topic = kafka_settings.orders_topic
        logger.info(f"Kafka Producer инициализирован. Брокер: {kafka_settings.kafka_bootstrap_servers}, Топик: {self.topic}")
    
    def _delivery_callback(self, err, msg):
        """Callback функция, вызываемая после отправки сообщения"""
        # region agent log
        # Hypothesis D: Track delivery callback execution
        import time
        with open(r'c:\Users\User\Desktop\BIM_Dil\Python\pride\1st task\OrderService\.cursor\debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"kafka/producer.py:33","message":"_delivery_callback called","data":{"has_error":err is not None,"error":str(err) if err else None,"topic":msg.topic() if msg else None},"timestamp":int(time.time()*1000)})+'\n')
        # endregion
        
        if err:
            logger.error(f"Ошибка доставки сообщения в Kafka: {err}")
        else:
            logger.info(f"Сообщение успешно отправлено в топик {msg.topic()} [партиция: {msg.partition()}, offset: {msg.offset()}]")
    
    def publish_order(self, order_data: Dict[str, Any]) -> bool:
        """
        Публикует заказ в Kafka топик orders
        
        Args:
            order_data: Словарь с данными заказа (order_id, user_id, item, quantity)
            
        Returns:
            bool: True если сообщение успешно поставлено в очередь, False при ошибке
        """
        # region agent log
        # Hypothesis C,D: Track publish_order execution and return value
        import time
        with open(r'c:\Users\User\Desktop\BIM_Dil\Python\pride\1st task\OrderService\.cursor\debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"kafka/producer.py:48","message":"publish_order called","data":{"order_id":order_data.get('order_id'),"topic":self.topic},"timestamp":int(time.time()*1000)})+'\n')
        # endregion
        
        try:
            # Сериализуем данные в JSON
            message_value = json.dumps(order_data, ensure_ascii=False)
            
            # region agent log
            # Hypothesis D: Check produce() call success
            with open(r'c:\Users\User\Desktop\BIM_Dil\Python\pride\1st task\OrderService\.cursor\debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"kafka/producer.py:54","message":"Before producer.produce()","data":{"order_id":order_data.get('order_id')},"timestamp":int(time.time()*1000)})+'\n')
            # endregion
            
            # Отправляем сообщение в Kafka
            # Ключ = order_id (для гарантии порядка обработки заказов с одним ID)
            self.producer.produce(
                topic=self.topic,
                key=order_data.get('order_id', '').encode('utf-8'),
                value=message_value.encode('utf-8'),
                callback=self._delivery_callback
            )
            
            # region agent log
            # Hypothesis D: Check before flush
            with open(r'c:\Users\User\Desktop\BIM_Dil\Python\pride\1st task\OrderService\.cursor\debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"kafka/producer.py:63","message":"Before producer.flush()","data":{"order_id":order_data.get('order_id')},"timestamp":int(time.time()*1000)})+'\n')
            # endregion
            
            # Принудительно отправляем сообщения (flush) - ждём доставки
            # В продакшене можно убрать flush и использовать периодический flush
            flush_result = self.producer.flush(timeout=5)
            
            # region agent log
            # Hypothesis D: Check flush result
            with open(r'c:\Users\User\Desktop\BIM_Dil\Python\pride\1st task\OrderService\.cursor\debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"D","location":"kafka/producer.py:71","message":"After producer.flush()","data":{"order_id":order_data.get('order_id'),"flush_result":flush_result},"timestamp":int(time.time()*1000)})+'\n')
            # endregion
            
            logger.info(f"Заказ {order_data.get('order_id')} отправлен в Kafka")
            
            # region agent log
            # Hypothesis C: Track return value
            with open(r'c:\Users\User\Desktop\BIM_Dil\Python\pride\1st task\OrderService\.cursor\debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"kafka/producer.py:78","message":"publish_order returning","data":{"order_id":order_data.get('order_id'),"return_value":True},"timestamp":int(time.time()*1000)})+'\n')
            # endregion
            return True
            
        except KafkaException as e:
            logger.error(f"Ошибка Kafka при отправке заказа: {e}")
            # region agent log
            # Hypothesis C,D: Track exception
            with open(r'c:\Users\User\Desktop\BIM_Dil\Python\pride\1st task\OrderService\.cursor\debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"kafka/producer.py:86","message":"KafkaException caught","data":{"order_id":order_data.get('order_id'),"exception":str(e)},"timestamp":int(time.time()*1000)})+'\n')
            # endregion
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке заказа в Kafka: {e}")
            # region agent log
            # Hypothesis C,D: Track exception
            with open(r'c:\Users\User\Desktop\BIM_Dil\Python\pride\1st task\OrderService\.cursor\debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"run1","hypothesisId":"C","location":"kafka/producer.py:94","message":"General exception caught","data":{"order_id":order_data.get('order_id'),"exception":str(e)},"timestamp":int(time.time()*1000)})+'\n')
            # endregion
            return False
    
    def close(self):
        """Закрывает соединение с Kafka"""
        self.producer.flush(timeout=10)
        logger.info("Kafka Producer закрыт")



_order_producer: OrderProducer | None = None


def get_producer() -> OrderProducer:
    """Получить глобальный экземпляр Producer (singleton pattern)"""
    global _order_producer
    if _order_producer is None:
        _order_producer = OrderProducer()
    return _order_producer