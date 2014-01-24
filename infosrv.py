#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys

from flask import Flask, request, send_file
from pymongo import *
import datetime
import gridfs
import bson.json_util
import json
import hashlib
import base64

from werkzeug.utils import secure_filename
app = Flask(__name__)

#common variable
APP_PATH = os.path.dirname(os.path.realpath(__file__))
log_file = APP_PATH+'/infosrv_log.txt'
UPLOAD_FOLDER = APP_PATH+'/Uploads'
DOWNLOAD_FOLDER = APP_PATH+'/Downloads'

#DB common variable
DB_IP = '192.168.1.101'
DB_PORT = 27017
DB_NAME = 'infosrv'
DB_COLLECTION = 'posts'
DB_COLLECTION_YEAR = 'items_year'
DB_COLLECTION_FIELD = 'items_field'
DB_COLLECTION_CLASS = 'items_class'
DB_COLLECTION_TARGET = 'items_target'
DB_COLLECTION_CREATOR = 'items_creator'
DB_COLLECTION_Users = 'users'

GRID_FS_FILE = "images"

#Remote Data Fields Name
REMOTE_FIELD_IMAGE1 = 'info_img1'

#hash key field name
#HASH_KEY_NAME = 'password'

#mongodb account infomation keys name
ACCOUNT_KEY_NAME = 'name'
ACCOUNT_KEY_PASSWORD = 'password'
ACCOUNT_KEY_HASH = 'hash'


#====================Common======================

#produce datetime string
def nowStr():
    yy = str(datetime.datetime.now().year)
    mm = str(datetime.datetime.now().month)
    dd = str(datetime.datetime.now().day)
    hh = str(datetime.datetime.now().hour)
    mins = str(datetime.datetime.now().minute)
    sec = str(datetime.datetime.now().second)
    micsec = str(datetime.datetime.now().microsecond)
    return yy+'_'+mm+'_'+dd+'_'+hh+'_'+mins+'_'+sec+'_'+micsec


#====================Testing======================

#For http connection testing
@app.route('/test/hello/', methods=['GET'])
def test_hello():
    return 'Hello World!'


#
@app.route('/test/path/', methods=['GET'])
def test_path():
    s = 'Log file:'+log_file+' Upload folder: '+UPLOAD_FOLDER+' Download folder:'+DOWNLOAD_FOLDER
    return s


#====================Data using======================

#Post FORM data to db (include image)
@app.route('/api/post/', methods=['GET', 'POST'])
def post_form_data():
    #log message
    log = open(log_file, 'a+')
    log.write('>>>Client contact /api/post/...'+str(datetime.datetime.now())+'\r\n')

    if request.method == 'POST':
        log.write('request method POST\r\n')
        ##write request
        request_data = request.data
        request_form = request.form
        log.write('request_form: '+str(request.form)+'\r\n')
        #Getting from client image form field
        request_file1 = request.files[REMOTE_FIELD_IMAGE1]
        log.write('request_file1: '+request_file1.filename+'\r\n')
        # get extension name
        main_name, ext_name = os.path.splitext(request_file1.filename)
        # now datetime as new file name
        new_filename = secure_filename(nowStr())+ext_name
        new_fullpath = os.path.join(UPLOAD_FOLDER, new_filename)
        ## Save to server location
        log.write('before write file on server: '+new_fullpath+'\r\n')
        request_file1.save(new_fullpath)
        log.write('after write file on server'+new_fullpath+'\r\n')

        #Write data into db
        ## db operation
        client = MongoClient(DB_IP, DB_PORT)
        db = client[DB_NAME]

        #Binary Data
        ## Store file to db (gridfs)
        fsdb = gridfs.GridFS(db, collection=GRID_FS_FILE)
        log.write('before store file into db...\r\n')
        outputdata = open(new_fullpath, 'rb')
        thedata = outputdata.read()
        fileid = fsdb.put(thedata, filename=new_filename, extname=ext_name)
        log.write('fileid: '+str(fileid)+'\r\n')
        outputdata.close()

        #Text Data
        collection = db[DB_COLLECTION]
        post_json = {}
        ## Traversal all items in ImmutableMultiDict. Convert into json
        for item in request_form:
            ## log every key&value in ImmutableMultiDict object
            item_json = {str(item):str(request_form[item])}
            post_json.update(item_json)
        ## add image id
        post_json.update({'image': fileid})
        log.write('post json: '+str(post_json)+'\r\n')
        ## Save form data to db
        log.write('before save to db...\r\n')
        ret_id = collection.save(post_json)
        log.write('after save to db:'+str(ret_id)+'\r\n')
        client.close()

        log.close()
        return "Data Saved!"
    else:

        log.close()
        return request.method


