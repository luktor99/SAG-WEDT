import nltk
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
