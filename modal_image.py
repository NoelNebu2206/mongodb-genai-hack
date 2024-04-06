from modal import Image

image = Image.debian_slim(python_version="3.11").pip_install("modal==0.62.21", "nomic").apt_install("git", "curl")