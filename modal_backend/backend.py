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
from modal import Volume
from generate_documentation import CohereChatbot
from fastapi import FastAPI, Request
from modal import asgi_app
#import NomicEmbed
#import git
#from git import Repo

web_app = FastAPI()

volume = Volume.from_name(
    "repo_data", create_if_missing=True
)

MODEL_DIR = "/model"


"""@stub.function(image=image,
                volumes={'/data': volume},
                #secrets=[modal.Secret.from_name("nomic-key")],
                )
def get_doc_embeddings(git_contents:[]):
    import os
    import nomic
    from nomic import embed
    #nomic_key = os.environ["NOMIC_API_KEY"]
    #cohere_key = os.environ["COHERE_API_KEY"]

    nomic_key = "nk-X4y_DNK3k1YZkMrzSOfkZVnzotSjbqtT32IiGShV-R4"
    cohere_key = "AtPKXCoEnTZlZdO2ntfu45juRMYkNtAvZdWssjWS"

    
    nomic.login(nomic_key)
    output = embed.text(
        texts=[file['documentation'] for file in git_contents],
        model='nomic-embed-text-v1.5',
        task_type='search_document',
        dimensionality=512,
    )
    for i,embedding in enumerate(output["embeddings"]):
        git_contents[i]['doc_embedding'] = embedding
    print(git_contents[0].keys())
    print(f" len of git_content: {len(git_contents)}")
    return git_contents"""

#                secrets=[modal.Secret.from_name("nomic-key")],
@stub.function(image=image,
                volumes={'/data': volume},
                )
@web_app.post("/git_complete")
async def get_git_data(request: Request):
#def get_git_data(github_url='https://github.com/anubhavghildiyal/Backdoor_Attack_DNN.git'):
    import subprocess
    import os
    import nomic
    from nomic import embed

    body = await request.json()
    github_url = body["website_url"]

    print('AG: inside get_git_data')
    # Run the git clone command
    print('AG: starting git clone ')

    subprocess.run(["git", "clone", github_url, 'github_data' ])
    #clone_dir = 'github_data'

    #git.Repo.clone_from(github_url, clone_dir)

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
                    

    # Usage
    read_file_content('/data')
    print(f"nu4m of files read: {len(git_content)}")
    sample_file_data = """
        Once upon a time, in a quaint little town nestled between rolling hills and lush forests, there lived a friendly and adventurous dog named Max. Max was a mix of a Golden Retriever and a Border Collie, which made him both clever and affectionate.
        Max's days were filled with excitement and exploration. He would often roam the town, making friends with everyone he met. His favorite spot was the town square, where he would eagerly greet the townspeople and play with the local children.
        One day, while exploring the woods on the outskirts of town, Max stumbled upon a hidden path that led to a mysterious old house. Curiosity piqued, he bravely ventured inside, only to discover that the house was home to a family of friendly squirrels.
        The squirrels welcomed Max with open arms (or rather, open paws), and they quickly became the best of friends. Together, they would explore the woods, play games, and share stories late into the night.
        As the seasons changed, so did Max's adventures. In the winter, he would frolic in the snow with his squirrel friends, while in the summer, they would swim in the nearby creek and bask in the warm sun.
        Through his adventures, Max taught the townspeople the importance of kindness, friendship, and the joy of exploring the world around them. And so, Max's story became a beloved tale in the town, inspiring everyone to embrace life with the same enthusiasm and curiosity as their furry friend."""

    
    #embeddings = nomicOb.generate_embeddings.remote([file['content'] for file in git_content])
    # embeddings = nomicOb.generate_embeddings.remote([sample_file_data]  , embedding_model='nomic-embed-text-v1.5', dimensionality=512, task_type='search_document')
    #embeddings = nomicOb.generate_embeddings.remote([sample_file_data])

    """nomic_key = os.environ["NOMIC_API_KEY"]
    nomic.login(nomic_key)
    
    output = embed.text(
        texts=[file['code'] for file in git_content],
        model='nomic-embed-text-v1.5',
        task_type='search_document',
        dimensionality=512,
    )

    #print(len(output['embeddings']))
    #print(len(output['embeddings'][0]))
    for i,embedding in enumerate(output["embeddings"]):
        git_content[i]['embedding'] = embedding
    print(f"git_content len: {len(git_content)}")
    print(git_content[0].keys())"""

    #volume.commit()
    
    print('AG: git clone done')
    print(git_content)
    return git_content
    
@stub.function(image=image)
@asgi_app()
def fastapi_app():
    return web_app

print('bye')
@stub.local_entrypoint()
def run():
    import os
    print('AG: inside local entrypoint...')
    
    github_repo = "https://github.com/anubhavghildiyal/Backdoor_Attack_DNN.git"

    git_contents = get_git_data.remote()

    # Create chatbot instance
    chatbot = CohereChatbot()

    #Pass the code of each file to the LLm to get documentation for the code
    for i, file in enumerate(git_contents):
        git_contents[i]['documentation'] = chatbot.generate_documentation.remote(file)
    
    git_contents = get_doc_embeddings.remote(git_contents)
    
    # print(git_contents[0]['code'])
    # print(git_contents[0]['documentation'])
    #generate_code_embeddings.remote(git_contents)
    print('AG: done run...')
    