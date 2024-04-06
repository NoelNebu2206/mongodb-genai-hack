# ---
# args: ["--query", "How many oil barrels were released from reserves"]
# ---
# # Question-answering with LangChain
#
# In this example we create a large-language-model (LLM) powered question answering
# web endpoint and CLI. Only a single document is used as the knowledge-base of the application,
# the 2022 USA State of the Union address by President Joe Biden. However, this same application structure
# could be extended to do question-answering over all State of the Union speeches, or other large text corpuses.
#
# It's the [LangChain](https://github.com/hwchase17/langchain) library that makes this all so easy. This demo is only around 100 lines of code!

# ## Defining dependencies
#
# The example uses three PyPi packages to make scraping easy, and three to build and run the question-answering functionality.
# These are installed into a Debian Slim base image using the `pip_install` function.
#
# Because OpenAI's API is used, we also specify the `openai-secret` Modal Secret, which contains an OpenAI API key.
#
# A `docsearch` global variable is also declared to facilitate caching a slow operation in the code below.
from pathlib import Path
import modal
from modal import Image, Secret, Stub, web_endpoint, Volume
print('hello')
image = Image.debian_slim(python_version="3.11").pip_install("modal==0.62.21", "nomic").apt_install("git")
# .run_commands(
#     "cd /root",
#     "ls ",
#     "git clone https://github.com/modal-labs/modal-client.git",
#     "cd modal-client && pip install -e .",
#     "cd modal-client/modal/ && grep -ir interactivity_enabled app.py",
#     #"cd modal-client && git checkout 5a04698526bb53c87de195e2decd46cd27d77f07",
#     "echo 'AG:: modal git cloned...'",
#     "ls",
# )
#     # scraping pkgs
#     "beautifulsoup4~=4.11.1",
#     "httpx~=0.23.3",
#     "lxml~=4.9.2",
#     # langchain pkgs
#     "faiss-cpu~=1.7.3",
#     "langchain~=0.0.138",
#     "openai~=0.27.4",
#     "tiktoken==0.3.0",
# )

print('hello')
stub = Stub(
    name="MongoTest",
    image=image,
    #secrets=[Secret.from_name("openai-secret")],
)
#docsearch = None  # embedding index that's relatively expensive to compute, so caching with global var.
print('hello')
volume = Volume.from_name(
    "repo_data", create_if_missing=True
)
print('hello')
MODEL_DIR = "/model"
# ## Constructing the Q&A chain
#
# At a high-level, this LLM chain will be able to answer questions asked about Biden's speech and provide
# references to which parts of the speech contain the evidence for given answers.
#
# The chain combines a text-embedding index over parts of Biden's speech with OpenAI's [GPT-3 LLM](https://openai.com/blog/chatgpt/).
# The index is used to select the most likely relevant parts of the speech given the question, and these
# are used to build a specialized prompt for the OpenAI language model.
#
# For more information on this, see [LangChain's "Question Answering" notebook](https://langchain.readthedocs.io/en/latest/use_cases/evaluation/question_answering.html).


def retrieve_sources(sources_refs: str, texts: list[str]) -> list[str]:
    """
    Map back from the references given by the LLM's output to the original text parts.
    """
    clean_indices = [
        r.replace("-pl", "").strip() for r in sources_refs.split(",")
    ]
    numeric_indices = (int(r) if r.isnumeric() else None for r in clean_indices)
    return [
        texts[i] if i is not None else "INVALID SOURCE" for i in numeric_indices
    ]


def qanda_langchain(query: str) -> tuple[str, list[str]]:
    from langchain.chains.qa_with_sources import load_qa_with_sources_chain
    from langchain.embeddings.openai import OpenAIEmbeddings
    from langchain.llms import OpenAI
    from langchain.text_splitter import CharacterTextSplitter
    from langchain.vectorstores.faiss import FAISS

    # Support caching speech text on disk.
    speech_file_path = Path("state-of-the-union.txt")

    if speech_file_path.exists():
        state_of_the_union = speech_file_path.read_text()
    else:
        print("scraping the 2022 State of the Union speech")
        state_of_the_union = scrape_state_of_the_union()
        speech_file_path.write_text(state_of_the_union)

    # We cannot send the entire speech to the model because OpenAI's model
    # has a maximum limit on input tokens. So we split up the speech
    # into smaller chunks.
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    print("splitting speech into text chunks")
    texts = text_splitter.split_text(state_of_the_union)

    # Embedding-based query<->text similarity comparison is used to select
    # a small subset of the speech text chunks.
    # Generating the `docsearch` index is too slow to re-run on every request,
    # so we do rudimentary caching using a global variable.
    global docsearch

    if not docsearch:
        # New OpenAI accounts have a very low rate-limit for their first 48 hrs.
        # It's too low to embed even just this single Biden speech.
        # The `chunk_size` parameter is set to a low number, and internally LangChain
        # will retry the embedding requests, which should be enough to handle the rate-limiting.
        #
        # Ref: https://platform.openai.com/docs/guides/rate-limits/overview.
        print("generating docsearch indexer")
        docsearch = FAISS.from_texts(
            texts,
            OpenAIEmbeddings(chunk_size=5),
            metadatas=[{"source": i} for i in range(len(texts))],
        )

    print("selecting text parts by similarity to query")
    docs = docsearch.similarity_search(query)

    chain = load_qa_with_sources_chain(
        OpenAI(model_name="gpt-3.5-turbo-instruct", temperature=0),
        chain_type="stuff",
    )
    print("running query against Q&A chain.\n")
    result = chain(
        {"input_documents": docs, "question": query}, return_only_outputs=True
    )
    output: str = result["output_text"]
    parts = output.split("SOURCES: ")
    if len(parts) == 2:
        answer, sources_refs = parts
        sources = retrieve_sources(sources_refs, texts)
    elif len(parts) == 1:
        answer = parts[0]
        sources = []
    else:
        raise RuntimeError(
            f"Expected to receive an answer with a single 'SOURCES' block, got:\n{output}"
        )
    return answer.strip(), sources


