from .db import *

# loading UserInfo relation into Table object called UserInfo
UserInfo = Table('userinfo', metadata, autoload=True, autoload_with=engine)  # Table(table_name, metadata, autoload=True, autoload_with=engine)

# load Room relation
Room = Table('room', metadata, autoload=True, autoload_with=engine)

# load DIYs relation
Diy = Table('diy', metadata, autoload=True, autoload_with=engine)

# load Favorites relation
Favorites = Table('favorites', metadata, autoload=True, autoload_with=engine)

# load Reviews relation
Reviews = Table('reviews', metadata, autoload=True, autoload_with=engine)

