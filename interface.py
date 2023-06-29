# импорты
import vk_api
from sqlalchemy import create_engine
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import comunity_token, acces_token, db_url_object
from core import VkTools
from data_store import Viewed
from data_store import engine



# отправка сообщений


class BotInterface():
    def __init__(self, comunity_token, acces_token):
        self.vk = vk_api.VkApi(token=comunity_token)
        self.longpoll = VkLongPoll(self.vk)
        self.vk_tools = VkTools(acces_token)
        self.params = {}
        self.worksheets = []
        self.offset = 0

    def message_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send',
                       {'user_id': user_id,
                        'message': message,
                        'attachment': attachment,
                        'random_id': get_random_id()}
                       )



# обработка событий / получение сообщений

    def event_handler(self):
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                if event.text.lower() == 'привет':
                    '''Логика для получения данных о пользователе'''
                    self.params = self.vk_tools.get_profile_info(event.user_id)
                    self.message_send(
                        event.user_id, f'Привет друг, {self.params["name"]} . Наберите "поиск"')
                    if self.params.get('city') is None:
                        self.params['city'] = self.city_add(event.user_id)
                    if self.params.get('bdate') is None:
                        self.params['bdate'] = self.bdate_add(event.user_id)

                elif event.text.lower() == 'поиск':
                    '''Логика для поиска анкет'''
                    self.message_send(
                        event.user_id, 'Начинаем поиск')
                    if self.worksheets:
                        worksheet = self.worksheets.pop()
                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                    else:
                        self.worksheets = self.vk_tools.search_worksheet(
                            self.params, self.offset)
                        # while len(self.worksheets) >= 1:
                        #     worksheet = self.worksheets.pop()
                            # if self.viewed.check_user(engine, event.user_id, worksheet['id']):
                            #     continue

                        worksheet = self.worksheets.pop()
                        # 'првоерка анкеты в бд в соотвествие с event.user_id'

                        photos = self.vk_tools.get_photos(worksheet['id'])
                        photo_string = ''
                        for photo in photos:
                            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
                        # self.viewed.add_user(engine, event.user_id, worksheet['id'])
                        self.offset += 10

                    self.message_send(
                        event.user_id,
                        f'имя: {worksheet["name"]} ссылка: vk.com/id{worksheet["id"]}',
                        attachment=photo_string
                    )

                    'добавить анкету в бд в соотвествие с event.user_id'

                elif event.text.lower() == 'пока':
                    self.message_send(
                        event.user_id, 'До новых встреч')
                else:
                    self.message_send(
                        event.user_id, 'Неизвестная команда')

    def city_add(self, user_id):
        self.message_send(user_id,
                          'Укажите свой город и после снова наберите команду "поиск"')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                # self.message_send(user_id, 'Записали, спасибо. Для поиска анкет введите: "Поиск"')
                # return self.api.get_city(event.text)
                return event.text

    def bdate_add(self, user_id):
        self.message_send(user_id,
                          'введите датурождения день.месяц.год и после снова наберите команду "поиск"')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                # self.message_send(user_id, 'Записали, спасибо. Для поиска анкет введите: "Поиск"')
                return event.text




    # def add_photos(self, worksheet_id):
    #     photos = self.vk_tools.get_photos(worksheet['id'])
    #     photo_string = ''
    #     for photo in photos:
    #         photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
    #
    #

if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, acces_token)
    bot_interface.event_handler()
    engine = create_engine(db_url_object)