import pika
import json
from cassandra.cluster import Cluster
import datetime
import uuid


class Statistician(object):

    def __init__(self):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = connection.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.queue_name = result.method.queue
        self.channel.exchange_declare(exchange='info', type='fanout')
        self.channel.queue_bind(exchange='info', queue=self.queue_name)

        cluster = Cluster(contact_points=["192.168.56.101"])
        self.session = cluster.connect('sports_matcher')
        self.__listen()

    def __listen(self):
        def callback(ch, method, properties, body):
            print body
            payload = json.loads(body)
            self.handle_message(payload)

        self.channel.basic_consume(callback, queue=self.queue_name, no_ack=True)
        self.channel.start_consuming()

    def handle_message(self, value):
        if value['event'] == 'match_created':
            query = self.session.prepare("INSERT INTO started_matches (match_id, time) VALUES (?, ?)").bind([uuid.uuid1(), datetime.datetime.now()])
            self.session.execute(query)
            print('Noticed that a match started')
        elif value['event'] == 'results_reported':
            print('Noticed that results are reported')

Statistician()
