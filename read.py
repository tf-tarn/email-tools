import email.policy
from email import message_from_file
from bs4 import BeautifulSoup

def header_field_names(message):
    return m.keys()

with open('raw/Thank you for your Digi-Key order! - Digi-Key <orders@t.digikey.com> - 2020-01-28 0006.eml', 'r') as file:
    m = message_from_file(file, policy=email.policy.default)
    print(dir(m))
    print(header_field_names(m))
    print(m['Message-ID'])
    payload = m.get_body().get_payload(decode=True)
    soup = BeautifulSoup(payload, 'html.parser')

    print(soup.prettify())
