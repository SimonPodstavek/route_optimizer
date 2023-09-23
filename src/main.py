import json
import time
from datetime import datetime


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from os import getcwd
from os.path import join, abspath

class Route:
    def __init__(self, inbound:str, outbound:str) -> None:
        self.inbound = inbound
        self.outbound = outbound
        self.next = None
        self.distance = float('inf')

    def set_distance(self, distance:int) -> None:
        self.distance = distance

    def set_next(self, next):
        self.next = next
        return next



CWD = getcwd() 

# Adjust path to match your drivers path
driver_path = abspath(join(CWD, r'driver/chromedriver.exe'))
raw_route_data_path = abspath(join(CWD, r'routes/route.json'))
raw_route_data_file = open(raw_route_data_path, encoding='utf-8')



raw_route_data = json.load(raw_route_data_file)



def generate_station_nodes():

    if len(raw_route_data['stations']) < 3:
        print('Insufficient amount of stations')
        exit

    head = Route(raw_route_data['stations'][0],raw_route_data['stations'][1])
    route = head

    for i, station in enumerate(raw_route_data['stations'][1:-1]):
        route = route.set_next(Route(station,raw_route_data['stations'][i+2]))

    return head


def browser_operation(nodes:Route):

    browser = webdriver.Chrome(executable_path=driver_path)
    browser.get("https://predaj.zssk.sk/search")

    time.sleep(4)

    # Refuse cookies
    browser.find_element_by_id('c-p-bn2').click()

    inbound_station_input = browser.find_element_by_xpath('dddd/html/body/div[1]/div/div[2]/div[3]/div/div/form/div[1]/div/div[1]/div[1]/div[1]/input')
    outbound_station_input = browser.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[3]/div/div/form/div[1]/div/div[1]/div[1]/div[3]/input')
    departure_time_input = browser.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[3]/div/div/form/div[1]/div/div[2]/div[2]/div/input')
    departure_date_input = browser.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[3]/div/div/form/div[1]/div/div[2]/div[1]/div[1]/input')
    direct_only_input = browser.find_element_by_xpath('/html/body/div[1]/div/div[2]/div[3]/div/div/form/div[2]/div/div/div/div[2]/div/div[1]/span/ul/li[2]/div/input')
    search_route_button = browser.find_element_by_id('actionSearchConnectionButton')

    departure_date = datetime.strptime(raw_route_data['date'], '%d.%m.%Y')

    node = nodes
    while node is not None:
        #Set outbound and inbound stations
        inbound_station_input.send_keys(node.inbound)
        outbound_station_input.send_keys(node.outbound)
        #set departure time and date
        departure_time_input.clear()
        departure_time_input.send_keys('0:00')
        time.sleep(0.5)
        browser.execute_script(f"arguments[0].value = '{departure_date.strftime('%#d. %#m. %Y')}';", departure_date_input)
        
        #Set direct conneciton only
        browser.execute_script()
        direct_only_input
        time.sleep(0.5)
        search_route_button.click()

        # Try to find train ID my loading more routes up to 10 times
        # for i in range(10):
        #     try:
        #         browser.find_element_by_xpath(f"//span[contains(text(), '{raw_route_data['train_ID']}')]")
        #     except NoSuchElementException:

    
        node = node.next


if __name__ == '__main__':
    nodes = generate_station_nodes()
    browser_operation(nodes)