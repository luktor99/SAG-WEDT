# General
resource_path = '../resources/'  # with reference to src

# GHinterface
top_repos_to_download = 10000

# Dictionary
dictionary_dir_path = resource_path + 'dictionary/'
dictionary_path = dictionary_dir_path + 'dictionary.dict'
tokenized_corpus_path = dictionary_dir_path + 'corpus/'
bow_corpus_path = resource_path + 'bow/corpus/'

# Tfidf
tfidf_dir_path = resource_path + 'tfidf/'
tfidf_model_path = tfidf_dir_path + 'model.tfidf'
tfidf_corpus_path = tfidf_dir_path + 'corpus/'

# Lsi
lsi_topics = 400
lsi_dir_path = resource_path + 'lsi/'
lsi_model_path = lsi_dir_path + 'model.lsi'
lsi_corpus_path = lsi_dir_path + 'corpus/'

# Indexing
index_path = resource_path + 'index/'

# Search
results_count = 20
search_result_path = resource_path + 'result.pickle'

# Agency
middle_task_wait = 0.5
agents_count = {'dict': 10, 'tfidf': 10, 'lsi': 6, 'index': 4, 'search': 10}
