from __future__ import absolute_import
import pika
from celery import task
from celery import Task
from celery.signals import celeryd_init
import json
from queuer.models import QueuedPlayer, Game
from django.db import IntegrityError

@celeryd_init.connect()
def startup(**kwargs):
    monitor_queue()

class MessageCommunicator(Task):

    _channel = None
    _queue_name = None

    @property
    def channel(self):
        if self._channel is None:
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
            self._channel = connection.channel()
        return self._channel

    @property
    def queue_name(self):
        if self._queue_name is None:
            result = self.channel.queue_declare(exclusive=True)
            self._queue_name = result.method.queue
            self.channel.exchange_declare(exchange='info', type='fanout')
            self.channel.queue_bind(exchange='info', queue=self._queue_name)

        return self._queue_name



@task(base=MessageCommunicator)
def send_message(message):
    send_message.channel.basic_publish(exchange='info', routing_key='', body=json.dumps(message))

@task(base=MessageCommunicator)
def monitor_queue():

    def handle_message(payload):
        if 'event' in payload and payload['event'] == 'queue_info':
            queued_players = payload['players_in_queue']
            matched = payload['in_game']
            if not matched:
                current_games = Game.objects.filter(active=True)
                if len(current_games) > 0:
                    current_game = current_games[0]
                    current_game.active = False
                    current_game.save()

                QueuedPlayer.objects.all().delete()
                for player in queued_players:
                    p = QueuedPlayer(name=player)
                    try:
                        p.save()
                    except IntegrityError as e:
                        print(e)

        elif 'event' in payload and payload['event'] == 'match_created':
            matched_players = payload['players']
            g = Game(p1=matched_players[0], p2=matched_players[1])
            g.save()

    def callback(ch, method, properties, body):
        handle_message(json.loads(body))

    monitor_queue.channel.basic_consume(callback, queue=monitor_queue.queue_name, no_ack=True)
    monitor_queue.channel.start_consuming()

