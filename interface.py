# импорты
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id

from config import comunity_token, acces_token
from core import VkTools

from data_store import check_user, add_user, engine


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
                    if self.params.get('sex') is None:
                        self.params['sex'] = self.sex_add(event.user_id)

                elif event.text.lower() == 'поиск':
                    '''Логика для поиска анкет'''

                    self.message_send(
                        event.user_id, 'Начинаем поиск')

                    msg = next(iter(self.get_profile(self.worksheets, event)))
                    if msg:
                        photo_string = self.add_photos(msg)
                        self.offset += 10
                        self.message_send(
                            event.user_id,
                            f'имя: {msg["name"]} ссылка: vk.com/id{msg["id"]}',
                            attachment=photo_string
                        )

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
                return event.text

    def bdate_add(self, user_id):
        self.message_send(user_id,
                          'введите дату рождения день.месяц.год '
                          'и после снова наберите команду "поиск"')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                return event.text

    def sex_add(self, user_id):
        self.message_send(user_id,
                          'введите свой пол: 1 - мужской, 2 - женский '
                          'и после снова наберите команду "поиск"')
        for event in self.longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                return event.text

    def add_photos(self, worksheet):
        photos = self.vk_tools.get_photos(worksheet['id'])
        photo_string = ''
        for photo in photos:
            photo_string += f'photo{photo["owner_id"]}_{photo["id"]},'
        return photo_string

    def get_profile(self, worksheets, event):
        while True:
            if worksheets:
                worksheet = worksheets.pop()
                if not check_user(engine, event.user_id, worksheet['id']):
                    add_user(engine, event.user_id, worksheet['id'])
                    yield worksheet
            else:
                worksheets = self.vk_tools.search_worksheet(
                    self.params, self.offset)


if __name__ == '__main__':
    bot_interface = BotInterface(comunity_token, acces_token)
    bot_interface.event_handler()
