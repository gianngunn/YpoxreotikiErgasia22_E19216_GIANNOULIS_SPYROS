# -*- coding: utf-8 -*-
"""
Created on Tue Jun 28 19:26:59 2022

@author: GiannGunn
"""

import pymongo
from pymongo import MongoClient
from flask import Flask, request, Response, jsonify
from datetime import datetime
import json


client = MongoClient('mongodb://docker:mongopw@localhost:49153')

db = client['DigitalNotes']
User = db['Users']
Note = db['Notes']
"""
User.createIndex({'email': 1}, {unique: true})
User.createIndex({'username': 1}, {unique: true})
"""
app = Flask(__name__)
logedin = 0
logedinUser = None


@app.route('/register', methods=['POST'])
def register():

    data = None

    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500)

    if data == None:
        return Response("bad request", status=500)

    if not 'email' in data or not 'username' in data or not 'name' in data or not 'lastname' in data or not 'password' in data:
        return Response("Information incompleted", status=500)

    if User.count_documents({'email': data['email']}) == 0:
        if User.count_documents({'username': data['username']}) == 0:
            user = {
                'email': data['email'],
                'username': data['username'],
                'name': data['name'],
                'lastname': data['lastname'],
                'password': data['password'],
                'role': 'Απλός Χρήστης'
            }
            User.insert_one(user)
            return Response("User successfully registered!!", status=201)
        else:
            return Response("username is used, try another one", status=200)
    else:
        return Response("email is used, try another one", status=200)


@app.route('/login', methods=['POST'])
def login():
    global logedin, logedinUser
    data = None
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500)

    if data == None:
        return Response("bad request", status=500)
    # thelei ftiajimo 1 if gia mail kai pass kai mia gia username kai pass
    if not 'email' in data and not 'username' in data or not 'password' in data:
        return Response("Information incompleted", status=500)

    if 'email' in data:
        user = User.find_one({'email': data['email']})
    else:
        user = User.find_one({'username': data['username']})

    if not user:
        logedinUser = None
        logedin = 0
        return Response("you must register first in order to log in, if you are admin use email only", status=404)

    if user['password'] == data['password']:
        logedinUser = user
        logedin = 1
        if user['role'] == 'admin':
            if user['changedPass'] == 'no':
                return Response("go to /changepassA to change your password", status=200)
            else:
                return Response('welcome admin!!',status=200)
        return Response("User successfully loged in!!", status=202)
    else:
        logedinUser = None
        logedin = 0
        return Response("Wrong password, try again!!", status=401)


@app.route('/createNote', methods=['POST'])
def createNote():
    global logedin, logedinUser
    data = None
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=500)

    if data == None:
        return Response("bad request", status=500)

    if not 'title' in data or not 'note' in data or not 'keyword' in data:
        return Response("Information incompleted", status=500)

    if Note.count_documents({'title': data['title'], 'user': logedinUser['_id']}) == 0:
        note = {
            'title': data['title'],
            'note': data['note'],
            'keyword': data['keyword'],
            'createdAt': datetime.now(),
            'user': logedinUser['_id']
        }
        """strftime("%d/%m/%Y %H:%M:%S")"""
        Note.insert_one(note)
        return Response("Note created!", status=201)
    else:
        return Response("change the title", status=200)


@app.route('/getNoteWithTitle/<string:title>', methods=['GET'])
def getNoteTitle(title):
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    if title == None:
        return Response("Bad request", status=400)

    note = Note.find_one({'title': title, 'user': logedinUser['_id']})
    if note != None:
        if note['user'] == logedinUser['_id'] and note['title'] == title:
            n = {
                'Note Title': note['title'],
                'Note': note['note'],
                'Keywords': note['keyword']
            }
            return jsonify(n)
    else:
        return Response('no note with that title', status=404)


@app.route('/getNoteWithKeyword/<string:keyword>', methods=['GET'])
def getNoteKeyWord(keyword):
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    if keyword == None:
        return Response("Bad request", status=500)

    notes = Note.find({'keyword': keyword, 'user': logedinUser['_id']}).sort(
        'createdAt', pymongo.DESCENDING)
    x = []
    for g in notes:
        g['_id'] = None
        g['user'] = logedinUser['username']
        x.append(g)

    if x == []:
        return Response("no notes", status=404)
    return jsonify(x)


