from atlas import AtlasClient
from generate_documentation import CohereChatbot
from modal import method, enter
from modal_image import image, stub
import os

@stub.cls(image = image, gpu="T4", container_idle_timeout=300)
class QueryResponder:
    @enter()
    def enter(self):
        #cohere_api_key = os.getenv('COHERE_API_KEY')
        self.chatbot = CohereChatbot()
        self.atlas_client = AtlasClient()

    @method()
    def generate_response(self, user_query, query_embedding, chat_history):
        """relevant_documents = self.atlas_client.vector_search(
            collection_name='your_collection_name',
            index_name='your_index_name',
            embedding_vector=query_embedding
        )"""

        relevant_documents = self.atlas_client.vector_search.remote(
        database_name = 'MongoHack',
        collection_name='MongoHackCollection',
        index_name='vector_index_github',
        embedding_vector=query_embedding[0]
        )

        context = "User Query:" + user_query + "Documentation and code obtained using a vector search with the user query:"
        for doc in relevant_documents:
            context += doc['documentation'] + "\n" + doc['code'] + "\n\n"

        # Append example query-response pairs and updated instructions
        context += """
        Instructions for generating responses:
        - You have access to relevant documentation and code content related to the user's query.
        - Generate a detailed and informative response that directly answers the user's query.
        - Use clear and technical language appropriate for a software developer.
        - Provide explanations, examples, or references to the provided documentation and code when necessary to clarify your response.
        - If the query is about a specific function or class, describe its purpose, usage, and any important parameters or return values.
        - If the query is about an error or issue, provide a possible explanation or solution based on the available code and documentation.
        - Ensure that your response is informative and helpful for someone working with GitHub codespaces.
        - If the query is unclear or lacks context, ask for clarification or additional information.
        """

        response = self.chatbot.chat.remote(message=context, chat_history=chat_history)
        
        return response

