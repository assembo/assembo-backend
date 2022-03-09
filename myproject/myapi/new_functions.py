from django.http import (Http404, HttpResponseBadRequest, JsonResponse)
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
import os
import json
from bson.json_util import dumps, loads
from bson.objectid import ObjectId
from myproject.myapi import users
import hashlib
import requests
from datetime import datetime
from django.shortcuts import HttpResponse

#!/usr/bin/python
# coding=utf-8
# 采用TextRank方法提取文本关键词
import sys
#import jieba.analyse
from textrank4zh import TextRank4Keyword, TextRank4Sentence
from ..myapi import db

# will move these env variables out
mongo_uri = "mongodb+srv://root:admin0123456@cluster0.puxa2.mongodb.net/myFirstDatabase?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
mongo_name = "dev"
database = db.DB(mongo_uri, mongo_name)

ASSEMBOWEBAPPID = "wxd71ae0c56c06742c"
ASSEMBOWEBAPPSECRET = "dc42329f35cc3b965e90410c2d5e910b"

ASSEMBOOAID = "wx69ed5dfefbea409f"
ASSEMBOOASECRET = "d6f81ac64d04149dc1b45198ddcdcb5a"

@api_view(['POST'])
def login_username(user):
    #format the data to JSON
    body_unicode = user.body.decode('utf-8')
    data = json.loads(body_unicode)

    #read data (email and password)
    email = data['username']
    password = data['password']

    #find user from database
    user_saved = database.users.find_one({
        'email': email
    })

    # not exist return error
    if not user_saved:
        return Response({
            'data': {
                'message': '用户名错误'
            }
        }, status=404)
    
    #hash password
    s = hashlib.sha256()
    s.update(password.encode('utf-8'))
    hashed_password = s.hexdigest()

    if user_saved['password'] != hashed_password:
        return Response({
            'data': {
                'message': '密码错误'
            }
        }, status=404)

    # add monitor
    monitor(str(user_saved['_id']), 'login')
    
    return Response({
        'data': {
            'userId': str(user_saved['_id']),
            'username': user_saved['name'],
            'accessToken': 'login_access',
            'refreshToken': 'login_refresh'
        }
    }, status=200)

@api_view(['POST'])
def login_wechat(data):    
    #format the data to JSON
    body_unicode = data.body.decode('utf-8')
    credential = json.loads(body_unicode)

    #read credential
    code = credential['code']
    state = credential['state']

    if state != 'AssemboFun777!':
        return Response({
            'data': {
                'message': 'Invalid request'
            }
        }, status=400)
    
    # get access_token from code return
    # assembo app credentials
    codeUrl = 'https://api.weixin.qq.com/sns/oauth2/access_token?appid={0}&secret={1}&code={2}&grant_type=authorization_code'.format(ASSEMBOWEBAPPID, ASSEMBOWEBAPPSECRET, code)

    codeData = requests.get(codeUrl)
    
    codeDataDecoded = json.loads(codeData.text)

    print('get code data decoded -- ', codeDataDecoded)

    appAccessToken = codeDataDecoded['access_token']
    appRefreshToken = codeDataDecoded['refresh_token']
    appOpenId = codeDataDecoded['openid']

    # get unionId and user wehchat data
    finalUrl = 'https://api.weixin.qq.com/sns/userinfo?access_token={0}&openid={1}'.format(appAccessToken, appOpenId)

    finalData = requests.get(finalUrl)

    finalData = finalData.text.encode('ISO-8859-1')

    decoded = json.loads(finalData)

    #find user from database
    user_saved = database.users.find_one({
        'unionId': decoded['unionid']
    })

    # if exist then login
    if user_saved:
        if user_saved.get('email'):
            return Response({
            'data': {
                'userId': str(user_saved['_id']),
                'username': user_saved['name'],
                'accessToken': get_user_access_token(str(user_saved['_id'])),
                'refreshToken': get_user_refresh_token(str(user_saved['_id'])),
                'emailExisted': True
            }
        }, status = 200)
        else:
            return Response({
                'data': {
                    'userId': str(user_saved['_id']),
                    'username': user_saved['name'],
                    'accessToken': get_user_access_token(str(user_saved['_id'])),
                    'refreshToken': get_user_refresh_token(str(user_saved['_id'])),
                    'emailExisted': False,
                }
            }, status=200)

    #if not exist -> save in database
    user_data = {
        'name': decoded['nickname'],
        'unionId': decoded['unionid'],
        'appAccessToken' : appAccessToken,
        'appRefreshToken' : appRefreshToken,
        'appOpenId' : appOpenId,
        'sessionTokens': [],
        'city': decoded['city'],
        'headimgurl': decoded['headimgurl']
    }

    new_user_result = database.users.insert_one(user_data)
    new_user_id = new_user_result.inserted_id

    signup_assign_task_cards(new_user_id)
    
    return Response({
        'data': {
            'userId': str(new_user_id),
            'username': decoded['nickname'],
            'accessToken': get_user_access_token(str(new_user_id)),
            'refreshToken': get_user_refresh_token(str(new_user_id)),
            'emailExisted': False,
        }
    }, status=200)

