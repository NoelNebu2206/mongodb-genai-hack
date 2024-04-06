from modal import method, enter
from modal_image import image, stub

@stub.cls(image = image, gpu="T4", container_idle_timeout=300)
class AtlasClient ():
    @enter()
    def enter(self):
        """
        Attempts to establish a connection to a MongoDB Atlas cluster by reading the connection URI (ATLAS_URI) from a .env file. It verifies the connection by sending a ping to the MongoDB server. If the connection is successful, it prints a confirmation message; otherwise, it raises an exception.
        
        Raises:
        - Exception: If the 'ATLAS_URI' is not found in the .env file, indicating that the connection URI is not set.
        """
        
        """atlas_uri = os.getenv('ATLAS_URI')
        if not atlas_uri:
            raise Exception("'ATLAS_URI' environment variable is required.")"""
        
        from pymongo import MongoClient
        from urllib.parse import quote_plus

        self.client = None

        username = "ys5250"
        password = "letsHack@1997"  # Example password with special characters
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)

        uri = f"mongodb+srv://{encoded_username}:{encoded_password}@mongogenai.d2rck3r.mongodb.net/"

        # Initialize MongoClient with the Atlas connection string
        self.client = MongoClient(uri)
        print('AtlasClient initialized with URI from environment variable.')

    @method()
    def insert_documents(self, database_name, collection_name, documents):
        """
        Insert a list of dictionaries into a MongoDB collection.

        Parameters:
        - uri (str): MongoDB Atlas connection URI.
        - database_name (str): Name of the database.
        - collection_name (str): Name of the collection.
        - documents (list of dict): List of dictionaries where each dictionary is a document.

        Returns:
        - result: Result of the bulk insert operation.
        """
        """from pymongo import MongoClient
        from urllib.parse import quote_plus

        self.client = None

        username = "ys5250"
        password = "letsHack@1997"  # Example password with special characters
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)

        uri = f"mongodb+srv://{encoded_username}:{encoded_password}@mongogenai.d2rck3r.mongodb.net/"

        # Initialize MongoClient with the Atlas connection string
        self.client = MongoClient(uri)
        print('AtlasClient initialized with URI from environment variable.')
        """

        # Ensure the MongoClient is properly initialized and connected
        if not self.client:
            raise Exception("MongoClient is not initialized. Call enter() method first.")

        # Access the database and collection
        db = self.client[database_name]
        collection = db[collection_name]

        try:
            # Insert documents into the collection
            result = collection.insert_many(documents)
            print(f"Inserted {len(result.inserted_ids)} documents into '{database_name}.{collection_name}'")
            return result
        except Exception as e:
            print(f"An error occurred: {e}")
            return None


    ## A quick way to test if we can connect to Atlas instance
    @method()
    def ping (self):
        self.client.admin.command('ping')

    @method()
    def get_collection (self, collection_name):
        collection = self.database[collection_name]
        return collection

    def find (self, collection_name, filter = {}, limit=10):
        collection = self.database[collection_name]
        items = list(collection.find(filter=filter, limit=limit))
        return items

    @method()
    def vector_search(self, collection_name, index_name, embedding_vector):
        """
        Perform a vector search on a specified collection in MongoDB, comparing a given vector 
        to vectors stored in the "documentation" field of documents. Returns documents that match 
        the query, including their "documentation" and "code" fields, along with the search score.

        Parameters:
        - collection_name (str): The name of the collection within the MongoDB database to perform the search.
        - index_name (str): The name of the Atlas Search index configured to support vector searches on the collection.
        - embedding_vector (list of float): The embedding vector to compare against the "documentation" vectors of the documents in the collection.

        Returns:
        - list: A list of dictionaries representing the matched documents. Each dictionary includes the "_id", "documentation", and "code" fields from the matching document, as well as the "search_score" indicating the relevance of the match.

        Note:
        - This function is designed to return as many relevant results as possible based on the query vector. The actual number of returned documents is subject to MongoDB's limits on response size and internal handling of vector search queries.
        - The effectiveness of the search depends on the configuration of the Atlas Search index specified by `index_name`, particularly how it's set up to handle vector searches for the "documentation" field.
        """
        """from pymongo import MongoClient
        from urllib.parse import quote_plus

        self.client = None

        username = "ys5250"
        password = "letsHack@1997"  # Example password with special characters
        encoded_username = quote_plus(username)
        encoded_password = quote_plus(password)

        uri = f"mongodb+srv://{encoded_username}:{encoded_password}@mongogenai.d2rck3r.mongodb.net/"

        # Initialize MongoClient with the Atlas connection string
        self.client = MongoClient(uri)
        print('AtlasClient initialized with URI from environment variable.')
        """

        collection = self.database[collection_name]
        results = collection.aggregate([
            {
                '$search': {
                    'index': index_name,
                    'compound': {
                        'should': [
                            {
                                'vector': {
                                    'documentation': {
                                        'query': embedding_vector,
                                        'path': 'documentation',  # The field in documents containing the vector to compare
                                        'score': {'boost': {'value': 1}}  # Optional score boosting
                                    }
                                }
                            }
                        ]
                    }
                }
            },
            {
                '$project': {
                    '_id': 1,
                    'documentation': 1,  # Include the documentation field in the results
                    'code': 1,  # Include the code field in the results
                    "search_score": {"$meta": "searchScore"}  # Include the search score in the results
                }
            }
        ])

        return list(results)

    def close_connection(self):
        self.client.close()

# For local testing
@stub.local_entrypoint()
def main():
    model = AtlasClient()
    dict_list = [
        {"ingredients": "Sauce", "shop": "TJ"},
        {"ingredients": "Cheese", "shop": "Target"}]
    model.insert_documents.remote(collection_name = 'Pizza', database_name = 'Food', documents = dict_list )

