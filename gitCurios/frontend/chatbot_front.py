import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
from time import sleep
from langchain_core.messages import AIMessage, HumanMessage
from query_responder import QueryResponder
import nomic
from nomic import embed
from dotenv import load_dotenv
import os
# from backend import get_git_data,get_doc_embeddings
# import os
# from pathlib import Path
# import modal
# from modal_image import image, stub
# from modal import Image, Secret, Stub, web_endpoint, Volume
# from generate_documentation import CohereChatbot

#import NomicEmbed
load_dotenv()

nomic_key = os.environ["NOMIC_API_KEY"]
nomic.login(nomic_key)
#from navigation import make_sidebar

#YAML Load
with open('/Users/lavi./Desktop/MongoDb/mongodb-genai-hack/password.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)


authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['pre-authorized']
)

# def hide_sidebar():
#     st.markdown("""
#     <style>
#         section[data-testid="stSidebar"][aria-expanded="true"]{
#             display: none;
#         }
#     </style>
#     """, unsafe_allow_html=True)

#Actually what we need to return
def get_response(user_input):
    output = embed.text(
            texts=[user_input],
            model='nomic-embed-text-v1.5',
            task_type='search_document',
            dimensionality=512,
            )
    queryResponder=QueryResponder()
    llm_output=queryResponder.generate_response(output,chat_history)
    #return "Test output long to check generation"
    return llm_output
#authenticator
authenticator.login()

#session
if st.session_state["authentication_status"]:
    #hide_sidebar()
    sleep(0.2)
    
    #authenticator.logout()
    #st.experimental_set_query_params(page="welcome", name=st.session_state.get("username", ""))
    #st.query_params.page("welcome").name(st.session_state.get("username", ""))
    st.query_params["page"] = "welcome"
    st.query_params["name"] = st.session_state.get("username", "")
    st.title('Welcome to GitCurious')
    with st.sidebar:
        st.write(f'Hit me up with your Link *{st.session_state["username"]}* !')
        website_url=st.text_input("")
       
        st.warning('Please enter valid github link, eg: https://github.com/samplename')
        authenticator.logout()

    if "github.com" not in website_url:
        st.info("Please enter a Git repo link to continue")
    else:
        #gitlink sent from here
        # st.info("Please be patient while we process the data.")
        # sleep(0.9)
        # git_contents = get_git_data.remote(website_url)
        # chatbot = CohereChatbot()
        # for i, file in enumerate(git_contents):
        #     git_contents[i]['documentation'] = chatbot.generate_documentation.remote(file)
    
        # git_contents = get_doc_embeddings.remote(git_contents)

        user_query=st.chat_input("Type your question here...")
        
        if "chat_history" not in st.session_state:
            st.session_state.chat_history=[AIMessage(content="Hello, I am a Bot. How can I help you today ?")]
        if user_query is not None and user_query!="":
           
            #response=get_response(user_query)
            response=get_response(user_query)
            st.session_state.chat_history.append(HumanMessage(content=user_query))
            st.session_state.chat_history.append(AIMessage(content=response))

        for message in st.session_state.chat_history:
            if isinstance(message,AIMessage):
                with st.chat_message("AI"):
                    #word="Hello long text to check word play"
                    #st.chat_message(word)
                    #word=word.split()
                    #sentence=""
                    #for w in word:
                        #sentence+=w+" "
                    #st.write(sentence, end="\r")
                    #sleep(0.2)
                    #st.write(word)
                    st.write(message.content)
            elif isinstance(message,HumanMessage):
                with st.chat_message("Human"):
                    st.write(message.content)
        # for message in st.session_state.chat_history:
        #     if isinstance(message, AIMessage):
        #         with st.chat_message("AI"):
        #         # Concatenate words with spaces between them
        #             ai_message = ' '.join(message.content.split())
        #             st.write(ai_message)
        #     elif isinstance(message, HumanMessage):
        #         with st.chat_message("Human"):
        #             st.write(message.content)
        # def gen_serialized():
        #     for i in gen():
        #         yield json.dumps(i) + "\x1e"

      
elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')


#hide_sidebar()

