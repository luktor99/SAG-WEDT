import asyncio
import os
import pickle
from functools import partial
from gensim import corpora
from pulsar.api import get_actor
from src import nlp_utils
from src.Agency import Agency
from src.ghinterface import GHInterface


async def work(arg, gh):
    json = gh.get_page(arg)
    tokens = []
    for repo in json:
        print(get_actor().name + ': Przetwarzam ' + repo['name'])
        tokens.append(nlp_utils.extract_tokens_from_markdown(repo['readme']))
        await asyncio.sleep(0.5)
    filename = 'corpus' + str(arg) + '.crp'
    with open('../resources/dictionary/corpus/' + filename, 'wb') as f:
        pickle.dump(tokens, f)


def work_gen():
    gh = GHInterface()
    for i in range(1, gh.get_pages_count() + 1):
        yield partial(work, i, gh)


async def arbiter_last_task():
    print('arbiter: Zaczynam tworzenie słownika')
    path = '../resources/dictionary/corpus/'
    filenames = []
    for (_, _, names) in os.walk(path):
        filenames.extend(names)
        break
    dictionary = corpora.Dictionary()
    for name in filenames:
        with open(path + name, 'rb') as f:
            docs = pickle.load(f)
            dictionary.add_documents(docs)

    dictionary.filter_extremes(no_below=0, no_above=0.5, keep_n=None)
    dictionary.compactify()
    dictionary.save('../resources/dictionary/dictionary.dict')
    print('arbiter: Tworzenie słownika zakończone!')


if __name__ == '__main__':
    Agency(10, work_gen=work_gen(), arbiter_last_task=arbiter_last_task)
