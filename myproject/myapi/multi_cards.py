from django.http import (Http404, HttpResponseBadRequest, JsonResponse)
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import json
from bson.json_util import dumps, loads
from bson.objectid import ObjectId
from myproject.myapi import users
from ..myapi import db

# will move these env variables out
mongo_uri = "mongodb+srv://root:admin0123456@cluster0.puxa2.mongodb.net/myFirstDatabase?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
mongo_name = "dev"
database = db.DB(mongo_uri, mongo_name)

@api_view(['POST'])

def select_task(request):
    """Move an array of cards from one task to another

    In post request the cardIds and both task ids are provided. We will update the card ids
    of both tasks and update the taskId of the the cards

    Args:
        request: Request sent to api server

    Returns:
        An array of the original card idss
    """
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    raw_card_ids = data['cardIds']
    task_from_id = data['taskFromId']
    task_to_id = data['taskToId']
    updated_by = data['updatedBy']
    update_date = data['updateDate']
    try:
        card_ids = [ ObjectId(id) for id in raw_card_ids ]
        # update task from
        task_from_query = { '_id': ObjectId( task_from_id ) }
        task_from_update = {
            '$set': {
                'updatedBy': ObjectId(updated_by),
                'updateDate': update_date,
            },
            '$pullAll': { 'cardIds': card_ids }
        }
        database.tasks.update_one(task_from_query, task_from_update)
        # update task to
        task_to_query = { '_id': ObjectId( task_to_id ) }
        task_to_update = {
            '$set': {
                'updatedBy': ObjectId(updated_by),
                'updateDate': update_date,
            },
            '$push': { 'cardIds': { "$each": card_ids, "$position": 0 } }
        }
        database.tasks.update_one(task_to_query, task_to_update)
        # update cards
        cards_query = { '_id': { '$in' : card_ids } }
        cards_update = {
            '$set': {
                'updatedBy': ObjectId(updated_by),
                'updateDate': update_date,
                'taskId': ObjectId( task_to_id )
            }
        }
        database.cards.update_many(cards_query, cards_update)
        return Response({
            'cardIds': json.dumps(raw_card_ids)
        })
    except ValueError:
        print(f"Unable to change task id for cards ${raw_card_ids} due to ${ValueError}")

@api_view(['POST'])

def delete_cards(request):
    """Delete an array of cards

    In post request the cardIds and corresponding task are provided. We will remove the cards
    and update the cardIds of the task

    Args:
        request: Request sent to api server

    Returns:
        An array of the original card idss
    """
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    raw_card_ids = data['cardIds']
    task_from_id = data['taskFromId']
    updated_by = data['updatedBy']
    update_date = data['updateDate']
    try:
        card_ids = [ ObjectId(id) for id in raw_card_ids ]
        # update task from
        task_from_query = { '_id': ObjectId( task_from_id ) }
        task_from_update = {
            '$set': {
                'updatedBy': ObjectId(updated_by),
                'updateDate': update_date,
            },
            '$pullAll': { 'cardIds': card_ids }
        }
        database.tasks.update_one(task_from_query, task_from_update)
        # delete cards
        cards_query = { '_id': { '$in' : card_ids } }
        database.cards.delete_many(cards_query)
        return Response({
            'cardIds': json.dumps(raw_card_ids)
        })
    except ValueError:
        print(f"Unable to delete cards ${raw_card_ids} due to ${ValueError}")