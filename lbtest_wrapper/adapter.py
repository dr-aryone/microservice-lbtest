#!/usr/bin/python
from sys import stdin
from kafka import KafkaClient, SimpleProducer, SimpleConsumer
import json

class CommandCreator(object):

    curr_player = 0

    def get_command(self, symbol):
        if(symbol == 'q'):
            command = {
                'event':'player_queued',
                'player': 'p' + str(self.curr_player)
            }
            self.curr_player += 1
            return command
        elif(symbol == 'd'):
            if (self.curr_player > 0):
                self.curr_player -= 1
            command = {
                'event':'player_dequeued',
                'player': 'p' + str(self.curr_player)
            }
            return command
        elif(symbol == 'r'):
            return {
                'event':'results_reported'
            }
        else:
            return {
                'event':'heartbeat'
            }

    def get_rollback_commands(self):
        deque = []

        while(self.curr_player > 0):
            self.curr_player -= 1
            deque.append({
                'event':'player_dequeued',
                'player': 'p' + str(self.curr_player)
            })
        return deque



def __send_testcase_messages(commands, producer, command_creator):
    command = command_creator.get_command('')
    producer.send_messages('queue', json.dumps(command))

    if(len(commands) == 1 and commands[0] == ''):
        return

    for c in commands:
        command = command_creator.get_command(c)
        producer.send_messages('queue', json.dumps(command))

def __get_state_sequence(consumer):

    def get_state(in_game, number_in_queue):
        if (number_in_queue == 0):
            number_in_queue = 'zero'
        elif (number_in_queue == 1):
            number_in_queue = 'one'
        elif (number_in_queue >= 2):
            number_in_queue = 'two'
        if (in_game):
            in_game = 'yes'
        else:
            in_game = 'no'
        return in_game+';'+number_in_queue
        
    printstring = ""

    for message in consumer:
        payload = json.loads(message.message.value)
        if (not payload or 'event' in payload and payload['event'] != 'queue_info'):
            continue
        printstring += get_state(payload['in_game'], len(payload['players_in_queue']))+","

    return printstring


def __rollback(producer, command_creator):
    producer.send_messages('queue', json.dumps({
        'event':'results_reported'
    }))

    rollbacks = command_creator.get_rollback_commands()

    for command in rollbacks:
        producer.send_messages('queue', json.dumps(command))


def execute_testcase(line, command_creator, consumer, producer):
    commands = line.split(",")

    consumer.seek(0, 2)

    __send_testcase_messages(commands, producer, command_creator)

    printstring = __get_state_sequence(consumer)

    __rollback(producer, command_creator)

    return printstring[:-1]

kafka = KafkaClient('localhost:9092')
consumer = SimpleConsumer(kafka, 'lbtest', 'queue', iter_timeout=0.1)
producer = SimpleProducer(kafka)
cc = CommandCreator()
while(True):
    line = stdin.readline().strip()
    result = execute_testcase(line, cc, consumer, producer)
    print result
kafka.close()
