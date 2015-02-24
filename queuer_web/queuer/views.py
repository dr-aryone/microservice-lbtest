from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json
from queuer.models import QueuedPlayer, Game
from queuer import tasks


def index(request):
    context = {
        'test' : True
    }
    return render(request, 'queuer/index.html', context)


@csrf_exempt
def queue_player(request):
    if request.method != 'POST':
        return HttpResponse('Not post')

    message = {
        'event':'player_queued',
        'player': request.POST['name']
    }

    _send_message(message)
    return HttpResponse("You are queued")


@csrf_exempt
def dequeue_player(request):
    if request.method != 'POST':
        return HttpResponse('Not post')

    message = {
        'event':'player_dequeued',
        'player': request.POST['name']
    }

    _send_message(message)

    return HttpResponse("You are dequeued")


@csrf_exempt
def report_results(request):
    if request.method != 'POST':
        return HttpResponse('Not post')
    message = {
        'event':'results_reported'
    }
    _send_message(message)
    return HttpResponse("You reported results")


def _send_message(message):
    tasks.send_message(message)

@csrf_exempt
def check(request):
    if request.method != 'GET':
        return HttpResponse('Not get')
    matched_players = []
    queued_players = []
    for player in QueuedPlayer.objects.all():
        queued_players.append(player.name)

    current_games = Game.objects.filter(active=True)
    if len(current_games) > 0:
        current_game = current_games[0]
        matched_players = [current_game.p1, current_game.p2]
        matched = True
    else:
        matched = False

    response = json.dumps({'queued_players': queued_players, 'matched_players': matched_players, 'matched': matched})

    return HttpResponse(response, content_type="application/json")
