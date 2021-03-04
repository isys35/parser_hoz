import requests
from bs4 import BeautifulSoup
import db
import re
from urllib.parse import quote, unquote


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
        data = {}
        name = self._parse_name(response)
        data['Имя'] = name
        description = self._parse_description(response)
        data['Описание'] = description
        aviable = self._parse_aviable(response)
        data['В наличии?'] = aviable
        categories = self._parse_categories(response)
        data['Категории'] = categories
        images = self._parse_images(response)
        data['Изображения'] = images
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

    def parse_data_product(self, response: str):
        soup = BeautifulSoup(response, 'lxml')
        data = {}
        name = soup.select_one('h1').text.strip()
        data['Имя'] = name
        categories_block = soup.select_one('.widget-680')
        categories = [el.text for el in categories_block.select('a')]
        categories = '>'.join(categories)
        data['Категории'] = categories
        mark = soup.select_one('.product-new')
        if mark:
            data['Метки'] = mark.text
        price_block = soup.select_one('.price-current')
        data['Базовая цена'] = price_block.text.strip()
        img = self.host + soup.select_one('.product-image-a')['href']
        data['Изображения'] = img
        description = soup.select_one('.product-description-body').text.strip()
        data['Описание'] = description
        option_title = soup.select_one('.option-title')
        if option_title:
            if option_title.text == 'Производитель:':
                data['Имя атрибута 1'] = 'Производитель:'
                data['Значение(-я) аттрибута(-ов) 1'] = soup.select_one('.option-body').text
        trs = soup.select('tr')
        for tr in trs:
            if tr.select('th')[0].text == 'Объем/ масса':
                data['Вес (kg)'] = tr.select('td')[0].text
                break
        aviable_block = soup.select_one('.shop-product-button.type-3.buy')
        if aviable_block:
            aviable = 1
        else:
            aviable = 0
        data['В наличии?'] = aviable
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

    def parse_data_product(self, response: str):
        soup = BeautifulSoup(response, 'lxml')
        data = {}
        name = soup.select_one('h1').text.strip()
        data['Имя'] = name
        categories = [el.text.strip() for el in soup.select_one('.bread').select('a')]
        categories = '>'.join(categories)
        data['Категории'] = categories
        parametrs_block = soup.select_one('.parametrs')
        paragraphs = parametrs_block.select('p')
        for paragraph in paragraphs:
            spans = paragraph.select('span')
            if spans:
                if spans[0].text == 'Стоимость за 1шт.:':
                    price = spans[1].text
                    data['Базовая цена'] = price
                    break
        discription = soup.select_one('.info_element').select_one('div').text
        data['Описание'] = discription
        dostupnost = soup.select_one('.dostupnost').select_one('span')
        if re.search('Под заказ', dostupnost.text):
            aviable = 0
        else:
            aviable = 1
        data['В наличии?'] = aviable
        img_block = soup.select_one('.img_element')
        main_image = self.host + img_block.select_one('.popular_list').select_one('a.img')['href']
        small_images_block = img_block.select_one('.small_img')
        small_images = []
        if small_images_block:
            small_images = [self.host + el['href'] for el in small_images_block.select('a')]
        images = [main_image] + small_images
        images = '\n'.join(images)
        data['Изображения'] = images
        property = soup.select_one('.korpus')
        trs = property.select('tr')
        for tr in trs:
            tds = tr.select('td')
            if tds[0].text == 'Вес:':
                data['Вес (kg)'] = tds[1].text
                break
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

    def parse_data_product(self, response: str):
        soup = BeautifulSoup(response, 'lxml')
        data = {}
        name = soup.select_one('.catalog_item_name').text.strip()
        data['Имя'] = name
        categories = [el.text.strip() for el in soup.select_one('.breadcrumb').select('a')]
        categories = '>'.join(categories)
        data['Категории'] = categories
        aviable = 0
        if soup.select_one('.nalichie'):
            if re.search('в наличии', soup.select_one('a').text):
                aviable = 1
        data['В наличии?'] = aviable
        description = soup.select_one('.text_holder').text
        data['Описание'] = description
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
    start()
