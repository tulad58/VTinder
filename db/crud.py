from db.session import session
from .models import User, Profile, UserFavouriteProfile, UserBlackList


class BaseCRUD:

    def get_or_create_user(self, vk_id: int):
        user = session.query(User).filter(User.user_vk_id == vk_id).first()
        if user:
            print(f'Пользователь {vk_id} уже был в базе')
            return user

        user = User(user_vk_id=vk_id)
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f'Создан новый пользователь {vk_id}')
        return user

    def add_favorite(self, db_user, profile_vk_id: int, profile_firstname: str, profile_lastname: str,
                     profile_domain: str) -> bool:
        try:
            profile = self.get_or_create_profile(profile_vk_id, profile_firstname, profile_lastname, profile_domain)

            new_favourite_profile = UserFavouriteProfile(
                user_id=db_user.id,
                profile_id=profile.id
            )

            session.add(new_favourite_profile)
            session.commit()
            print(f'Профиль {profile_vk_id} добавлен в избранные к {db_user.user_vk_id}')
            return True
        except:
            return False

    def add_to_blacklist(self, db_user: int, profile_vk_id: int) -> bool:

        try:
            profile = self.get_or_create_profile(profile_vk_id)

            new_blacklist_profile = UserBlackList(
                user_id=db_user.id,
                profile_id=profile.id
            )

            session.add(new_blacklist_profile)
            session.commit()
            print(f'Профиль {profile_vk_id} добавлен в черный список к {db_user.user_vk_id}')
            return True
        except:
            return False

    def get_or_create_profile(self, profile_vk_id, profile_firstname=None, profile_lastname=None, profile_domain=None):
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

    def get_favorites(self, db_user):
        fav = db_user.favorite_profiles
        if fav:
            return fav
        return []

    def exist_in_user_lists(self, db_user, profile_vk_id):
        black_list = [profile.profile_id for profile in db_user.black_list]
        favorites = [profile.profile_id for profile in db_user.favorite_profiles]

        if profile_vk_id in set(black_list + favorites):
            return True
        return False


db = BaseCRUD()
