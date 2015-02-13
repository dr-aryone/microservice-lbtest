from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from kafka import KafkaClient, SimpleProducer, SimpleConsumer
import json
from queuer.models import QueuedPlayer, Game
from django.db import IntegrityError

def index(request):
    context = {
        'test' : True
    }
    return render(request, 'queuer/index.html', context)


@csrf_exempt
def queue_player(request):
    if request.method != 'POST':
        return HttpResponse('Not post')

    internalMessage = {
        'event':'player_queued',
        'player': request.POST['name']
    }


    kafka = KafkaClient('localhost:9092')
    producer = SimpleProducer(kafka)

    producer.send_messages('queue', json.dumps(internalMessage))
    kafka.close()

    return HttpResponse("You are queued")

@csrf_exempt
def dequeue_player(request):
    if request.method != 'POST':
        return HttpResponse('Not post')

    internalMessage = {
        'event':'player_dequeued',
        'player': request.POST['name']
    }


    kafka = KafkaClient('localhost:9092')
    producer = SimpleProducer(kafka)

    producer.send_messages('queue', json.dumps(internalMessage))
    kafka.close()

    return HttpResponse("You are dequeued")


@csrf_exempt
def report_results(request):
    if request.method != 'POST':
        return HttpResponse('Not post')

    internalMessage = {
        'event':'results_reported'
    }


    kafka = KafkaClient('localhost:9092')
    producer = SimpleProducer(kafka)

    producer.send_messages('queue', json.dumps(internalMessage))
    kafka.close()

    return HttpResponse("You reported results")

@csrf_exempt
def check(request):
    if request.method != 'GET':
        return HttpResponse('Not get')

    kafka = KafkaClient('localhost:9092')
    consumer = SimpleConsumer(kafka, 'client', 'queue', iter_timeout=0.2)

    matched = False
    queued_players = []
    matched_players = []
    update = False

    for message in consumer:
        payload = json.loads(message.message.value)
        if('event' in payload and payload['event'] == 'queue_info'):
            update = True
            queued_players = payload['players_in_queue']
            matched = payload['in_game']
            if (not matched):
                current_games = Game.objects.filter(active=True)
                if (len(current_games) > 0):
                    current_game = current_games[0]
                    current_game.active = False
                    current_game.save()
        elif('event' in payload and payload['event'] == 'match_created'):
            matched_players = payload['players']
            queued_players = []
            g = Game(p1=matched_players[0], p2=matched_players[1])
            g.save()

    kafka.close()

    if (not matched and update):
        QueuedPlayer.objects.all().delete()
        for player in queued_players:
            p = QueuedPlayer(name=player)
            try:
                p.save()
            except IntegrityError as e:
                print(e)

    if (not update):
        queued_players = []
        for player in QueuedPlayer.objects.all():
            queued_players.append(player.name)

    current_games = Game.objects.filter(active=True)
    if (len(current_games) > 0):
        current_game = current_games[0]
        matched_players = [current_game.p1, current_game.p2]
        matched = True
    else:
        matched = False

    response = json.dumps({'queued_players':queued_players,'matched_players': matched_players, 'matched': matched})

    return HttpResponse(response, content_type="application/json")
