import os
import pymongo
from pymongo import MongoClient, UpdateOne
from bson.objectid import ObjectId
from copy import deepcopy

class DB:
  '''
  Wrapper class that handles DB read/write
  '''
  # local variables
  def __init__(self, uri, name):
    if uri is None:
      raise ValueError("MONGO_URI is not set")
    if name is None:
      raise ValueError("MONGO_NAME is not set") 
    self._database = MongoClient(uri)
    databaseRoot = self._database[name]
    self.tasks = databaseRoot.tasks
    self.cards = databaseRoot.cards
    self.users = databaseRoot.users
    self.userTaskMap = databaseRoot.userTaskMap
    self.userCardMap = databaseRoot.userCardMap
    self.monitor = databaseRoot.monitor
    self.subscription = databaseRoot.subscription

  def find_user_task_maps(self, user_id):
    query = {
      'userId':ObjectId(user_id)
    }
    return self.userTaskMap.find(query)

  def find_user_card_maps(self, user_id):
    query = {
      'userId':ObjectId(user_id)
    }
    return self.userCardMap.find(query)

  def find_user(self, user_id):
    query = {
      '_id':ObjectId(user_id)
    }
    return self.users.find_one(query)

  def find_task(self,task_id):
    query = {
      '_id':ObjectId(task_id)
    }
    return self.tasks.find_one(query)

  def find_tasks(self, taskIds):
    query = {
      '_id': {
        '$in': taskIds
      }
    }
    return self.tasks.find(query).sort('_id', -1)
  
  def find_multi_task_cards(self, taskIds, user_id, page):
    count = 10
    query = {
      'taskId': {
        '$in': taskIds
      },
      'read': { 
        '$nin': [ObjectId(user_id)] 
      }
    }
    return self.cards.find(query).sort('_id', -1).skip(count * (page)).limit(count)

  def find_user_task_cards(self, user_id, page):
    """retrieve cards for user based cards on pagination
    Args:
      user_id: A string representing id of user
    Returns:
      Cards belonging to user from user card map.
    """
    user_task_maps = list(self.find_user_task_maps(user_id))
    task_ids = [user_task_map['taskId'] for user_task_map in user_task_maps]
    cards = list(self.find_multi_task_cards(task_ids, user_id, page))
    return cards

  def find_user_taskless_cards(self, user_id, page):
    """retrieve cards from userCardMap based on pagination
    Args:
      user_id: A string representing id of user
    Returns:
      Cards belonging to user from user card map.
    """
    pipeline = [
      { '$match': { 'userId': ObjectId(user_id) }},
      { '$sort': { '_id': -1 } },
      { '$lookup': {
          'from': 'cards',
          'localField': 'cardId',
          'foreignField': '_id',
          'as': 'card'
        }
      }
    ]
    if page > 0:
      pipeline.append({
        '$skip': 10 * page
      })
    pipeline.append({
      '$limit': 10
    })
    pipeline.append({
      '$project': {'card': {'$arrayElemAt': ['$card', 0] } }
    })
    aggregated_result = list(self.userCardMap.aggregate(pipeline))
    cards = []
    for item in aggregated_result:
      if 'card' in item:
        cards.append(item['card'])
      else: 
        cards.append({})
    return cards

  def find_card(self,card_id):
    query = {
      '_id':ObjectId(card_id)
    }
    return self.cards.find_one(query)

  def find_cards(self,task_id):
    query = {
      'taskId':ObjectId(task_id)
    }
    return self.cards.find(query)

  def create_card(self, card_data):
    result = self.cards.insert_one(card_data)
    task_id = card_data.get('taskId', None)
    if task_id:
      task_query = {
        '_id': task_id
      }
      update = { '$set': { 'updateDate': card_data['createDate'], 'updatedBy': card_data['createdBy'] }, '$push': { 'cardIds': { "$each" : [result.inserted_id], "$position": 0 } } }
      self.tasks.update_one(task_query, update)
    else:
      self.userCardMap.insert_one({
        'userId': card_data['createdBy'],
        'cardId': result.inserted_id
      })
    return result.inserted_id