@app.route('/editNote/<string:title>', methods=['PATCH'])
def editNote(title):
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    print(title)
    if title == None:
        return Response("Bad request", status=400)
    data = None

    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400)

    if data == None:
        return Response("bad request", status=400)

    note = Note.find_one({'title': title, 'user': logedinUser['_id']})

    if note == None:
        return Response("no note with that title", status=404)
    else:
        if note['user'] == logedinUser['_id'] and note['title'] == title:
            if 'title' in data:
                if data['title'] == "":
                    return Response('title is empty', status=400)
                else:
                    Note.update_one({'title': note['title']}, {
                                    '$set': {'title': data['title']}})
                    return Response("title updated!", status=202)

            if 'note' in data:
                if data['note'] == "":
                    return Response('note is empty', status=400)
                else:
                    Note.update_one({'note': note['note']}, {
                                    '$set': {'note': data['note']}})
                    return Response("note updated!", status=202)

            if 'keyword' in data:
                if data['keyword'] == "":
                    return Response('keyword is empty', status=400)
                else:
                    Note.update_one({'keyword': note['keyword']}, {
                                    '$set': {'keyword': data['keyword']}})
                    return Response("keyword updated!", status=202)
            else:
                return Response("wrong data", status=400)


@app.route('/deleteNote/<string:title>', methods=['DELETE'])
def deleteNote(title):
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)

    note = Note.find_one({'title': title, 'user': logedinUser['_id']})
    if note == None:
        return Response("no note with that title", status=404)
    else:
        if note['user'] == logedinUser['_id'] and note['title'] == title:
            Note.delete_one({'title': note['title']})
            return Response("note deleted!", status=200)


@app.route('/getAllNotes/<string:order>', methods=['GET'])
def getAllNotes(order):
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    if order == 'asc':
        notes = Note.find({'user': logedinUser['_id']}).sort(
            'createdAt', pymongo.ASCENDING)
        x = []
        for g in notes:
            g['_id'] = None
            g['user'] = logedinUser['username']
            x.append(g)

        if x == []:
            return Response("no notes", status=404)
        return jsonify(x)
    if order == 'des':
        notes = Note.find({'user': logedinUser['_id']}).sort(
            'createdAt', pymongo.DESCENDING)
        x = []
        for g in notes:
            g['_id'] = None
            g['user'] = logedinUser['username']
            x.append(g)

        if x == []:
            return Response("no notes", status=404)
        return jsonify(x)
    """return Response('you need to use the keywords "asc" or "des"', status=400)"""


@app.route('/deleteAccount/<string:username>', methods=['DELETE'])
def deleteAccount(username):
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)

    u = User.find_one({'username': username})
    if u == None:
        return Response("No user!!", status=404)
    if logedinUser['username'] == u['username']:
        Note.delete_many({'user': logedinUser['_id']})
        User.delete_one({'username': logedinUser['username']})

        return Response("You deleted your account!!", status=200)
    else:
        return Response("This is another user!!", status=405)


@app.route('/logout', methods=['GET'])
def logout():

    global logedin
    global logedinUser
    print(logedin)
    print(logedinUser)
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    logedin = 0
    logedinUser = None
    print(logedin)
    print(logedinUser)
    return Response("loged out!!", status=200)


@app.route('/newAdmin', methods=['POST'])
def newAdmin():
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    if logedinUser['role'] == 'admin':
        data = None

        try:
            data = json.loads(request.data)
        except Exception as e:
            return Response("bad json content", status=400,)

        if data == None:
            return Response("bad request", status=400)

        if User.count_documents({'email': data['email']}) == 0:

            admin = {
                'name': data['name'],
                'email': data['email'],
                'password': data['password'],
                'role': 'admin',
                'changedPass': 'no'
            }
            User.insert_one(admin)
            return Response("Admin successfully registered!!", status=201)

        else:
            return Response("email is used, try another one", status=200)
    else:
        return Response('This is for admins only!!', status=405)


@app.route('/changepassA', methods=['PATCH'])
def changepassA():
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    data = None

    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content", status=400)

    if data == None:
        return Response("bad request", status=400)
    
    if 'password' not in data:
        return Response('wrong data', status= 400)
    
    if logedinUser['role'] == 'admin':
        User.update_one({'email': logedinUser['email']}, {
                        '$set': {'password': data['password'], 'changedPass': 'yes'}})
        return Response('Pass changed!!', status=200)
    else:
        return Response('go back', status=405)
@app.route('/deleteUser/<string:username>', methods=['DELETE'])
def deleteUser(username):
    global logedin, logedinUser
    if logedin == 0 or logedinUser == None:
        return Response("login first!!", status=404)
    if logedinUser['role'] != 'admin':
        return Response('this is for admins only',status=405)
    
    user = User.find_one({'username': username})
    if user == None:
        return Response("No user!!", status=404)
    else:
        Note.delete_many({'user': user['_id']})
        User.delete_one({'username': user['username']})
        return Response('user deleted!!', status=200)

        return Response("You deleted your account!!", status=200)
if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)

    
    
    
    
    
    
    
    
    
    
    
    
    
    
