import json
import links_from_header
import nltk
import time
import pickle
import re
import requests
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from requests.auth import HTTPBasicAuth
from test import config


def safe_request(link):
    auth = HTTPBasicAuth(config.login, config.password)
    while True:
        try:
            response = requests.get(link, auth=auth)
            if response.status_code == 200 or response.status_code == 400:
                break
        except requests.exceptions.ConnectionError:
            print('Waiting 10 seconds...')
            print(link)
            time.sleep(10)
            continue
        print('Waiting 10 seconds...')
        print(link)
        time.sleep(10)
    return response


def find_files(repo, pattern):
    result = []
    download_prefix = 'https://raw.githubusercontent.com/'
    file_id_regex = re.compile('.*blob(.*)\\b')
    link = 'https://api.github.com/search/code?q=' + pattern + '%20in:path+repo:' + repo
    response = safe_request(link)
    for element in json.loads(response.content)['items']:
        file_id = file_id_regex.search(element['html_url']).group(1)
        link = download_prefix + repo + file_id
        file = safe_request(link)
        result.append(file.content)

    return result


def tokenize(document, re_filter, stop_words):
    st = PorterStemmer()
    try:
        tokens = nltk.word_tokenize(document.decode('utf-8'))
    except UnicodeDecodeError:
        return []
    tokens = [t.lower() for t in tokens]
    tokens = [st.stem(t) for t in tokens if t not in stop_words and re_filter.match(t)]
    return tokens


def github_corpus_generator():
    link = 'https://api.github.com/search/repositories?q=stars:%3E=8000'
    re_filter = re.compile('[a-zA-Z]+')
    stop_words = set(stopwords.words('english'))

    while True:
        response = safe_request(link)
        for repo in json.loads(response.content)['items']:
            readme_files = find_files(repo['full_name'], 'readme')
            for document in readme_files:
                result = tokenize(document, re_filter, stop_words)
                if len(result) > 0:
                    yield result

        links = links_from_header.extract(response.headers['link'])
        if 'next' not in links.keys():
            break
        link = links['next']
        print('Next page...')


if __name__ == '__main__':
    with open('texts.txt', 'wb') as f:
        for text in github_corpus_generator():
            print(text)
            pickle.dump(text, f)
