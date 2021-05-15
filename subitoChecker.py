from typing import Any, Tuple
from bs4 import BeautifulSoup
from bs4.element import Tag
from requests import request
from os import getenv
from time import sleep
from pymongo import MongoClient, collection

class SubitoChecker():
    def __init__(self) -> None:
        self._setEnv()
        self._cleanInput()
        self._collection = self._connectToDB()
        self._documents = self._getDocumentsFromCollection()

        self._mainLoop()

    def _mainLoop(self) -> None:
        while(True):
            soup = self._obtainSoup()
            lastPage = self._setDataLastPage(soup.select_one('div.pagination-container'))
            data = {}

            for page in range(1, lastPage+1):
                self._pageScraper(soup, data)

                if not page%12:
                    print('Waiting to prevent too much requests in a few seconds...')
                    sleep(10)
            
            self._removeOldDataFromDb()
            
            print(f'Sleeping for {str(self._runEvery)} minutes.')
            sleep(self._runEvery)
            print('Checking again')


    def _connectToDB(self) -> collection:
        if self._useMongo:
            client = MongoClient(self._mongo)
            return client.SubitoChecker.items
        return []

    def _setEnv(self) -> None:
        self._url = '' if getenv('URL') is None else getenv('URL').split('&o=')[0]
        self._budget = 0 if getenv('MAXIMUM_BUDGET') is None else float(getenv('MAXIMUM_BUDGET'))
        self._minimumBudget = 0 if getenv('MINIMUM_BUDGET') is None else float(getenv('MINIMUM_BUDGET'))
        self._textMessage = 'Found article in your budget!' if getenv('CUSTOM_MESSAGE') is None else getenv('CUSTOM_MESSAGE').lower() == 'true'
        self._includeAll = False if getenv('INCLUDE_ITEMS_WITHOUT_PRICE') is None else getenv('INCLUDE_ITEMS_WITHOUT_PRICE')
        self._runEvery = 3600 if getenv('RUN_EVERY') is None else int(getenv('RUN_EVERY'))*60
        self._mongo = '' if getenv('MONGO_SCHEMA') is None else getenv('MONGO_SCHEMA')
        self._useMongo = True

    def _cleanInput(self) -> None:
        if 'subito.it/' not in self._url:
            print('Wrong URL!')
            exit(0)

        if self._budget <= 0:
            print('Wrong maximum budget!')
            exit(0)

        if 'mongodb://' not in self._mongo:
            self._useMongo = False
    
    def _setDataLastPage(self, container: Tag) -> int:
        if container is None:
            return 1
        lastPageContainer = container.select('div')[-1]
        lastPage = lastPageContainer.select_one('a')['href'].split('&o=')[1]

        return int(lastPage)

    def _sendWithTelegram(self, data: dict) -> None:
        message = f"*{self._textMessage}*\n[{data['name']}]({data['_id']})\n💶 Price: {data['price']}\n📍 Place: {data['place']}"
        message += '\n📦 Shipping available' if data['shipping'] else '\n🚗 Shipping not available'
        
        for id in getenv('TELEGRAM_ID').split(','):
            res = request('POST', 'https://api.telegram.org/bot' + getenv('TELEGRAM_TOKEN') + '/sendMessage?chat_id=' + id + '&parse_mode=markdown&text=' + message).json()
            if not res['ok']:
                print(f"Error {str(res['error_code'])}: {res['description']}")

                if res['error_code'] == 429:
                    sleep(30)
                    self._sendWithTelegram(data)

    def _priceIsGood(self, item: Tag, data: dict) -> Tuple[bool, dict]:
        scrapedPrice = item.select_one('p.classes_price__HmHqw')
        data['shipping'] = False
        
        if scrapedPrice is None:
            data['price'] = 'N.D.'

            if self._includeAll:
                return True, data
            
            print('Missing price, skipping...')
            return False, data

        scrapedPrice = scrapedPrice.text.replace('€', '').replace('\xa0', '').replace('.', '')

        if "Spedizione disponibile" in scrapedPrice:
            scrapedPrice = int(scrapedPrice.split('Spedizion')[0])
            data['shipping'] = True
        
        data['price'] = '€' + str(scrapedPrice)
    
        return int(scrapedPrice) <= self._budget and int(scrapedPrice) >= self._minimumbudget, data

    def _obtainSoup(self, page: int = 1):
        body = request('GET',  f'{self._url}&o={str(page).text}')
        return BeautifulSoup(body, features='html.parser').select_one('div.items')

    def _searchInDb(self, item: Tag, data: dict) -> Tuple[bool, dict]:
        if self._useMongo and item.select_one('a') is not None:
            data['_id'] = item.select_one('a')['href']
            query = self._collection.select_one(f"#{data['_id']}")

            if query is None:
                return True, data
            
            if data['_id'] in self._documents:
                self._documents.remove(data['_id'])
            
            return False, data
        return True, data

    def _pageScraper(self, itemsContainer: list, data: dict) -> None:
        for item in itemsContainer.select('div.items__item'):
            conditionPrice, data = self._priceIsGood(item, data)
            conditionDb, data = self._searchInDb(item, data)
            
            if conditionPrice and conditionDb:
                data['name'] = item.select_one('h2.ItemTitle-module_item-title__39PNS')

                if data['name'] is None:
                    continue
                    
                data['name'] = data['name'].text
                data['price'] = item.select_one('div.item-posting-time-place').text.split('Oggi')[0]

                if self._mongo:
                    self._collection.insert_one(data)
                
                self._sendWithTelegram(data)

    def _getDocumentsFromCollection(self) -> list:
        if self._useMongo:
            docs = list(self._collection.find())
            return (doc['_id'] for doc in docs)
        
        return []
    
    def _removeOldDataFromDb(self) -> None:
        if self._useMongo and len(self._documents):
            print(f'Removing {str(len(self._documents))} items not in Subito anymore')
            
            for item in self._documents:
                self._collection.delete_one({'_id':item})

if __name__ == '__main__':
    checker = SubitoChecker()
    


