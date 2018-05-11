import asyncio
from functools import partial
from time import sleep
from pulsar.api import arbiter, command, spawn, send, ensure_future
from pulsar.async.actor import get_actor


def work(arg):
    print('Pracuję: ' + str(arg))


def work_gen():
    for i in range(100):
        yield partial(work, i)


def final_work():
    pass


def actor_init_task():
    '''Pierwsze zadanie aktora początkowa aktora'''
    print(str(get_actor().name) + ': Moje pierwsze zadanie')

def actor_last_job():
    '''Ostatenie zadanie aktora'''
    print(str(get_actor().name) + ': Oto moja ostatnia przysługa, Panie Pawle!')
    sleep(1)
    print(str(get_actor().name) + ': Skończyłem ostatnią przysługę, Panie Pawle!')


@command()
def _assign_work(request):
    print(request)
    me = get_actor()
    try:
        task = next(me.extra['gen'])
        return task
    except StopIteration:
        pass


class Arbiter:
    def __init__(self, work_gen, final_work, actor_init_task, actor_last_task):
        arbiter().extra['gen'] = work_gen
        self.final_work = final_work
        self.actor_init_task = actor_init_task
        self.actor_last_task = actor_last_task
        self.id = 23
        arbiter()._loop.call_later(1, self)
        arbiter().start()

    def __call__(self):
        ensure_future(self._arbiter_work())

    async def _arbiter_work(self):
        actors = []
        arbiter().extra['todo'] = list(range(100))

        for i in range(10):
            actor_name = 'actor{}'.format(i)
            print('Tworzę aktora: ' + actor_name + '...')

            actor = await spawn(name=actor_name, start=partial(Arbiter._init_actor, arb=arbiter().proxy,
                                                               init_func=partial(self.actor_init_task),
                                                               last_job=partial(self.actor_last_task)))
            actors.append(actor)

        while True in [actor.is_alive() for actor in actors]:
            await asyncio.sleep(1)

        self.final_work()

        try:
            arbiter().stop()
        except PermissionError:  # Windows
            quit()

    @staticmethod
    def _init_actor(_, arb, init_func, last_job):
        init_func()
        print('Inicjalizacja aktora ' + get_actor().name + ' zakończona!')
        ensure_future(Arbiter._actor_loop(arb, last_job))

    @staticmethod
    async def _actor_loop(arb, last_job):
        print(get_actor().name + ': Startuję!')
        while True:
            await asyncio.sleep(0.5)
            order = await send(arb.proxy, '_assign_work')
            if order is None:
                last_job()
                get_actor().stop()
                await asyncio.sleep(2)
            else:
                order()


if __name__ == '__main__':
    Arbiter(work_gen(), final_work, actor_init_task, actor_last_job)
