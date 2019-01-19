
import csv
import requests
from bs4 import BeautifulSoup
from urllib.request import urlopen
import json
import re
import datetime
from time import sleep

now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d-%H-%M")
pattern = re.compile('[\W_]+')
mesh_url = 'http://nyzo.co/mesh'
block_url = 'http://nyzo.co/block/last'
balance_url = 'https://nyzo.co/balanceListPlain/'
balance = 0
count = 0

request_url = requests.get(block_url)
page_decoded = request_url.content.decode('utf-8')
start_position = page_decoded.find('<h1>Nyzo block ')
end_position = page_decoded.find('</h1><h2>hash')
block_number = str(page_decoded[start_position + 15: end_position])
balance_url = balance_url + block_number
request_url = requests.get(balance_url)

balance_list_decoded = request_url.content.decode('utf-8')

csv_data = [['IP', 'Name', 'Public identifier', 'Balance', 'Host provider']]
with open('nodes.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(csv_data)

start_pos_filter = 'italic;">Current cycle:'
end_pos_filter = '.cycle-event a:link { text-decoration: none; } .cycle-event a:hover { text-decoration:'

request_url = requests.get(mesh_url)
page_decoded = request_url.content.decode('utf-8')
start_position = page_decoded.find(start_pos_filter)
end_position = page_decoded.find(end_pos_filter)
cycle_page = str(page_decoded[start_position: end_position])

soup = BeautifulSoup(cycle_page, "lxml")
urls = []
for link in soup.findAll('a'):
    pre_url = link.get('href')
    full_url = 'https://nyzo.co' + pre_url
    urls.append(full_url)

pub_id_filter = 'Full identifier</h3><ul><li>'
end_pub_id_filter = '</li></ul><h3>N'

ip_filter = '<div class="verifier verifier-active">IP address: '
end_ip_filter = '<br>last queried'

name_filter = '<br>nickname: '
end_name_filter = '<br>version:'

for node in urls:
    request_url = requests.get(node)
    node_page_content = request_url.content.decode('utf-8')

    start_pos_pub_id_filter = node_page_content.find(pub_id_filter) + len(pub_id_filter)
    start_pos_ip_filter = node_page_content.find(ip_filter) + len(ip_filter)
    start_pos_name_filter = node_page_content.find(name_filter) + len(name_filter)
    end_pos_name_filter = node_page_content.find(end_name_filter)
    end_pos_ip_filter = node_page_content.find(end_ip_filter)
    end_pos_pub_id_filter = node_page_content.find(end_pub_id_filter)

    nickname_clean = node_page_content[start_pos_name_filter:end_pos_name_filter]
    ip_address_clean = node_page_content[start_pos_ip_filter:end_pos_ip_filter]
    public_id_clean = node_page_content[start_pos_pub_id_filter:end_pos_pub_id_filter]

    public_id = public_id_clean + "     ∩"
    start_position = balance_list_decoded.find(public_id) + 73
    end_position = start_position + 25
    split_me = (balance_list_decoded[start_position:end_position]).split(" ")
    temp_bal = split_me[0]

    # addresses with zero balance disappear from the balance list, thus we will grab wrong data
    # and attempt to make this a float, this will fail but balance is zero
    try:
        temp_bal = float(temp_bal)
    except:
        temp_bal = 0

    sleep(1.5)  # api limit
    try:
        if len(ip_address_clean) < 50:
            ip_info_response = urlopen("http://ip-api.com/json/" + ip_address_clean)
            geo = json.load(ip_info_response)
            status = geo["status"]
            if status == 'success':
                ip_isp = geo["isp"]
            else:
                ip_isp = "ERROR"
                print('STATUS NOK: Unable to retrieve IP info for: ' + str(ip_address_clean) + '\nNickname: ' +
                      nickname_clean)
        else:
            ip_isp = "ERROR"
            ip_address_clean = "0.0.0.0"
    except:
        sleep(2)
        try:
            if len(ip_address_clean) < 50:
                ip_info_response = urlopen("http://ip-api.com/json/" + ip_address_clean)
                geo = json.load(ip_info_response)
                status = geo["status"]
                if status == 'success':
                    ip_isp = geo["isp"]
                else:
                    ip_isp = "ERROR"
                    print('STATUS NOK: Unable to retrieve IP info for: ' + str(ip_address_clean))
            else:
                ip_isp = "ERROR"
                ip_address_clean = "0.0.0.0"
        except:
            ip_isp = "ERROR"
            print('LOAD NOK: Unable to retrieve IP info for: ' + str(ip_address_clean))

    row = [str(ip_address_clean), str(nickname_clean), str(public_id_clean), str(temp_bal), str(ip_isp)]
    print('Appending info about ' + nickname_clean)

    with open('nodes.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(row)
