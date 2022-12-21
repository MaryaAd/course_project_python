import requests
import json
from datetime import datetime
from settings import TOKEN_Y, TOKEN_VK
import time
from tqdm import tqdm

def largest_size(sizes):
    sizes_list = ['w', 'z', 'y', 'x', 'm', 's']
    for item in sizes_list:
        for size in sizes:
            if size['type'] == item:
                return size


def create_file_names(photos):
    for photo in photos:
        photo.name = str(photo.likes)
        photo.date = datetime.fromtimestamp(photo.date).strftime('%Y-%m-%d')
        if [p.likes for p in photos].count(photo.likes) > 1:
            photo.name += '_' + str(photo.date)
        photo.name += '.jpg'


class Photo:
    name = ''

    def __init__(self, date, likes, sizes):
        self.date = date
        self.likes = likes
        self.sizes = sizes
        self.size_type = sizes['type']
        self.url = sizes['url']
        self.maxsize = max(sizes['width'], sizes['height'])

    def __repr__(self):
        return f'date: {self.date}, likes: {self.likes}, size: {self.maxsize}, url: {self.url}'


class VK:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {
            'access_token': token,
            'v': version,
        }

    def get_photos(self, id_, count=5):
        get_url = self.url + 'photos.get'
        params = {
            'owner_id': id_,
            'album_id': 'profile',
            'photo_sizes': 1,
            'extended': 1,
            'rev': 1
        }
        resp = requests.get(get_url, params={**self.params, **params}).json().get('response').get('items')
        return sorted([Photo(photo.get('date'),
                             photo.get('likes')['count'],
                             largest_size(photo.get('sizes'))) for photo in resp],
                      key=lambda p: p.maxsize, reverse=True)[:count]


class Yandex:

    def __init__(self, token: str):
        self.token = token

    def create_folder(self, folder_name):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        headers = {"Authorization": self.token}
        if requests.get(url, headers=headers, params={"path": folder_name}).status_code != 200:
            requests.put(url, params={"path": folder_name}, headers=headers)
            print(f'\nПапка "{folder_name}" успешно создана в корневом каталоге Яндекс диска.\n')

        else:
            print(f'\nПапка "{folder_name}" уже существует. Файлы могут быть загружены повторно.\n')
        return folder_name

    def upload(self, id_, photos):
        folder_name = input('Введите имя папки: ')
        create_file_names(photos)
        if self.create_folder(folder_name):
            result = []
            for photo in tqdm(photos):
                response = requests.post("https://cloud-api.yandex.net/v1/disk/resources/upload",
                                         params={"path": '/' + folder_name + '/' + photo.name,
                                                 "url": photo.url},
                                         headers={"Authorization": self.token})
                time.sleep(1)
                if response.status_code == 202:
                    result.append({"file_name": photo.name, "size": photo.size_type})
                else:
                    print(f'Ошибка загрузки "{photo.name}": '
                          f'{response.json().get("message")}. Status code: {response.status_code}')
            print(f'В папку "{folder_name}" загружено {len(result)} фото.')
            with open(f'{id_}_{datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}_files.json', "w") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    token_VK = TOKEN_VK
    vk_id = input('\nВведите id профиля, с которого хотите загрузить фотографии:\n')
    counter_need_photo = int(input('\nВведите количество фотографий для скачивания (по умолчанию 5):\n'))
    vk_user = VK(TOKEN_VK, '5.131')
    ya_user = Yandex(TOKEN_Y)
    ya_user.upload(vk_id, vk_user.get_photos(vk_id, int(counter_need_photo)))
