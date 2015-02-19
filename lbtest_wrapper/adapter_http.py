#!/usr/local/bin/python
from sys import stdin
import requests
import json

class Adapter(object):
    curr_player = 0

    def _get_command(self, symbol):
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

    def _get_rollback_commands(self):
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

    def _send_testcases(self, commands):
        command = self._get_command('')
        responses = []
        responses.append(requests.get(command[0]))

        if(len(commands) == 1 and commands[0] == ''):
            return responses

        for c in commands:
            command = self._get_command(c)
            requests.post(command[0], data=command[1])
            responses.append(requests.get(self._get_command('')[0]))

        return responses

    def _get_state_sequence(self, responses):
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


    def _rollback(self):
        requests.post('http://127.0.0.1:8000/queuer/report_results')
        rollbacks = self._get_rollback_commands()
        for command in rollbacks:
            requests.post(command[0], data=command[1])


    def execute_testcase(self, line):
        commands = line.split(",")
        responses = self._send_testcases(commands)
        printstring = self._get_state_sequence(responses)
        self._rollback()
        return printstring[:-1]

    def run(self):
        while(True):
            line = stdin.readline().strip()
            result = self.execute_testcase(line)
            print result

Adapter().run()