@api_view(['POST'])
def signup_username(user):
    #format the data to JSON
    body_unicode = user.body.decode('utf-8')
    data = json.loads(body_unicode)

    #read data (email and password)
    email = data['username']
    password = data['password']

    #find user from database
    user_saved = database.users.find_one({
        'email': email
    })

    # if exist then return error
    if user_saved:
        return Response({
            'data': {
                'message': '您已注册。请登录。'
            }
        }, status = 404)
    
    #hash password
    s = hashlib.sha256()
    s.update(password.encode('utf-8'))
    hashed_password = s.hexdigest()

    #set data to store in database
    
    user_data = {
        'name': email,
        'email': email,
        'password': hashed_password,
        'sessionTokens': []
    }

    new_user_result = database.users.insert_one(user_data)
    new_user_id = new_user_result.inserted_id

    signup_assign_task_cards(new_user_id)

    # add monitor
    monitor(str(new_user_id), 'login')
    
    return Response({
        'data': {
            'userId': str(new_user_id),
            'username': data['userName'],
            'accessToken': get_user_access_token(str(new_user_id)),
            'refreshToken': get_user_refresh_token(str(new_user_id)),
        }
    }, status=200)

@api_view(['POST']) 
def signup_wechat(user):
    #format the data to JSON
    body_unicode = user.body.decode('utf-8')
    data = json.loads(body_unicode)

    #read data (email and password)
    email = data['username']
    password = data['password']
    userId = data['userId']

    #find user from database
    user_saved = database.users.find_one({
        'email': email
    })

    #hash password
    s = hashlib.sha256()
    s.update(password.encode('utf-8'))
    hashed_password = s.hexdigest()

    user_wechat = database.users.find_one({
        '_id': ObjectId(userId)
    })

    # if exist, check password / if password invalid, return error
    if user_saved:
        if user_saved['password'] != hashed_password:
            return Response({
                'data': {
                    'message': '密码错误/用户名已存在'
                }
            }, status = 404)
        else:
            # add to the email one and delete wechat one
            query = {
                '_id': ObjectId(user_saved['_id'])
            }
            
            # delete the wechat one
            database.users.delete_one({ '_id': ObjectId(userId) })

            user_update_query = {
                '$set' : {
                    'name': user_wechat['name'],
                    'unionId': user_wechat['unionId'],
                    'appAccessToken' : user_wechat['access_token'],
                    'appRefreshToken' : user_wechat['refresh_token'],
                    'appOpenId' : user_wechat['appOpenId'],
                    'city': user_wechat['city'],
                    'headimgurl': user_wechat['headimgurl']
                }
            }
            database.users.update_one(query, user_update_query)

            return Response({
                'data': {
                    'userId': str(user_saved['_id']),
                    'username': user_wechat['name'],
                    'accessToken': get_user_access_token(str(user_saved['_id'])),
                    'refreshToken': get_user_refresh_token(str(user_saved['_id'])),
                }
            }, status=200)

    #set data to store in database
    user_data = {
        'email': email,
        'password': hashed_password,
    }

    query = {
        '_id': ObjectId(userId)
    }

    user_update_query = {
        '$set' : {
            'email': email,
            'password': hashed_password
        }
    }
    database.users.update_one(query, user_update_query)

    return Response({
        'data': {
            'userId': userId,
            'username': user_wechat['name'],
            'accessToken': 'signup_access',
            'refreshToken': 'signup_refresh',
        }
    }, status=200)

