import requests
from pathlib import Path
from datetime import date
import time
import json


class Parse5kaProductPerCategory:
    categories_url = 'https://5ka.ru/api/v2/categories/'  # страница с parents_group
    products_url = 'https://5ka.ru/api/v2/special_offers/'  # страница с страницам с акционными товарами
    headers = {'User-Agent': 'Accountant Ivanov'}

    def __init__(self, save_dir_name):
        self.save_dir_path = self.make_save_dir_and_get_path(save_dir_name)

    # @staticmethod  # я так понимаю, что делать его статичным -- необязательно
    def make_save_dir_and_get_path(self, save_dir_name):  # создание директории для сохранения файлов
        current_date = str(date.today())
        save_dir_path = Path.cwd() / f'{save_dir_name}_{current_date}'
        counter = 0
        while True:  # создаётся директория с заданным именем и окончанием в виде текущей даты
            if not save_dir_path.exists():
                Path.mkdir(save_dir_path)
                return save_dir_path
            else:  # если директория с таким именем уже существует, то к создаваемой директории прибавится counter
                counter += 1
                save_dir_path = Path.cwd() / f'{save_dir_name}_{current_date}_{str(counter)}'
                save_dir_path = Path(save_dir_path)

    # @staticmethod
    def get_group_code(self, group):
        return list(group.values())[0]  # получение кода группы

    def get_response_data(self, url, params=None):  # для чего делать метод защищённым?
        while True:
            response = requests.get(url, headers=self.headers, params=params)
            if response.status_code == 200:
                return response.json()
            time.sleep(0.25)

    def subgpoup_check(self, group):  # проверка на наличие подгрупп
        group_code = self.get_group_code(group)
        group_url = f'{self.categories_url}{group_code}/'
        if self.get_response_data(group_url):
            return True

    def products_check(self, group):  # проверка на наличие товаров, относящихся к группе
        group_code = self.get_group_code(group)
        params = {'categories': group_code}
        data = self.get_response_data(self.products_url, params)
        if data['results']:
            return True

    def parse(self, url, params=None):  # для чего делать метод защищённым?
        while url:
            data = self.get_response_data(url, params)
            url = data['next']
            for product in data['results']:
                yield product

    # @staticmethod
    def save(self, data, file_path):  # для чего делать метод защищённым?
        file_path.write_text(json.dumps(data, ensure_ascii=False), 'utf8')

    def recursive_processing_group(self, group, super_file_name=None, super_group_data=None):
        group_code = self.get_group_code(group)  # получение кода группы
        if not super_group_data:  # получение информации о группе -- кода и имени
            group_data = group
        else:
            group_data = super_group_data  # для дочерней группы присоединяется информация о родительской
            group_key_0 = list(group.keys())[0]
            group_key_1 = list(group.keys())[1]
            if group_key_0 in set(group_data.keys()):
                group_data[f'sub_{group_key_0}'] = group[group_key_0]
                group_data[f'sub_{group_key_1}'] = group[group_key_1]
            else:
                group_data.update(group)
        if not super_file_name:  # создание имени файла
            file_name = f'{group_code}'
        else:  # имя файла дочерней группы начинается с кода родительской группы
            file_name = f'{super_file_name}_{group_code}'
        if not self.subgpoup_check(group):  # если подгрупп нет, то проверка на наличие акционных товаров
            if self.products_check(group):  # проверка на наличие акционных товаров, относящихся к группе
                group_params = {'categories': group_code}  # параметры для обращения к акционным товарам группы
                products_data = list(self.parse(self.products_url, group_params))  # список акционных товаров группы
                total_data = {}  # инициализая итогового словаря данных
                total_data.update(group_data)  # внесение данных о группе
                total_data['products'] = products_data  # внесение данных об акционных товарах группы
                file_name = f'{file_name}.json'  # определение имени файла группы
                file_path = self.save_dir_path.joinpath(file_name)  # путь к файлу группы
                self.save(total_data, file_path)  # сохранение
        else:  # если в группе есть подгруппы, то выполняется рекурсия до достижения "нижней" группы
            group_cat_url = f'{self.categories_url}{group_code}/'
            for subgroup in self.get_response_data(group_cat_url):
                self.recursive_processing_group(subgroup, file_name, group_data)

    def run(self):
        for group in self.get_response_data(self.categories_url):  # обращение к странице с parent_group
            self.recursive_processing_group(group)


save_dir_name = 'parse5ka_prod_per_group'
parser = Parse5kaProductPerCategory(save_dir_name)
parser.run()

# Меня несколько смутили следующие группы. Ничего не придумал, что с ними можно сделать.
# 940 14 февраля
# 941 8 марта
# 938 Лучшее по акции
# 939 Лидеры рейтинга
