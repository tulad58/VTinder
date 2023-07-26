from db.session import session
from .models import User, FavoriteProfile, UserFavouriteProfile, UserBlackList, BlackList


class UserCRUD:

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

    def add_favorite(self, user_vk_id: int, profile_vk_id: int) -> bool:

        try:
            profile = self.get_or_create_new_favorite_profile(profile_vk_id)
            user = self.get_or_create_user(user_vk_id)

            new_favourite_profile = UserFavouriteProfile(
                user_id=user.id,
                profile_id=profile.id
            )

            session.add(new_favourite_profile)
            session.commit()
            print(f'Профиль {profile_vk_id} добавлен в избранные к {user_vk_id}')
            return True
        except:
            return False

    def add_to_blacklist(self, user_vk_id: int, profile_vk_id: int) -> bool:

        try:
            profile = self.get_or_create_new_blacklist_profile(profile_vk_id)
            user = self.get_or_create_user(user_vk_id)

            new_blacklist_profile = UserBlackList(
                user_id=user.id,
                profile_id=profile.id
            )

            session.add(new_blacklist_profile)
            session.commit()
            print(f'Профиль {profile_vk_id} добавлен в черный список к {user_vk_id}')
            return True
        except:
            return False

    def get_or_create_new_favorite_profile(self, profile_vk_id: int):
        profile = session.query(FavoriteProfile).filter(FavoriteProfile.profile_id == profile_vk_id).first()
        if profile:
            print(f'Профиль {profile_vk_id} уже был в избранных')
            return profile

        profile = FavoriteProfile(profile_id=profile_vk_id)
        session.add(profile)
        session.commit()
        session.refresh(profile)
        print(f'Создан новый профиль: {profile_vk_id}')
        return profile

        new_favourite_profile = UserFavouriteProfile(user_id=current_user, profile_id=person_id)
        session.add(new_favourite_profile)
        session.commit()

    def get_or_create_new_blacklist_profile(self, profile_vk_id: int):
        profile = session.query(BlackList).filter(BlackList.profile_id == profile_vk_id).first()
        if profile:
            print(f'Профиль {profile_vk_id} уже был в черных списках')
            return profile

        profile = BlackList(profile_id=profile_vk_id)
        session.add(profile)
        session.commit()
        session.refresh(profile)
        print(f'Создан новый профиль: {profile_vk_id}')
        return profile

        new_favourite_profile = UserFavouriteProfile(user_id=current_user, profile_id=person_id)
        session.add(new_favourite_profile)
        session.commit()

    def get_favorites(self, user_vk_id: int):
        user = self.get_or_create_user(user_vk_id)
        fav = user.favorite_profiles
        if fav:
            return fav
        return []

    def exist_in_user_lists(self, user_vk_id, profile_vk_id):
        user = self.get_or_create_user(user_vk_id)
        black_list = [profile.profile_id for profile in user.black_list]
        favorites = [profile.profile_id for profile in user.favorite_profiles]

        if profile_vk_id in set(black_list + favorites):
            return True
        return False


user = UserCRUD()
