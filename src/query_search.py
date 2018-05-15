import asyncio
import pickle
from functools import partial
from gensim import corpora, models
from pulsar.api import command, get_actor, send
from src import nlp_utils
from src.Agency import Agency
from src.ghinterface import GHInterface


async def work(index, name, query):
    print(get_actor().name + ': Przetwarzam plik ' + name)
    page_id = int(nlp_utils.get_id_from_name(name))
    page = get_actor().extra['gh'].get_page(page_id)
    sims = index[query]

    result = []
    for i, elem in enumerate(sims):
        result.append({'score': elem,
                       'name': page[i]['name'],
                       'url': page[i]['html_url']})
    result += get_actor().extra['result']
    result = sorted(result, key=lambda x: -x['score'])[:20]
    get_actor().extra['result'] = result
    await asyncio.sleep(0.5)


def work_gen(query):
    gen = nlp_utils.page_gen('../resources/index/')

    query = nlp_utils.extract_tokens_from_markdown(query)
    query = get_actor().extra['dict'].doc2bow(query)
    query = get_actor().extra['tfidf'][query]
    query = get_actor().extra['lsi'][query]

    for name, index in gen:
        yield partial(work, index, name, query)


def arbiter_init_task():
    get_actor().extra['dict'] = corpora.Dictionary.load('../resources/dictionary/dictionary.dict')
    get_actor().extra['tfidf'] = models.TfidfModel.load('../resources/tfidf/model.tfidf')
    get_actor().extra['lsi'] = models.LsiModel.load('../resources/lsi/model.lsi')
    get_actor().extra['results'] = []


async def arbiter_last_task():
    print(get_actor().name + ': Porządkuję wyniki')
    result = sorted(get_actor().extra['results'], key=lambda x: -x['score'])[:20]
    print('\n\n')
    for elem in result:
        print(elem)
    print('\n\n')
    with open('../resources/result.pickle', 'wb') as f:
        pickle.dump(result, f)
    print(get_actor().name + ': Wyniki zapisano do ../resources/result.json')


def actor_init_task():
    get_actor().extra['gh'] = GHInterface()
    get_actor().extra['result'] = []


async def actor_last_task():
    print(get_actor().name + ': Przesyłam wyniki')
    result = get_actor().extra['result']
    await send(get_actor().monitor, 'save_partial_result', result)


@command()
def save_partial_result(_, result):
    get_actor().extra['results'] += result


if __name__ == '__main__':
    query = input('Please insert your query: ')

    Agency(10, work_gen=work_gen(query),
           arbiter_init_task=arbiter_init_task,
           arbiter_last_task=arbiter_last_task,
           actor_init_task=actor_init_task,
           actor_last_task=actor_last_task)
