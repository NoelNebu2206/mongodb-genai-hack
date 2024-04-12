import os
from modal import Image, Stub, method, enter, Secret
from modal_image import image, stub

@stub.cls(image = image, gpu="T4", container_idle_timeout=300, 

        secrets=[Secret.from_name("nomic-key")],)
class NomicEmbeddings:
    @enter()
    def start(self): 
        import os
        import nomic
        nomic.login(os.environ["NOMIC_API_KEY"])

    @method()
    def get_doc_embeddings(self, git_contents=[], dimensionality=512, embedding_model="nomic-embed-text-v1.5"):
        from nomic import embed
        output = embed.text(
        texts=[file['documentation'] for file in git_contents],
        model=embedding_model,
        task_type='search_document',
        dimensionality=dimensionality,
        )
        for i,embedding in enumerate(output["embeddings"]):
            git_contents[i]['doc_embedding'] = embedding
        print(git_contents[0].keys())
        print(f" len of git_content: {len(git_contents)}")
        return git_contents

    @method()
    def get_query_embeddings(self, query=[], dimensionality=512, embedding_model="nomic-embed-text-v1.5"):
        from nomic import embed
        output = embed.text(
        texts=[query],
        model=embedding_model,
        task_type='search_document',
        dimensionality=dimensionality,
        )
        return output["embeddings"]