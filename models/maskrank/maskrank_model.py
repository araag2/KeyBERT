from typing import List, Tuple, Set
from nltk.stem import PorterStemmer


from datasets.process_datasets import *

from models.base_KP_model import BaseKPModel
from models.maskrank.maskrank_document_abstraction import Document

from models.pre_processing.language_mapping import choose_tagger, choose_lemmatizer
from models.pre_processing.pos_tagging import POS_tagger_spacy
from models.pre_processing.pre_processing_utils import remove_punctuation, remove_whitespaces

from tqdm import tqdm

class MaskRank(BaseKPModel):
    """
    Simple class to encapsulate MaskRank functionality. Uses
    the KeyBert backend to retrieve models
    """

    def __init__(self, model, tagger):
        super().__init__(model)
        self.tagger = POS_tagger_spacy(tagger)
        self.grammar = """  NP: 
        {<PROPN|NOUN|ADJ>*<PROPN|NOUN>+<ADJ>*}"""
        self.counter = 0

    def update_tagger(self, dataset : str = "") -> None:
        self.tagger = POS_tagger_spacy(choose_tagger(dataset)) if choose_tagger(dataset) != self.tagger.name else self.tagger

    def pre_process(self, doc = "", **kwargs) -> str:
        """
        Method that defines a pre_processing routine, removing punctuation and whitespaces
        """
        doc = remove_punctuation(doc)
        return remove_whitespaces(doc)[1:]

    def extract_mdkpe_embeds(self, txt, top_n, min_len, stemmer = None, lemmer = None, **kwargs) -> Tuple[List[Tuple], List[str]]:
        doc = Document(txt, self.counter)
        doc.pos_tag(self.tagger, False if "pos_tag_memory" not in kwargs else kwargs["pos_tag_memory"], self.counter)
        doc.extract_candidates(min_len, self.grammar, lemmer)
        
        cand_embeds, candidate_set = doc.embed_n_candidates(self.model, min_len, stemmer, **kwargs)
    
        print(f'document {self.counter} processed\n')
        self.counter += 1
        torch.cuda.empty_cache()
    
        return (doc, cand_embeds, candidate_set)

    def extract_kp_from_doc(self, doc, top_n, min_len, stemmer = None, lemmer = None, **kwargs) -> Tuple[List[Tuple], List[str]]:
        """
        Concrete method that extracts key-phrases from a given document, with optional arguments
        relevant to its specific functionality
        """

        doc = Document(doc, self.counter)
        doc.pos_tag(self.tagger, False if "pos_tag_memory" not in kwargs else kwargs["pos_tag_memory"], self.counter)
        doc.extract_candidates(min_len, self.grammar, lemmer)

        top_n, candidate_set = doc.top_n_candidates(self.model, top_n, min_len, stemmer, **kwargs)

        print(f'document {self.counter} processed\n')
        self.counter += 1

        return (top_n, candidate_set)

    def extract_kp_from_corpus(self, corpus, dataset: str = "DUC", 
    top_n: int = 15, min_len: int = 5, stemming: bool = False, lemmatize: bool = False, **kwargs) -> List[List[Tuple]]:
        """
        Concrete method that extracts key-phrases from a list of given documents, with optional arguments
        relevant to its specific functionality
        """
        self.counter = 0
        self.update_tagger(dataset)

        stemer = None if not stemming else PorterStemmer()
        lemmer = None if not lemmatize else choose_lemmatizer(dataset)

        return [self.extract_kp_from_doc(doc[0], top_n, min_len, stemer, lemmer, **kwargs) for doc in tqdm(corpus)]