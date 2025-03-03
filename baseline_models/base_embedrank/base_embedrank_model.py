import numpy as np

from nltk import RegexpParser
from nltk.stem import PorterStemmer
from sklearn.metrics.pairwise import cosine_similarity
from re import search, escape
from typing import List, Tuple, Set

from models.base_KP_model import BaseKPModel
from models.pre_processing.pos_tagging import POS_tagger_spacy
from models.pre_processing.pre_processing_utils import remove_punctuation, remove_whitespaces
from models.models_utils import test_data
from datasets.process_datasets import *
from evaluation.evaluation_tools import evaluate_kp_extraction, extract_dataset_labels, extract_res_labels
from keybert.mmr import mmr

class BaseEmbedRank (BaseKPModel):
    """
    Simple class to encapsulate EmbedRank functionality. Uses
    the KeyBert backend to retrieve models
    """

    def __init__(self, model, tagger):
        super().__init__(model)

        self.tagger = POS_tagger_spacy(tagger)
        self.grammar = """  NP: 
        {<PROPN|NOUN|ADJ>*<PROPN|NOUN>+<ADJ>*}"""


    def pre_process(self, doc = "", **kwargs) -> str:
        """
        Method that defines a pre_processing routine, removing punctuation and whitespaces
        """
        doc = remove_punctuation(doc)
        return remove_whitespaces(doc)[1:]

    def pos_tag_doc(self, doc : str = "", stemming : bool = True, **kwargs) -> List[List[Tuple]]:
        """
        Method that handles POS_tagging of an entire document, pre-processing or stemming it in the process
        """
        return self.tagger.pos_tag_doc(doc)

    def extract_candidates(self, tagged_doc : List[List[Tuple]] = [], **kwargs) -> List[str]:
        """
        Method that uses Regex patterns on POS tags to extract unique candidates from a tagged document
        """
        candidate_set = set()
        parser = RegexpParser(self.grammar)
        np_trees = parser.parse_sents(tagged_doc)
        
        for tree in np_trees:
            for subtree in tree.subtrees(filter = lambda t : t.label() == 'NP'):
                candidate_set.add(' '.join(word for word, tag in subtree.leaves()))

        candidate_set = {kp for kp in candidate_set if len(kp.split()) <= 5}

        #candidate_res = []
        #for s in sorted(candidate_set, key=len, reverse=True):
            #if not any(search(r'\b{}\b'.format(escape(s)), r) for r in candidate_res):
                #candidate_res.append(s)
                
        return list(candidate_set)

    def top_n_candidates(self, doc : str = "", candidate_list : List[str] = [], top_n: int = 5, min_len : int = 3, stemming : bool = True, **kwargs) -> List[Tuple]:
        doc_embedding = []
        candidate_embedding = []

        if stemming:
            stemmer = PorterStemmer()
            doc_embedding = self.model.embed(stemmer.stem(doc))
            candidate_embedding = [self.model.embed(stemmer.stem(candidate)) for candidate in candidate_list]
        
        else:
            doc_embedding = self.model.embed(doc)
            candidate_embedding = [self.model.embed(candidate.lower()) for candidate in candidate_list]
        
        doc_sim = []
        if "MMR" not in kwargs:
            doc_sim = np.absolute(cosine_similarity(candidate_embedding, doc_embedding.reshape(1, -1)))
        else:
            doc_sim = mmr(doc_embedding.reshape(1, -1), candidate_embedding, candidate_list, top_n, kwargs["MMR"])

        candidate_score = sorted([(candidate_list[i], doc_sim[i][0]) for i in range(len(doc_sim))], reverse= True, key= lambda x: x[1])

        return candidate_score[:top_n]

    def extract_kp_from_doc(self, doc, top_n, min_len, stemming, **kwargs) -> Tuple[List[Tuple], List[str]]:
        """
        Concrete method that extracts key-phrases from a given document, with optional arguments
        relevant to its specific functionality
        """

        tagged_doc = self.pos_tag_doc(doc, **kwargs)
        candidate_list = self.extract_candidates(tagged_doc, **kwargs)
        top_n = self.top_n_candidates(doc, candidate_list, top_n, min_len, stemming, **kwargs)
        return (top_n, candidate_list)

    def extract_kp_from_corpus(self, corpus, top_n=5, min_len=0, stemming=True, **kwargs) -> List[List[Tuple]]:
        """
        Concrete method that extracts key-phrases from a list of given documents, with optional arguments
        relevant to its specific functionality
        """
        return [self.extract_kp_from_doc(doc[0], top_n, min_len, stemming, **kwargs) for doc in corpus]