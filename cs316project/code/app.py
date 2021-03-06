from flask import Flask, request, jsonify
import random
from sqlalchemy import *
from flask_cors import CORS


# connect to db
engine = create_engine('postgresql://postgres:cs316@vcm-17053.vm.duke.edu:5432/userdesign', echo=True) # if this doesn't work, try: 'postgresql+psycopg2://michaela:cs316@vcm-17053.vm.duke.edu:5432/userdesign'
connection = engine.connect()
metadata = MetaData()

# Init app
app = Flask(__name__)
cors = CORS(app)  # This is what allows for this backend to enable CORS (webbrowser blocking loading data)


# loading relations
UserInfo = Table('userinfo', metadata, autoload=True, autoload_with=engine)
Room = Table('room', metadata, autoload=True, autoload_with=engine)
Diy = Table('diy', metadata, autoload=True, autoload_with=engine)
Likes = Table('favorites', metadata, autoload=True, autoload_with=engine)
Reviews = Table('reviews', metadata, autoload=True, autoload_with=engine)
CreateDesign = Table('createdesign', metadata, autoload=True, autoload_with=engine)


""" USER APIS"""
@app.route('/users', methods=['GET', 'POST'])
def get_users():
    # returns entire UserInfo relation (i.e. select * from UserInfo)
    if request.method == 'GET':
        users = select([UserInfo])
        query = connection.execute(users)
        result = query.fetchall()
        return jsonify({'result': [dict(row) for row in result]})

    # adds new user to UserInfo. Assign userid to user
    if request.method == 'POST':
        data = request.get_json()
        unique_id = random.randrange(20000, 100000)
        new_user = insert(UserInfo).values(uid=unique_id, name=data['name'], password=data['password'], email=data['email'],
                                           bio=data['bio'], score=data['score'], wherelive=data['wherelive'], avatar=data['avatar'], netid=data["netid"])
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
        if result:
            return jsonify({'result': dict(result)})
        else:
            return jsonify({'message': "User does not exist."})

    # updates any fields of user info
    if request.method == 'PUT':
        data = request.get_json()
        query = update(UserInfo).values(name=data['name'], password=data['password'], email=data['email'], bio=data['bio'], score=data['score'], wherelive=data['wherelive'], avatar=data['avatar'], netid=data['netid']).where(UserInfo.columns.uid == uid)
        connection.execute(query)
        return {'message': 'User information has been updated.'}

    # deletes user from UserInfo and all designs, reviews and favorites associated with them.
    if request.method == 'DELETE':
        # store designid & type to use when deleting from room, diy and createdesign
        designid = select([CreateDesign.columns.designid, CreateDesign.columns.typedesign]).where(CreateDesign.columns.uid == uid)
        query = connection.execute(designid)
        result = query.fetchall()

        # delete user's reviews
        query1 = delete(Reviews).where(Reviews.columns.uid == uid)
        connection.execute(query1)

        # delete user's favorites
        query2 = delete(Likes).where(Likes.columns.uid == uid)
        connection.execute(query2)

        # delete user's diys and rooms
        for row in result:
            if row[1] == "diy":
                query3 = delete(Diy).where(Diy.columns.designid == row[0])
                connection.execute(query3)

            else:
                query4 = delete(Room).where(Room.columns.designid == row[0])
                connection.execute(query4)

        # delete user from creates
        query5 = delete(CreateDesign).where(CreateDesign.columns.uid == uid)
        connection.execute(query5)

        # delete user from UserInfo
        query6 = delete(UserInfo).where(UserInfo.columns.uid == uid)
        connection.execute(query6)

        return {'message': 'User has been deleted.'}


# same as above endpoint, but uses user's email as input instead of uid
@app.route('/users/<email>', methods=['GET', 'PUT'])
def get_single_user_email(email):
    # returns user row
    if request.method == 'GET':
        user = select([UserInfo]).where(
            UserInfo.columns.email == email)
        query = connection.execute(user)
        result = query.fetchone()
        if result:
            return jsonify({'result': dict(result)})
        else:
            return jsonify({'message': "User does not exist."})

    # updates any fields of user info
    if request.method == 'PUT':
        data = request.get_json()
        query = update(UserInfo).values(name=data['name'], password=data['password'], uid=data['uid'],
                                        bio=data['bio'], score=data['score'], wherelive=data['wherelive'],
                                        avatar=data['avatar'], netid=data['netid']).where(UserInfo.columns.email == email)
        connection.execute(query)
        return {'message': 'User information has been updated.'}


