import json
import os.path
import re
import sys

import email.policy
from email import message_from_file
from bs4 import BeautifulSoup
from collections import namedtuple
import requests

def header_field_names(message):
    return m.keys()

def get_inner_tables(soup):
    return soup.find_all('table', attrs={'class':'inner'}, recursive=True)

def get_wrapper_tables(soups):
    for soup in soups:
        for wt in soup.find_all('table', attrs={'class':'wrapper'}):
            yield wt

Part = namedtuple('Part', ('image_url', 'part_mfr', 'part_dk', 'desc'))
OrderDetail = namedtuple('OrderDetail', ('qty', 'backorder', 'unit_price', 'ext_price'))

def extract_part_info(tab):
    for tr in tab.find_all('tr'):
        tds = list(tr.find_all('td'))
        if len(tds) != 2:
            return None
        image_td, info_td = tds
        info = list(info_td.stripped_strings)
        return Part(image_td.a.img['src'], info[0], info[1], info[2])

def extract_other_info(tab):
    trs = list(tab.tbody.find_all('tr'))
    if len(trs) < 4:
        return None
    info = tuple(trs[3].stripped_strings)
    if len(info) != 4:
        return None
    # qty, backorder, unit_price, ext_price = info
    return OrderDetail(*info)

Order = namedtuple('Order', ('no', 'part', 'detail'))

def get_orders_from_email_file(filename):
    with open(filename, 'r') as file:
        m = message_from_file(file, policy=email.policy.default)
        payload = m.get_body().get_payload(decode=True)
        soup = BeautifulSoup(payload, 'html.parser')
        order_no = None
        for s in list(soup.find_all('table', attrs={'class':'wrapper'}, recursive=True))[0].tbody.tr.td.table.tbody.stripped_strings:
            m = re.match('.*salesorder number is ([0-9]+).', s)
            if m:
                order_no = m.group(1)
                break

        inner_tables = get_inner_tables(soup)

        part = None
        for it in inner_tables:
            for i, tab in enumerate(it.tr.td.find_all('table')):
                if i == 0:
                    part = extract_part_info(tab)
                elif i == 1:
                    if part is not None:
                        detail = extract_other_info(tab)
                        if detail is None:
                            raise Exception('No detail??')
                        order = Order(order_no, part, detail)
                        part = None
                        yield order

def normalize_part_number(pn):
    return re.sub('[^a-zA-Z0-9_-]+', '_', pn)

# 'raw/Thank you for your Digi-Key order! - Digi-Key <orders@t.digikey.com> - 2020-01-28 0006.eml'

orders = []
for email_filename in sys.argv[1:]:
    order_no = None
    for order in get_orders_from_email_file(email_filename):
        image_filename = None
        url = order.part.image_url
        part_no = normalize_part_number(order.part.part_dk)
        image_filename = url.split("/")[-1]
        image_filename = ''.join(('images/', part_no, os.path.splitext(image_filename)[1]))
        if not os.path.isfile(image_filename):
            print('Fetching image for', part_no)
            with requests.get(url) as response:
                with open(image_filename, 'wb') as file:
                    file.write(response.content)
        if order.no is not None:
            order_no = order.no
        orders.append({'no': order.no, 'part': order.part._asdict(), 'detail': order.detail._asdict()})
print(json.dumps(orders, indent=2))

# /html/body/table/tbody/tr/td/table/tbody/tr[1]/td/table/tbody/tr[13]/td/table/tbody/tr[1]/td/table[1]/tbody/tr/td[2]/strong[1]

# .html.body.table.tbody.tr.td.table.tbody.
