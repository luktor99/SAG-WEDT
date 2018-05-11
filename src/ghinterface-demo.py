from src.ghinterface import GHInterface

if __name__ == '__main__':
    gh = GHInterface()

    # Download 555 top-rated repositories (if they're not already downloaded)
    gh.download(10000)

    repos = gh.get_all()
    unique_names = set([r['name'] for r in repos])
    pages_count = gh.get_pages_count()

    print("Repos in db: %d" % len(repos))
    print("Unique repos: %d" % len(unique_names))
    print("Pages: %d" % pages_count)
