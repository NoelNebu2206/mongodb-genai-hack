from modal import Image, Stub

image = Image.debian_slim(python_version="3.11").pip_install(
    "modal==0.62.21",
     "nomic",
     "cohere",
     "python-dotenv==1.0.0",
     "pymongo==4.6.2",
     "boto3",
     "langchain",
     ).apt_install("git", "curl")
    #  .run_commands(
    #      "cd /pkg/modal && echo pwd"
    #  )

stub = Stub(
    name="MongoTest",
    image=image,
    #secrets=[Secret.from_name("openai-secret")],
)
