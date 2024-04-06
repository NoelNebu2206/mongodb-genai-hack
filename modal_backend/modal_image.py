from modal import Image, Stub

image = Image.debian_slim(python_version="3.11").pip_install(
    "modal==0.62.21",
     "nomic",
     "cohere",).apt_install("git", "curl")

stub = Stub(
    name="MongoTest",
    image=image,
    #secrets=[Secret.from_name("openai-secret")],
)