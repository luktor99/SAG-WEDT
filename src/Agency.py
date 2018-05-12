import asyncio
from functools import partial
from pulsar.api import arbiter, command, spawn, send, ensure_future, Config
from pulsar.async.actor import get_actor


async def _mock_work(arg):
    print(get_actor().name + ': Pracuję ' + str(arg))
    await asyncio.sleep(1)


def _mock_work_gen():
    for i in range(100):
        yield partial(_mock_work, i)


async def _mock_arbiter_last_task():
    print('arbiter: Wykonuję ostatnie zadanie')
    await asyncio.sleep(5)
    print('arbiter: Dokonało się!')


def _mock_actor_init_task():
    '''Pierwsze zadanie aktora początkowa aktora'''
    print(str(get_actor().name) + ': Moje pierwsze zadanie')


async def _mock_actor_last_task():
    '''Ostatnie zadanie aktora'''
    print(str(get_actor().name) + ': Oto moja ostatnia przysługa, Panie Pawle!')
    await asyncio.sleep(1)
    print(str(get_actor().name) + ': Skończyłem ostatnią przysługę, Panie Pawle!')


@command()
def _assign_work(request):
    me = get_actor()
    try:
        task = next(me.extra['gen'])
        print(get_actor().name + ': Przypisuję zadanie aktorowi ' + request.caller.name)
        return task
    except StopIteration:
        pass


class Agency:
    def __init__(self, actors_count,
                 work_gen=_mock_work_gen(),
                 arbiter_last_task=_mock_arbiter_last_task,
                 actor_init_task=_mock_actor_init_task,
                 actor_last_task=_mock_actor_last_task):

        self._actors_count = actors_count
        self._work_gen = work_gen
        self._arbiter_last_task = arbiter_last_task
        self._actor_init_task = actor_init_task
        self._actor_last_task = actor_last_task
        self._initialize_arbiter()

    def __call__(self):
        ensure_future(self._arbiter_work())

    def _initialize_arbiter(self):
        arbiter(cfg=Config(workers=4, timeout=120))
        arbiter().extra['gen'] = self._work_gen
        arbiter()._loop.call_later(1, self)
        arbiter().start()

    async def _arbiter_work(self):
        actors = []
        arbiter().extra['todo'] = list(range(100))

        for i in range(10):
            actor_name = 'actor{}'.format(i)
            print(get_actor().name + ': Tworzę aktora ' + actor_name + '...')

            actor = await spawn(name=actor_name, start=partial(Agency._init_actor,
                                                               init_func=partial(self._actor_init_task),
                                                               last_job=partial(self._actor_last_task)))
            actors.append(actor)

        while True in [actor.is_alive() for actor in actors]:
            await asyncio.sleep(1)

        await self._arbiter_last_task()
        await asyncio.sleep(5)

        try:
            arbiter().stop()
        except PermissionError:  # Windows
            quit()

    @staticmethod
    def _init_actor(_, init_func, last_job):
        init_func()
        ensure_future(Agency._actor_loop(last_job))

    @staticmethod
    async def _actor_loop(last_job):
        print(get_actor().name + ': Startuję!')
        while True:
            order = await send(get_actor().monitor, '_assign_work')
            if order is None:
                await last_job()
                get_actor().stop()
                await asyncio.sleep(2)
            else:
                await order()


if __name__ == '__main__':
    Agency(10)
