from typing import Text
from bs4 import BeautifulSoup
from requests import request
from os import getenv
import argparse

def getLastPage(container):
    lastPage = 1

    if container is not None:
        lastPageLink = container.find_all('div')[-1]
        lastPageLink = lastPageLink.find('a')['href']
        lastPage = int(lastPageLink.split('&o=')[1])

    return lastPage

def sendWithTelegram(url):
    ids = getenv('TELEGRAM_ID')

    if type(ids) == str or type(ids) == int:
        ids = [str(ids)]

    for id in ids:
        request('POST', 'https://api.telegram.org/bot' + getenv('TELEGRAM_TOKEN') + '/sendMessage?chat_id=' + id + '&text='+ args.message + '\n' + url)

def priceIsGood(item):
    scrapedPrice = item.find('p', {'class':'classes_price__HmHqw'})

    if scrapedPrice is None:
        if args.includeall:
            return True
            
        print("Missing price...")
        print("Skipping")
        return False
    
    scrapedPrice = scrapedPrice.text.replace('€', '').replace('\xa0', '').replace('.', '')
    scrapedPrice = scrapedPrice.split('Spedizion')[0]

    return int(scrapedPrice) < args.budget

def prepareSoup(page = 1):
    body = request('GET', args.url + '&o=' + str(page)).text
    return BeautifulSoup(body, features='html.parser')

def scrapePage(itemsContainer):
    for item in itemsContainer.find_all('div', {'class':'items__item'}):
        if priceIsGood(item):
            sendWithTelegram(item.find('a')["href"])

def checkAndCleanInput():
    if 'subito.it/' not in args.url:
        print('Wrong URL!')
        exit(0)
    
    args.url = args.url.split('&o=')[0]

    args.includeall = args.includeall is not None

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', help='A Subito.it search URL', type=str, required=True)
    parser.add_argument('-b', '--budget', help='Your maximum budget', type=float, required=True)
    parser.add_argument('-m', '--message', help='The message that will sent to your Telegram account', default='Found article in your budget!', type=str)
    parser.add_argument('-a', '--includeall', help='Sends also items without price')


    args = parser.parse_args()

    soup = prepareSoup().find('div', {'class':'skeletons'})   

    lastPageNumber = getLastPage(soup.find('div', {'class':'pagination-container'}))

    for page in range(1, lastPageNumber+1):
        scrapePage(soup)
        soup = prepareSoup(page)
    


