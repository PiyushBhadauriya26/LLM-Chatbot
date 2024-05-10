"""Upload a PDF file or web articles to the pinecone vector database

Usage:
  update_verctordb.py (--web_url=<web_id> | --pdf_file=<file_id> )[--index_name=<index_name>][--name_space=<name_space>][--nlp_id=<nlp_id>][--chunk_size=<chunk_size>][--stride=<stride>][--page_begin=<page_begin>][--page_end=<page_end>][--embed_model=<embed_model>]
  update_verctordb.py -h | --help

Options:
    -h --help                             Show this screen.
    --web_url=<web_id>                    A web url to search for.
    --pdf_file=<file_id>                  PDF file name.
    --index_name=<index_name>             The pinecone index name.
    --name_space=<name_space>             The namespace we want to place for all related docuement.
    --nlp_id=<nlp_id>                     A common ID prefix to reference to document.
    --chunk_size=<chunk_size>             The chunk size, how many lines as one chunks.
    --stride=<stride>                     The overlap side, how many lines as overlap between chunks.
    --page_begin=<page_begin>             Which page in the PDF file to begin for upsert.
    --page_end=<page_end>                 Which page is the ending page for upsert.
    --embed_model=<embed_model>           The model to embed the text.

"""
from PyPDF2 import PdfReader
import docopt
import pinecone as pc
import os
import time
from openai import OpenAI
from pinecone import Pinecone # We now will use PineCone
from dotenv import load_dotenv
load_dotenv()
client = OpenAI()
# Assign pinecone PINECONE_API_KEY
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)

def split_text_into_lines(input_text, max_words_per_line):
    words = input_text.split()
    lines = []
    current_line = []

    for word in words:
        if len(current_line) + len(word) + 1 <= max_words_per_line:
            current_line.append(word)
        else:
            lines.append(" ".join(current_line))
            current_line = [word]

    if current_line:
        lines.append(" ".join(current_line))

    return lines

# process the knowledge base file upsert to a namespace
# from tqdm import tqdm

def nlp_upsert(filename, index_name, name_space, nlp_id, chunk_size, stride, page_begin, page_end, embed_model):
    """
    upsert a whole PDF file (with begin page and end page information) to the pinecone vector database

    Parameters:
    filename (str): The file name.
    index_name (str): The pinecone index name.
    name_space (str): The namespace we want to place for all related docuement.
    nlp_id (str): A common ID prefix to reference to document.
    chunk_size (int): The chunk size, how many lines as one chunks.
    stride (int): The overlap side, how many lines as overlap between chunks.
    page_begin (int): Which page in the PDF file to begin for upsert.
    page_end (int): Which page is the ending page for upsert.
    embed_model (str): The model to embed the text.
    Returns:
    None: No return.
    """
    doc = ""

    reader = PdfReader(filename)

    for i in range(page_begin, page_end):
        doc += reader.pages[i].extract_text()
        print("page completed:", i)

    doc = split_text_into_lines(doc, 30)
    print("The total lines: ", len(doc))

    # Connect to index
    index = pc.Index(index_name)

    count = 0
    for i in range(0, len(doc), chunk_size):
        # find begining and end of the chunk
        i_begin = max(0, i - stride)
        i_end = min(len(doc), i_begin + chunk_size)

        doc_chunk = doc[i_begin:i_end]
        print("-" * 80)
        print("The ", i // chunk_size + 1, " doc chunk text:", doc_chunk)

        texts = ""
        for x in doc_chunk:
            texts += x
        print("Texts:", texts)

        # Create embeddings of the chunk texts
        try:
            res = client.embeddings.create(input=texts, model=embed_model)
        except:
            done = False
            while not done:
                time.sleep(10)
                try:
                    res = client.embeddings.create(input=texts, model=embed_model)
                    done = True
                except:
                    pass
        embed = res.data[0].embedding
        print("Embeds length:", len(embed))

        # Meta data preparation
        metadata = {
            "text": texts
        }

        count += 1
        print("Upserted vector count is: ", count)
        print("=" * 80)

        # upsert to pinecone and corresponding namespace

        index.upsert(vectors=[{"id": nlp_id + '_' + str(count), "metadata": metadata, "values": embed}],
                     namespace=name_space)

arguments = docopt.docopt(__doc__)
if __name__ == "__main__":
    # print(arguments)
    try:
        index_name = arguments['--index_name'] if arguments['--index_name'] else "medical-kb"
        name_space = arguments['--name_space'] if arguments['--name_space'] else "medical"
        nlp_id = arguments['--nlp_id'] if arguments['--nlp_id'] else "default"
        chunk_size = int(arguments['--chunk_size']) if arguments['--chunk_size'] else 5
        stride = int(arguments['--stride']) if arguments['--stride'] else 2

        embed_model = arguments['--embed_model'] if arguments['--embed_model'] else "text-embedding-3-small"
        if arguments['--web_url']:
            web_url = arguments['--web_url']
            print("web_url:", web_url)
            raise NotImplementedError("Web URL is not implemented yet.")
        elif arguments['--pdf_file']:
            pdf_file = arguments['--pdf_file']
            print("pdf_file:", pdf_file)
            reader = PdfReader(pdf_file)
            page_len = len(reader.pages)
            print("length of the knowledge base file:", page_len)
            page_begin = int(arguments['--page_begin']) if arguments['--page_begin'] else 0
            page_end = int(arguments['--page_end']) if arguments['--page_end'] else page_len-1

            nlp_upsert(pdf_file, index_name, name_space, nlp_id, chunk_size, stride, page_begin, page_end, embed_model)

    except docopt.DocoptExit as e:
        print(e)