""" DESIGN APIS"""
@app.route('/designs', methods=['GET'])
def get_designs():
    # returns all attributes from createdesign table
    designs = select([CreateDesign.columns.uid, CreateDesign.columns.designid, CreateDesign.columns.photo, CreateDesign.columns.typedesign, CreateDesign.columns.dateposted, CreateDesign.columns.caption, CreateDesign.columns.style])  # currently not returning photo because byte not JSON serializable
    query = connection.execute(designs)
    result = query.fetchall()
    return jsonify({'result': [dict(row) for row in result]})


@app.route('/designs/<int:uid>', methods=['GET'])
def get_users_designs(uid):
    # returns all designIDs + attributes in CreateDesign relation associated with a user
    designs = select([CreateDesign]).where(CreateDesign.columns.uid == uid)
    query = connection.execute(designs)
    result = query.fetchall()

    return jsonify({'result': [dict(row) for row in result]})


"""EXPLORE PAGE API"""
@app.route('/explore', methods=['GET'])
# this method returns a number of randomly selected designs
def get_explore_page():
    offset = random.randint(2, 20)
    random_designs = select([CreateDesign, UserInfo.columns.name]).select_from(CreateDesign.join(UserInfo)).limit(20).offset(offset)
    query = connection.execute(random_designs)
    result = query.fetchall()

    return jsonify({'result': [dict(row) for row in result]})


""" ROOM APIS"""
@app.route('/rooms', methods=['GET', 'POST'])
def get_rooms():

    # returns all attributes from Room & CreateDesign for each design id
    if request.method == 'GET':
        rooms = select([Room.columns.building, Room.columns.occupancy, Room.columns.roomcheck, CreateDesign.columns.designid, CreateDesign.columns.caption, CreateDesign.columns.style, CreateDesign.columns.dateposted, CreateDesign.columns.uid]).where(Room.columns.designid == CreateDesign.columns.designid)
        query = connection.execute(rooms)
        result = query.fetchall()
        return jsonify({'result': [dict(row) for row in result]})

    # adds new room to both Room and CreateDesign table (to follow foreign key constraints)
    if request.method == 'POST':
        data = request.get_json() # needs to include the uid
        design_id = random.randrange(100001, 300000)

        # create design id and add to Design relation
        query1 = insert(CreateDesign).values(designid=design_id, style=data['style'], caption=data['caption'], dateposted=data['dateposted'], photo=data['photo'], uid=data['uid'], typedesign=data['roomcheck'])
        connection.execute(query1)

        # create new room, add to Room and give design ID
        query2 = insert(Room).values(designid=design_id, occupancy=data['occupancy'], building=data['building'], roomcheck=data['roomcheck'])
        connection.execute(query2)
        return {'message': 'New room has been added.'}


@app.route('/rooms/<int:designid>', methods=['GET', 'PUT', 'DELETE'])
def get_single_room(designid):

    # returns all attributes from Room and CreateDesign for a given designid
    if request.method == 'GET':
        test = select([CreateDesign.columns.style, CreateDesign.columns.photo, CreateDesign.columns.caption, CreateDesign.columns.dateposted, CreateDesign.columns.typedesign, CreateDesign.columns.uid, Room.columns.occupancy, Room.columns.building, Room.columns.roomcheck]).where(and_(CreateDesign.columns.designid == designid, Room.columns.designid == CreateDesign.columns.designid))
        query = connection.execute(test)
        result = query.fetchone()
        if result:
            return jsonify({'result': dict(result)})
        else:
            return jsonify({'message': "Room does not exist."})

    # updates attributes of a room for a given designid
    if request.method == 'PUT':
        data = request.get_json()

        # update CreateDesign relation with new info
        query1 = update(CreateDesign).values(style=data['style'], photo=data['photo'], caption=data['caption'], dateposted=data['dateposted'], typedesign=data['typedesign'], uid=data['uid']).where(CreateDesign.columns.designid == designid)
        connection.execute(query1)

        # update Room relation with new info
        query2 = update(Room).values(occupancy=data['occupancy'], building=data['building'], roomcheck=data['roomcheck']).where(Room.columns.designid == designid)
        connection.execute(query2)

        return jsonify({'message': "Room has been updated."})

    # deletes design
    if request.method == 'DELETE':
        query1 = delete(Room).where(Room.columns.designid == designid)
        connection.execute(query1)

        query2 = delete(Likes).where(Likes.columns.designid == designid)
        connection.execute(query2)

        query3 = delete(Reviews).where(Reviews.columns.designid == designid)
        connection.execute(query3)

        query4 = delete(CreateDesign).where(CreateDesign.columns.designid == designid)
        connection.execute(query4)

        return {'message': 'Room has been deleted.'}


