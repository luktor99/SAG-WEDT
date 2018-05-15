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
    if non_english_percent(tokens) > 0.05:
        return ['xxxxxxxxxx']
    tokens = [token for token in tokens if re.search('^([a-zA-Z]+[\w-]*\w+)$', token)]
    tokens = [token.lower() for token in tokens]
    tokens = [token for token in tokens if token not in set(stopwords.words('english'))]
    tokens = [st.stem(token) for token in tokens]

    return tokens


def doc_gen(path):
    gen = page_gen(path)
    for _, page in gen:
        for doc in page:
            yield doc


def page_gen(path):
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


def is_english(doc):
    try:
        doc.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        return False
    else:
        return True


def non_english_percent(tokens):
    if len(tokens) == 0:
        return 0

    result = 0.
    for token in tokens:
        if not is_english(token):
            result += 1.
    result /= len(tokens)
    return result
