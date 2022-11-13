import ibm_db as db
from flask import Flask, render_template, request, redirect, session, abort
from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
import os
import pathlib
import requests
import json
import base64


from clarifai_setup import (
    DOG_IMAGE_URL,
    GENERAL_MODEL_ID,
    NON_EXISTING_IMAGE_URL,
    RED_TRUCK_IMAGE_FILE_PATH,
    both_channels,
    metadata,
    raise_on_failure,
    post_model_outputs_and_maybe_allow_retries,
)

from ibm_bucket_integration import (
  get_bucket_contents,
  get_item,
  multi_part_upload
)

from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2
from ibm_botocore.client import Config,ClientError
import ibm_boto3

def test_predict_image_url():
    stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())

    req = service_pb2.PostModelOutputsRequest(
        model_id=GENERAL_MODEL_ID,
        inputs=[
            resources_pb2.Input(
                data=resources_pb2.Data(image=resources_pb2.Image(url=DOG_IMAGE_URL))
            )
        ],
    )

    response = post_model_outputs_and_maybe_allow_retries(stub, req, metadata=metadata())
    print(response)
    raise_on_failure(response)

    assert len(response.outputs[0].data.concepts) > 0

app = Flask(__name__)

DRIVER="{IBM DB2 ODBC DRIVER}"
HOSTNAME = "b70af05b-76e4-4bca-a1f5-23dbb4c6a74e.c1ogj3sd0tgtu0lqde00.databases.appdomain.cloud"
USERNAME = "lhw31626"
PASSWORD = "kNBpZuKRbSyEzwg5"
PORT_NUMBER = "32716"
DATABASE_NAME = "bludb"


SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY

connection_string = "DATABASE={1};HOSTNAME={2};PORT={3};PROTOCOL=TCPIP;Security=SSL;UID={4};PWD={5};".format( "",DATABASE_NAME, HOSTNAME, PORT_NUMBER, USERNAME, PASSWORD)
conn = db.connect(connection_string,"","")
 
server = db.server_info(conn)
print("hii",server.DBMS_NAME)
print("hii",server.DB_NAME) 

SIGN_UP_PAGE_URL = '/'
LOG_IN_PAGE_URL = '/login'
HOME_PAGE_URL = '/home'
GOOGLE_LOGIN_PAGE_URL = '/google_login'

def execute_sql(statement, **params):
    global conn
    stmt = db.prepare(conn, statement)
    
    param_id = 1
    for key, val in params.items():
        db.bind_param(stmt, param_id, val)
        param_id += 1
    
    result = ''
    try:
        db.execute(stmt)
        result = db.fetch_assoc(stmt)
    except:
        pass
    
    return result

create_table = "CREATE TABLE IF NOT EXISTS user(email varchar(30), username varchar(30), password varchar(30), contact varchar(12))"
execute_sql(statement=create_table)


@app.route(SIGN_UP_PAGE_URL, methods=['GET', 'POST'])
def signup():
    msg = ''
    if session.get('user'):
        return redirect(HOME_PAGE_URL)
    if request.method == 'POST':
        user = request.form['user']
        email = request.form['email']
        password = request.form['password']
        contact = request.form['password']
        print(user,email,password)
        duplicate_check = "SELECT * FROM user WHERE username=?"
        account = execute_sql(statement=duplicate_check, user=user)
        
        if account:
            msg = "There is already an account with this username!"
        else:
            insert_query = "INSERT INTO user values(?, ?, ?, ?)"
            execute_sql(statement=insert_query, email=email, user=user, password=password, contact=contact)
            return redirect(LOG_IN_PAGE_URL)
    return render_template('signup.html', msg=msg)

@app.route(LOG_IN_PAGE_URL, methods=['GET', 'POST'])
def login():
    msg = ''
    if session.get('user'):
        return redirect(HOME_PAGE_URL)

    if request.method == "POST":
        user = request.form['user']
        password = request.form['password']
        print(user,password)
        duplicate_check = "SELECT * FROM user WHERE username=?"
        account = execute_sql(statement=duplicate_check, user=user)
        print(account)
        if account and account['PASSWORD'] == password:
            session['user'] = user
            return redirect(HOME_PAGE_URL)
        elif account and account['PASSWORD'] != password:
            msg = 'Invalid Password!'
        else:
            msg = "Invalid Username!"
            
    return render_template('signin.html', msg=msg)
        
@app.route(HOME_PAGE_URL, methods=['GET', 'POST'])
def homepage():
    if request.method == "POST":
        print(request.files['file'].filename)
        stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())
        result=multi_part_upload("cloud-object-storage-6y-cos-standard-m3z",request.files['file'].filename,request.files['file'])
        print(result)
        req = service_pb2.PostModelOutputsRequest(
        model_id=GENERAL_MODEL_ID,
        inputs=[resources_pb2.Input(data=resources_pb2.Data(image=resources_pb2.Image(url="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSq9PtFcLCRnufDPFMqiIvSrI0k5vPwLiWE4Q&usqp=CAU")))],)
        response = post_model_outputs_and_maybe_allow_retries(stub, req, metadata=metadata())
        print(response)
        raise_on_failure(response)
        assert len(response.outputs[0].data.concepts) > 0
        return response

    if not session.get('user'):
        return redirect(LOG_IN_PAGE_URL)
    return render_template('homepage.html', user=session.get('user'))
    


if __name__ == '__main__':
    app.run(debug=True)