# ## Modal Functions
#
# With our application's functionality implemented we can hook it into Modal.
# As said above, we're implementing a web endpoint, `web`, and a CLI command, `cli`.


@stub.function()
@web_endpoint(method="GET")
def web(query: str, show_sources: bool = False):
    answer, sources = qanda_langchain(query)
    if show_sources:
        return {
            "answer": answer,
            "sources": sources,
        }
    else:
        return {
            "answer": answer,
        }
print("tototo")

@stub.function(image=image,
                volumes={'/data': volume},
                secrets=[modal.Secret.from_name("nomic-key")],
                )
def get_git_data(github_url:str):
    import subprocess
    import os
    import nomic
    #import pdb
    #import modal
    
    print('stop[]')
    # modal.interact()
    # import IPython
    # IPython.embed()
    # image = image.run_commands(
    #     "cd /root",
    #     "git clone {github_url}",
    #     "echo 'git cloned...' ",
    # )
    #modal.interact()
    #breakpoint()
    print('AG: inside get_git_data')
    #os.makedirs("/data", exist_ok=True)
    #os.chdir("/data")
    
    # #print()
    # # Run the git clone command
    print('AG: starting git clone ')
    subprocess.run(["echo", 'bobobo' ])
    subprocess.run(["git", "clone", github_url, 'github_data' ])
    git_content = []
    def read_file_content(directory):
        code_extensions = ['.py', '.js', '.cpp']  # Add more extensions as needed
        for root, dirs, files in os.walk(directory):
            
            
            for file in files:
                file_path = os.path.join(root, file)
                _, file_extension = os.path.splitext(file_path)
                if file_extension in code_extensions:
                    file_dict = {}
                    file_dict['path'] = file_path

                    with open(file_path, 'r') as f:
                        file_dict['content'] = f.read()
                        print(f"AG: {read_file_content.__name__} Contents saved for {file_path}:")
                    git_content.append(file_dict)
                    

    # Usage
    read_file_content('/data')
    print(f"num of files read: {len(git_content)}")
    sample_file_data = """
        Once upon a time, in a quaint little town nestled between rolling hills and lush forests, there lived a friendly and adventurous dog named Max. Max was a mix of a Golden Retriever and a Border Collie, which made him both clever and affectionate.
        Max's days were filled with excitement and exploration. He would often roam the town, making friends with everyone he met. His favorite spot was the town square, where he would eagerly greet the townspeople and play with the local children.
        One day, while exploring the woods on the outskirts of town, Max stumbled upon a hidden path that led to a mysterious old house. Curiosity piqued, he bravely ventured inside, only to discover that the house was home to a family of friendly squirrels.
        The squirrels welcomed Max with open arms (or rather, open paws), and they quickly became the best of friends. Together, they would explore the woods, play games, and share stories late into the night.
        As the seasons changed, so did Max's adventures. In the winter, he would frolic in the snow with his squirrel friends, while in the summer, they would swim in the nearby creek and bask in the warm sun.
        Through his adventures, Max taught the townspeople the importance of kindness, friendship, and the joy of exploring the world around them. And so, Max's story became a beloved tale in the town, inspiring everyone to embrace life with the same enthusiasm and curiosity as their furry friend.
        """
    
    # curl https://api-atlas.nomic.ai/v1/embedding/text \
    # -H "Authorization: Bearer $NOMIC_API_KEY" \
    # -H "Content-Type: application/json" \
    # -d '{ "model": "nomic-embed-text-v1", "texts": ["The quick brown fox..."]}'
    # #pdb.set_trace()
    volume.commit()
    
    print('AG: git clone done')
    


print('bye')
@stub.local_entrypoint()
def run():
    print('AG: starting...')
    
    github_repo = "https://github.com/anubhavghildiyal/ML_for_cybersec_F23_square_attack"

    ##Call modal function remotely to clone github on volume
    get_git_data.remote(github_repo)
    print('AG: done run...')
    
# ## Test run the CLI
#
# ```bash
# modal run potus_speech_qanda.py --query "What did the president say about Justice Breyer"
# 🦜 ANSWER:
# The president thanked Justice Breyer for his service and mentioned his legacy of excellence. He also nominated Ketanji Brown Jackson to continue in Justice Breyer's legacy.
# ```
#
# To see the text of the sources the model chain used to provide the answer, set the `--show-sources` flag.
#
# ```bash
# modal run potus_speech_qanda.py \
#    --query "How many oil barrels were released from reserves" \
#    --show-sources=True
# ```
#
# ## Test run the web endpoint
#
# Modal makes it trivially easy to ship LangChain chains to the web. We can test drive this app's web endpoint
# by running `modal serve potus_speech_qanda.py` and then hitting the endpoint with `curl`:
#
# ```bash
# curl --get \
#   --data-urlencode "query=What did the president say about Justice Breyer" \
#   https://modal-labs--example-langchain-qanda-web.modal.run
# ```
#
# ```json
# {
#   "answer": "The president thanked Justice Breyer for his service and mentioned his legacy of excellence. He also nominated Ketanji Brown Jackson to continue in Justice Breyer's legacy."
# }
# ```
