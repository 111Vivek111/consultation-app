# import pickle

# from rank_bm25 import BM25Okapi


# class BM25Retriever:

#     def __init__(self):

#         with open("bm25_chunks.pkl", "rb") as f:
#             self.documents = pickle.load(f)

#         tokenized = [

#             doc.page_content.lower().split()

#             for doc in self.documents
#         ]

#         self.bm25 = BM25Okapi(tokenized)

#     def invoke(self, query, k=8):

#         query_tokens = query.lower().split()

#         scores = self.bm25.get_scores(query_tokens)

#         ranked = sorted(

#             zip(scores, self.documents),

#             reverse=True,

#             key=lambda x: x[0]
#         )

#         return [

#             doc

#             for score, doc

#             in ranked[:k]
#         ]