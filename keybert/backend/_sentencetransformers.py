import numpy as np
from typing import List, Union
from sentence_transformers import SentenceTransformer

from keybert.backend import BaseEmbedder


class SentenceTransformerBackend(BaseEmbedder):
    """ Sentence-transformers embedding model
    The sentence-transformers embedding model used for generating document and
    word embeddings.
    Arguments:
        embedding_model: A sentence-transformers embedding model
    Usage:
    To create a model, you can load in a string pointing to a
    sentence-transformers model:
    ```python
    from keybert.backend import SentenceTransformerBackend
    sentence_model = SentenceTransformerBackend("distilbert-base-nli-stsb-mean-tokens")
    ```
    or  you can instantiate a model yourself:
    ```python
    from keybert.backend import SentenceTransformerBackend
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer("distilbert-base-nli-stsb-mean-tokens")
    sentence_model = SentenceTransformerBackend(embedding_model)
    ```
    """
    def __init__(self, embedding_model: Union[str, SentenceTransformer]):
        super().__init__()

        if isinstance(embedding_model, SentenceTransformer):
            self.embedding_model = embedding_model
        elif isinstance(embedding_model, str):
            self.embedding_model = SentenceTransformer(embedding_model)
        else:
            raise ValueError("Please select a correct SentenceTransformers model: \n"
                             "`from sentence_transformers import SentenceTransformer` \n"
                             "`model = SentenceTransformer('distilbert-base-nli-stsb-mean-tokens')`")

    def embed(self,
              documents: List[str],
              verbose: bool = False) -> np.ndarray:
        """ Embed a list of n documents/words into an n-dimensional
        matrix of embeddings
        Arguments:
            documents: A list of documents or words to be embedded
            verbose: Controls the verbosity of the process
        Returns:
            Document/words embeddings with shape (n, m) with `n` documents/words
            that each have an embeddings size of `m`
        """
        embeddings = self.embedding_model.encode(documents, show_progress_bar=verbose)
        return embeddings

    def embed_full(self, 
                   documents: List[str]) -> dict:
        return self.embedding_model.encode(documents, show_progress_bar=False, output_value = None)