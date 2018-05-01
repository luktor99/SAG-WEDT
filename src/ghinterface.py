import os
import json
import requests
from ghtoken import GITHUB_TOKEN
import datetime, time
import base64
from multiprocessing import Pool

REPOS_PER_PAGE = 100
API_CALLS_AT_ONCE = 25
NO_README_STRING = ""
INITIAL_STARS_LIMIT = 1000000

GITHUB_AUTH = {"Authorization": "token %s" % GITHUB_TOKEN}


class GHInterface():
    def __init__(self, db_path="../gh-database"):
        """
        C-tor
        :param db_path: Database directory (defaults to ../gh-database)
        """
        self.db_path = db_path
        self.data_file_path = os.path.join(self.db_path, "data.json")
        self.data = {}

        # Try to load an existing database, otherwise create a new one
        if os.path.exists(self.data_file_path):
            with open(self.data_file_path, "r") as fp:
                self.data = json.load(fp)
        else:
            # Create the db path if it doesn't exist yet
            if not os.path.exists(self.db_path):
                os.makedirs(self.db_path)

            # Populate a new data structure
            self.data['pages'] = 0
            self.data['repos'] = 0
            self.data['stars_limit'] = INITIAL_STARS_LIMIT

    def get_page(self, page_index):
        """
        Returns the contents of page with the given index.
        :param page_index: the page index (the first page has index 1)
        :return: contents of the page
        """
        with open(self.__get_page_file_path(page_index)) as fp:
            return json.load(fp)

    def get_pages_count(self):
        """
        Returns the total number of pages stored in the database.
        :return: the total number of pages stored in the database
        """
        return self.data['pages']

    def get_repos_count(self):
        """
        Returns the total number of repositories stored in the database.
        :return: the total number of repositories stored in the database
        """
        return self.data['repos']

    def get_all(self):
        """
        Returns a list containing all repositories stored in the database.
        :return: list containing all repositories stored in the database
        """
        repos = []
        for p in range(1, self.get_pages_count() + 1):
            repos = repos + self.get_page(p)

        return repos

    def download(self, repos_count):
        """
        Downloads a given number of top-rated repositories and stores them in the database
        :param repos_count: The number of repos to be downloaded
        :return:
        """
        if self.data['repos'] < repos_count:
            if self.data['repos'] > 0:
                print("There are %d repositories in the database. Downloading the missing %d repositories..." % (
                    self.data['repos'], repos_count - self.data['repos']))
                print("Warning: the database might contain duplicate entries.")
            else:
                print("Downloading %d repositories..." % repos_count)
        else:
            print("There are %d repositories in the database. No need to download anything." % self.data['repos'])
            return

        stars_limit = INITIAL_STARS_LIMIT
        while self.data['repos'] < repos_count:
            repos = self.__api_get_top_repos(self.data['stars_limit'], repos_count - self.data['repos'])

    def __api_get_top_repos(self, stars_limit, repos_count, page=1):
        res = requests.get("https://api.github.com/search/repositories", headers=GITHUB_AUTH, params={
            'q': "stars:1..%d" % stars_limit,
            'sort': "stars",
            'page': page,
            'per_page': REPOS_PER_PAGE
        })
        self.__wait_if_necessary(res)
        self.__check_result(res)

        # Get the required number of repos from the retrieved page and extract interesting data
        repos = self.__extract_repo_data(res.json()['items'][:repos_count])

        # Acquire readme content for each repo
        global print_once_flag
        print_once_flag = True
        with Pool(API_CALLS_AT_ONCE) as p:
            readmes = p.map(get_readme_content, repos)
            for repo, readme in zip(repos, readmes):
                repo['readme'] = readme

        # Store the page
        self.__store_next_page(repos)

        print("Downloaded %d repositories." % self.data['repos'])

        # Check the next page if required and the page is available
        repos_remaining = repos_count - len(repos)
        if 'next' in res.links and repos_remaining > 0:
            return repos + self.__api_get_top_repos(stars_limit, repos_remaining, page + 1)
        else:
            return repos

    @staticmethod
    def __check_result(res):
        if res.status_code == 403:
            raise ConnectionRefusedError(res.text)
        elif res.status_code != 200:
            raise ConnectionError(res.text)

    @staticmethod
    def __wait_if_necessary(res):
        if int(res.headers['X-RateLimit-Remaining']) == 0:
            reset_time = datetime.datetime.fromtimestamp(float(res.headers['X-RateLimit-Reset']))
            dt = (reset_time - datetime.datetime.now()).total_seconds() + 0.5
            print("API rate limit was hit. Waiting until %s (%f sec)" % (reset_time, dt))
            time.sleep(dt)

    @staticmethod
    def __extract_repo_data(items):
        return [{
            'name': item['full_name'],
            'stars': item['stargazers_count'],
            'url': item['url'],
            'html_url': item['html_url']
        } for item in items]

    def __get_readme_content(self, repo):
        res = requests.get(repo['url'] + "/readme", headers=GITHUB_AUTH)
        self.__wait_if_necessary(res)
        if res.status_code != 200:
            print("Repository %s has no readme!" % repo['name'])
            return ""
        else:
            return base64.b64decode(res.json()['content']).decode("UTF-8")

    def __get_page_file_path(self, page_number):
        filename = "page%d.json" % page_number
        return os.path.join(self.db_path, filename)

    def __store_page(self, page_number, page_data):
        path = self.__get_page_file_path(page_number)
        with open(path, "w") as fp:
            json.dump(page_data, fp)
        self.__store_db_data()

    def __store_next_page(self, page_data):
        self.data['pages'] += 1
        self.data['repos'] += len(page_data)
        self.data['stars_limit'] = min([repo['stars'] for repo in page_data]) - 1
        self.__store_page(self.data['pages'], page_data)

    def __store_db_data(self):
        with open(self.data_file_path, "w") as fp:
            json.dump(self.data, fp)


def get_readme_content(repo):
    """
    Retrieves readme content for a given repo.
    This function must stay outside the GHInterface class to allow parallel execution
    :param repo: a dictionary describing a repository
    :return: readme content
    """
    res = requests.get(repo['url'] + "/readme", headers=GITHUB_AUTH)

    if int(res.headers['X-RateLimit-Remaining']) == 0:
        reset_time = datetime.datetime.fromtimestamp(float(res.headers['X-RateLimit-Reset']))
        dt = (reset_time - datetime.datetime.now()).total_seconds() + 0.5
        print("API rate limit was hit. Waiting until %s (%f sec)" % (reset_time, dt))
        time.sleep(dt)

        # Retry if required
        if not 'content' in res.json():
            return __get_readme_content(repo)

    if res.status_code != 200:
        print("Repository %s has no readme!" % repo['name'])
        return NO_README_STRING
    else:
        return base64.b64decode(res.json()['content']).decode("UTF-8")