""" DIY APIS"""
@app.route('/diy', methods=['GET', 'POST'])
def get_diys():
    # returns all attributes from Diy and CreateDesign table for every design id
    if request.method == 'GET':
        diys = select([Diy.columns.score, Diy.columns.designid, Diy.columns.timetakes, Diy.columns.link, Diy.columns.materials, Diy.columns.title, Diy.columns.instructions, Diy.columns.diycheck, CreateDesign.columns.uid, CreateDesign.columns.style, CreateDesign.columns.caption, CreateDesign.columns.dateposted, CreateDesign.columns.photo, CreateDesign.columns.typedesign]).where(Diy.columns.designid == CreateDesign.columns.designid)
        query = connection.execute(diys)
        result = query.fetchall()
        return jsonify({'result': [dict(row) for row in result]})

    # adds new Diy
    if request.method == 'POST':
        data = request.get_json()
        design_id = random.randrange(300001, 500000)

        # create design id and add to Design relation
        query1 = insert(CreateDesign).values(designid=design_id, style=data['style'], caption=data['caption'],
                                       dateposted=data['dateposted'], photo=data['photo'], uid=data['uid'], typedesign=data['diycheck'])
        connection.execute(query1)

        # create new room, add to Room and give design ID
        query3 = insert(Diy).values(designid=design_id, score=data['score'], timetakes=data['timetakes'], link=data['link'], materials=data['materials'], title=data['title'], instructions=data['instructions'], diycheck=data['diycheck'])
        connection.execute(query3)
        return {'message': 'New DIY has been added.'}


@app.route('/diy/<int:designid>', methods=['GET', 'PUT', 'DELETE'])
def get_single_diy(designid):
    # returns attributes from Diy and CreateDesign for given designid
    if request.method == 'GET':
        diy = select([Diy.columns.score, Diy.columns.timetakes, Diy.columns.link, Diy.columns.materials, Diy.columns.title, Diy.columns.instructions, Diy.columns.diycheck, CreateDesign.columns.uid, CreateDesign.columns.style, CreateDesign.columns.caption, CreateDesign.columns.dateposted, CreateDesign.columns.photo]).where(
            and_(Diy.columns.designid == CreateDesign.columns.designid, Diy.columns.designid == designid))
        query = connection.execute(diy)
        result = query.fetchone()
        if result:
            return jsonify({'result': dict(result)})
        else:
            return jsonify({'message': "Diy does not exist."})

    # updates all attributes of Diy
    if request.method == 'PUT':
        data = request.get_json()

        # update Design relation with new info
        query1 = update(CreateDesign).values(style=data['style'], caption=data['caption'],
                                       dateposted=data['dateposted'], photo=data['photo'], typedesign=data['diycheck']).where(CreateDesign.columns.designid == designid)
        connection.execute(query1)

        # update Diy relation with new info
        query2 = update(Diy).values(score=data['score'], timetakes=data['timetakes'], link=data['link'], diycheck=data['diycheck'], materials=data['materials'], title=data['title'], instructions=data['instructions']).where(
            Diy.columns.designid == designid)
        connection.execute(query2)
        return jsonify({'message': 'Diy updated.'})

    # deletes Diy
    if request.method == 'DELETE':

        query1 = delete(Diy).where(Diy.columns.designid == designid)
        connection.execute(query1)

        query2 = delete(Likes).where(Likes.columns.designid == designid)
        connection.execute(query2)

        query3 = delete(Reviews).where(Reviews.columns.designid == designid)
        connection.execute(query3)

        query4 = delete(CreateDesign).where(CreateDesign.columns.designid == designid)
        connection.execute(query4)

        return {'message': 'Diy has been deleted.'}


