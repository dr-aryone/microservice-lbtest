from kafka import KafkaClient, SimpleProducer, SimpleConsumer
from kafka.common import OffsetOutOfRangeError
import json
from collections import deque

class Matcher(object):

    people_in_queue = deque()
    in_game = False

    def __init__(self, match_goal):
        kafka = KafkaClient('localhost:9092')
        self.consumer = SimpleConsumer(kafka, 'matcher', 'queue')
        self.producer = SimpleProducer(kafka)
        self.match_goal = match_goal
        self.__listen()

    def __listen(self, break_after_first=False):
        while True:
            try:
                message = self.consumer.get_message(block=not break_after_first)
                if message:
                    payload = json.loads(message.message.value)
                    self.handle_message(payload)
            except Exception:
                print('faulty message')

    def handle_message(self, value):
        if (value['event'] == 'player_queued'):
            if('player' in value and not self.in_game):
                self.__queue_player(value['player'])
            self.send_status()
        elif (value['event'] == 'player_dequeued'):
            if('player' in value and not self.in_game):
                self.__dequeue_player(value['player'])
            self.send_status()
        elif (value['event'] == 'results_reported'):
            self.in_game = False
            self.send_status()
        elif (value['event'] == 'heartbeat'):
            self.send_status()

    def __queue_player(self, player):
        if (self.people_in_queue.count(player) > 0):
            return
        self.people_in_queue.append(player)
        if(len(self.people_in_queue) >= self.match_goal):
            self.__match()

    def __dequeue_player(self, player):
        try:
            self.people_in_queue.remove(player)
        except ValueError:
            print('No player '+player+' to dequeue')

    def __match(self):
        if (len(self.people_in_queue) < self.match_goal):
            return

        players = []

        for p in range(self.match_goal):
            players.append(self.people_in_queue.popleft())

        message = json.dumps({"event": 'match_created', "players": players})

        self.producer.send_messages('queue', message)
        print('sent '+message)
        self.in_game = True

    def send_status(self):
        message = json.dumps({'event' : 'queue_info', 'players_in_queue' : list(self.people_in_queue), 'in_game':self.in_game})
        self.producer.send_messages('queue', message)

Matcher(2)
