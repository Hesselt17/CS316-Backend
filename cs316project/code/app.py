from flask import Flask, request,jsonify
# from flask_restful import Resource, Api # only needed if doing class-based routing
import uuid

from sqlalchemy import *

# these are for authentication, not sure if will still be using:
# from flask_jwt import JWT, jwt_required
# from .security import authenticate, identity


# connect to db
engine = create_engine('postgresql://postgres:cs316@vcm-17053.vm.duke.edu:5432/userdesign', echo=True) # if this doesn't work, try: 'postgresql+psycopg2://michaela:cs316@vcm-17053.vm.duke.edu:5432/userdesign'
connection = engine.connect()
metadata = MetaData()

# Init app
app = Flask(__name__)
app.secret_key = 'julia' # what is this used for?
# api = Api(app)

# Init jwt object for authentication
# jwt = JWT(app, authenticate, identity)


# loading UserInfo relation into Table object called UserInfo
UserInfo = Table('userinfo', metadata, autoload=True, autoload_with=engine)  # Table(table_name, metadata, autoload=True, autoload_with=engine)


@app.route('/users', methods=['GET', 'POST'])
def get_users():
    # returns entire UserInfo relation (i.e. select * from UserInfo)
    if request.method == 'GET': # not sure if this is needed
        users = select([UserInfo])
        query = connection.execute(users)
        result = query.fetchall()
        return jsonify({'result': [dict(row) for row in result]})

    # adds new user to UserInfo. Assign userid to user
    if request.method == 'POST':
        data = request.get_json()
        unique_id = int(uuid.uuid4())  # made this an int (default is class uuid.UUID)
        new_user = insert(UserInfo).values(uid=20, name=data['name'], password=data['password'], email=data['email'],
                                           bio=data['bio'], score=data['score'], wherelive=data['wherelive'])
        connection.execute(new_user)
        return {'message': 'A profile for {} was created with this email: {}'.format(data['name'], data['email'])}


@app.route('/users/<int:uid>', methods=['GET', 'PUT', 'DELETE'])
def get_single_user(uid):
    # returns user row
    if request.method == 'GET':
        user = select([UserInfo]).where(
            UserInfo.columns.uid == uid)
        query = connection.execute(user)
        result = query.fetchone()
        return jsonify({'result': dict(result)})

    # updates any fields of user info
    if request.method == 'PUT':
        data = request.get_json()
        query = update(UserInfo).values(name=data['name'], password=data['password'], email=data['email'], bio=data['bio'], score=data['score'], wherelive=data['wherelive']).where(UserInfo.columns.uid == uid)
        connection.execute(query)
        return {'message': 'User information has been updated.'}

    # deletes user from UserInfo
    if request.method == 'DELETE':
        query = delete(UserInfo).where(UserInfo.columns.uid == uid)
        connection.execute(query)
        return {'message': 'User has been deleted.'}


if __name__ == '__main__':
    app.run(debug=True)