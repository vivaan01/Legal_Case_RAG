import pickle

try:
    with open(r'data\\bm25_docs.pkl', 'rb') as f:
        docs = pickle.load(f)
    print(f"Loaded {len(docs)} documents")
except Exception as e:
    print(f"Error: {str(e)}")