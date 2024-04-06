# Assuming the AtlasClient class is defined in atlas.py
from atlas import AtlasClient
# Assuming the CohereChatbot class is defined in generate_documentation.py
from generate_documentation import CohereChatbot
import os

class QueryResponder:
    def __init__(self, chatbot, atlas_client):
        self.chatbot = chatbot
        self.atlas_client = atlas_client

    def generate_response(self, query_embedding, chat_history):
        relevant_documents = self.atlas_client.vector_search(
            collection_name='your_collection_name',
            index_name='your_index_name',
            embedding_vector=query_embedding
        )

        context = ""
        for doc in relevant_documents:
            context += doc['documentation'] + "\n" + doc['code'] + "\n\n"

        # Append example query-response pairs and updated instructions
        context += """
        Instructions for generating responses:
        - You have access to relevant documentation and code content related to the user's query about GitHub codespaces.
        - Generate a detailed and informative response that directly answers the user's query.
        - Use clear and technical language appropriate for a software developer.
        - Provide explanations, examples, or references to the provided documentation and code when necessary to clarify your response.
        - If the query is about a specific function or class, describe its purpose, usage, and any important parameters or return values.
        - If the query is about an error or issue, provide a possible explanation or solution based on the available code and documentation.
        - Ensure that your response is informative and helpful for someone working with GitHub codespaces.
        - If the query is unclear or lacks context, ask for clarification or additional information.
        """

        response = self.chatbot.chat(message=context, chat_history=chat_history)
        return response

if __name__ == "__main__":
    cohere_api_key = os.getenv('COHERE_API_KEY')
    chatbot = CohereChatbot(api_key=cohere_api_key)
    atlas_client = AtlasClient()

    query_responder = QueryResponder(chatbot, atlas_client)
    query_embedding = [0.1, 0.2, 0.3]  # Example query embedding
    chat_history = []  # Initialize chat history
    response = query_responder.generate_response(query_embedding, chat_history)
    print("Response:", response)
