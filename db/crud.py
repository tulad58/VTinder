from sqlalchemy.orm import joinedload

from db.session import SessionLocal
from .models import User, Profile, UserFavouriteProfile, UserBlackList


class BaseCRUD:
    @staticmethod
    def get_or_create_user(vk_id: int):
        with SessionLocal() as session:
            user = session.query(User).filter(User.user_vk_id == vk_id).options(joinedload(User.black_list), joinedload(
                User.favorite_profiles)).first()
            if user:
                print(f'Пользователь {vk_id} уже был в базе')
                return user

            user = User(user_vk_id=vk_id)
            session.add(user)
            session.commit()
            session.refresh(user)
            print(f'Создан новый пользователь {vk_id}')
            return user

    def add_to_lists(self, db_user, profile_vk_id: int, profile_firstname: str, profile_lastname: str,
                     profile_domain: str, blacklist=False) -> bool:
        try:
            profile = self.get_or_create_profile(profile_vk_id, profile_firstname, profile_lastname, profile_domain)

            if blacklist:
                profile = UserBlackList(
                    user_id=db_user.id,
                    profile_id=profile.id
                )
            else:
                profile = UserFavouriteProfile(
                    user_id=db_user.id,
                    profile_id=profile.id
                )
            with SessionLocal() as session:
                session.add(profile)
                session.commit()
                print(f'Профиль {profile_vk_id} добавлен в списки к {db_user.user_vk_id}')
                return True
        except:
            return False

    @staticmethod
    def get_or_create_profile(profile_vk_id, profile_firstname=None, profile_lastname=None, profile_domain=None):
        with SessionLocal() as session:
            profile = session.query(Profile).filter(Profile.profile_id == profile_vk_id).first()
            if profile:
                if profile_firstname:
                    profile.first_name = profile_firstname
                if profile_lastname:
                    profile.last_name = profile_lastname
                if profile_domain:
                    profile.domain = profile_domain
                return profile
            else:
                profile = Profile(
                    profile_id=profile_vk_id,
                    first_name=profile_firstname,
                    last_name=profile_lastname,
                    domain=profile_domain
                )
                session.add(profile)
            session.commit()
            session.refresh(profile)
            print(f'Создан новый профиль: {profile_vk_id}')
            return profile

    @staticmethod
    def get_favorites(db_user):
        with SessionLocal() as session:
            user = session.query(User).filter(User.id == db_user.id).first()
            fav = user.favorite_profiles
        if fav:
            return fav
        return []

    @staticmethod
    def exist_in_user_lists(db_user, profile_vk_id):
        black_list = [profile.profile_id for profile in db_user.black_list]
        favorites = [profile.profile_id for profile in db_user.favorite_profiles]

        if profile_vk_id in set(black_list + favorites):
            return True
        return False


db = BaseCRUD()
