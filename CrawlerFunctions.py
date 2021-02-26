from __future__ import absolute_import
from __future__ import division, print_function, unicode_literals


from urllib.request import urlopen
from urllib.error import URLError
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urlsplit
import re
import pandas as pd


def getTree(searchTerm):
    html_page= urlopen(searchTerm)
    html_tree = BeautifulSoup(html_page,'html.parser')
    return html_tree

def getTitle(head):
    title_string = re.split('\\||-|;|:|,',head.find_all('title')[0].text)
    title_dict = {'title':'','slogan':''}
    #Slogans are often shorter than names
    # Creating a dictionary to assign a title to a title key
    # and a slogan to a slogan key from the title of the page.
    if(len(title_string)>1):
        if(len(title_string[0].split(' '))>len(title_string[1].split(' '))):
            title_dict['title'] = title_string[1]
            title_dict['slogan'] = title_string[0]
        else:
            title_dict['title'] = title_string[0]
            title_dict['slogan'] = title_string[1]
    return title_dict

def getScreenShot(url): # Using Selenium to obtain Screenshots
    from selenium import webdriver
    import os
    wd = os.getcwd()
    try:
        DRIVER = 'chromedriver'
        driver = webdriver.Chrome(DRIVER)
        driver.get(url)
        screenshot = driver.save_screenshot('my_screenshot.png')
        driver.quit()
        return str(wd+'my_screenshot.png')
    except:
        return 'No Screenshot'


def logo_icon(base,tree): # Obtaining Company Logos
    content_a = tree.find_all('a', href=re.compile(".*logo.*"))
    content_img = tree.find_all('img', src=re.compile(".*logo.*"))
    images = []
    for i in content_a:
        if 'href' in i.attrs:
            link = i['href']
            if link.startswith('/'):
                link = base + link
            if link.endswith('.png') or link.endswith('.svg') or link.endswith('.jpg'):
                images.append(link)
    for i in content_img:
        if 'src' in i.attrs:
            link = i['src']
            if link.startswith('/'):
                link = base + link
            if link.endswith('.png') or link.endswith('svg') or link.endswith('.jpg') or link.endswith('glyph'):
                images.append(link)
    return images[0:3]


def summarize(url): #Using Summerizer tool Sumy
    from sumy.parsers.html import HtmlParser
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.lsa import LsaSummarizer as Summarizer
    from sumy.nlp.stemmers import Stemmer
    from sumy.utils import get_stop_words
    import lxml
    import nltk
    nltk.download('stopwords')
    nltk.download('punkt')
    summary = ''
    LANGUAGE = "english"
    SENTENCES_COUNT = 10
    parser = HtmlParser.from_url(url, Tokenizer(LANGUAGE))
    # or for plain text files
    # parser = PlaintextParser.from_file("document.txt", Tokenizer(LANGUAGE))
    stemmer = Stemmer(LANGUAGE)

    summarizer = Summarizer(stemmer)
    summarizer.stop_words = get_stop_words(LANGUAGE)

    for sentence in summarizer(parser.document, SENTENCES_COUNT):
        summary+=str(sentence)
    return summary


def short_Description(url): # Using Summarizer Sumy
    import re
    import requests
    from urllib.parse import urlsplit
    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer
    from sumy.summarizers.lex_rank import LexRankSummarizer
    import nltk
    nltk.download('punkt')
    html = urlopen(url)
    tree = BeautifulSoup(html,'html.parser')
    parts = urlsplit(url)
    base = '{0.netloc}'.format(parts)
    sdesc = ''
    links = tree.find_all('a', {'href': re.compile(base)})
    url = set([i.attrs['href'] for i in links])
    count = 0

    for i in url:
        if (count < 5):
            try:
                page = urlopen(i)
                bs = BeautifulSoup(page, 'html.parser')
                paras = bs.find_all('p')
                for j in paras:
                    sdesc += "\n" + j.text
            except(URLError):
                continue
        count+=1
    gist = ""
    parser = PlaintextParser.from_string(sdesc, Tokenizer("english"))
    # Using LexRank
    summarizer = LexRankSummarizer()
    # Summarize the document with 2 sentences
    summary = summarizer(parser.document, 2)
    for sentence in summary:
        gist +=str(sentence)

    return gist




