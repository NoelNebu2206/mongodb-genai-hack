from pathlib import Path
import modal
from modal_image import image, stub
from modal import Image, Secret, Stub, web_endpoint, Volume, asgi_app
from generate_documentation import CohereChatbot
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from atlas import AtlasClient
from NomicCls import NomicEmbeddings
from query_responder import QueryResponder
import nomic
from nomic import embed
<<<<<<< Updated upstream
import shutil

import logging

logging.basicConfig(level=logging.INFO)

web_app = FastAPI()

volume = Volume.from_name("repo_data", create_if_missing=True)
=======
from fastapi.middleware.cors import CORSMiddleware

web_app = FastAPI()
origins = ["*"]
web_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
volume = Volume.from_name(
    "repo_data", create_if_missing=True
)
>>>>>>> Stashed changes

chatbot = CohereChatbot()
# nomicObj = NomicEmbeddings()
mongoDbClient = AtlasClient()
queryResponder = QueryResponder()

@web_app.post("/get_response_endpoint")
async def get_response(request: Request):
    logging.info("Received user query in backend")
    data = await request.json()
    user_input = data.get('user_query')
    chat_history = data.get("chat_history")
    chatId = data.get('chatId')
    print(chat_history)
    #mongoDbClient.empty_collection.remote(collection_name = "MongoHackCollection", database_name = 'MongoHack')
    transcript = []
    for message in chat_history:
        temp_dict = {}
        temp_dict['role'] = message['name']
        temp_dict['message'] = message['content']
        transcript.append(temp_dict)
    print(transcript)
    print("Creating user query embeddings")

    query = [user_input]
    query_embeddings = chatbot.create_embeddings.remote(doc=query, input_type="search_query").tolist()
    
    logging.info("Sending the data for response from LLM")
    llm_output = queryResponder.generate_response.remote(user_input, query_embeddings, transcript)

    #mongoDbClient.update_chat.remote(database_name="MongoHack", collection_chat="collection_chat", chatId = chatId, )

    print(llm_output)
    return {"response": llm_output}

@web_app.post("/get_git_data")
async def get_git_data_endpoint(request: Request):
    logging.info("Received URL at get_git_data")
    data = await request.json()
    github_url = data.get('github_url')
    email = data.get('email')
    #email = golu123@gmail.com
    if ".git" not in github_url:
        github_url = github_url + ".git"

    logging.info('Redirecting to get_git_data')
    git_contents, repository_name = get_git_data.remote(github_url)
    logging.info("Sending for creating documentation")
    logging.info(git_contents)
    
    for i, file in enumerate(git_contents):
        future = chatbot.generate_documentation.remote(file)
        git_contents[i]['documentation'] = [str(future)]
        logging.info([str(future)])
        
    logging.info('Done generating documentation')
    
    for i, file in enumerate(git_contents):
        git_contents[i]['doc_embedding'] = chatbot.create_embeddings.remote(doc=git_contents[i]['documentation'], input_type="search_document").tolist()

    print("Starting the insert process")
    chatId = mongoDbClient.update_files.remote(documents = git_contents, repo_name = repository_name, email = email)
    print('Documents saved on MongoDB.')
    return {"response": str(chatId)}

@web_app.post("/get_previous_conversation")
async def get_previous_conversation(request: Request):
    print("Recieved URL at get_git_data")
    data = await request.json()
    chatId = data.get('repo_name')
    print("Starting the Chat ID retrieval process")
    chat_history, cloned_files = mongoDbClient.retrieve_chat.remote(database_name="MongoHack", collection_chat="collection_chat", chatId = chatId)
    print('Chat Retrieved')

    return {"history": chat_history, "files": cloned_files}

@web_app.post("/user")
async def user(request: Request):
    print("Recieved user information")
    data = await request.json()
    email = data.get('email')
    print("Starting the user verification process")
    chats = mongoDbClient.user.remote(email = email)
    print('User Document Created')
    return {"response": chats}

    # Delete the cloned repository after processing
    delete_git_data.remote(repo_path)

@stub.function(image=image, volumes={'/data': volume}, secrets=[modal.Secret.from_name("nomic-key")])
def get_git_data(github_url):
    import subprocess
    import os

    logging.info('Inside get_git_data function')
    logging.info(f'Starting git clone {github_url}')
    subprocess.run(f"cd /data && git clone {github_url}", shell=True)
    volume.commit()

    git_content = []

    def read_file_content(directory):
        code_extensions = ['.py', '.js', '.cpp']
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                _, file_extension = os.path.splitext(file_path)
                if file_extension in code_extensions:
                    with open(file_path, 'r') as f:
<<<<<<< Updated upstream
                        git_content.append({'path': file_path, 'code': f.read()})
                        logging.info(f"Contents saved for {file_path}")
=======
                        file_dict['code'] = f.read()
                        print(f"AG: {read_file_content.__name__} Contents saved for {file_path}:")
                    git_content.append(file_dict)
    
    # Split the URL and extract the repository name without the '.git' extension
    repository_name = github_url.split('/')[-1][:-4]
    # Use f-string to include the variables in the command
    subprocess.run(f"echo AG1234 && echo /data/{repository_name}", shell=True)
    read_file_content(f'/data/{repository_name}')
    print(f"Num of files read: {len(git_content)}")
    print('Git clone done')
    return git_content, repository_name
>>>>>>> Stashed changes

    repository_name = github_url.split('/')[-1][:-4]
    repo_path = f'/data/{repository_name}'
    subprocess.run(f"echo /data/{repository_name}", shell=True)
    read_file_content(repo_path)
    logging.info(f"Num of files read: {len(git_content)}")
    return git_content, repo_path

@stub.function(image=image, volumes={'/data': volume})
def generate_response(query_embedding):
    relevant_documents = mongoDbClient.vector_search.remote(
        database_name='MongoHack',
        collection_name='MongoHackCollection',
        index_name='vector_index_github',
        embedding_vector=query_embedding[0]
    )
    return relevant_documents

@stub.function(image=image, volumes={'/data': volume}, secrets=[modal.Secret.from_name("nomic-key")])
def delete_git_data(repo_path):
    import subprocess

    logging.info(f"Deleting repository data at {repo_path}")
    try:
        # Navigate to the /data directory and delete the repository
        subprocess.run(f"cd /data && rm -rf {repo_path}", shell=True, check=True)
        logging.info("Repository data deleted successfully")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to delete repository data: {e}")

@stub.function(image=image, volumes={'/data': volume}, secrets=[modal.Secret.from_name("nomic-key")])
@asgi_app()
def fastapi_app():
    logging.info('Starting FastAPI app')
    return web_app
