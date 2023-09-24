import json
import time
from datetime import datetime


from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

from os import getcwd
from os.path import join, abspath

class Route:
    def __init__(self, inbound:str, outbound:str) -> None:
        self.inbound = inbound
        self.outbound = outbound
        self.next = None
        self.available = None
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


    node = nodes
    while node is not None:
        browser = webdriver.Chrome(executable_path=driver_path)
        # browser.minimize_window()
        browser.get("https://predaj.zssk.sk/search")
        

        wait = WebDriverWait(browser, timeout=10)
    

        # Wait for page to load
        wait.until(EC.visibility_of_element_located((By.ID, 'actionSearchConnectionButton')))
        time.sleep(0.5)

        # Refuse cookies
        try:
            browser.find_element(By.ID, 'c-p-bn2').click()
        except Exception:
            pass

        wait.until(EC.visibility_of_element_located((By.ID, 'actionSearchConnectionButton')))
        time.sleep(0.5)
        

        inbound_station_input = browser.find_element(By.ID, 'fromInput')
        outbound_station_input = browser.find_element(By.ID, 'toInput')
        departure_time_input = browser.find_element(By.ID, 'departTime')
        departure_date_input = browser.find_element(By.ID, 'departDate')
        direct_only_input = browser.find_element(By.ID, 'TrainSearchFormDirect')
        search_route_button = browser.find_element(By.ID, 'actionSearchConnectionButton')

        departure_date = datetime.strptime(raw_route_data['date'], '%d.%m.%Y')

        #Set outbound and inbound stations
        inbound_station_input.clear()
        time.sleep(0.1)
        inbound_station_input.send_keys(node.inbound)
        outbound_station_input.clear()
        time.sleep(0.1)
        outbound_station_input.send_keys(node.outbound)
        #set departure time and date
        departure_time_input.clear()
        departure_time_input.send_keys(raw_route_data['departure_time'])
        time.sleep(0.1)
        browser.execute_script(f"arguments[0].value = '{departure_date.strftime('%#d. %#m. %Y')}';", departure_date_input)
        
        #Set direct conneciton only
        browser.execute_script(f'arguments[0].checked = true', direct_only_input)
        time.sleep(0.8)



        search_route_button.click()

        wait.until(EC.visibility_of_element_located((By.ID, 'j_idt503')))


        # Try to find train ID my loading more routes up to 15 times
        for i in range(15):
            try:
                queried_connection = browser.find_element(By.XPATH, f"//span[contains(text(), '{raw_route_data['train_ID']}')]")
                break
            except NoSuchElementException:
                    try:
                        browser.find_element(By.ID,'j_idt503').click()
                    except Exception:
                        continue
                    time.sleep(1.8)


        # Get distance
        distance = browser.find_element(By.XPATH, f"//span[contains(text(), '{raw_route_data['train_ID']}')]/../../../../../../ \
                                                 div[contains(@class, 'connectionSummary')]/div[contains(@class, 'connectionDistance')]")
        node.distance = distance.text.split()[0]

        # Add to cart
        time.sleep(0.5)
        browser.find_element(By.XPATH, f"//span[contains(text(), '{raw_route_data['train_ID']}')]/../../../../../../div").click()
        time.sleep(0.5)
        cart_button = browser.find_element(By.XPATH, f"//span[contains(text(), '{raw_route_data['train_ID']}')]/../../../../../../../../div[2]/div/div/div[1]/a[1]")
        cart_button.click()


        # Wait for page to load
        wait.until(EC.visibility_of_element_located((By.ID, 'actionIndividualContinue')))


        # Select age category
        browser.find_element(By.XPATH, "//*[contains(@data-cy, 'ageCategory-0')]").click()
        time.sleep(0.5)
        browser.find_element(By.XPATH, "//*[contains(text(), 'Mladý  16 - 25 r.')]").click()
        time.sleep(0.5)

        # Select ISIC discount
        browser.find_element(By.XPATH, "//*[contains(@data-cy, 'discountType-0')]").click()
        time.sleep(0.5)
        browser.find_element(By.XPATH, "//*[contains(text(), 'ISIC aktivovaný školou v SR')]").click()
        time.sleep(0.5)

        # Activate discount
        browser.find_element(By.XPATH, "//*[contains(@data-cy, 'freeTicket-0')]").click()
        time.sleep(0.5) 
        
        # Continue to next tep
        browser.find_element(By.ID, 'actionIndividualContinue').click()

        # Wait for page to load
        wait.until(EC.visibility_of_element_located((By.ID, 'ticketsForm:offerPanel:final-price:j_idt586')))
        browser.find_element(By.ID, 'ticketsForm:offerPanel:final-price:j_idt586').click()

        try:
            time.sleep(1)
            browser.find_element(By.XPATH, "//h1[contains(text(), 'Obsah košíka')]")
        except:
            node.available = False

        while True:
            if browser.current_url == 'https://predaj.zssk.sk/cart':
                node.available = True
                break
            else:
                try:
                    browser.find_element(By.XPATH, "//*[contains(text(), 'Na zvolené spojenie už nie sú k dispozícii bezplatné lístky')]")
                    node.available = False
                    break
                except NoSuchElementException:        
                    pass
        browser.close()
        node = node.next

    print('-'*80)
    print(f"Report for: {raw_route_data['train_ID']} on {raw_route_data['date']} at {raw_route_data['departure_time']}")
    node = nodes
    while node is not None:
        print(f"{node.inbound} -> {node.outbound}, Availability: {node.available}")
        node = node.next


if __name__ == '__main__':
    nodes = generate_station_nodes()
    browser_operation(nodes)