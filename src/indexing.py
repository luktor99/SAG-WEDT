import asyncio
import pickle
from functools import partial
from gensim import models, similarities
from pulsar.api import get_actor
from src import config
from src import nlp_utils
from src.Agency import Agency


async def work(name, docs):
    print(get_actor().name + ': Przetwarzam plik ' + name)
    corpus = []
    for doc in docs:
        corpus.append(get_actor().extra['lsi'][doc])
    with open(config.lsi_corpus_path + name, 'wb') as f:
        pickle.dump(corpus, f)

    index = similarities.MatrixSimilarity(corpus)
    index_name = 'index' + nlp_utils.get_id_from_name(name) + '.idx'
    index.save(config.index_path + index_name)
    await asyncio.sleep(config.middle_task_wait)


def work_gen():
    gen = nlp_utils.page_gen(config.tfidf_corpus_path)
    for name, doc in gen:
        yield partial(work, name, doc)


def actor_init_task():
    print(get_actor().name + ': Wczytuję model lsi...')
    lsi = models.LsiModel.load(config.lsi_model_path)
    get_actor().extra['lsi'] = lsi


if __name__ == '__main__':
    Agency(config.agents_count['index'], work_gen=work_gen(), actor_init_task=actor_init_task)
