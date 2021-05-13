from bs4 import BeautifulSoup
from requests import request
from os import getenv
from time import sleep


def getLastPage(container):
    lastPage = 1

    if container is not None:
        lastPageLink = container.find_all('div')[-1]
        lastPageLink = lastPageLink.find('a')['href']
        lastPage = int(lastPageLink.split('&o=')[1])

    return lastPage

def sendWithTelegram():
    message = "*" + args['textmessage'] + "*\n[" + scrapedItem['name'] + "](" + scrapedItem['url'] + ")\n💶 Price: €" + str(scrapedItem['price']) + '\n📍 Place: ' + scrapedItem['place']
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
        if args['includeall']:
            return True
            
        print("Missing price...", "Skipping")
        return False
    
    scrapedPrice = scrapedPrice.text.replace('€', '').replace('\xa0', '').replace('.', '')

    if "Spedizione disponibile" in scrapedPrice:
        scrapedPrice = int(scrapedPrice.split('Spedizion')[0])
        scrapedItem['shipping'] = True
    
    scrapedItem['price'] = int(scrapedPrice)

    return scrapedItem['price'] <= args['budget'] and scrapedItem['price'] >= args['minimumbudget']

def prepareSoup(page = 1):
    body = request('GET', args['url'] + '&o=' + str(page)).text
    return BeautifulSoup(body, features='html.parser')

def scrapePage(itemsContainer):
    for item in itemsContainer.find_all('div', {'class':'items__item'}):
        if priceIsGood(item):
            scrapedItem['name'] = item.find('h2', {'class':'ItemTitle-module_item-title__39PNS'})
            if scrapedItem['name'] is None:
                continue
            
            scrapedItem['name'] = scrapedItem['name'].text
            scrapedItem['place'] = item.find('div', {'class':'item-posting-time-place'}).text.split('Oggi')[0]
            scrapedItem['url'] = item.find('a')["href"]
            sendWithTelegram()

def checkAndCleanInput():
    args = {'url': getenv('URL'),'budget':getenv('MAXIMUM_BUDGET'),'minimumbudget':getenv('MINIMUM_BUDGET'),'textmessage':getenv('CUSTOM_MESSAGE'),'includeall':getenv('INCLUDE_ITEMS_WITHOUT_PRICE'),'run_every':getenv('RUN_EVERY')}

    if 'subito.it/' not in args['url'] or args['url'] is None:
        print('Wrong URL!')
        exit(0)
    
    if args['budget'] is None:
        print('Wrong maximum budget!')
        exit(0)

    if args['minimumbudget'] is None:
        args['minimumbudget'] = 0
    
    if args['textmessage'] is None:
        args['textmessage'] = 'Found article in your budget!'
    
    if args['includeall'] is None:
        args['includeall'] = False
    
    if args['run_every'] is None:
        args['run_every'] = 60

    args['url'] = args['url'].split('&o=')[0]
    args['budget'] = float(args['budget'])
    args['minimumbudget'] = float(args['minimumbudget'])
    args['includeall'] = bool(args['includeall'])
    args['run_every'] = int(args['run_every'])*60

    return args

if __name__ == '__main__':
    args = checkAndCleanInput()

    while(True):
        soup = prepareSoup().find('div', {'class':'items'})   

        lastPageNumber = getLastPage(soup.find('div', {'class':'pagination-container'}))
        scrapedItem = {}

        for page in range(2, lastPageNumber+1):
            scrapePage(soup)
            soup = prepareSoup(page)

            if not page%12:
                print('Waiting to prevent too much requests in a few seconds...')
                sleep(5)

        scrapePage(soup)
        print('Sleeping')
        sleep(args['run_every'])
        print('Checking again')
    


