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

    setting = relationship('UserSetting', backref='user')

    def __str__(self):
        return f'User {self.id}: vk_id: {self.user_vk_id}'


class UserSetting(Base):
    __tablename__ = 'user_setting'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('user.id'), nullable=False)
    gender_vk_id = Column(Integer, nullable=False)
    target_gender_id = Column(Integer, nullable=False)
    date_of_birth = Column(Date, nullable=True)


class Profile(Base):
    __tablename__ = 'profile'
    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    domain = Column(String, nullable=False)

    def __str__(self):
        return f'Profile {self.id}: vk_id: {self.profile_id}'