@api_view(['POST'])
def invite_accept(request):
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
            'data': {
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
        'task': dumps(task),
        'cards': dumps(cards),
        'userTaskMaps': json.dumps(user_task_maps)
    }, status=200)

def media_update (data):
    #format the data to JSON
    body_unicode = data.body.decode('utf-8')
    data = json.loads(body_unicode)

    #read data 
    target = data['target']
    targetId = data['id']
    medias = data['medias']

    targetData = database.tasks.find_one({ '_id': ObjectId(targetId) }) if target == 'task' else database.cards.find_one({ '_id': ObjectId(targetId) })

    if not targetData:
        return HttpResponse('no targetdata is found!')
    
    query = { '_id': ObjectId(targetId)}
    update_query = {
        '$set': {
            'medias': medias
        }
    }

    if target == 'task':
        database.tasks.update_one(query, update_query)
    else :
        database.cards.update_one(query, update_query)
    
    return HttpResponse("targetData medias updated successfully")
@api_view(['GET', 'POST'])
def wechat_oa(request):
    print('method --', request.method)
    if request.method == "GET":
        print("request: ", request)
        print('request data --', request.GET)
        # 接受微信服务器get请求发过来的参数
        # 将参数list中排序合成字符串，再用sha1加密得到新的字符串与微信发过来的signature对比，如果相同就返回echostr给服务器，校验通过
        # ISSUES: TypeError: '<' not supported between instances of 'NoneType' and 'str'
        # 解决方法：当获取的参数值为空是传空，而不是传None
        signature = request.GET.get('signature', '')
        timestamp = request.GET.get('timestamp', '')
        nonce = request.GET.get('nonce', '')
        echostr = request.GET.get('echostr', '')
        # 微信公众号处配置的token
        token = str("secrettoken")

        hashlist = [token, timestamp, nonce]
        hashlist.sort()
        print("[token, timestamp, nonce]: ", hashlist)

        hashstr = ''.join([s for s in hashlist]).encode('utf-8')

        hashstr = hashlib.sha1(hashstr).hexdigest()
        print('hashstr sha1: ', hashstr)
        print('signature: ', signature)

        if hashstr == signature:
            return HttpResponse(echostr)
        else:
            return HttpResponse("weixin index")
    elif request.method == "POST":
        # autoreply方法时用来回复消息的
        print('in POST')
        otherContent = autoreply(request)
        return HttpResponse(otherContent)
    else:
        print("你的方法不正确....")

