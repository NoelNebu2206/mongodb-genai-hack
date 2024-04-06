import cohere
import os

class CohereChatbot:
    def __init__(self, api_key, model='command-r', max_tokens=4000, temperature=0.5):
        self.client = cohere.Client(api_key)
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature

    def chat(self, message, chat_history=[]):
        response = self.client.chat(
            chat_history=chat_history,
            message=message,
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature
        )
        return response.text

    def generate_documentation(self, code_content, user_query="Generate documentation for this code."):
        prompt = f"""
        You are an assistant for code documentation tasks. Use the following code content to generate documentation for the code.
            Code content:\n{code_content}\n\nUser query: {user_query}\n\n
            Please generate documentation for the code based on the following guidelines:
            - Describe the purpose of the code in detail, including its intended use and any specific features or functionalities it offers.
            - Explain the overall logic and structure of the code, highlighting how different components interact and the flow of data.
            - For each important function or class, provide a detailed description that includes:
              - Parameters: List and explain each parameter, including its type and purpose.
              - Return values: Describe what the function or method returns and its type.
              - Side effects: Mention any changes the function makes to the state of the program or external effects.
            - Include specific code examples for using key functions or classes, demonstrating how they can be implemented in practice.
            - Document any potential errors or exceptions that the functions might raise, and provide guidance on how to handle them effectively.
            - If applicable, include notes on the performance characteristics of the code, such as time complexity, memory usage, or scalability considerations.
            - List any external dependencies required by the code, along with instructions on how to install and configure them.
            - Provide usage examples that show how to run the code, including any necessary command-line arguments or configuration settings.
            \nResponse:
            """
        return self.chat(prompt)

# Example usage
if __name__ == "__main__":
    cohere_api_key = os.getenv('COHERE_API_KEY')
    code = "def add(a, b): return a + b"

    chatbot = CohereChatbot(api_key=cohere_api_key)
    documentation = chatbot.generate_documentation(code)
    print(documentation)


