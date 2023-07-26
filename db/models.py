from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserFavouriteProfile(Base):
    __tablename__ = 'user_favorite_profiles'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    profile_id = Column(Integer, ForeignKey('favorite_profile.id'), primary_key=True)


class UserBlackList(Base):
    __tablename__ = 'user_black_list'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    profile_id = Column(Integer, ForeignKey('black_list.id'), primary_key=True)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    user_vk_id = Column(Integer, nullable=False)

    favorite_profiles = relationship(
        'FavoriteProfile',
        secondary='user_favorite_profiles',
        back_populates='users'
    )
    black_list = relationship(
        'BlackList',
        secondary='user_black_list',
        back_populates='users'
    )

    def __str__(self):
        return f'User {self.id}: vk_id: {self.user_vk_id}'


class FavoriteProfile(Base):
    __tablename__ = 'favorite_profile'
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, nullable=False)

    users = relationship(
        'User',
        secondary='user_favorite_profiles',
        back_populates='favorite_profiles'
    )

    def __str__(self):
        return f'Profile {self.id}: vk_id: {self.profile_id}'


class BlackList(Base):
    __tablename__ = 'black_list'
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, nullable=False)

    users = relationship(
        'User',
        secondary='user_black_list',
        back_populates='black_list'
    )

    def __str__(self):
        return f'Profile {self.id}: vk_id: {self.profile_id}'
