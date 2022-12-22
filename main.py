import requests
import json
from datetime import datetime
from settings import TOKEN_Y, TOKEN_VK
import time
from tqdm import tqdm


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
        response = requests.get(get_url, params={**self.params, **params})
        photo_profile = []
        if response.status_code == 200:
            for photo in response.json()['response']['items']:
                photo_profile.append(
                    {
                        'likes': photo['likes']['count'],
                        'type': photo['sizes'][-1]['type'],
                        'url': photo['sizes'][-1]['url'],
                        'date': datetime.fromtimestamp(photo['date']).strftime('%d-%m-%Y')
                    }
                )
            return photo_profile[:count]
        else:
            print(f'Ошибка {response.status_code}')


class Yandex:

    def __init__(self, token: str, url_downloadable_files):
        self.token = token
        self.url_downloadable_files = url_downloadable_files

    def create_folder(self, folder_name):
        url = "https://cloud-api.yandex.net/v1/disk/resources"
        headers = {"Authorization": self.token}
        response = requests.put(url, params={"path": folder_name}, headers=headers)
        if response.status_code == 201:
            print(f'\nПапка "{folder_name}" успешно создана в корневом каталоге Яндекс диска.\n')
        else:
            print(f' {response.json().get("message")} Файлы могут быть загружены повторно. '
                  f'Status code: {response.status_code}')
        return folder_name

    def upload(self, id_, folder_name):
        name_list = []
        result = []
        headers = {"Authorization": self.token}
        url = "https://cloud-api.yandex.net/v1/disk/resources/upload"
        for urls in tqdm(self.url_downloadable_files):
            if urls['likes'] not in name_list:
                result.append({'file_name': str(urls['likes']) + '.jpg', 'size': urls['type']})
                name_list.append(urls['likes'])
                path = '/' + folder_name + '/' + str(urls['likes']) + '.jpg'
            else:
                result.append({'file_name': str(urls['likes']) + f"_{urls['date']}" + '.jpg', 'size': urls['type']})
                name_list.append(urls["likes"])
                path = '/' + folder_name + '/' + str(urls['likes']) + f"_{urls['date']}" + '.jpg'
            params = {"path": path, "url": urls["url"]}
            time.sleep(1)
            response = requests.post(url, headers=headers, params=params)
            if response.status_code == 202:
                pass
            else:
                print(f'Ошибка загрузки {response.json().get("message")}. Status code: {response.status_code}')
        print(f'Загрузка завершена. В папку "{folder_name}" загружено {len(result)} фото.')
        with open(f'{id_}_{datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}_files.json', "w") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    vk_id = input('\nВведите id профиля, с которого хотите загрузить фотографии:\n')
    counter_need_photo = input('\nВведите количество фотографий для скачивания (по умолчанию 5):\n')
    vk_user = VK(TOKEN_VK, '5.131')
    ya_user = Yandex(TOKEN_Y, vk_user.get_photos(vk_id, int(counter_need_photo)))
    name_folder = ya_user.create_folder('VK_PHOTO')
    ya_user.upload(vk_id, name_folder)

