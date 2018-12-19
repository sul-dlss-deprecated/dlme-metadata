from lxml import etree
import urllib.request
import os
from math import ceil
import time
import re

# Add key-value pairs where the key is the file name and the value is the url to the first page in the search results
BnF_data = {
    'ifea': 'https://gallica.bnf.fr/services/engine/search/sru?operation=searchRetrieve&version=1.2&startRecord=0&maximumRecords=50&page=1&collapsing=true&exactSearch=false&query=dc.source%20all%20%22Institut%20Fran%C3%A7ais%20d%E2%80%99%C3%89tudes%20Anatoliennes%22%20%20and%20%28provenance%20adj%20%22bnf.fr%22%29',
    'salt': 'https://gallica.bnf.fr/services/engine/search/sru?operation=searchRetrieve&version=1.2&startRecord=0&maximumRecords=50&page=1&collapsing=true&exactSearch=false&query=%28provenance%20adj%20%22saltresearch%22%29',
    'bo': 'https://gallica.bnf.fr/services/engine/search/sru?operation=searchRetrieve&version=1.2&startRecord=0&maximumRecords=50&page=1&collapsing=true&exactSearch=false&query=dc.source%20all%20%22Biblioth%C3%A8que%20Orientale%22%20%20and%20%28provenance%20adj%20%22bnf.fr%22%29',
    'ebaf': 'https://gallica.bnf.fr/services/engine/search/sru?operation=searchRetrieve&version=1.2&startRecord=0&maximumRecords=50&page=1&collapsing=true&exactSearch=false&query=dc.source%20all%20%22%20Ecole%20biblique%20et%20arch%C3%A9ologique%20fran%C3%A7aise%20de%20J%C3%A9rusalem%22%20%20and%20%28provenance%20adj%20%22bnf.fr%22%29',
    'cealex': 'https://gallica.bnf.fr/services/engine/search/sru?operation=searchRetrieve&version=1.2&startRecord=0&maximumRecords=50&page=1&collapsing=true&exactSearch=false&query=dc.source%20all%20%22cealex%22%20%20and%20%28provenance%20adj%20%22bnf.fr%22%29',
    'ideo': 'https://gallica.bnf.fr/services/engine/search/sru?operation=searchRetrieve&version=1.2&startRecord=0&maximumRecords=15&page=1&collapsing=true&exactSearch=false&query=%28%28bibliotheque%20adj%20%22Institut%20dominicain%20d%27%C3%A9tudes%20orientales%22%29%29#resultat-id-3',     
    'ifao': 'https://gallica.bnf.fr/services/engine/search/sru?operation=searchRetrieve&version=1.2&startRecord=0&maximumRecords=50&page=1&collapsing=true&exactSearch=false&query=dc.source%20all%20%22Institut%20fran%C3%A7ais%20d%E2%80%99arch%C3%A9ologie%20orientale%22%20%20and%20%28provenance%20adj%20%22bnf.fr%22%29',
}

# add all namespaces
ns = {'srw': "http://www.loc.gov/zing/srw/"}


def to_str(bytes_or_str):
    '''Takes bytes or string and returns string'''
    if isinstance(bytes_or_str, bytes):
        value = bytes_or_str.decode('utf-8')
    else:
        value = bytes_or_str

    return value # Instance of str


def base_url_to_xml(base_url):
    '''Takes a url to a search results webpage from gallica and returns a url to the xml data of the objects displayed in that page'''
    url_for_xml_file = base_url.replace('https://gallica.bnf.fr/services/engine/search/sru?', 'https://gallica.bnf.fr/SRU?')

    return url_for_xml_file


def get_number_of_records(url):
    '''Reads in an xml file from a provided url and retrieves the value in the numberOfRecords 
    element.''' 
    url = base_url_to_xml(url)
    site = urllib.request.urlopen(url)
    contents = site.read()
    file = open('temp.xml', 'w')
    file.write(to_str(contents))
    file.close()
    tree = etree.ElementTree(file='temp.xml')
    number_of_records = tree.find('srw:numberOfRecords', ns).text
    os.remove('temp.xml')

    return number_of_records
 

