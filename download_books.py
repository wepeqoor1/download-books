import argparse
import logging
from pathlib import Path
from urllib.parse import urljoin, urlparse, urlsplit

import requests as requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename
from tqdm import tqdm


def check_for_redirect(response: requests.Response) -> None:
    """Проверяет ссылки на редирект"""
    response_url = response.url
    if response_url == 'https://tululu.org/' or response.history:
        raise requests.HTTPError()


def download_txt(book_id: int, file_name: str, url: str, dir_name: str = 'books/') -> None:
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    clear_file_name = sanitize_filename(file_name)

    with open(f'{dir_name}/{book_id}. {clear_file_name}.txt', 'wb') as file:
        file.write(response.content)


def download_image(url: str, dir_name: str = 'images/') -> None:
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    file_name = urlparse(url).path.split('/')[-1]

    with open(f'{dir_name}/{file_name}', 'wb') as file:
        file.write(response.content)


def parse_book_page(url: str) -> dict:
    response = requests.get(url)
    response.raise_for_status()
    page_html = BeautifulSoup(response.text, 'lxml')

    if book_title := page_html.find('h1'):
        title, author = [book.strip() for book in book_title.text.split('::')]
    else:
        raise ValueError

    image_path = page_html.find('div', class_='bookimage').find('img')['src']
    image_url = urljoin(f'https://{urlsplit(url).netloc}', image_path)

    comments = page_html.find_all('div', class_='texts')
    comments = [comment.find('span', class_='black').text for comment in comments] if comments else None

    genres = page_html.find('span', class_='d_book').find_all('a')
    genres = [genre.text for genre in genres] if comments else None

    return {
        'title': title,
        'author': author,
        'image_url': image_url,
        'comments': comments,
        'genre': genres,
    }


def parsing_arguments() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(""" \
    Программа предназначена для скачивания книг с сайта 'https://tululu.org'
    """)
    parser.add_argument('first', type=int, default=1, help='id первой книги')
    parser.add_argument('last', type=int, default=10, help='id последней книги')

    return parser


def main() -> None:
    logging.basicConfig(filename='information.log', level=logging.INFO, encoding='utf-8')

    parser = parsing_arguments()
    args = parser.parse_args()
    book_id_from = args.first
    book_id_last = args.last

    Path('books').mkdir(parents=True, exist_ok=True)
    Path('images').mkdir(parents=True, exist_ok=True)

    for book_id in tqdm(range(book_id_from, book_id_last + 1)):
        url = f'https://tululu.org/b{book_id}/'
        try:
            page_values = parse_book_page(url)
        except ValueError:
            logging.info(f'На странице {url} отсутствует книга. Переходим к следующей.')
            continue

        try:
            download_txt(book_id, page_values['title'], url)
        except requests.HTTPError:
            logging.info(f'Книга на странице {url} на скачена. Текст отсутствует по данному адресу.')

        try:
            download_image(page_values['image_url'])
        except requests.HTTPError:
            logging.info(f'Обложка на странице {url} на скачена. Картинка отсутствует по данному адресу.')


if __name__ == '__main__':
    main()