def autoreply(request):
    try:
        webData = request.body
        print("Handle POST webData is: ", webData)

        '''

        in POST
        Handle POST webData is:  
        b'<xml>
        <ToUserName><![CDATA[gh_81e2d9938466]]></ToUserName>\n
        <FromUserName><![CDATA[oSsul5nSE1djiyNHEgMpCMQL1XpQ]]></FromUserName>\n
        <CreateTime>1624518883</CreateTime>\n
        <MsgType><![CDATA[event]]></MsgType>\n
        <Event><![CDATA[subscribe]]></Event>\n<EventKey><![CDATA[]]></EventKey>\n
        </xml>'

        '''

        '''
            Handle POST webData is:  
            b'<xml><ToUserName><![CDATA[gh_81e2d9938466]]></ToUserName>\n
            <FromUserName><![CDATA[oSsul5nSE1djiyNHEgMpCMQL1XpQ]]></FromUserName>\n
            <CreateTime>1624518916</CreateTime>\n
            <MsgType><![CDATA[text]]></MsgType>\n
            <Content><![CDATA[\xe7\xac\xac\xe4\xba\x8c\xe6\xac\xa1\xe5\x95\xa6]]></Content>\n
            <MsgId>23257521296626200</MsgId>\n
            </xml>'

        '''

        recMsg = receive.parse_xml(webData)

        if recMsg.MsgType == 'event':
            print('-- do event -- ')
            if(recMsg.Event == 'subscribe'):
                print('-- do subscribe -- ')
                toUser = recMsg.FromUserName
                fromUser = recMsg.ToUserName
                content = (
                    "你好哇！\n\n"

                    "也许你也经历过在团队合作的时候，\n"
                    "信息、文档满天飞，团队成员们沟通脱节，不在同一个步调上。\n\n"

                    "Assembo致力于让你的工作更清晰，信息流更顺畅，减轻工作环境的焦虑，\n"
                    "花50%更少的时间重复沟通、同步、开会，\n"
                    "花更多的时间创造价值！\n\n"

                    "让Assembo为你开启工作的新旅程 (๑•ㅂ•)و✧\n\n"

                    "关注 Assembo咔嗒 公众号并微信注册账号后，给公众号发信息，就可以在app里面生成卡片噢！\n\n"

                    "登录入口 -> \n"
                    "https://www.assembo.cc/app"
                    # "微信注册方法：\n"
                    # "1. 用电脑浏览器打开https://www.assembo.cc/app/\n"
                    # "2. 点击微信登录获取二维码\n"
                    # "3. 用手机扫电脑的二维码\n"
                    # "4. 为微信账户添加用户名密码\n"
                    # "5. 可以在手机浏览器用用户名密码登录App了！https://www.assembo.cc/app/（iPhone建议使用Safari打开）\n"
                )
                replyMsg = reply.TextMsg(toUser, fromUser, content)
                return replyMsg.send()
        elif isinstance(recMsg, receive.Msg):
            toUser = recMsg.FromUserName
            fromUser = recMsg.ToUserName
            if recMsg.MsgType == 'text':
                status = saveWechatOAUser(request)
                replyMsg = reply.TextMsg(toUser, fromUser, status)
                return replyMsg.send()
            if recMsg.MsgType == 'image':
                statusImage = saveWechatOAUserImage(request)
                replyMsg = reply.TextMsg(toUser, fromUser, statusImage)
                return replyMsg.send()
            else:
                print('enter is instance else')
                replyMsg = reply.TextMsg(toUser, fromUser, '暂不处理')
                return replyMsg.send()
        else:
            print("暂不处理")
            toUser = recMsg.FromUserName
            fromUser = recMsg.ToUserName
            replyMsg = reply.TextMsg(toUser, fromUser, '暂不处理')
            return reply.Msg().send()
    except Exception as e:
        print(e)

