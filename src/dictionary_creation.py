import asyncio
import pickle
from functools import partial
from gensim import corpora
from pulsar.api import get_actor
from src import config
from src import nlp_utils
from src.Agency import Agency
from src.ghinterface import GHInterface


async def work(arg, gh):
    json = gh.get_page(arg)
    tokens = []
    for repo in json:
        print(get_actor().name + ': Przetwarzam ' + repo['name'])
        tokens.append(nlp_utils.extract_tokens_from_markdown(repo['readme']))
        await asyncio.sleep(config.middle_task_wait)
    filename = 'corpus' + str(arg) + '.crp'
    with open(config.tokenized_corpus_path + filename, 'wb') as f:
        pickle.dump(tokens, f)


def work_gen():
    gh = GHInterface()
    for i in range(1, gh.get_pages_count() + 1):
        yield partial(work, i, gh)


async def arbiter_last_task():
    print(get_actor().name + ': Zaczynam tworzenie słownika')
    gen = nlp_utils.doc_gen(config.tokenized_corpus_path)
    dictionary = corpora.Dictionary(gen)
    dictionary.filter_extremes(no_below=0, no_above=0.5, keep_n=None)
    dictionary.compactify()
    dictionary.save(config.dictionary_path)
    print(get_actor().name + ': Tworzenie słownika zakończone!')


if __name__ == '__main__':
    Agency(config.agents_count['dict'], work_gen=work_gen(),
           arbiter_last_task=arbiter_last_task)