## Get ListItems
@app.route('/api/items/<item_class>/', methods=['GET', 'POST'])
def get_list_items(item_class):
    #Open log message file
    log = open(log_file, 'a+')
    log.write('\r\n>>>>>>>>>>>> Client contact /api/items/<'+item_class+'/>...'+str(datetime.datetime.now())+'\r\n')
    ## db operation
    client = MongoClient(DB_IP, DB_PORT)
    db = client[DB_NAME]
    #Judgment query parameters
    if item_class == "year":
        # Query year items
        collection = db[DB_COLLECTION_YEAR]
    elif item_class == "target":
        # Query target items
        collection = db[DB_COLLECTION_TARGET]
    elif item_class == "field":
        # Query field items
        collection = db[DB_COLLECTION_FIELD]
    elif item_class == "class":
        # Query class items
        collection = db[DB_COLLECTION_CLASS]
    elif item_class == "creator":
        # Query creator items
        collection = db[DB_COLLECTION_CREATOR]
    else:
        #return item_class
        return 'Your parameter '+item_class+' are not in the range!'

    # GET or POST or Other
    if request.method == 'GET':
        posts = collection.find()
        log.write('To find documents from %s documents count: %s \r\n' % (collection.name, str(posts.count())))
        post_json = {}
        for idx, iDoc in enumerate(posts):
            iDoc_json = bson.json_util.dumps(iDoc, ensure_ascii=False)
            post_json.update({idx: iDoc_json})
        #jsonarray = json.dumps(post_json, ensure_ascii=False)
        log.write("Post data to json:"+str(post_json)+"\r\n")
        client.close()
        log.close()
        #return bson.json_util.dumps(post_json, ensure_ascii=False)
        return bson.json_util.dumps(post_json)
    elif request.method == 'POST':
        # Client post data
        request_data = request.data
        if not request_data:
            log.write('Request data fail!\r\n')
            log.close()
            return 'None Data'
        data = json.loads(str(request_data, encoding='utf-8'))
        log.write('Request POST Data:'+str(data)+'\r\n')
        ## Traversal all items in ImmutableMultiDict. Convert into json
        post_json = {}
        for item in data:
            ## log every key&value in ImmutableMultiDict object
            item_json = {str(item):str(data[item])}
            post_json.update(item_json)
        log.write('Post data to json:'+str(post_json)+'\r\n')
        ## Save form data to db
        obj_id = collection.save(post_json)
        log.write('Request POST Data save OK.\r\n')

        client.close()
        log.close()
        return 'POST OK.'
    else:
        client.close()
        log.close()
        return request.method


## Get all data
@app.route('/api/query/all/', methods=['GET'])
def query_all():
    log = open(log_file, 'a+')
    log.write('>>>Client contact /api/query/all/...'+str(datetime.datetime.now())+'\r\n')

    ## db operation
    client = MongoClient(DB_IP, DB_PORT)
    db = client[DB_NAME]
    collection = db[DB_COLLECTION]
    posts = collection.find()
    log.write('Find all data count: %s \r\n' % str(posts.count()))
    post_json = {}
    for idx, iDoc in enumerate(posts):
        iDoc_json = bson.json_util.dumps(iDoc, ensure_ascii=False)
        post_json.update({idx: iDoc_json})
    jsonarray = bson.json_util.dumps(post_json, ensure_ascii=False)
    #log.write('%s' % str(jsonarray))
    log.write('%s\r\n' % post_json)
    log.close()
    return bson.json_util.dumps(post_json, ensure_ascii=False)


