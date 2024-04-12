##nomic-embed-code

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

# A `docsearch` global variable is also declared to facilitate caching a slow operation in the code below.
from pathlib import Path
import modal
from modal_image import image, stub
from modal import Image, Secret, Stub, web_endpoint, Volume, asgi_app
from generate_documentation import CohereChatbot
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from atlas import AtlasClient
from NomicCls import NomicEmbeddings

web_app = FastAPI()

volume = Volume.from_name(
    "repo_data", create_if_missing=True
)
chatbot = CohereChatbot()
nomicObj = NomicEmbeddings()
@stub.function(image=image,
                volumes={'/data': volume},
                )
def push_to_db(github_content, repository_name) :
    mongoDbClient =  AtlasClient()
    mongoDbClient.insert_documents.remote(collection_name = "MongoHackCollection", database_name = 'MongoHack', documents = github_content )

@web_app.post("/user_query")
async def user_query(request: Request):
    data = await request.json()
    query = data.get('query')
    chat_history = data.get('chat_history')
    query_embeddings = nomicObj.get_query_embeddings.remote(query)
    # print(len(query_embeddings[0]))
    # print(query_embeddings[0][:5])
    rel_docs = [
    "The quick brown fox jumps over the lazy dog. This sentence is the second one.",
    "She sells seashells by the seashore. The shells she sells are surely seashells.",
    "How much wood would a woodchuck chuck if a woodchuck could chuck wood? I bet he'd chuck all the wood he could chuck, if a woodchuck could chuck wood.",
    "I scream, you scream, we all scream for ice cream. Ice cream is delicious, especially on a hot day.",
    "It was the best of times, it was the worst of times. It was the age of wisdom, it was the age of foolishness."
    ]
    response = chatbot.chat.remote(query, chat_history, rel_docs)

    return {"response": response}
    
@web_app.post("/get_git_data")
async def get_git_data_endpoint(request: Request):
    data = await request.json()
    github_url = data.get('github_url')
    if ".git" not in github_url:
        github_url = github_url + ".git"
    print('AG: inside get_git_data_endpoint.. redirecting to get_git_data')
    git_contents = get_git_data.remote(github_url)
    
    # Pass the code of each file to the LLm to get documentation for the code
    for i, file in enumerate(git_contents):
        git_contents[i]['documentation'] = chatbot.generate_documentation.remote(file)
    print('AG: done generate documentation...')
    git_contents = nomicObj.get_doc_embeddings.remote(git_contents)
    
    repository_name = github_url.split('/')[-1][:-4]
    print(git_contents[0].keys())
    push_to_db.remote(git_contents, repository_name)
    print('AG: push done...')


@stub.function(image=image,
                volumes={'/data': volume},
                secrets=[modal.Secret.from_name("nomic-key")],
                )
def get_git_data(github_url='https://github.com/anubhavghildiyal/Backdoor_Attack_DNN.git'):
    import subprocess
    import os
    import nomic
    from nomic import embed

    print('AG: inside get_git_data @stub.funtion')
    # Run the git clone command
    print(f'AG: starting git clone {github_url}')
    subprocess.run(f"cd /data && git clone {github_url}", shell=True)
    volume.commit()
    # Git content is list of dicts. Each element of list is a git file
    # and each dict has keys: path and code
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
                        file_dict['code'] = f.read()
                        print(f"AG: {read_file_content.__name__} Contents saved for {file_path}:")
                    git_content.append(file_dict)
    
    # Split the URL and extract the repository name without the '.git' extension
    repository_name = github_url.split('/')[-1][:-4]
    # Use f-string to include the variables in the command
    subprocess.run(f"echo AG1234 && echo /data/{repository_name}", shell=True)
    read_file_content(f'/data/{repository_name}')
    print(f"Num of files read: {len(git_content)}")
    sample_file_data = """
        Once upon a time, in a quaint little town nestled between rolling hills and lush forests, there lived a friendly and adventurous dog named Max. Max was a mix of a Golden Retriever and a Border Collie, which made him both clever and affectionate.
        Max's days were filled with excitement and exploration. He would often roam the town, making friends with everyone he met. His favorite spot was the town square, where he would eagerly greet the townspeople and play with the local children.
        One day, while exploring the woods on the outskirts of town, Max stumbled upon a hidden path that led to a mysterious old house. Curiosity piqued, he bravely ventured inside, only to discover that the house was home to a family of friendly squirrels.
        The squirrels welcomed Max with open arms (or rather, open paws), and they quickly became the best of friends. Together, they would explore the woods, play games, and share stories late into the night.
        As the seasons changed, so did Max's adventures. In the winter, he would frolic in the snow with his squirrel friends, while in the summer, they would swim in the nearby creek and bask in the warm sun.
        Through his adventures, Max taught the townspeople the importance of kindness, friendship, and the joy of exploring the world around them. And so, Max's story became a beloved tale in the town, inspiring everyone to embrace life with the same enthusiasm and curiosity as their furry friend."""
    print('AG: git clone done')
    return git_contentgit git 

@stub.function(image=image,
                volumes={'/data': volume},
                secrets=[modal.Secret.from_name("nomic-key")],
                )
@asgi_app()
def fastapi_app():
    print('AG: starting fastapi app...')
    return web_app