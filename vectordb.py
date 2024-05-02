import os
from pinecone import Pinecone, ServerlessSpec, PodSpec
from dotenv import load_dotenv
load_dotenv()
from openai import OpenAI
client = OpenAI()
class Pinecode_DB:
    def __init__(self, api_key=None, index_name="medical-kb",name_space="medical"):
        if api_key is None:
            api_key = os.getenv("PINECONE_API_KEY")
        self.pinecone = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.name_space = name_space
        self.retrieve_limit = 3600  # set the limit of knowledge base words, leave some space for chat history and query.

    def retrieve(self, query, name_space="medical"):
        embed_model = "text-embedding-3-small"
        delimiter = "###"
        res = client.embeddings.create(
            input=[query],
            model=embed_model
        )
        # print("res:", res)

        # retrieve from Pinecone knowledge base
        xq = res.data[0].embedding
        # print("xq:", xq)
        index = self.pinecone.Index(self.index_name)

        # get relevant contexts
        res = index.query(vector=xq,
                          top_k=5,
                          include_metadata=True,
                          namespace=name_space)
        contexts = [
            x["metadata"]["text"] for x in res["matches"]
        ]
        # print("contexts:", contexts)

        # build our prompt with the retrieved contexts included
        prompt = " "
        count = 0
        proceed = True
        while proceed and count < len(contexts):
            if len(prompt) + len(contexts[count]) >= self.retrieve_limit:
                proceed = False
            else:
                prompt += contexts[count]

            count += 1
        # End of while loop

        prompt = delimiter + prompt + delimiter
        return prompt
