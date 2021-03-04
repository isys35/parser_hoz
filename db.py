import csv
import os

FILE_NAME = 'data.csv'

header = ['ID', 'Тип', 'Артикул', 'Имя', 'Опубликован', 'рекомендуемый?',
          'Видимость в каталоге', 'Короткое описание', 'Описание', 'Дата начала действия продажной цены',
          'Дата окончания действия продажной цены', 'Статус налога', 'Налоговый класс', 'В наличии?',
          'Запасы', 'Величина малых запасов', 'Возможен ли предзаказ?', 'Продано индивидуально?',
          'Вес (kg)', 'Длина (cm)', 'Ширина (cm)', 'Высота (cm)', 'Разрешить отзывы от клиентов?',
          'Примечание к покупке', 'Цена распродажи', 'Базовая цена', 'Категории', 'Метки',
          'Класс доставки', 'Изображения', 'Лимит загрузок', 'Число дней до просроченной загрузки',
          'Родительский', 'Сгруппированные товары', 'Апсейл', 'Кросселы', 'Внешний URL', 'Текст кнопки',
          'Позиция', 'Имя атрибута 1', 'Значение(-я) аттрибута(-ов) 1', 'Видимость атрибута 1',
          'Глобальный атрибут 1']


def create_data_file():
    with open(FILE_NAME, "w", newline="", encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=header, delimiter=',')
        writer.writeheader()


def add_data(data_product: dict):
    if not os.path.isfile(FILE_NAME):
        create_data_file()
    with open(FILE_NAME, "a",  newline='', encoding='utf-8') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=header, delimiter=',')
        writer.writerow(data_product)
