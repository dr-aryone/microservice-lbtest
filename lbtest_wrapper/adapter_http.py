#!/usr/local/bin/python
from sys import stdin
import requests
import json

class CommandCreator(object):

    curr_player = 0

    def get_command(self, symbol):
        if(symbol == 'q'):
            payload = {
                'name': 'p' + str(self.curr_player)
            }
            self.curr_player += 1
            return ('http://127.0.0.1:8000/queuer/queue_player', payload, 'post')
        elif(symbol == 'd'):
            if (self.curr_player > 0):
                self.curr_player -= 1
            payload = {
                'name': 'p' + str(self.curr_player)
            }
            return ('http://127.0.0.1:8000/queuer/dequeue_player', payload, 'post')
        elif(symbol == 'r'):
            return ('http://127.0.0.1:8000/queuer/report_results', '', 'post')
        else:
            return ('http://127.0.0.1:8000/queuer/check', '', 'get')

    def get_rollback_commands(self):
        deque = []

        while(self.curr_player > 0):
            self.curr_player -= 1
            deque.append(
            ('http://127.0.0.1:8000/queuer/dequeue_player',
                {
                    'name': 'p' + str(self.curr_player)
                })
            )
        return deque



def __send_testcases(commands, command_creator):
    command = command_creator.get_command('')
    responses = []
    responses.append(requests.get(command[0]))

    if(len(commands) == 1 and commands[0] == ''):
        return responses

    for c in commands:
        command = command_creator.get_command(c)
        requests.post(command[0], data=command[1])
        responses.append(requests.get(command_creator.get_command('')[0]))

    return responses

def __get_state_sequence(responses):
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

    for response in responses:
        payload = response.json()
        printstring += get_state(payload['matched'], len(payload['queued_players']))+","

    return printstring


def __rollback(command_creator):
    requests.post('http://127.0.0.1:8000/queuer/report_results')

    rollbacks = command_creator.get_rollback_commands()

    for command in rollbacks:
        requests.post(command[0], data=command[1])


def execute_testcase(line, command_creator):
    commands = line.split(",")
    responses = __send_testcases(commands, command_creator)
    printstring = __get_state_sequence(responses)
    __rollback(command_creator)
    return printstring[:-1]

cc = CommandCreator()
while(True):
    line = stdin.readline().strip()
    result = execute_testcase(line, cc)
    print result
