import requests
from bs4 import BeautifulSoup
import db
import re
from urllib.parse import quote
import traceback


class Parser:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:85.0) Gecko/20100101 Firefox/85.0'
        }
        self.host = None
        self.template_search_url = None

    def get_response(self, url):
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.text
        else:
            print('[WARNING] Response status code: {}'.format(response.status_code))
            return response.text

    def parse_found_url(self, response, search_name):
        pass

    def parse_data_product(self, response):
        return {}

    def search_data(self, search_name):
        if not self.template_search_url:
            return
        url = self.template_search_url.format(self.host, search_name.lower())
        response = self.get_response(url)
        found_url = self.parse_found_url(response, search_name.lower())
        if not found_url:
            print('[ERROR] Данный товар не найден')
            return
        response_product = self.get_response(found_url)
        data_product = self.parse_data_product(response_product)
        print('[INFO] Продукт сохранён')
        db.add_data(data_product)

    @staticmethod
    def save_page(response: str, file_name='page.html'):
        with open(file_name, 'w', encoding='cp1251') as html_file:
            html_file.write(response)


class VhozParser(Parser):
    def __init__(self):
        super().__init__()
        self.host = 'https://www.vhoz.ru'
        self.template_search_url = '{}/search/?q={}'

    def parse_found_url(self, response: str, search_name: str):
        soup = BeautifulSoup(response, 'lxml')
        found_items = soup.select('.search-item')
        if not found_items:
            return
        for el in found_items:
            if el.select_one('a').text.lower() == search_name:
                return self.host + el.select_one('a')['href']

    @staticmethod
    def _parse_name(response):
        soup = BeautifulSoup(response, 'lxml')
        name = soup.select_one('h1').text
        return name

    @staticmethod
    def _parse_description(response):
        soup = BeautifulSoup(response, 'lxml')
        return soup.select_one('.main-text').text.replace('\n\n\n\n\n\n\n\n\n\n \nКупить', '').strip()

    @staticmethod
    def _parse_aviable(response):
        soup = BeautifulSoup(response, 'lxml')
        aviable_block = soup.select_one('.block.nal-wrapper')
        if aviable_block.select_one('.value').text == 'есть':
            aviable = 1
        else:
            aviable = 0
        return aviable

    @staticmethod
    def _parse_categories(response):
        soup = BeautifulSoup(response, 'lxml')
        breadcrumbs = soup.select_one('.breadcrumbs_wrap')
        categories = [el.text.strip() for el in breadcrumbs.select('a')[:-1]]
        categories = '>'.join(categories)
        return categories

    def _parse_images(self, response):
        soup = BeautifulSoup(response, 'lxml')
        img_blocks = soup.select('.photo-fancy-wrap')
        imgs = [self.host + img_block['href'] for img_block in img_blocks if img_block['href'] != '#']
        imgs = '\n'.join(imgs)
        return imgs

    def parse_data_product(self, response: str):
        data = {'Имя': self._parse_name(response), 'Описание': self._parse_description(response),
                'В наличии?': self._parse_aviable(response), 'Категории': self._parse_categories(response),
                'Изображения': self._parse_images(response)}
        return data


class IvanovskoeParser(Parser):
    def __init__(self):
        super().__init__()
        self.host = 'http://ivanovskoe.pro'
        self.template_search_url = '{}/search?search={}'

    def parse_found_url(self, response: str, search_name):
        soup = BeautifulSoup(response, 'lxml')
        found_list = soup.find('ul', {'style': 'list-style-type:square'})
        if not found_list:
            return
        found_items = found_list.select('a')
        if not found_items:
            return
        return self.host + found_items[0]['href']

    @staticmethod
    def _parse_name(response):
        soup = BeautifulSoup(response, 'lxml')
        return soup.select_one('h1').text.strip()

    @staticmethod
    def _parse_categories(response):
        soup = BeautifulSoup(response, 'lxml')
        categories_block = soup.select_one('.widget-680')
        categories = [el.text for el in categories_block.select('a')]
        categories = '>'.join(categories)
        return categories

    @staticmethod
    def _parse_mark(response):
        soup = BeautifulSoup(response, 'lxml')
        mark_block = soup.select_one('.product-new')
        if mark_block:
            return mark_block.text

    @staticmethod
    def _parse_price(response):
        soup = BeautifulSoup(response, 'lxml')
        price_block = soup.select_one('.price-current')
        return price_block.text.strip()

    def _parse_images(self, response):
        soup = BeautifulSoup(response, 'lxml')
        return self.host + soup.select_one('.product-image-a')['href']

    @staticmethod
    def _parse_description(response):
        soup = BeautifulSoup(response, 'lxml')
        return soup.select_one('.product-description-body').text.strip()

    @staticmethod
    def _parse_option(response):
        soup = BeautifulSoup(response, 'lxml')
        option_title = soup.select_one('.option-title')
        if option_title:
            if option_title.text == 'Производитель:':
                return 'Производитель:', soup.select_one('.option-body').text
        return None, None

    @staticmethod
    def _parse_weight(response):
        soup = BeautifulSoup(response, 'lxml')
        trs = soup.select('tr')
        for tr in trs:
            if tr.select('th')[0].text == 'Объем/ масса':
                return tr.select('td')[0].text

    @staticmethod
    def _parse_aviable(response):
        soup = BeautifulSoup(response, 'lxml')
        aviable_block = soup.select_one('.shop-product-button.type-3.buy')
        if aviable_block:
            aviable = 1
        else:
            aviable = 0
        return aviable

    def parse_data_product(self, response: str):
        data = {'Имя': self._parse_name(response), 'Категории': self._parse_categories(response),
                'Метки': self._parse_mark(response), 'Базовая цена': self._parse_price(response),
                'Изображения': self._parse_images(response), 'Описание': self._parse_description(response),
                'Имя атрибута 1': self._parse_option(response)[0],
                'Значение(-я) аттрибута(-ов) 1': self._parse_option(response)[1],
                'Вес (kg)': self._parse_weight(response), 'В наличии?': self._parse_aviable(response)}
        return data


