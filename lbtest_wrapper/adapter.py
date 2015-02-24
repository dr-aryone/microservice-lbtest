#!/usr/local/bin/python
from sys import stdin
import json
import subprocess
import atexit
import os
import time
import pika


class Adapter(object):
    curr_player = 0

    def __init__(self):
        self.print_string = ""
        self.devnull = open(os.devnull, 'w')
        self._save_state()
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
        self.channel = connection.channel()
        result = self.channel.queue_declare(exclusive=True)
        self.queue_name = result.method.queue
        self.channel.exchange_declare(exchange='info', type='fanout')
        self.channel.queue_bind(exchange='info', queue=self.queue_name)

        def exit_handler():
            subprocess.call(["VBoxManage", "controlvm", "Cassandra 2.0.6", "poweroff"], stdout=self.devnull, stderr=self.devnull)
            subprocess.call(["VBoxManage", "snapshot", "Cassandra 2.0.6", "restorecurrent"], stdout=self.devnull, stderr=self.devnull)
            subprocess.call(["VBoxManage", "startvm", "Cassandra 2.0.6"], stdout=self.devnull, stderr=self.devnull)
            subprocess.call(["VBoxManage", "snapshot", "Cassandra 2.0.6", "delete", "lbtest"], stdout=self.devnull, stderr=self.devnull)

        atexit.register(exit_handler)

    def run(self):
        while True:
            line = stdin.readline().strip()
            result = self.execute_testcase(line)
            print result

    def _get_command(self, symbol):
        if symbol == 'q':
            command = {
                'event': 'player_queued',
                'player': 'p' + str(self.curr_player)
            }
            self.curr_player += 1
            return command
        elif symbol == 'd':
            if self.curr_player > 0:
                self.curr_player -= 1
            command = {
                'event': 'player_dequeued',
                'player': 'p' + str(self.curr_player)
            }
            return command
        elif symbol == 'r':
            return {
                'event': 'results_reported'
            }
        else:
            return {
                'event': 'heartbeat'
            }

    def _send_testcase_messages(self, commands):
        command = self._get_command('')
        self._send_message(command)

        if len(commands) == 1 and commands[0] == '':
            return
        for c in commands:
            self._send_message(self._get_command(c))

    def _send_message(self, message):
        self.channel.basic_publish(exchange='info', routing_key='', body=json.dumps(message))

    @staticmethod
    def _get_state(in_game, number_in_queue):
            if number_in_queue == 0:
                number_in_queue = 'zero'
            elif number_in_queue == 1:
                number_in_queue = 'one'
            elif number_in_queue >= 2:
                number_in_queue = 'two'
            if in_game:
                in_game = 'yes'
            else:
                in_game = 'no'
            return in_game+';'+number_in_queue

    def _get_state_sequence(self, time_out=0.2):
        print_string = ""
        timed_out = False

        while True:
            method_frame, header, body = self.channel.basic_get(queue=self.queue_name, no_ack=True)
            if not method_frame:
                if timed_out:
                    break
                time.sleep(time_out)
                timed_out = True
                continue
            payload = json.loads(body)
            if not payload or 'event' in payload and payload['event'] != 'queue_info':
                continue
            print_string += self._get_state(payload['in_game'], len(payload['players_in_queue']))+","
            timed_out = False

        return print_string

    def _rollback(self):
        def get_rollback_commands():
            deque = []
            while self.curr_player > 0:
                self.curr_player -= 1
                deque.append({
                    'event': 'player_dequeued',
                    'player': 'p' + str(self.curr_player)
                })
            return deque

        self._send_message({
            'event': 'results_reported'
        })
        rollbacks = get_rollback_commands()
        for command in rollbacks:
            self._send_message(command)

    def _save_state(self):
        def wait_for_cassandra():
            p = ""
            while "64 bytes from 192.168.56.101" not in p:
                try:
                    p = subprocess.check_output(["ping", "-c", "1", "-t", "1", "192.168.56.101"], stderr=self.devnull)
                except subprocess.CalledProcessError:
                    continue
        wait_for_cassandra()

        subprocess.call(["VBoxManage", "snapshot", "Cassandra 2.0.6", "take", "lbtest"], stdout=self.devnull, stderr=self.devnull)

    def execute_testcase(self, line):
        commands = line.split(",")
        self._get_state_sequence()

        self._send_testcase_messages(commands)
        print_string = self._get_state_sequence()
        self._rollback()
        return print_string[:-1]


Adapter().run()
