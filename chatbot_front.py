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
import requests
import json
from json import JSONEncoder

    
#import NomicEmbed
load_dotenv()

nomic_key = os.environ["NOMIC_API_KEY"]
nomic.login(nomic_key)
#from navigation import make_sidebar

#YAML Load
with open('password.yaml') as file:
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


#authenticator
authenticator.login()

#modal_backend_server = "https://yogyagit--mongotest-fastapi-app-dev.modal.run"
modal_backend_server = "https://anubhavghildiyal--mongotest-fastapi-app-dev.modal.run"
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
        if "git_data_fetched" not in st.session_state or not st.session_state["git_data_fetched"]:
            # Data to be sent
            data = {
                "github_url": website_url
            }
            requests.post(modal_backend_server + '/get_git_data', json=data)
            st.session_state["git_data_fetched"] = True
        
        user_query=st.chat_input("Type your question here...")
        
        if "chat_history" not in st.session_state:
            #st.session_state.chat_history=[AIMessage(content="Hello, I am a Bot. How can I help you today ?")]
            st.session_state.chat_history=[AIMessage(content="Hello, I am a Bot. How can I help you today ?", name = "CHATBOT")]
        if user_query is not None and user_query!="":
            chat_history_dicts = [message.dict() for message in st.session_state.chat_history]
            #chat_history = str(chat_history_dicts)
            data = {
                "user_query": user_query,
                "chat_history": chat_history_dicts
            }
            response = requests.post(modal_backend_server + '/get_response_endpoint', json=data)
            print(response.json()["response"])
            st.session_state.chat_history.append(HumanMessage(content=user_query, name = "USER"))
            st.session_state.chat_history.append(AIMessage(content=str(response.json()["response"]), name = "CHATBOT"))

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

