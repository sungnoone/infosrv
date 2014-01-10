#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from flask import Flask, request, send_file
from pymongo import *
import datetime
import gridfs
import bson.json_util
import json
from werkzeug.utils import secure_filename
app = Flask(__name__)

#common variable
log_file = '/tmp/infosrv_log.txt'
UPLOAD_FOLDER = '/tmp/Uploads'
DOWNLOAD_FOLDER = '/tmp/Downloads'

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

GRID_FS_FILE = "images"

#Remote Data Fields Name
REMOTE_FIELD_IMAGE1 = 'info_img1'


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


#For http connection testing
@app.route('/')
def hello_world():
    return 'Hello World!'


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
    log.write('%s' % post_json)
    log.close()
    return bson.json_util.dumps(post_json, ensure_ascii=False)


## Get file
@app.route('/api/file/<fileid>', methods=['GET'])
def test4(fileid):
    log = open(log_file, 'a+')
    log.write('>>>Client contact /api/srv4/<fileid>...'+str(datetime.datetime.now())+'\r\n')

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


if __name__ == '__main__':
    app.run('192.168.1.109')