def crawl_emails(url):
    import re
    import requests
    from urllib.parse import urlsplit
    from collections import deque
    from bs4 import BeautifulSoup
    import pandas as pd

    original_url = url
    parts = urlsplit(url)
    base = "{0.netloc}".format(parts)
    unscraped = deque([original_url])
    scraped = set()
    emails = set()
    linkedin = ''
    counter = 0
    crawl_limit = 20

    pricing = 'No'
    # This part is crucial , Every website has a different amount of links in it and recursive scrapping is sometimes time consuming and at
    # certain times in the day depending on server capacity and internet speed, the api may fail.
    while  len(unscraped) and counter < crawl_limit:
        url = unscraped.popleft()
        scraped.add(url)
        parts = urlsplit(url)
        base_url = "{0.scheme}://{0.netloc}".format(parts) # Splitting URL into Parts to obtain base

        if '/' in parts.path:
            path = url[:url.rfind('/') + 1]
        else:
            path = url

        if base in url:
            print("Crawling URL %s" % url)
            try:
                response = requests.get(url)
            except (
            requests.exceptions.MissingSchema, requests.exceptions.InvalidURL, requests.exceptions.ConnectionError):
                continue

            new_emails = set(re.findall(r"[a-z0-9\.\-+_]+@" +base, response.text, re.I))
            emails.update(new_emails)

            soup = BeautifulSoup(response.text, 'html.parser')

            for anchor in soup.find_all("a"):
                if "href" in anchor.attrs:
                    link = anchor.attrs["href"]
                else:
                    link = ''

                if link.startswith('/'):
                    link = base_url + link

                elif not link.startswith('http'):
                    link = path + link
                elif 'linkedin.com/company' in link:
                    linkedin = link
                elif 'pricing' in link or 'buy' in link or 'courses' in link or 'services' in link:
                    pricing = 'Yes'

            counter += 1
        else:
            continue
    return linkedin, list(emails),pricing

def assemble_Content(url):
    contact = crawl_emails(url)
    html_tree = getTree(url)
    title_dict = getTitle(html_tree.find('head'))
    description = short_Description(url)
    logo = logo_icon(url,html_tree)
    linkedin = contact[0]
    emails = contact[1]
    pricing = contact[2]
    screenshot = getScreenShot(url)
    summary =summarize(url)

    response = {'name': title_dict['title'], 'slogan': title_dict['slogan'], 'logo': logo, 'Screenshot': screenshot, 'description':description,
                'emails': emails, 'Summary': summary, 'Linkedin': linkedin, 'pricing':pricing}
    return response
# This part onwards is to push data into a local Data Table .csv.
def data_push(url,response):
    import pandas as pd
    inpt = pd.read_csv('index.csv')
    #inpt = format_df(inpt) # Uncomment Only if data is not formated
    inpt.set_index('website', inplace=True)
    inpt.at[url,'company'] =response['name'].capitalize()
    inpt.at[url,'title'] = response['name']
    inpt.at[url,'screenshot'] = response['Screenshot']
    inpt.at[url,'description']=response['description']
    inpt.at[url,'logo'] = response['logo']
    inpt.at[url,'emails'] = response['emails']
    inpt.at[url,'linkedin'] = response['Linkedin']
    inpt.at[url,'summary']=response['Summary']
    inpt.at[url,'paid'] = response['pricing']

    inpt.to_csv('index.csv',index=True)

def format_df(df):

    df = df.astype(
        {'Company_Name': 'str', 'Title': 'str', 'Website image/screenshot': 'str', 'Short_Description': 'str',
         'company_icon': 'str', 'contact_email': 'str', 'LinkedIn': 'str', 'Summarize the website content': 'str',
         'Is the website has paid service?': 'str'})
    df.rename(columns={'Given_Website': 'website', 'Company_Name': 'company', 'Title': 'title',
                         'Website image/screenshot': 'screenshot', 'Short_Description': 'description',
                         'company_icon': 'logo', 'contact_email': 'emails', 'LinkedIn': 'linkedin',
                         'Summarize the website content': 'summary', 'Is the website has paid service?': 'paid'},
                inplace=True)


    return df