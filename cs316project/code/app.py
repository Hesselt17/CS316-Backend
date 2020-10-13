from flask import Flask, request, jsonify
# from flask_restful import Resource, Api # only needed if doing class-based routing
import uuid

from sqlalchemy import *

from flask_cors import CORS


# connect to db
engine = create_engine('postgresql://postgres:cs316@vcm-17053.vm.duke.edu:5432/userdesign', echo=True) # if this doesn't work, try: 'postgresql+psycopg2://michaela:cs316@vcm-17053.vm.duke.edu:5432/userdesign'
connection = engine.connect()
metadata = MetaData()

# Init app
app = Flask(__name__)
cors = CORS(app)  # This is what allows for this backend to enable CORS (webbrowser blocking loading data)
app.secret_key = 'julia'  # what is this used for?
# api = Api(app)


# loading relations
UserInfo = Table('userinfo', metadata, autoload=True, autoload_with=engine)
Design = Table('design', metadata, autoload=True, autoload_with=engine)
Room = Table('room', metadata, autoload=True, autoload_with=engine)
Diy = Table('diy', metadata, autoload=True, autoload_with=engine)
Favorites = Table('favorites', metadata, autoload=True, autoload_with=engine)
Reviews = Table('reviews', metadata, autoload=True, autoload_with=engine)


""" USER APIS"""
@app.route('/users', methods=['GET', 'POST'])
def get_users():
    # returns entire UserInfo relation (i.e. select * from UserInfo)
    if request.method == 'GET':  # not sure if this is needed
        users = select([UserInfo])
        query = connection.execute(users)
        result = query.fetchall()
        return jsonify({'result': [dict(row) for row in result]})

    # adds new user to UserInfo. Assign userid to user
    if request.method == 'POST':
        data = request.get_json()
        unique_id = int(uuid.uuid4())  # made this an int (default is class uuid.UUID)
        new_user = insert(UserInfo).values(uid=unique_id, name=data['name'], password=data['password'], email=data['email'],
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


""" ROOM APIS"""
@app.route('/rooms', methods=['GET', 'POST'])
def get_rooms():

    if request.method == 'GET':
        rooms = select([Room, Design]).where(Room.columns.designid == Design.columns.designid)
        query = connection.execute(rooms)
        result = query.fetchall()
        return jsonify({'result': [dict(row) for row in result]})

    if request.method == 'POST':
        data = request.get_json()
        design_id = int(uuid.uuid4())

        # create design id and add to Design relation
        query1 = insert(Design).values(designid=design_id, style=data['style'], caption=data['caption'], dateposted=data['dateposted'])
        connection.execute(query1)

        # create new room, add to Room and give design ID
        query2 = insert(Room).values(designid=design_id, occupancy=data['occupancy'], building=data['building'])
        connection.execute(query2)
        return {'message': 'New room has been added.'}


@app.route('/rooms/designid', methods=['GET', 'PUT', 'DELETE'])
def get_single_room(designid):

    if request.method == 'GET':
        room = select([Room, Design]).where(and_(Room.columns.designid == Design.columns.designid, Room.columns.designid == designid))
        query = connection.execute(room)
        result = query.fetchone()
        return jsonify({'result': dict(result)})

    if request.method == 'PUT':
        data = request.get_json()

        # update Design relation with new info
        query1 = update(Design).values(style=data['style'], caption=data['caption'], dateposted=data['dateposted']).where(Design.columns.designid == designid)
        connection.execute(query1)

        # update Room relation with new info
        query2 = update(Room).values(occupancy=data['occupancy'], building=data['building']).where(Room.columns.designid == designid)
        connection.execute(query2)

    if request.method == 'DELETE':
        query1 = delete(Design).where(Design.columns.designid == designid)
        connection.execute(query1)

        query2 = delete(Room).where(Room.columns.designid == designid)
        connection.execute(query2)

        return {'message': 'Design has been deleted.'}


""" DIY APIS"""
@app.route('/diy', methods=['GET', 'POST'])
def get_diy():
    if request.method == 'GET':
        diys = select([Diy, Design]).where(Diy.columns.designid == Design.columns.designid)
        query = connection.execute(diys)
        result = query.fetchall()
        return jsonify({'result': [dict(row) for row in result]})

    if request.method == 'POST':
        data = request.get_json()
        design_id = int(uuid.uuid4())

        # create design id and add to Design relation
        query1 = insert(Design).values(designid=design_id, style=data['style'], caption=data['caption'],
                                       dateposted=data['dateposted'])
        connection.execute(query1)

        # create new room, add to Room and give design ID
        query2 = insert(Diy).values(designid=design_id, score=data['score'], timetakes=data['timetakes'], link=data['link'], materials=data['materials'], title=data['title'], instructions=data['instructions'])
        connection.execute(query2)
        return {'message': 'New DIY has been added.'}


@app.route('/diy/designid', methods=['GET', 'PUT', 'DELETE'])
def get_single_diy():
    pass


""" FAVORITES APIS"""
@app.route('/favorites', methods=['GET', 'PUT', 'DELETE'])
def get_favorites():
    pass


@app.route('/favorites/userid', methods=['GET', 'PUT', 'DELETE'])
def get_single_favorite():
    pass


""" REVIEWS APIS"""
@app.route('/reviews', methods=['GET'])
def get_reviews():
    if request.method == 'GET':
        reviews = select([Reviews])  # do we ever need the entire list of reviews?
        query = connection.execute(reviews)
        result = query.fetchall()
        return jsonify({'result': [dict(row) for row in result]})


@app.route('/reviews/designid', methods=['GET', 'PUT', 'DELETE'])
def get_single_review():
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)  # alternatively -$ flask run --host=0.0.0.0

