from kafka import KafkaClient, SimpleProducer, SimpleConsumer
from kafka.common import OffsetOutOfRangeError
import json
from collections import deque
from cassandra.cluster import Cluster
import datetime
import uuid

class Statistician(object):

    def __init__(self):
        kafka = KafkaClient('localhost:9092')
        self.consumer = SimpleConsumer(kafka, 'statistician', 'queue')
        cluster = Cluster()
        self.session = cluster.connect('sports_matcher')
        self.__listen()

    def __listen(self):
        while True:
            try:
                message = self.consumer.get_message(block=True)
                if message:
                    payload = json.loads(message.message.value)
                    self.handle_message(payload)
            except Exception:
                print('faulty message')


    def handle_message(self, value):
        if (value['event'] == 'match_created'):
            query = self.session.prepare("INSERT INTO started_matches (match_id, time) VALUES (?, ?)").bind([uuid.uuid1(), datetime.datetime.now()])
            self.session.execute(query)
            print('Noticed that a match started')
        elif (value['event'] == 'results_reported'):
            print('Noticed that results are reported')

Statistician()
