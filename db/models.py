from sqlalchemy import Column, Integer, ForeignKey, Date, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserFavouriteProfile(Base):
    __tablename__ = 'user_favorite_profiles'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    profile_id = Column(Integer, ForeignKey('profile.id'), primary_key=True)


class UserBlackList(Base):
    __tablename__ = 'user_black_list'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    profile_id = Column(Integer, ForeignKey('profile.id'), primary_key=True)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    user_vk_id = Column(Integer, nullable=False)

    favorite_profiles = relationship(
        'Profile',
        secondary='user_favorite_profiles',
        backref='likers'
    )
    black_list = relationship(
        'Profile',
        secondary='user_black_list',
        backref='haters'
    )

    # setting = relationship('UserSetting', backref='user')

    def __str__(self):
        return f'User {self.id}: vk_id: {self.user_vk_id}'


class UserSetting(Base):
    __tablename__ = 'user_setting'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, unique=True, nullable=False)
    gender_id = Column(Integer, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    city_id = Column(Integer, nullable=True)
    token = Column(String(length=220), unique=True, nullable=False)

    def __init__(self, user_id, token, gender_id=0, date_of_birth=None, city_id=None):
        if gender_id not in [0, 1, 2]:
            raise ValueError("Недопустимое значение gender_id. Допустимы значения: 0, 1, 2.")


class Profile(Base):
    __tablename__ = 'profile'
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    domain = Column(String, nullable=False)

    def __str__(self):
        return f'Profile {self.id}: vk_id: {self.profile_id}'
