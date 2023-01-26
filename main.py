import requests as requests
from bs4 import BeautifulSoup
from pathvalidate import sanitize_filename

from pathlib import Path
from urllib.parse import urljoin, urlsplit, urlparse


def check_for_redirect(response: requests.Response) -> None:
    """Проверяет ссылки на редирект"""
    response_url = response.url
    if response_url == 'https://tululu.org/' or response.history:
        raise requests.HTTPError()


def download_txt(book_id: int, file_name: str, url: str, dir_name: str = 'books/',) -> None:
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    clear_file_name = sanitize_filename(file_name)

    with open(f'{dir_name}/{book_id}. {clear_file_name}.txt', 'wb') as file:
        file.write(response.content)


def download_image(url: str, dir_name: str = 'images/',) -> None:
    response = requests.get(url)
    response.raise_for_status()
    check_for_redirect(response)

    file_name = urlparse(url).path.split('/')[-1]
    print(file_name)

    with open(f'{dir_name}/{file_name}', 'wb') as file:
        file.write(response.content)


def create_directory(name: str) -> None:
    Path(name).mkdir(parents=True, exist_ok=True)


def parsing_page(url: str):
    response = requests.get(url)
    response.raise_for_status()
    page_html = BeautifulSoup(response.text, 'lxml')

    if book_title := page_html.find('h1'):
        title, author = [book.strip() for book in book_title.text.split('::')]
    else:
        raise ValueError

    image_path = page_html.find('div', class_='bookimage').find('img')['src']
    image_url = urljoin(f'https://{urlsplit(url).netloc}', image_path)

    return {
        'title': title,
        'author': author,
        'image_url': image_url,
    }


def main():
    dir_books = 'books'
    dir_images = 'images'

    create_directory(dir_books)
    create_directory(dir_images)

    for book_id in range(1, 10):
        url = f'https://tululu.org/b{book_id}/'
        try:
            page_values = parsing_page(url)
        except ValueError:
            continue
        # print(page_values['title'], page_values['author'], page_values['image_url'], sep=' | ')

        download_image(page_values['image_url'])

        # try:
        #     download_txt(book_id, title, url, dir_name)
        # except requests.HTTPError:
        #     continue


if __name__ == '__main__':
    main()
