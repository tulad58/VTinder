from sqlalchemy import Column, Integer, ForeignKey
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

    def __str__(self):
        return f'User {self.id}: vk_id: {self.user_vk_id}'


class Profile(Base):
    __tablename__ = 'profile'
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, nullable=False)

    def __str__(self):
        return f'Profile {self.id}: vk_id: {self.profile_id}'