def saveWechatOAUserImage(request):
    print('in saveWechatOAUserImage --')
    webData = request.body
    recMsg = receive.parse_xml(webData)

    oaOpenId = recMsg.FromUserName
    #createTime = recMsg.CreateTime
    MsgId = recMsg.MsgId

    # get access_token
    accessUrl = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={0}&secret={1}'.format(ASSEMBOOAID, ASSEMBOOASECRET)

    accessRequest = requests.get(accessUrl)

    accessDataDecoded = json.loads(accessRequest.text)

    print('accessDataDecoded -- ', accessDataDecoded)

    access_token = accessDataDecoded['access_token']

    # get unionId and user wehchat data
    finalUrl = 'https://api.weixin.qq.com/cgi-bin/user/info?access_token={0}&openid={1}'.format(access_token, oaOpenId)

    finalData = requests.get(finalUrl)

    decoded = json.loads(finalData.text)

    print('decoded data -- ', decoded)
    
    #find user from database
    user_saved = database.users.find_one({
        'unionId': decoded['unionid']
    })

    if not user_saved:
        return '您还未注册，请先在进行微信注册！注册网址:https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx69ed5dfefbea409f&redirect_uri=https%3A%2F%2Fwww.assembo.cc%2Fapp%2Fwechat%2Fsignup&response_type=code&scope=snsapi_userinfo&state=secretstate#wechat_redirect'

    if user_saved and not user_saved.get('oaOpenId'):
        query = {
            '_id': ObjectId(user_saved['_id'])
        }
        user_update_query = {
            '$set' : {
                'oaOpenId': decoded['openid'],
            }
        }
        database.users.update_one(query, user_update_query)

    # create card

    # get medias
    picUrl = recMsg.PicUrl

    r = requests.get(picUrl)

    dataUrl = ("data:" + r.headers['Content-Type'] + ";" + "base64," + base64.b64encode(r.content).decode('utf-8'))

    # save to Bmob and get Bmob url
    headers = {
        'X-Bmob-Application-Id': 'e2366e18d49153637237e3bbece1620f',
        'X-Bmob-REST-API-Key': 'a64e59db677385b62fecdee5a4d47f1e',
        'Content-Type': r.headers['Content-Type'],
    }

    data = dataUrl

    bmob = requests.post('https://api2.bmob.cn/2/files/wechatUpload-' + recMsg.MediaId + '.' + r.headers['Content-Type'].split('/')[1], headers=headers, data=data)

    current_time = str( datetime.utcnow().isoformat() ).split('T')[0]
     
    card_data = {
        'title': '微信导入: 图片' ,
        'description': '',
        'createdBy': user_saved['_id'],
        'createDate': current_time,
        'updatedBy': user_saved['_id'],
        'updateDate': current_time,
        'MsgId': 'image' + '__' + MsgId,
        'link': '',
        'owner': user_saved['_id'],
        'medias': [{ 
            'name': '微信导入', 
            'type': r.headers['Content-Type'], 
            'size': '---', 
            'dataUrl': '', 
            'from': 'card', 
            'id': '', 
            'userName': user_saved['name'], 
            'date': current_time, 
            'keyId': r.headers['Content-Type'] + '-' + MsgId, 
            'bmobUrl': json.loads(bmob.content)['url']  
            }]
    }

    # check if done already
    checkMsgId = 'image' + '__' + MsgId
    saved_card = database.cards.find({'MsgId': checkMsgId })
    isNull = dumps(saved_card) == '[]'

    if(isNull):
        card_id = database.create_card(card_data)

        userCardMap = {
            'userId': user_saved['_id'],
            'cardId': card_id
        }

        new_card_result = database.userCardMap.insert_one(userCardMap)
        new_card_id = new_card_result.inserted_id

        _card = database.cards.find({'_id': card_id })
        card = json.loads(dumps(_card[0]) )       

        # update the card media's id
        query = {
            '_id': card_id
        }
        media = card['medias'][0]
        media['id'] = str(card_id)
        print('to update media to ', media)
        print('type of to update ', type(media))
        newMedias = [media]
        card_update_query = {
            '$set' : {
                'medias': newMedias
            }
        }
        database.cards.update_one(query, card_update_query)
        
    return '卡片添加完成！请在更新页面刷新查看！'

