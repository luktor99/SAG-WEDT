import asyncio
import pickle
from functools import partial
from gensim import corpora, models
from pulsar.api import get_actor
from src import nlp_utils
from src.Agency import Agency


async def work(name, docs):
    print(get_actor().name + ': Przetwarzam plik ' + name)
    corpus = []
    for doc in docs:
        corpus.append(get_actor().extra['tfidf'][doc])
    with open('../resources/tfidf/corpus/' + name, 'wb') as f:
        pickle.dump(corpus, f)
    await asyncio.sleep(1)


def work_gen():
    gen = nlp_utils.page_corpus_gen('../resources/bow/corpus/')
    for name, doc in gen:
        yield partial(work, name, doc)


def actor_init_task():
    print(get_actor().name + ': Wczytuję model tfidf...')
    tfidf = corpora.Dictionary.load('../resources/tfidf/model.tfidf')
    get_actor().extra['tfidf'] = tfidf


async def arbiter_last_task():
    print(get_actor().name + ': Tworzę model lsi')
    dictionary = corpora.Dictionary.load('../resources/dictionary/dictionary.dict')
    corpus_gen = nlp_utils.doc_corpus_gen('../resources/tfidf/corpus/')
    lsi = models.LsiModel(corpus=corpus_gen, id2word=dictionary)
    lsi.save('../resources/lsi/model.lsi')
    print(get_actor().name + ': Model lsi utworzony')


if __name__ == '__main__':
    Agency(10, work_gen=work_gen(),
           actor_init_task=actor_init_task,
           arbiter_last_task=arbiter_last_task)