""" LIKES APIS"""
@app.route('/likes', methods=['GET', 'POST'])
def get_favorites():
    # returns all uid, designid
    if request.method == 'GET':
        likes = select([Likes])
        query = connection.execute(likes)
        result = query.fetchall()
        return jsonify({'result': [dict(row) for row in result]})

    # adds new like (enforces one like per user per design)
    if request.method == 'POST':
        data = request.get_json()
        check_like = select([Likes]).where(and_(Likes.columns.uid == data['uid'], Likes.columns.designid == data['designid']))
        check_result = connection.execute(check_like)

        # check that user has not already liked this design
        if check_result.first() is not None:
            return jsonify({'message': "User {} has already liked design {}".format(data['uid'], data['designid'])})

        else:
            new_like = insert(Likes).values(uid=data['uid'], designid=data['designid'])
            connection.execute(new_like)
            return jsonify({'message': 'New like has been added.'})


# given a userid, returns all designs that a user has liked
@app.route('/likes/users/<int:uid>', methods=['GET'])
def get_user_likes(uid):
    likes = select([Likes.columns.designid, CreateDesign.columns.uid, CreateDesign.columns.typedesign, CreateDesign.columns.dateposted, CreateDesign.columns.style, CreateDesign.columns.caption, CreateDesign.columns.photo]).where(and_(Likes.columns.uid == uid, Likes.columns.uid == CreateDesign.columns.uid))
    query = connection.execute(likes)
    result = query.fetchall()
    return jsonify({'result': [dict(row) for row in result]})


# given a designid, returns all users who have liked it
@app.route('/likes/designs/<int:designid>', methods=['GET'])
def get_design_likes(designid):
    likes = select([Likes.columns.uid]).where(Likes.columns.designid == designid)
    query = connection.execute(likes)
    result = query.fetchall()
    return jsonify({'result': [dict(row) for row in result]})


# given designid and uid, deletes like
@app.route('/likes/<int:designid>/<int:uid>', methods=['DELETE'])
def delete_like(designid, uid):
    delete_likes = delete(Likes).where(and_(Likes.columns.designid == designid, Likes.columns.uid == uid))
    connection.execute(delete_likes)

    return jsonify({'message': "User {} has unliked design {}".format(uid, designid)})


""" REVIEWS APIS"""
@app.route('/reviews', methods=['GET', 'POST'])
def get_reviews():
    # returns list of all reviews made
    if request.method == 'GET':
        reviews = select([Reviews])
        query = connection.execute(reviews)
        result = query.fetchall()
        return jsonify({'result': [dict(row) for row in result]})

    # adds new review (enforces one review per user per design)
    if request.method == 'POST':
        data = request.get_json()
        check = select([Reviews]).where(and_(Reviews.columns.uid == data['uid'], Reviews.columns.designid == data['designid']))
        check_review = connection.execute(check)

        if check_review.first() is not None:
            return jsonify({'message': "User {} has already reviewed design {}".format(data['uid'], data['designid'])})
        else:
            new_review = insert(Reviews).values(uid=data['uid'], designid=data['designid'], comment=data['comment'], rating=data['rating'])
            connection.execute(new_review)
            return jsonify({'message': 'New review has been added.'})


@app.route('/reviews/<int:designid>', methods=['GET', 'PUT'])
def get_single_review(designid):
    # returns all reviews of a given design id
    if request.method == 'GET':
        reviews = select([Reviews.columns.uid, Reviews.columns.comment, Reviews.columns.rating]).where(Reviews.columns.designid == designid)
        query = connection.execute(reviews)
        result = query.fetchall()
        return jsonify({'result': [dict(row) for row in result]})

    # updates a users review of given design id
    if request.method == 'PUT':
        data = request.get_json()
        query = update(Reviews).values(comment=data['comment'], rating=data['rating']).where(and_(Reviews.columns.designid == designid, Reviews.columns.uid == data['uid']))
        connection.execute(query)
        return jsonify({'message': 'Review has been updated.'})


# deletes review
@app.route('/reviews/<int:designid>/<int:uid>', methods=['DELETE'])
def delete_review(designid, uid):
    delete_rev = delete(Reviews).where(and_(Reviews.columns.designid == designid, Reviews.columns.uid == uid))
    connection.execute(delete_rev)

    return jsonify({'message': "User {}'s review of design {} has been deleted.".format(uid, designid)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