def records_viewed_per_page(url):
    '''Takes a url and extracts the number of records viewed'''
    text_before = url[:url.index("maximumRecords=")]
    text_before_stripped = url.strip(text_before).strip("maximumRecords=")
    number_records_per_page = text_before_stripped[:text_before_stripped.index("&page")]

    return number_records_per_page


def get_urls(url):
    '''takes the base url and returns a list of urls for all subsequent pages. The number of records is limited to 50 per page so each 
    collection will be spread over multiple pages (the numberOfRecords divided by 50 and rounded up one digit).'''
    number_of_records = get_number_of_records(url) 
    url = base_url_to_xml(url)
    number_records_per_page = int(records_viewed_per_page(url))
    number_of_pages = ceil(int(number_of_records) / number_records_per_page)
    urls = []
    urls.append(url)
    page_count = 1
    record_count = 0
    for i in range(number_of_pages - 1):
        next_url = url
        next_url = next_url.replace('page=1', 'page=' + str(page_count + 1))
        next_url = next_url.replace('startRecord=0', 'startRecord=' + str(record_count + number_records_per_page))
        urls.append(next_url)
        page_count += 1
        record_count += number_records_per_page 
        
    return urls


def main():
    '''Reads in a dictionary of form 'file_name: base_url', passes base_url to get_urls, then iterates over the list of urls-one for 
    each page of records–and saves the xml from each page to a file'''    
    for key, value in BnF_data.items():
        urls = get_urls(value)
        file_count = 1

        # Get the xml surrounding the set of records 
        base_file_contents = urllib.request.urlopen(urls[0]).read()
        base_file_name = 'base.xml'
        base_file = open(base_file_name, 'w')
        base_file.write(to_str(base_file_contents))
        base_file.close()
        base_tree = etree.parse(base_file_name)
        root = base_tree.find('srw:searchRetrieveResponse', ns)
        number_of_records = get_number_of_records(value)

        # Get a list of records from the collection
        records = base_tree.find('srw:records', ns)

        # Debugging delete
        print('{0}: {1} of {2} records'.format(key, len(records), number_of_records ))

        for url in urls[1:]:
            site = urllib.request.urlopen(url)
            temp_contents = site.read()
            directory_name = '{0}/data/'.format(key) #'data/'+key+str(file_count)+'.xml'
            if not os.path.exists(directory_name):
                os.makedirs(directory_name)
            temp_file_name = '{0}{1}.xml'.format(key, str(file_count))
            temp_file = open(temp_file_name, 'w')
            temp_file.write(to_str(temp_contents))
            temp_file.close()
            temp_tree = etree.parse(temp_file_name)
            temp_records = temp_tree.find('srw:records', ns)
            children = list(temp_records)
            for child in children:
            	records.append(child)
            os.remove(temp_file_name)
            file_count += 1
            time.sleep(3)        
        
            # Debugging delete
            print('{0}: {1} of {2} records'.format(key, len(records), number_of_records ))


        out_file = '{0}/data/{1}.xml'.format(key, key) 
        with open(out_file, 'w') as f:
        	f.write(etree.tostring(records, encoding='unicode', pretty_print=True))
        f.close()
        os.remove(base_file_name)

        # Quality Assurance Testing
        stats = open('{0}/{1}_stats.txt'.format(key, key), 'w')
        record_count = 0
        for record in records:
        	record_count += 1 
        if number_of_records == record_count:
        	stats.write("Number of records = {0}".format(record_count))
        else:
        	stats.write("Error: expected {0} records, read {1} records".format(number_of_records, record_count))
        stats.close()


if __name__ == "__main__":
    main()
