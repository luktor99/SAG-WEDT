import asyncio
import pickle
from functools import partial
from gensim import corpora, models
from pulsar.api import get_actor
from src import config
from src import nlp_utils
from src.Agency import Agency


async def work(name, docs):
    print(get_actor().name + ': Przetwarzam plik ' + name)
    bows = []
    for doc in docs:
        bows.append(get_actor().extra['dict'].doc2bow(doc))
    with open(config.bow_corpus_path + name, 'wb') as f:
        pickle.dump(bows, f)
    await asyncio.sleep(config.middle_task_wait)


def work_gen():
    gen = nlp_utils.page_gen(config.tokenized_corpus_path)
    for name, doc in gen:
        yield partial(work, name, doc)


def actor_init_task():
    print(get_actor().name + ': Wczytuję słownik...')
    dictionary = corpora.Dictionary.load(config.dictionary_path)
    get_actor().extra['dict'] = dictionary


async def arbiter_last_task():
    print(get_actor().name + ': Tworzę model tfidf')
    dictionary = corpora.Dictionary.load(config.dictionary_path)
    corpus_gen = nlp_utils.doc_gen(config.bow_corpus_path)
    tfidf = models.TfidfModel(corpus=corpus_gen, id2word=dictionary)
    tfidf.save(config.tfidf_model_path)
    print(get_actor().name + ': Model tfidf utworzony')


if __name__ == '__main__':
    Agency(config.agents_count['tfidf'], work_gen=work_gen(),
           actor_init_task=actor_init_task,
           arbiter_last_task=arbiter_last_task)