class GardenParser(Parser):
    def __init__(self):
        super().__init__()
        self.host = 'https://garden-rs.ru'
        self.template_search_url = '{}/search/?q={}'

    def parse_found_url(self, response: str, search_name):
        soup = BeautifulSoup(response, 'lxml')
        found_list = soup.select_one('.popular_list')
        if not found_list:
            return
        return self.host + found_list.select_one('a.img')['href']

    @staticmethod
    def _parse_name(response):
        soup = BeautifulSoup(response, 'lxml')
        return soup.select_one('h1').text.strip()

    @staticmethod
    def _parse_categories(response):
        soup = BeautifulSoup(response, 'lxml')
        categories = [el.text.strip() for el in soup.select_one('.bread').select('a')]
        categories = '>'.join(categories)
        return categories

    @staticmethod
    def _parse_price(response):
        soup = BeautifulSoup(response, 'lxml')
        parametrs_block = soup.select_one('.parametrs')
        paragraphs = parametrs_block.select('p')
        for paragraph in paragraphs:
            spans = paragraph.select('span')
            if spans:
                if spans[0].text == 'Стоимость за 1шт.:':
                    price = spans[1].text
                    return price

    @staticmethod
    def _parse_description(response):
        soup = BeautifulSoup(response, 'lxml')
        return soup.select_one('.info_element').select_one('div').text

    @staticmethod
    def _parse_aviable(response):
        soup = BeautifulSoup(response, 'lxml')
        dostupnost = soup.select_one('.dostupnost').select_one('span')
        if re.search('Под заказ', dostupnost.text):
            aviable = 0
        else:
            aviable = 1
        return aviable

    def _parse_images(self, response):
        soup = BeautifulSoup(response, 'lxml')
        img_block = soup.select_one('.img_element')
        main_image = self.host + img_block.select_one('.popular_list').select_one('a.img')['href']
        small_images_block = img_block.select_one('.small_img')
        small_images = []
        if small_images_block:
            small_images = [self.host + el['href'] for el in small_images_block.select('a')]
        images = [main_image] + small_images
        images = '\n'.join(images)
        return images

    @staticmethod
    def _parse_weight(response):
        soup = BeautifulSoup(response, 'lxml')
        property = soup.select_one('.korpus')
        trs = property.select('tr')
        for tr in trs:
            tds = tr.select('td')
            if tds[0].text == 'Вес:':
                return tds[1].text

    def parse_data_product(self, response: str):
        data = {'Имя': self._parse_name(response), 'Категории': self._parse_categories(response),
                'Базовая цена': self._parse_price(response), 'Описание': self._parse_description(response),
                'В наличии?': self._parse_aviable(response), 'Изображения': self._parse_images(response),
                'Вес (kg)': self._parse_weight(response)}
        return data


class AsemenaParser(Parser):
    def __init__(self):
        super().__init__()
        self.host = 'http://www.asemena.ru'
        self.template_search_url = '{}/search/index.php?q={}'

    def parse_found_url(self, response: str, search_name):
        soup = BeautifulSoup(response, 'lxml')
        found_product = soup.select_one('a.catalog_item_name')
        if not found_product:
            return
        return self.host + found_product['href']

    @staticmethod
    def _parse_name(response):
        soup = BeautifulSoup(response, 'lxml')
        return soup.select_one('.catalog_item_name').text.strip()

    @staticmethod
    def _parse_categories(response):
        soup = BeautifulSoup(response, 'lxml')
        categories = [el.text.strip() for el in soup.select_one('.breadcrumb').select('a')]
        categories = '>'.join(categories)
        return categories

    @staticmethod
    def _parse_aviable(response):
        soup = BeautifulSoup(response, 'lxml')
        aviable = 0
        if soup.select_one('.nalichie'):
            if re.search('в наличии', soup.select_one('a').text):
                aviable = 1
        return aviable

    @staticmethod
    def _parse_description(response):
        soup = BeautifulSoup(response, 'lxml')
        description = soup.select_one('.text_holder').text
        return description

    def parse_data_product(self, response: str):
        data = {'Имя': self._parse_name(response), 'Категории': self._parse_categories(response),
                'В наличии?': self._parse_aviable(response), 'Описание': self._parse_description(response)}
        return data

    def search_data(self, search_name):
        search_name = quote(search_name.encode('cp1251'))
        super().search_data(search_name)


def start():
    info = """
Доступные сайты:
    1 -  https://www.vhoz.ru
    2 - http://ivanovskoe.pro
    3 - https://garden-rs.ru
    4 - http://www.asemena.ru
    """
    print(info)
    select_parser = input('Выберите сайт (1,2,3,4): ')
    if select_parser == '1':
        parser = VhozParser()
    elif select_parser == '2':
        parser = IvanovskoeParser()
    elif select_parser == '3':
        parser = GardenParser()
    elif select_parser == '4':
        parser = AsemenaParser()
    else:
        parser = None
    while True:
        search_keyword = input('Введите наименование для парсинга: ')
        if parser:
            parser.search_data(search_keyword)


if __name__ == '__main__':
    try:
        start()
    except Exception:
        print(traceback.format_exc())
        input('Нажмите любую кнопку...')

