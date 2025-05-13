from transformers import RagRetriever

retriever = RagRetriever.from_pretrained(

    "facebook/dpr-ctx_encoder-single-nq-base", dataset="wiki_dpr", index_name="compressed"
)