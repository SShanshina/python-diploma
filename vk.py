import os
import time
import json
import requests
from tqdm import tqdm

VK_TOKEN = '958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008'
PHOTOS_GET_URL = 'https://api.vk.com/method/photos.get'
YA_TOKEN = input('Введите Яндекс-токен: ')
ID = input('Введите id пользователя vk: ')
FOLDER_NAME = 'photos_data'
V = '5.124'


def get_photos_info(count=5):
    response = requests.get(PHOTOS_GET_URL, params={
        'access_token': VK_TOKEN,
        'v': V,
        'owner_id': ID,
        'album_id': 'profile',
        'photo_sizes': 1,
        'extended': 1,
        'count': count
    })
    return response.json()


def take_photos_data():
    os.mkdir(FOLDER_NAME)
    data = get_photos_info()
    photos_names = []
    photos_sizes = []
    for photo in data['response']['items']:
        sizes = photo['sizes']
        likes = str(photo['likes']['count'])
        date = str(time.strftime("%d_%b_%Y", time.localtime(photo['date'])))
        size = sizes[-1]
        url = size['url']
        size_type = size['type']
        file_url = url
        file_name = likes + '.' + url.split('.')[3]
        if file_name not in photos_names:
            photos_names.append(file_name)
        else:
            file_name = likes + '_' + date + '.' + url.split('.')[3]
            photos_names.append(file_name)
        photos_sizes.append(size_type)
        photos = requests.get(file_url)
        with open(os.path.join(FOLDER_NAME, file_name), 'wb') as f:
            f.write(photos.content)
    return list(zip(photos_names, photos_sizes))


def save_photos_and_create_json():
    json_list = []
    for tuples in take_photos_data():
        file_name, size_type = tuples
        photo_data_dict = {'file_name': file_name, 'size': size_type}
        json_list.append(photo_data_dict)
    with open(os.path.join(FOLDER_NAME, 'photos_data.json'), 'w') as f:
        json.dump(json_list, f, indent=2)
    return 'Файлы загружены на локальный компьютер, данные о фото были записаны в формате json.'


def create_folder(folder_name):
    response = requests.put(
        'https://cloud-api.yandex.net/v1/disk/resources',
        params={'path': folder_name},
        headers={'Authorization': f'OAuth {YA_TOKEN}'},
    )
    return f'Новая папка "{folder_name}" была успешно создана на Яндекс-диске.'


def upload(folder_name, file_path):
    response = requests.get(
        'https://cloud-api.yandex.net/v1/disk/resources/upload',
        params={'path': folder_name + '/' + file_path},
        headers={'Authorization': f'OAuth {YA_TOKEN}'},
    )
    json_response = response.json()
    url = json_response['href']
    operation_id = json_response['operation_id']
    files = {'file': open(os.path.join(FOLDER_NAME, file_path), 'rb')}
    result = requests.put(url, files=files)
    while True:
        check_operation = requests.get(
            f'https://cloud-api.yandex.net/v1/disk/operations/{operation_id}',
            headers={'Authorization': f'OAuth {YA_TOKEN}'}
        )
        if check_operation.status_code == 200 and check_operation.json()['status'] != 'in-progress':
            return f'Файл {file_path} был успешно загружен на Яндекс-диск.'
        time.sleep(1)


if __name__ == '__main__':
    folder = []
    print(save_photos_and_create_json())
    print(create_folder(FOLDER_NAME))
    for item in os.walk(FOLDER_NAME):
        folder.append(item)
    for address, dirs, files in folder:
        for file in tqdm(files):
            print(upload(FOLDER_NAME, file))
