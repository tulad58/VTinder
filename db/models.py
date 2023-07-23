from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserFavouriteProfile(Base):
    __tablename__ = 'user_favorite_profiles'

    user_id = Column(Integer, ForeignKey('user.id'), primary_key=True)
    profile_id = Column(Integer, ForeignKey('favorite_profile.id'), primary_key=True)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, index=True)
    user_vk_id = Column(String, nullable=False)

    def __str__(self):
        return f'Book {self.id}: {self.title}'

    favorite_profiles = relationship(
        'FavoriteProfile',
        secondary=UserFavouriteProfile,
        back_populates='users'
    )


class FavoriteProfile(Base):
    __tablename__ = 'favorite_profile'
    id = Column(Integer, primary_key=True)
    profile_id = Column(String, nullable=False)

    users = relationship(
        'User',
        secondary=UserFavouriteProfile,
        back_populates='favorite_profiles'
    )
