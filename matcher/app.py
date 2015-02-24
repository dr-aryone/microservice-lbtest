#!/usr/local/bin/python
import pika
import json
from collections import deque
import signal
import sys


class Matcher(object):

    people_in_queue = deque()
    in_game = False

    def __init__(self, match_goal):
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = connection.channel()
        self.channel.queue_declare(queue="queue", durable=True)
        self.queue_name = "queue"
        self.channel.exchange_declare(exchange='info', type='fanout')
        self.channel.queue_bind(exchange='info', queue=self.queue_name)

        def exit_handler(signum, frame):
            connection.close()
            sys.exit(0)

        for sig in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP, signal.SIGQUIT]:
            signal.signal(sig, exit_handler)

        self.match_goal = match_goal
        self.__listen()

    def __listen(self, break_after_first=False):
        def callback(ch, method, properties, body):
            payload = json.loads(body)
            self.handle_message(payload)
            ch.basic_ack(delivery_tag=method.delivery_tag)

        self.channel.basic_consume(callback, queue=self.queue_name)
        self.channel.start_consuming()

    def handle_message(self, value):
        if value['event'] == 'player_queued':
            if 'player' in value and not self.in_game:
                self.__queue_player(value['player'])
            self.send_status()
        elif value['event'] == 'player_dequeued':
            if 'player' in value and not self.in_game:
                self.__dequeue_player(value['player'])
            self.send_status()
        elif value['event'] == 'results_reported':
            self.in_game = False
            self.send_status()
        elif value['event'] == 'heartbeat':
            self.send_status()

    def __queue_player(self, player):
        if self.people_in_queue.count(player) > 0:
            return
        self.people_in_queue.append(player)
        if len(self.people_in_queue) >= self.match_goal:
            self.__match()

    def __dequeue_player(self, player):
        try:
            self.people_in_queue.remove(player)
        except ValueError:
            print('No player '+player+' to dequeue')

    def __match(self):
        if len(self.people_in_queue) < self.match_goal:
            return

        players = []

        for p in range(self.match_goal):
            players.append(self.people_in_queue.popleft())

        message = json.dumps({"event": 'match_created', "players": players})

        self.channel.basic_publish(exchange='info', routing_key='', body=message)
        self.in_game = True

    def send_status(self):
        message = json.dumps({'event': 'queue_info', 'players_in_queue': list(self.people_in_queue), 'in_game': self.in_game})
        self.channel.basic_publish(exchange='info', routing_key='', body=message)

m = Matcher(2)
