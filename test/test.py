import json
import nltk
import pickle
import re
from bs4 import BeautifulSoup
from gensim import corpora
from gensim import models
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer
from markdown2 import markdown


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


if __name__ == '__main__':
    # Dictionary and tokens
    # with open('../gh-database/page1.json', 'r') as f:
    #     file = json.loads(f.read())
    #     readme_tokens = []
    #     for repo in file:
    #         print('Processing ' + repo['name'] + 'repository...')
    #         readme = repo['readme']
    #         readme_tokens.append(extract_tokens_from_markdown(readme))
    #     with open('../resources/tokens/tokens1.tk', 'wb') as tokens_file:
    #         pickle.dump(readme_tokens, tokens_file)
    #
    #     dictionary = corpora.Dictionary()
    #     dictionary.add_documents(readme_tokens)
    #     dictionary.filter_extremes(no_below=0, no_above=0.5, keep_n=None)
    #     dictionary.save('../resources/bow/dictionary1.dict')

    # BoW corpus
    # readme_tokens = 0
    # dictionary = corpora.Dictionary.load('../resources/bow/dictionary1.dict')
    # with open('../resources/tokens/tokens1.tk', 'rb') as f:
    #     readme_tokens = pickle.load(f)
    # bows = [dictionary.doc2bow(token) for token in readme_tokens]
    # with open('../resources/bow/bows1.bow', 'wb') as bows_file:
    #     pickle.dump(bows, bows_file)

    # Tfidf
    # corpus = 0
    # with open('../resources/bow/bows1.bow', 'rb') as f:
    #     corpus = pickle.load(f)
    # tfidf = models.TfidfModel(corpus)
    # tfidf.save('../resources/tfidf/model.tfidf')

    # Tfidf corpus
    # tfidf = models.TfidfModel.load('../resources/tfidf/model.tfidf')
    # corpus = 0
    # with open('../resources/bow/bows1.bow', 'rb') as f:
    #     corpus = pickle.load(f)
    # corpus_tfidf = tfidf[corpus]
    # with open('../resources/tfidf/corpus1.tfidf', 'wb') as f:
    #     pickle.dump(corpus_tfidf, f)

    # Lsi
    corpus_tfidf = 0
    with open('../resources/tfidf/corpus1.tfidf', 'rb') as f:
        corpus_tfidf = pickle.load(f)
    dictionary = corpora.Dictionary.load('../resources/bow/dictionary1.dict')
    lsi = models.LsiModel(corpus=corpus_tfidf, id2word=dictionary, num_topics=300)
    lsi.save('../resources/lsi/model.lsi')

    # Lsi corpus and indexing

    # Search