## Get file
@app.route('/api/file/<fileid>', methods=['GET'])
def query_file(fileid):
    log = open(log_file, 'a+')
    log.write('>>>Client contact /api/file/<fileid>...'+str(datetime.datetime.now())+'\r\n')

    client = MongoClient(DB_IP, DB_PORT)
    db = client[DB_NAME]
    fs = gridfs.GridFS(db, GRID_FS_FILE)
    ## pymongo get file
    outputdata = fs.get(bson.json_util.ObjectId(fileid))

    thedata = outputdata.read()
    save_full_path = os.path.join(DOWNLOAD_FOLDER, str(fileid)+'.jpg')
    log.write(save_full_path+'\r\n')
    # write definition
    outputfile = open(save_full_path, 'wb')
    #save to disk
    outputfile.write(thedata)

    #outputdata.close()
    #outputfile.close()
    client.close()
    log.close()

    #return str(str(fileid)+'.jpg')
    return send_file(save_full_path, mimetype='image/jpg')


#====================security validate======================


## Add User
@app.route('/api/user/add/', methods=['POST'])
def user_add():
    log = open(log_file, 'a+')
    log.write('>>>Client contact /api/user/add/...'+str(datetime.datetime.now())+'\r\n')
    if request.method == 'POST':
        log.write('request method POST\r\n')
        ##write request
        request_data = request.data
        request_form = request.form
        data = json.loads(str(request_data, encoding='utf-8'))
        #Write data into db
        #db operation
        client = MongoClient(DB_IP, DB_PORT)
        db = client[DB_NAME]
        #Text Data
        collection = db[DB_COLLECTION_Users]
        post_json = {}
        ## Traversal all items in ImmutableMultiDict. Convert into json
        encrypt_Source = ''
        for item in data:
            ## log every key&value in ImmutableMultiDict object
            item_json = {str(item):str(data[item])}
            post_json.update(item_json)
            #Using password as hash key
            if str(item)==ACCOUNT_KEY_PASSWORD:
                encrypt_Source = data[item]
        log.write('encrypt_Source:'+encrypt_Source+'\r\n')
        hash_object = hashlib.sha256(str.encode(encrypt_Source))
        hex_dig = hash_object.hexdigest()
        post_json.update({'hash':hex_dig})
        log.write('post json: '+str(post_json)+'\r\n')
        ## Save form data to db
        log.write('before save to db...\r\n')
        ret_id = collection.save(post_json)
        log.write('after save to db:'+str(ret_id)+'\r\n')
        client.close()

        log.close()
        return "Data Saved:"#+str(ret_id)
    else:
        log.close()
        return request.method


## Query User
@app.route('/api/user/check/<hash_code>', methods=['GET'])
def user_check(hash_code):
    log = open(log_file, 'a+')
    log.write('>>>Client contact /api/user/check/'+hash_code+"..."+str(datetime.datetime.now())+'\r\n')
    #decode base64 encoding
    try:
        log.write('Decoding...'+hash_code+'\r\n')
        decode_data = base64.b64decode(hash_code)
        #convert to utf-8
        decode_data = decode_data.decode("utf-8")
    except:
        log.write('Decoding fail...\r\n')
        log.close()
        return ""
    ## db operation
    try:
        client = MongoClient(DB_IP, DB_PORT)
        db = client[DB_NAME]
        collection = db[DB_COLLECTION_Users]
        posts = collection.find()
        log.write('Find all data count: %s \r\n' % str(posts.count()))
    except:
        log.write('DB operation fail...\r\n')
        log.close()
        return ""
    post_json = {}
    for idx, iDoc in enumerate(posts):
        #mongodb doc dump to string
        doc_json = bson.json_util.dumps(iDoc, ensure_ascii=False)
        #string convert to json
        doc_json = json.loads(doc_json)
        #To get key value
        val_username = doc_json[ACCOUNT_KEY_NAME]
        val_password = doc_json[ACCOUNT_KEY_PASSWORD]
        val_hash = doc_json[ACCOUNT_KEY_HASH]
        if val_hash == decode_data:
            log.write('Find match hash code: '+decode_data + ' , return username: '+ val_username + '\r\n')
            log.close()
            client.close()
            #return match result
            return val_username
    #no match user hash
    log.close()
    client.close()
    #return bson.json_util.dumps(post_json, ensure_ascii=False)
    return ""


if __name__ == '__main__':
    app.run('192.168.1.109')