def saveWechatOAUser(request):
    print('in saveWechatOAUser --')
    webData = request.body
    recMsg = receive.parse_xml(webData)

    oaOpenId = recMsg.FromUserName
    content = recMsg.Content.decode('utf-8')
    #createTime = recMsg.CreateTime
    MsgId = recMsg.MsgId

    print('oaOpenId & content -- ', oaOpenId, content)

    print('content slice -- ', content[:8])

    #assembo official account credentials
    appId = 'wx69ed5dfefbea409f'
    secret = 'd6f81ac64d04149dc1b45198ddcdcb5a'

    # get access_token
    accessUrl = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={0}&secret={1}'.format(appId, secret)

    accessRequest = requests.get(accessUrl)

    accessDataDecoded = json.loads(accessRequest.text)

    print('accessDataDecoded -- ', accessDataDecoded)

    access_token = accessDataDecoded['access_token']

    # get unionId and user wehchat data
    finalUrl = 'https://api.weixin.qq.com/cgi-bin/user/info?access_token={0}&openid={1}'.format(access_token, oaOpenId)

    finalData = requests.get(finalUrl)

    decoded = json.loads(finalData.text)

    print('decoded data -- ', decoded)
    
    #find user from database
    user_saved = database.users.find_one({
        'unionId': decoded['unionid']
    })

    if not user_saved:
        return '您还未注册，请先在进行微信注册！注册网址:https://open.weixin.qq.com/connect/oauth2/authorize?appid=wx69ed5dfefbea409f&redirect_uri=https%3A%2F%2Fwww.assembo.cc%2Fapp%2Fwechat%2Fsignup&response_type=code&scope=snsapi_userinfo&state=secretstate#wechat_redirect'

    if user_saved and not user_saved.get('oaOpenId'):
        query = {
            '_id': ObjectId(user_saved['_id'])
        }
        user_update_query = {
            '$set' : {
                'oaOpenId': decoded['openid'],
            }
        }
        database.users.update_one(query, user_update_query)

    # create card
    current_time = str( datetime.utcnow().isoformat() ).split('T')[0]
     
    card_data = {
        'title': '微信导入: ' + content[:8] + '...',
        'description': content,
        'createdBy': user_saved['_id'],
        'createDate': current_time,
        'updatedBy': user_saved['_id'],
        'updateDate': current_time,
        'MsgId': content + '__' + MsgId
    }

    # check if done already
    checkMsgId = content + '__' + MsgId
    saved_card = database.cards.find({'MsgId': checkMsgId })
    isNull = dumps(saved_card) == '[]'

    if(isNull):
        card_id = database.create_card(card_data)

        userCardMap = {
            'userId': user_saved['_id'],
            'cardId': card_id
        }

        new_card_result = database.userCardMap.insert_one(userCardMap)
        new_card_id = new_card_result.inserted_id
    
    return '卡片添加完成！请在更新页面刷新查看！'

@api_view(['POST'])
def user_update_name (user) :
    #format the data to JSON
    body_unicode = user.body.decode('utf-8')
    data = json.loads(body_unicode)

    #read data (email and password)
    userId = data['userId']
    nickname = data['nickname']

    #find user from database
    user_saved = database.users.find_one({
        '_id': ObjectId(userId)
    })

    if user_saved:
        query = {
            '_id': ObjectId(userId)
        }
        user_update_query = {
            '$set' : {
                'name': nickname
            }
        }
        database.users.update_one(query, user_update_query)
    
    return Response({
        'data': {
            'userId': userId,
        }
    }, status=200)

def get_user_access_token (userId):
    return 'access_token_released'

def get_user_refresh_token (userId):
    return 'refresh_token_released'

def monitor(userId, action):
    #find user from database
    user_monitor = database.monitor.find_one({
        'userId': ObjectId(userId) 
    })

    if not user_monitor:
        sample = {
            'userId': ObjectId(userId),
            'login': 1,
            'createCard': 0,
            'createTask': 0,
            'startDate': str( datetime.utcnow().isoformat() ),
            'endDate': str( datetime.utcnow().isoformat() )
        }
        new_user_monitor = database.monitor.insert_one(sample)
        new_user_monitor_id = new_user_monitor.inserted_id

        return Response({
            'userMonitor': {
                '_id': str(new_user_monitor_id),
            }
        }, status=200)
    
    query = {
            '_id': user_monitor['_id']
        }
    update_query = {
        '$set' : {
            action: user_monitor[action] + 1,
            'endDate': str( datetime.utcnow().isoformat() )
        }
    }
    database.monitor.update_one(query, update_query)
    
    return Response({
        'user_monitor': {
            '_id': str(user_monitor['_id']),
        }
    }, status=200)

