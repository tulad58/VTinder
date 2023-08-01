from db.session import session
from .models import User, Profile, UserFavouriteProfile, UserBlackList, UserSetting


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
            session.add(profile)
            session.commit()
            print(f'Профиль {profile_vk_id} добавлен в списки к {db_user.user_vk_id}')
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

    def get_user_setting(self, user_id):
        try:
            user_setting = session.query(UserSetting).filter(UserSetting.user_id == user_id).first()
            if user_setting:
                print(f'Настройки пользователя {user_id} есть в базе данных')
                return user_setting

        except Exception as e:
            print("Ошибка:", e)
            return None

    def create_user_setting(self, user_id, token, gender_id=0, date_of_birth=None, city_id=None):
        try:
            user_setting = self.get_user_setting(user_id)

            if user_setting is None:
                user_setting = UserSetting(user_id=user_id, token=token, gender_id=gender_id,
                                           date_of_birth=date_of_birth, city_id=city_id)
                session.add(user_setting)
            else:
                user_setting.token = token
                user_setting.gender_id = gender_id
                user_setting.date_of_birth = date_of_birth
                user_setting.city_id = city_id

            session.commit()
            session.refresh(user_setting)
            print(f'Добавлены/обновлены настройки пользователя {user_id}')
            return user_setting

        except Exception as e:
            print("Ошибка:", e)
            return None


db = BaseCRUD()
