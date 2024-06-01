from modal import method, enter
from modal_image import image, stub
#from bson import ObjectId

@stub.cls(image = image, gpu="T4", container_idle_timeout=300)
class AtlasClient ():
    @enter()
    def enter(self):
        """
        Establishes a connection to a MongoDB Atlas cluster using a MongoDB URI constructed from a username and password.
        It uses the MongoClient from pymongo to initiate the connection.
        Raises:
            Exception: If the MongoClient is not initialized successfully.
        """
        
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
    def update_files(self, database_name = "MongoHack", collection_name = "collection_files", documents = [], email = "", repo_name = ""):
        """
        Inserts a list of documents into a specified MongoDB collection.

        Parameters:
            database_name (str): Name of the MongoDB database.
            collection_name (str): Name of the MongoDB collection.
            documents (list of dict): Documents to insert.

        Returns:
            result (InsertManyResult): MongoDB response object with the status of the insert operation.
        """
        if not self.client:
            raise Exception("MongoClient is not initialized. Call enter() method first.")

        db = self.client[database_name]
        try:
            collection = db[collection_name]
            result_files = collection.insert_many(documents)
            print(f"Inserted {len(result_files.inserted_ids)} documents into '{database_name}.{collection_name}'")
            inserted_ids = result_files.inserted_ids

            new_chat = {
                "chat_history": {},
                "cloned_files": inserted_ids
            }
            collection = db["collection_chat"]
            # Inserting the new document into the new collection
            result_chat = collection.insert_one(new_chat)
            print(f"Appended {new_chat} in collection_chat")

            inserted_id = result_chat.inserted_id

            print(inserted_id)

            # Appending the new entry to the list in another collection
            collection = db["collection_user"]
            repo_name = repo_name
            new_entry = {repo_name: inserted_id}

            # Match the document by email and update the 'chats' list
            email = email 
            collection.update_one(
                {"email": email},
                {"$push": {"chats": new_entry}}
            )

            # Optionally, print a success message or return a result
            print(f"Appended {new_entry} to 'chats' list in 'collection_user' for email {email}")

            return inserted_id
        
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    """@method()
    def update_chat(self, database_name = "MongoHack", collection_name = "collection_chat", documents = []):
        
        Inserts a list of documents into a specified MongoDB collection.

        Parameters:
            database_name (str): Name of the MongoDB database.
            collection_name (str): Name of the MongoDB collection.
            documents (list of dict): Documents to insert.

        Returns:
            result (InsertManyResult): MongoDB response object with the status of the insert operation.
        
        if not self.cli ent:
            raise Exception("MongoClient is not initialized. Call enter() method first.")

        db = self.client[database_name]

        try:
            collection = db[collection_name]
            result = collection.insert_many(documents)
            print(f"Inserted {len(result.inserted_ids)} documents into '{database_name}.{collection_name}'")
            inserted_ids = result.inserted_ids
            collection = db[collection_name]
            
            return result
        except Exception as e:
            print(f"An error occurred: {e}")
            return None"""

    @method()
    def retrieve_chat(self, database_name="MongoHack", collection_name="collection_chat", chatId=""):
        """
        Retrieves specific fields from a document in the specified MongoDB collection where the _id matches the given chatId.

        Parameters:
            database_name (str): Name of the MongoDB database.
            collection_chat (str): Name of the MongoDB collection.
            chatId (str): The _id of the document to retrieve.

        Returns:
            dict: A dictionary with the 'chat_history' and 'cloned_files' fields or None if not found.
        """
        if not self.client:
            raise Exception("MongoClient is not initialized. Call enter() method first.")

        db = self.client[database_name]

        try:
            collection = db[collection_name]

            """# Convert the chatId to an ObjectId if it is not already one
            if not isinstance(chatId, ObjectId):
                chatId = ObjectId(chatId)"""
            
            # Retrieve the document where _id matches chatId
            document = collection.find_one({"_id": chatId}, {"chat_history": 1, "cloned_files": 1})

            if document:
                chat_history = document.get("chat_history", [])
                cloned_files = document.get("cloned_files", [])

                print(f"Retrieved chat_history: {chat_history}")
                print(f"Retrieved cloned_files: {cloned_files}")

                return chat_history, cloned_files
            
            else:
                print(f"No document found with _id: {chatId}")
                return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    @method()
    def user(self, database_name="MongoHack", collection_name="collection_user", email=""):
        """
        Checks if a user with the specified email exists. If the user exists, returns the 'chats' field.
        If the user does not exist, inserts a new document with the specified email and an empty 'chats' list.

        Parameters:
            database_name (str): Name of the MongoDB database.
            collection_name (str): Name of the MongoDB collection.
            email (str): The email to be included in the document.

        Returns:
            dict: A dictionary with the 'chats' field if the user exists or the result of the insert operation if a new user is created.
        """
        if not self.client:
            raise Exception("MongoClient is not initialized. Call enter() method first.")

        db = self.client[database_name]
        try:
            collection = db[collection_name]
            
            # Check if the user with the specified email already exists
            existing_user = collection.find_one({"email": email})
            
            if existing_user:
                print(f"User with email '{email}' already exists.")
                return {"chats": existing_user.get("chats", [])}
            else:
                # Prepare the document to be inserted
                document = {
                    "email": email,
                    "chats": []
                }
                # Insert the document into the collection
                result = collection.insert_one(document)
                print(f"Inserted document with email '{email}' into '{database_name}.{collection_name}'")
                return {"inserted_id": str(result.inserted_id)}
            
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
       
    ## A quick way to test if we can connect to Atlas instance
    @method()
    def ping(self):
        """
        Sends a ping command to the MongoDB server to check the connection status.

        Returns:
            None: Outputs the server response to the console.
        """
        response = self.client.admin.command('ping')
        print(response)

    @method()
    def find (self, collection_name, filter = {}, limit=10):
        """
        Retrieves a list of documents from a specified MongoDB collection based on a filter and limit.

        Args:
            collection_name (str): The name of the MongoDB collection to retrieve documents from.
            filter (dict, optional): A query that filters the documents to be returned. Defaults to an empty dictionary.
            limit (int, optional): The maximum number of documents to return. Defaults to 10.

        Returns:
            list: A list of documents from the collection that match the filter criteria, limited by the specified number.
        """
        collection = self.database[collection_name]
        items = list(collection.find(filter=filter, limit=limit))
        return items

    @method()
    def get_collection(self, database_name, collection_name):
        """
        Retrieves a collection object from a specified database.

        Parameters:
            database_name (str): Name of the database.
            collection_name (str): Name of the collection.

        Returns:
            collection (Collection): The MongoDB Collection object.
        """
        db = self.client[database_name]
        collection = db[collection_name]
        return collection

    @method()
    def empty_collection(self, database_name, collection_name):
        """
        Deletes all documents from a specified collection in a MongoDB database.

        Parameters:
            database_name (str): Name of the database.
            collection_name (str): Name of the collection.

        Returns:
            None: Confirms the deletion of documents via console output.
        """
        db = self.client[database_name]
        collection = db[collection_name]
        result = collection.delete_many({})
        print(f"Emptied collection '{database_name}.{collection_name}', deleted {result.deleted_count} documents.")

    @method()
    def vector_search(self, database_name, collection_name, index_name, embedding_vector):
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
        database = self.client[database_name]
        collection = database[collection_name]

        print(embedding_vector)
        # Define the pipeline for vector search
        pipeline = [
            {
                '$vectorSearch': {
                    'index': index_name,  # Replace with your actual index name
                    'path': "doc_embedding",  # The field in the documents containing the vector
                    'queryVector': embedding_vector,  # Replace with your actual query vector
                    'numCandidates': 200,  # Adjust as needed for your use case
                    'limit': 1  # Limit the number of results returned
                }
            },
            {
                '$project': {
#                    '_id': 1,
                    'path': 1,
                    'documentation': 1,
                    'code': 1,
#                    'score': {'$meta': 'vectorSearchScore'}
                }
            }
        ]

        # Run the pipeline on the specified collection in the database
        results = self.client[database_name][collection_name].aggregate(pipeline)

        # Convert and print the results
        print(list(results))

        return list(results)


    def close_connection(self):
        """
        Closes the MongoDB connection.

        Returns:
            None: Confirms the connection closure via console output.
        """
        self.client.close()
        print("Connection closed.")
