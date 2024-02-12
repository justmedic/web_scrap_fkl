import aiohttp
from bs4 import BeautifulSoup
import asyncio
import aiosqlite
import sys 
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Асинхронная функция для добавления данных в БД
async def insert_product(conn, product):
    sql = ''' INSERT OR IGNORE INTO products(url, product_name, specifications, description, size_and_price)
          VALUES(?,?,?,?,?) '''
    async with conn.execute(sql, product) as cur:
        await conn.commit()
        logging.info(f"Данные успешно добавлены - ID последнего товара: {cur.lastrowid}")
        return cur.lastrowid

# Асинхронное собирание информации о товаре
async def find_info(conn, url, session):
    try:
        async with session.get(url) as response:
            if response.status == 404:
                logging.warning(f'Товар на {url} не найден (404)')
                return

            html_content = await response.text()
            soup = BeautifulSoup(html_content, 'html.parser')

            product_name = soup.find('h1', class_='content__title wrapper').text.strip()
            if not product_name:
                logging.warning(f'Отсутствует название продукта для {url}. Продукт будет пропущен.')
                return
            
            specs_table = soup.find('table', class_='info__specs-table')
            if not specs_table:
                logging.warning(f'Отссутсвует таблица характеристик для {url}')
                return 
                          
            specifications = ''
            if specs_table:
                for row in specs_table.find_all('tr'):
                    spec_name = row.find('th').text.strip()
                    spec_value = row.find('td').text.strip()
                    specifications += f'{spec_name}: {spec_value}\n'
            
            # Сбор описания товара
            product_info = soup.find('div', class_='wysiwyg').text.strip()
            if not product_info:
                logging.warning(f'Отсутствует информация о товаре дле {url}')
                return
            
            # Сбор размеров и цены
            size_and_price = ''
            product_rows = soup.find_all('tr', class_='product-table__size')
            if not product_rows:
                logging.warning(f'отсуствует  таблица размеров для {url}')
                return
            
            for row in product_rows:
                product_and_size = row.find('div', class_='product-table__name').text.strip()
                product_price = row.find('span', class_='product-table__price').text.strip()
                available_quantity = row.find('span', class_='product-table__available').text.strip() if row.find('span', class_='product-table__available') else 'Информация отсутствует'
                units = row.find('span', class_='product-table__units').text.strip() if row.find('span', class_='product-table__units') else 'Н/Д'

                size_and_price += f"Размер товара: {product_and_size}, Цена: {product_price}, Доступное количество: {available_quantity} {units}\n"
                product = (url, product_name, specifications, product_info, size_and_price)
                await insert_product(conn, product)
            logging.info(f"Информация о товаре {url} успешно обработана")
            
    except Exception as e:
        logging.error(f"Ошибка при обработке URL {url}: {e}", exc_info=True)

# Асинхронный главный метод
async def main():
    database = "fakel_data.db"

    async with aiosqlite.connect(database) as conn:
        async with aiohttp.ClientSession() as session:
            # Ограничиваем количество одновременных задач, используя семафор
            semaphore = asyncio.Semaphore(20)  # Вы можете выбрать другое значение
            
            async def bound_find_info(*args):
                async with semaphore:  # Ожидаем доступного слота в семафоре
                    await find_info(*args)
            
            tasks = [bound_find_info(conn, f'https://www.f-tk.ru/catalog/item-{i}/', session) for i in range(10)]
            
            await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())