def signup_assign_task_cards(new_user_id):
    current_time = str( datetime.utcnow().isoformat() )

    #save the tutorial task and cards
    #populate first time tutorial task and its update cards
    createdBy = ObjectId('60c9990cede6134a7155dbf1')
    tutorialTask = {
        'title': "欢迎！这是一个新手引导任务",
        "description":"Assembo致力于帮您和团队: 1. 以最简洁的卡片🔖形式归档所有项目资料 2. 以最简便的方式左右滑👈👉同步和处理项目信息卡片。⭐试试去页面底部中间的更新页处理这些卡片吧！" ,
        'creator': "Assembo团队",
        'createdBy': createdBy,
        'startDate': current_time,
        'endDate': current_time,
        'updateDate': current_time,
        'updatedBy': createdBy,
        'tags': [ '其他' ]

    }

    #save the task
    new_task_result = database.tasks.insert_one(tutorialTask)
    new_task_id = new_task_result.inserted_id

    tutorialUpdate1 = {
        'title': "1a 关于同一个任务的信息都以一个个卡片🔖的形式存储",
        "description":"在任务页中部的蓝色加号“添加更新”，或更新页👈左滑卡片点击蓝色加号“添加更新”都可以为任务添加更新卡片" ,
        'createdBy': createdBy,
        'createDate': current_time,
        'updatedBy': createdBy,
        'updateDate': current_time,
        'taskId': new_task_id
    }

    tutorialUpdate2 = {
        'title': "1b 邀请队友共同编辑",
        "description":"在“可见成员”栏，点击最右边的添加用户按键，即可复制此任务链接分享给想邀请的队友🙋‍♀️🙋‍♂️" ,
        'createdBy': createdBy,
        'createDate': current_time,
        'updatedBy': createdBy,
        'updateDate': current_time,
        'taskId': new_task_id
    }

    tutorialUpdate3 = {
        'title': "1c （敬请期待）智能生成卡片标题",
        "description":"创建任务/卡片时，粘贴一段文字📄并点击“文本识别”，文本摘要算法可自动生成卡片标题" ,
        'createdBy': createdBy,
        'createDate': current_time,
        'updatedBy': createdBy,
        'updateDate': current_time,
        'taskId': new_task_id
    }

    tutorialUpdate4 = {
        'title': "1d （敬请期待）微信转发到公众号生成更新卡片",
        "description":"在第三方App产生的工作信息/文档💻📞📱，都可以一键转发归档到这里来" ,
        'createdBy': createdBy,
        'createDate': current_time,
        'updatedBy': createdBy,
        'updateDate': current_time,
        'taskId': new_task_id
    }

    tutorialUpdate5 = {
        'title': "2a 在任务页左右滑快速处理卡片",
        "description":"所有任务的更新卡片动态都在任务页 👉右滑可查看卡片所属任务或分享所属任务链接 2. 👈左滑可添加更新卡片或标记卡片为已读归档（不显示在更新页）" ,
        'createdBy': createdBy,
        'createDate': current_time,
        'updatedBy': createdBy,
        'updateDate': current_time,
        'taskId': new_task_id
    }

    tutorialUpdate6 = {
        'title': "2b（敬请期待）按照您的标签智能筛选和排序任务/卡片",
        "description":"当任务和卡片多起来的时候，可按需添加标签和选择排序逻辑，专注🙇‍♂️在最重要最紧急的任务/卡片上" ,
        'createdBy': createdBy,
        'createDate': current_time,
        'updatedBy': createdBy,
        'updateDate': current_time,
        'taskId': new_task_id
    }
    
    #save the cards
    database.create_card(tutorialUpdate1)
    database.create_card(tutorialUpdate2)
    database.create_card(tutorialUpdate3)
    database.create_card(tutorialUpdate4)
    database.create_card(tutorialUpdate5)
    database.create_card(tutorialUpdate6)


    #update the userTaskMap
    new_task_user_map = database.userTaskMap.insert_one({
        'taskId': new_task_id,
        'userId': new_user_id
    })
    new_task_user_map.inserted_id
