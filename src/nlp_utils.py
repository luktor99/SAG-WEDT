import nltk
import os
import pickle
import re
from bs4 import BeautifulSoup
from markdown2 import markdown
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer


def extract_tokens_from_markdown(document):
    html = markdown(document)
    text = BeautifulSoup(html, 'html5lib').findAll(text=True)
    text = "".join(text)
    text = text.replace("\\n", " ")

    st = PorterStemmer()
    tokens = nltk.word_tokenize(text)
    tokens = [token for token in tokens if re.search('^([a-zA-Z]+[\w-]*\w+)$', token)]
    tokens = [token.lower() for token in tokens]
    tokens = [token for token in tokens if token not in set(stopwords.words('english'))]
    tokens = [st.stem(token) for token in tokens]

    return tokens


def doc_corpus_gen(path):
    gen = page_corpus_gen(path)
    for _, page in gen:
        for doc in page:
            yield doc


def page_corpus_gen(path):
    filenames = []
    for (_, _, names) in os.walk(path):
        filenames.extend(names)
        break
    for name in filenames:
        with open(path + name, 'rb') as f:
            page = pickle.load(f)
            yield name, page


def get_id_from_name(name):
    match = re.match('^.*?([0-9]+)\..*$', name)
    return match.group(1)
