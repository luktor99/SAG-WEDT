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
    corpus = []
    for doc in docs:
        corpus.append(get_actor().extra['tfidf'][doc])
    with open(config.tfidf_corpus_path + name, 'wb') as f:
        pickle.dump(corpus, f)
    await asyncio.sleep(config.middle_task_wait)


def work_gen():
    gen = nlp_utils.page_gen(config.bow_corpus_path)
    for name, doc in gen:
        yield partial(work, name, doc)


def actor_init_task():
    print(get_actor().name + ': Wczytuję model tfidf...')
    tfidf = models.TfidfModel.load(config.tfidf_model_path)
    get_actor().extra['tfidf'] = tfidf


async def arbiter_last_task():
    print(get_actor().name + ': Tworzę model lsi')
    dictionary = corpora.Dictionary.load(config.dictionary_path)
    corpus_gen = nlp_utils.doc_gen(config.tfidf_corpus_path)
    lsi = models.LsiModel(corpus=corpus_gen, id2word=dictionary, num_topics=config.lsi_topics)
    lsi.save(config.lsi_model_path)
    print(get_actor().name + ': Model lsi utworzony')


if __name__ == '__main__':
    Agency(config.agents_count['lsi'], work_gen=work_gen(),
           actor_init_task=actor_init_task,
           arbiter_last_task=arbiter_last_task)
