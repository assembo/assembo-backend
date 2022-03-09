from django.http import (Http404, HttpResponseBadRequest, JsonResponse)
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from bson.json_util import dumps, loads
from bson.objectid import ObjectId
from myproject.myapi import users
import json
import copy


#!/usr/bin/python
# coding=utf-8
# 采用TextRank方法提取文本关键词
#import jieba.analyse
from textrank4zh import TextRank4Keyword, TextRank4Sentence
from ..myapi import db

# will move these env variables out
mongo_uri = "mongodb+srv://root:admin0123456@cluster0.puxa2.mongodb.net/myFirstDatabase?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
mongo_name = "dev"
database = db.DB(mongo_uri, mongo_name)

@api_view(['GET', 'POST'])

def run_script(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    task_string = data['taskString']
    task_id = data['taskId']
    created_by = data['createdBy']
    created_time = data['createdTime']
    tr4w = TextRank4Keyword()
    tr4w.analyze(text=task_string, lower=True, window=2)
    key_words = tr4w.get_keywords(10, word_min_len=1)
    key_phrases = tr4w.get_keyphrases(keywords_num=20, min_occur_num= 2)
    tr4s = TextRank4Sentence()
    tr4s.analyze(text=task_string, lower=True, source = 'all_filters')
    key_sentences = tr4s.get_key_sentences(num=3)
    card_data = {
        "keyWords": key_words,
        "keyPhrases": key_phrases,
        "keySentences": key_sentences,
        "cardString": task_string,
        "taskId": ObjectId(task_id),
        "createdBy": ObjectId(created_by),
        "createdTime": created_time
    }
    card_id = database.create_card(card_data)
    return Response({
        "_id": str( card_id ),
        "keyWords": key_words,
        "keyPhrases": key_phrases,
        "keySentences": key_sentences
    })

@api_view(['GET', 'POST'])

def get_configuration(request, user_id):
    user = database.find_user(user_id)
    if not user:
        raise Http404
    user_task_maps = database.find_user_task_maps(user_id)
    user_card_maps = database.find_user_card_maps(user_id)

    taskIds = [user_task_map.get('taskId', None) for user_task_map in user_task_maps ]
    tasks = database.find_tasks(taskIds)
    cards = []
    cards_with_no_task_ids = [user_card_map.get('cardId', None) for user_card_map in user_card_maps ]
    cards_with_no_task = database.find_cards_with_no_task(cards_with_no_task_ids)
    cards_with_no_task = [ card_with_no_task for card_with_no_task in cards_with_no_task ]
    cards += cards_with_no_task
    tasks = [ task for task in tasks]
    user_task_maps = []
    for task in tasks:
        taskId = task['_id']
        taskCards = database.cards.find({'taskId': ObjectId(taskId) })
        taskCards = [taskCard for taskCard in taskCards]
        cards += taskCards
        users_on_task = database.userTaskMap.find( { 'taskId': taskId } )
        for user_on_task in users_on_task:
            user_name = database.users.find_one({ '_id': user_on_task['userId'] }, { 'name': 1, 'headimgurl': 1 })
            if user_name:
                if (user_name.get('headimgurl')):
                    user_task_maps.append( { 'taskId': str(user_on_task['taskId']), 'userId': str(user_on_task['userId']), "userName": user_name['name'], "headimgurl": user_name['headimgurl'] } )
                else:
                    user_task_maps.append( { 'taskId': str(user_on_task['taskId']), 'userId': str(user_on_task['userId']), "userName": user_name['name'] } )
    return Response({
        'user': dumps(user),
        'tasks': dumps(tasks),
        'cards': dumps(cards),
        'userTaskMaps': json.dumps(user_task_maps)
    })

@api_view(['GET'])
def get_user(request, user_id):
    user = database.find_user(user_id)
    return Response({
        'user': dumps(user)
    })

@api_view(['GET'])
def get_user_tasks(request, user_id):
    user = database.find_user(user_id)
    if not user:
        raise Http404
    user_task_maps = list(database.find_user_task_maps(user_id))
    taskIds = [user_task_map.get('taskId', None) for user_task_map in user_task_maps ]
    tasks = database.find_tasks(taskIds)
    return Response({
        'user': dumps(user),
        'tasks': dumps(tasks),
        'userTaskMaps': dumps(user_task_maps)
    })

@api_view(['GET'])
def get_task_cards(request, task_id):
    task = database.find_task(task_id)
    if not task:
        raise Http404
    cards = list(database.cards.find({'taskId': ObjectId(task_id) }))
    return Response({
        'cards': dumps(cards),
        'tasks': dumps([task])
    })

@api_view(['GET'])
def get_user_cards(request, user_id):
    page = int(request.GET.get('page'))
    from_wechat = int(request.GET.get('fromWeChat'))

    if not user_id:
        raise Http404
    try:
        if from_wechat == 1:
            cards = database.find_user_taskless_cards(user_id, page)
            return Response({
                'cards': dumps(cards)
            })
        else:
            cards = database.find_user_task_cards(user_id, page)
            return Response({
                'cards': dumps(cards)
            })
    except ValueError:
        print(f"Unable to retrieve card for user ${user_id} due to ${ValueError}")

@api_view(['POST'])

def create_card(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    title = data['title']
    description = data['description']
    created_by = ObjectId(data['createdBy'])
    create_date = data['createDate']
    task_id = data.get('taskId', None)
    link = data['link']
    card_data = {
        'title': title,
        'description': description,
        'createdBy': created_by,
        'createDate': create_date,
        'updatedBy': created_by,
        'updateDate': create_date,
        'link': link
    }
    if task_id:
        card_data['taskId'] = ObjectId(task_id)

    card_id = database.create_card(card_data)

    # add monitor
    users.monitor(data['createdBy'], 'createCard')

    return Response({
        'cardData': {
            '_id': str(card_id)
        }
    })

@api_view(['POST'])

def delete_card(request, card_id):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    updated_by = ObjectId(data['updatedBy'])
    update_date = data['updateDate']
    query = { '_id': ObjectId( card_id ) }
    card = database.cards.find_one( query )
    task_id = None
    if 'taskId' in card:
        task_id = card['taskId']
    database.cards.delete_one( query )
    if task_id:
        task_query = {
            '_id': task_id
        }
        task_update = {
            '$set': {
                'updatedBy': updated_by,
                'updateDate': update_date,
            },
            '$pull': {
                'cardIds': ObjectId( card_id )
            }
        }
        database.tasks.update_one(task_query, task_update)
    return Response({
        'cardId': card_id
    })

@api_view(['POST'])

def mark_card_as_read(request, card_id):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    updated_by = data['updatedBy']
    query = { '_id': ObjectId( card_id ) }
    update = { '$push': { 'read': ObjectId(updated_by) } }
    database.cards.update_one( query, update )
    return Response({
        'cardId': card_id
    })

@api_view(['POST'])

def summarize(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    text_string = data['text']
    tr4w = TextRank4Keyword()
    tr4w.analyze(text=text_string, lower=True, window=2)
    key_words = tr4w.get_keywords(10, word_min_len=1)
    key_phrases = tr4w.get_keyphrases(keywords_num=20, min_occur_num= 2)
    tr4s = TextRank4Sentence()
    tr4s.analyze(text=text_string, lower=True, source = 'all_filters')
    key_sentences = tr4s.get_key_sentences(num=3)
    return Response({
        "keyWords": key_words,
        "keyPhrases": key_phrases,
        "keySentences": key_sentences
    })

@api_view(['POST'])

def update_card(request, card_id):
    try:
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        data_copy = copy.deepcopy(data)
        if 'owner' in data_copy:
            data_copy['owner'] = ObjectId(data_copy['owner'])
        if 'taskId' in data_copy:
            data_copy['taskId'] = ObjectId(data_copy['taskId'])
        if 'updatedBy' in data_copy:
            data_copy['updatedBy'] = ObjectId(data_copy['updatedBy'])
        if '_id' in data_copy:
            del data_copy['_id']
        query = {
            '_id': ObjectId(card_id)
        }
        update_query = {
            '$set': data_copy
        }
        database.cards.update_one(query, update_query)
        return Response({
            'card': {
                **data, '_id': card_id
            }
        })
    except ValueError:
        print(f"Unable to update card {card_id} due to ${ValueError}")

@api_view(['POST'])

def update_card_taskid(request, card_id):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    updated_by = ObjectId(data['updatedBy'])
    update_date = data['updateDate']
    task_id = data['taskId']
    user_task_map = database.userTaskMap.find_one({
        'taskId': ObjectId(task_id),
        'userId': updated_by
    })
    if user_task_map:
        query = {
            '_id': ObjectId(card_id)
        }
        update_query = {
            '$set': {
                'taskId': ObjectId(task_id),
                'updateDate': update_date,
                'updatedBy': updated_by
            }
        }
        database.cards.update_one(query, update_query)
        user_card_map_query = {
            'cardId': ObjectId(card_id)
        }
        database.userCardMap.delete_one(user_card_map_query)
    
        return Response({
            'card': {
                '_id': card_id,
                'updatedBy': str(updated_by),
                'updateDate': update_date,
                'taskId': task_id
            }
        })
    else:
        return HttpResponseBadRequest('This invalid operation, user {0} does not have access'.\
            format( str( updated_by ) ), status=400)


@api_view(['POST'])

def create_task(request):
    """function to create tasks in the database based on request

    In post request the content of the task are provided. It is important to note two different behaviors are
    required based on whether the task need a placeholder card. The condition is based on whether the task
    already contains cards (ie cardIds is not empty)
    Args:
        request: Request sent to api server

    Returns:
        the content of the task
    """
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    title = data['title']
    description = data['description']
    creator = ObjectId(data['creator'])
    start_date = data['startDate']
    end_date = data['endDate']
    update_date = data['updateDate']
    link = data['link']
    tags = data['tags']
    card_ids = list(data['cardIds'])
    create_placehold_card = len(card_ids) == 0
    card_object_ids = [ ObjectId(id) for id in card_ids ]
    task_data = {
        'title': title,
        'description': description,
        'creator': creator,
        'startDate': start_date,
        'endDate': end_date,
        'updateDate': update_date,
        'link': link,
        'tags': tags,
        'cardIds': card_object_ids
    }
    new_task_result = database.tasks.insert_one(task_data)
    new_task_id = new_task_result.inserted_id
    database.userTaskMap.insert_one({
        'taskId': new_task_id,
        'userId': creator
    })
    if create_placehold_card:
        placeholder_card_data ={
            "title": f"已创建任务{title}",
            "description": f"你已踏上了完成“{title}的第一步!",
            "createdBy": creator,
            "taskId": new_task_id,
            "updatedBy": creator,
            'createDate': update_date,
            'updateDate': update_date,
            "link": "",
        }
        placeholder_card_result = database.cards.insert_one(placeholder_card_data)
        placeholder_card_id = placeholder_card_result.inserted_id
        task_query = { '_id':  new_task_id }
        task_update = {
            '$push': { 'cardIds': placeholder_card_id }
        }
        database.tasks.update_one(task_query, task_update)
    else:
        cards_query = { '_id': { '$in': card_object_ids } }
        cards_update = {
            '$set': {
                'taskId': new_task_id
            }
        }
        database.cards.update_many(cards_query, cards_update)
    # add monitor
    users.monitor(data['creator'], 'createTask')
    if create_placehold_card:
        card_ids.insert(0, str(placeholder_card_id))
    return Response({
        'task': {
            '_id': str(new_task_id),
            'title': title,
            'description': description,
            'creator': str(creator),
            'startDate': start_date,
            'endDate': end_date,
            'updateDate': update_date,
            'link': link,
            'tags': tags,
            'cardIds': card_ids
        }
    })

@api_view(['POST'])

def update_task(request, task_id):
    try:
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        data_copy = copy.deepcopy(data)
        if 'owner' in data_copy:
            data_copy['owner'] = ObjectId(data_copy['owner'])
        if 'taskId' in data_copy:
            data_copy['taskId'] = ObjectId(data_copy['taskId'])
        if 'updatedBy' in data_copy:
            data_copy['updatedBy'] = ObjectId(data_copy['updatedBy'])
        if 'cardIds' in data_copy and len(data_copy['cardIds']) > 0:
            # task = database.tasks.find_one(query)
            # existing_card_object_id = list(task['cardIds'])
            # existing_set = set(existing_card_object_id)
            # new_set = set(card_object_ids)
            # missing_cards = list(existing_set - new_set)
            # card_object_ids += missing_cards
            card_ids = data_copy['cardIds']
            data_copy['cardIds'] = [ ObjectId(id) for id in card_ids]
        if '_id' in data_copy:
            del data_copy['_id']
        query = {
            '_id': ObjectId(task_id)
        }
        update_query = {
            '$set': data_copy
        }
        database.tasks.update_one(query, update_query)
        return Response({
            'task': {
                **data, '_id': task_id
            }
        })
    except ValueError:
        print(f"Unable to update task {task_id} due to ${ValueError}")

@api_view(['POST'])

def delete_task(request, task_id):
    query = { '_id': ObjectId( task_id ) }
    database.tasks.delete_one( query )
    user_task_map_query = { 'taskId': ObjectId( task_id ) }
    database.userTaskMap.delete_one(user_task_map_query)
    database.cards.delete_many(user_task_map_query)
    return Response({
        'taskId': task_id
    })

@api_view(['POST'])

def task_invite(request):

    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)

    taskId = ObjectId(data['taskId'])
    userId = ObjectId(data['userId'])

    #check if exist
    user_task_map = database.userTaskMap.find_one({
        'taskId': taskId,
        'userId': userId
    })

    #if exist -> return the task id
    if( user_task_map):
        return JsonResponse({
            'userTaskMap': {
                'taskId': str(taskId),
            }
        }, status=200)

    #if not exist -> add to the database
    task_data = {
        'taskId': taskId,
        'userId': userId
    }
    
    new_task_invite = database.userTaskMap.insert_one(task_data)
    new_task_invite_id = new_task_invite.inserted_id

    # get the invite task and corresponding cards
    task = database.tasks.find_one({ '_id': taskId })
    tasks = [task]
    taskCards = database.cards.find({'taskId': taskId })
    cards = [taskCard for taskCard in taskCards]
    user_task_maps = []
    users_on_task = database.userTaskMap.find( { 'taskId': taskId } )
    for user_on_task in users_on_task:
        user_name = database.users.find_one({ '_id': user_on_task['userId'] }, { 'name': 1, 'headimgurl': 1 })
        if user_name:
            if (user_name.get('headimgurl')):
                user_task_maps.append( { 'taskId': str(user_on_task['taskId']), 'userId': str(user_on_task['userId']), "userName": user_name['name'], "headimgurl": user_name['headimgurl'] } )
            else:
                user_task_maps.append( { 'taskId': str(user_on_task['taskId']), 'userId': str(user_on_task['userId']), "userName": user_name['name'] } )
    return Response({
        'tasks': dumps(tasks),
        'cards': dumps(cards),
        'userTaskMaps': json.dumps(user_task_maps)
    })
    

@api_view(['POST'])

def task_invite_exist(request):
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)

    taskId = ObjectId(data['taskId'])
    userId = ObjectId(data['userId'])

    #check if exist
    user_task_map = database.userTaskMap.find_one({
        'taskId': taskId,
        'userId': userId
    })

    #if exist -> return the task id
    if( user_task_map):
        return JsonResponse({
            'userTaskMap': {
                'exist': True,
            }
        }, status=200)
    else:
        return JsonResponse({
            'userTaskMap': {
                'exist': False,
            }
        }, status=200)

@api_view(['GET'])
def get_task_collaborators(request, task_id):
    """Fetches users on a specific task.

    Use all document from userTaskMap (collection) that shares a specific task id
    Then use result to query users (collection)

    Args:
        request: Request sent to api server

    Returns:
        A dict mapping user id to the corresponding user data
    """
    pipeline = [
        { '$match': { 'taskId': ObjectId(task_id) }},
        { '$lookup': {
            'from': 'users',
            'localField': 'userId',
            'foreignField': '_id',
            'as': 'userInfo'
            }
        },
        {
            '$project': {
                'userInfo': {
                    '$map': {
                        'input': '$userInfo', 
                        'as': 'userInfo', 
                        'in': {
                            '_id': '$$userInfo._id',
                            'name': '$$userInfo.name',
                            'email': '$$userInfo.email',
                            'headimgurl': '$$userInfo.headimgurl'
                        }
                    },
                },
                '_id': 0
            }
        },
        {
            '$project': {
                'userInfo': {
                    '$arrayElemAt': ['$userInfo', 0],
                }
            }
        }
    ]
    aggregateResult = list(database.userTaskMap.aggregate(pipeline))
    users = []
    for item in aggregateResult:
        if 'userInfo' in item:
            users.append(item[ 'userInfo'])
    return Response({
        'users': dumps(users)
    })