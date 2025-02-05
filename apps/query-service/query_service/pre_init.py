import os

# Need to disable multithreading otherwise faiss and sentence transformers break
os.environ["OMP_NUM_THREADS"] = "1"
# os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from sentence_transformers import SentenceTransformer  # noqa
import faiss  # noqa


def pre_init():
    pass
