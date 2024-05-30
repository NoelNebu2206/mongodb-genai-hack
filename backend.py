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
import shutil

import logging

logging.basicConfig(level=logging.INFO)

web_app = FastAPI()

volume = Volume.from_name("repo_data", create_if_missing=True)

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
    logging.info(chat_history)
    
    transcript = [{'role': message['name'], 'message': message['content']} for message in chat_history]
    logging.info(transcript)
    
    logging.info("Creating user query embeddings")
    query = [user_input]
    query_embeddings = chatbot.create_embeddings.remote(doc=query, input_type="search_query").tolist()
    
    logging.info("Sending the data for response from LLM")
    llm_output = queryResponder.generate_response.remote(user_input, query_embeddings, transcript)
    logging.info(llm_output)
    
    return {"response": llm_output}

@web_app.post("/get_git_data")
async def get_git_data_endpoint(request: Request):
    logging.info("Received URL at get_git_data")
    data = await request.json()
    github_url = data.get('github_url')
    if ".git" not in github_url:
        github_url = github_url + ".git"

    logging.info('Redirecting to get_git_data')
    git_contents, repo_path = get_git_data.remote(github_url)
    logging.info("Sending for creating documentation")
    logging.info(git_contents)
    
    for i, file in enumerate(git_contents):
        future = chatbot.generate_documentation.remote(file)
        git_contents[i]['documentation'] = [str(future)]
        logging.info([str(future)])
        
    logging.info('Done generating documentation')
    
    for i, file in enumerate(git_contents):
        git_contents[i]['doc_embedding'] = chatbot.create_embeddings.remote(doc=git_contents[i]['documentation'], input_type="search_document").tolist()

    logging.info("Starting the insert process")
    mongoDbClient.insert_documents.remote(collection_name="MongoHackCollection", database_name='MongoHack', documents=git_contents)
    logging.info('Push done')

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
                        git_content.append({'path': file_path, 'code': f.read()})
                        logging.info(f"Contents saved for {file_path}")

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
