import asyncio
import pickle
from functools import partial
from gensim import corpora, models
from pulsar.api import get_actor
from src import nlp_utils
from src.Agency import Agency


async def work(name, docs):
    print(get_actor().name + ': Przetwarzam plik ' + name)
    bows = []
    for doc in docs:
        bows.append(get_actor().extra['dict'].doc2bow(doc))
    with open('../resources/bow/corpus/' + name, 'wb') as f:
        pickle.dump(bows, f)
    await asyncio.sleep(1)


def work_gen():
    gen = nlp_utils.page_corpus_gen('../resources/dictionary/corpus/')
    for name, doc in gen:
        yield partial(work, name, doc)


def actor_init_task():
    print(get_actor().name + ': Wczytuję słownik...')
    dictionary = corpora.Dictionary.load('../resources/dictionary/dictionary.dict')
    get_actor().extra['dict'] = dictionary


async def arbiter_last_task():
    print(get_actor().name + ': Tworzę model tfidf')
    dictionary = corpora.Dictionary.load('../resources/dictionary/dictionary.dict')
    corpus_gen = nlp_utils.doc_corpus_gen('../resources/bow/corpus/')
    tfidf = models.TfidfModel(corpus=corpus_gen, id2word=dictionary)
    tfidf.save('../resources/tfidf/model.tfidf')
    print(get_actor().name + ': Model tfidf utworzony')


if __name__ == '__main__':
    Agency(10, work_gen=work_gen(),
           actor_init_task=actor_init_task,
           arbiter_last_task=arbiter_last_task)
