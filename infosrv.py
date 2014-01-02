#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

from flask import Flask, request, send_file
from pymongo import *
import datetime
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
DB_FILE_COLLECTION = 'images'

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

        # #Getting from client image form field
        # request_file1 = request.files[REMOTE_FIELD_IMAGE1]
        # ## get extension name
        # main_name, ext_name = os.path.splitext(request_file1.filename)
        # # now datetime as new file name
        # new_filename = secure_filename(nowStr())+ext_name
        # new_fullpath = os.path.join(UPLOAD_FOLDER, new_filename)
        # ## Save to server location
        # log.write('before write file on server: '+new_fullpath+'\r\n')
        # request_file1.save(new_fullpath)
        # log.write('after write file on server'+new_fullpath+'\r\n')

        #Write data into db
        ## db operation
        client = MongoClient(DB_IP, DB_PORT)
        db = client[DB_NAME]
        #Binary Data

        #Text Data
        collection = db[DB_COLLECTION]
        post_json = {}
        ## Traversal all items in ImmutableMultiDict. Convert into json
        for item in request_form:
            ## log every key&value in ImmutableMultiDict object
            item_json = {str(item):str(request_form[item])}
            post_json.update(item_json)
        ## add image id
        #post_json.update({'image': fileid})
        log.write('post json: '+str(post_json)+'\r\n')
        ## Save form data to db
        log.write('before save to db...\r\n')
        ret_id = collection.save(post_json)
        log.write('after save to db:'+str(ret_id)+'\r\n')
        client.close()

        log.close()
    else:

        log.close()
        return ""+request.method


if __name__ == '__main__':
    app.run('192.168.1.109')
