from typing import Text
from bs4 import BeautifulSoup
from requests import request
from os import getenv
import argparse
from time import sleep


def getLastPage(container):
    lastPage = 1

    if container is not None:
        lastPageLink = container.find_all('div')[-1]
        lastPageLink = lastPageLink.find('a')['href']
        lastPage = int(lastPageLink.split('&o=')[1])

    return lastPage

def sendWithTelegram():
    message = "*" + args.textmessage + "*\n[" + scrapedItem['name'] + "](" + scrapedItem['url'] + ")\n💶 Price: €" + str(scrapedItem['price']) + '\n📍 Place: ' + scrapedItem['place']
    message += '\n📦 Shipping available' if scrapedItem['shipping'] else '\nShipping not available'
    
    for id in getenv('TELEGRAM_ID').split(','):
        res = request('POST', 'https://api.telegram.org/bot' + getenv('TELEGRAM_TOKEN') + '/sendMessage?chat_id=' + id + '&parse_mode=markdown&text=' + message).json()
        if not res['ok']:
            print('Error {}: {}'.format(str(res['error_code']), res['description']))

def priceIsGood(item):
    scrapedPrice = item.find('p', {'class':'classes_price__HmHqw'})
    scrapedItem['shipping'] = False

    if scrapedPrice is None:
        scrapedItem['price'] = 'N.D.'
        if args.includeall:
            return True
            
        print("Missing price...", "Skipping")
        return False
    
    scrapedPrice = scrapedPrice.text.replace('€', '').replace('\xa0', '').replace('.', '')

    if "Spedizione disponibile" in scrapedPrice:
        scrapedPrice = int(scrapedPrice.split('Spedizion')[0])
        scrapedItem['shipping'] = True
    
    scrapedItem['price'] = int(scrapedPrice)

    return scrapedItem['price'] <= args.budget and scrapedItem['price'] >= args.minimumbudget

def prepareSoup(page = 1):
    body = request('GET', args.url + '&o=' + str(page)).text
    return BeautifulSoup(body, features='html.parser')

def scrapePage(itemsContainer):
    for item in itemsContainer.find_all('div', {'class':'items__item'}):
        if priceIsGood(item):
            scrapedItem['name'] = item.find('h2', {'class':'ItemTitle-module_item-title__39PNS'}).text
            scrapedItem['place'] = item.find('div', {'class':'item-posting-time-place'}).text.split('Oggi')[0]
            scrapedItem['url'] = item.find('a')["href"]
            sendWithTelegram()

def checkAndCleanInput():
    if 'subito.it/' not in args.url:
        print('Wrong URL!')
        exit(0)
    
    args.url = args.url.split('&o=')[0]
    
    return fixIDs()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--url', help='A Subito.it search URL', type=str, required=True)
    parser.add_argument('-b', '--budget', help='Your maximum budget', type=float, required=True)
    parser.add_argument('-m', '--minimumbudget', help='Minimum accepted price', type=float, default=0)
    parser.add_argument('-t', '--textmessage', help='The message that will sent to your Telegram account', default='Found article in your budget!', type=str)
    parser.add_argument('-a', '--includeall', help='Sends also items without price', action='store_true')
    args = parser.parse_args()

    soup = prepareSoup().find('div', {'class':'skeletons'})   

    lastPageNumber = getLastPage(soup.find('div', {'class':'pagination-container'}))
    scrapedItem = {}
    lastPageNumber = 3

    for page in range(2, lastPageNumber+1):
        scrapePage(soup)
        soup = prepareSoup(page)

        if not page%12:
            print('Waiting to prevent too much requests in a few seconds...')
            sleep(5)

    scrapePage(soup)
    


