import os
import tempfile
from functools import lru_cache

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.environ['SERPAPI_API_KEY'] = ''

import langchain
import streamlit as st
from langchain.cache import InMemoryCache
from streamlit import logger
from streamlit_chat import message

from docGPT import GPT4Free, create_doc_gpt
from model import PDFLoader

langchain.llm_cache = InMemoryCache()

OPENAI_API_KEY = ''
SERPAPI_API_KEY = ''
model = None

st.session_state.openai_api_key = None
st.session_state.serpapi_api_key = None
st.session_state.g4f_provider = None
app_logger = logger.get_logger(__name__)


def theme() -> None:
    st.set_page_config(page_title="Document GPT")
    st.image('./img/repos_logo.png', width=250)

    with st.sidebar:

        with st.expander(':orange[How to use?]'):
            st.markdown(
                """
                1. Enter your API keys: (You can choose to skip it and use the `gpt4free` free model)
                    * `OpenAI API Key`: Make sure you still have usage left
                    * `SERPAPI API Key`: Optional. If you want to ask questions about content not appearing in the PDF document, you need this key.
                2. Upload a PDF file (choose one method):
                    * method1: Browse and upload your own `.pdf` file from your local machine.
                    * method2: Enter the PDF `URL` link directly.
                3. Start asking questions!
                4. More details.(https://github.com/Lin-jun-xiang/docGPT-streamlit)
                5. If you have any questions, feel free to leave comments and engage in discussions.(https://github.com/Lin-jun-xiang/docGPT-streamlit/issues)
                """
            )


def load_api_key() -> None:
    with st.sidebar:
        if st.session_state.openai_api_key:
            OPENAI_API_KEY = st.session_state.openai_api_key
            st.sidebar.success('API key loaded form previous input')
        else:
            OPENAI_API_KEY = st.sidebar.text_input(
                label='#### Your OpenAI API Key 👇',
                placeholder="sk-...",
                type="password",
                key='OPENAI_API_KEY'
            )
            st.session_state.openai_api_key = OPENAI_API_KEY

        os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

    with st.sidebar:
        if st.session_state.serpapi_api_key:
            SERPAPI_API_KEY = st.session_state.serpapi_api_key
            st.sidebar.success('API key loaded form previous input')
        else:
            SERPAPI_API_KEY = st.sidebar.text_input(
                label='#### Your SERPAPI API Key 👇',
                placeholder="...",
                type="password",
                key='SERPAPI_API_KEY'
            )
            st.session_state.serpapi_api_key = SERPAPI_API_KEY

        os.environ['SERPAPI_API_KEY'] = SERPAPI_API_KEY

    with st.sidebar:
        st.session_state.g4f_provider = st.selectbox(
            (
                "#### Select a provider if you want to use free model. "
                "([details](https://github.com/xtekky/gpt4free#models))"
            ),
            (GPT4Free().PROVIDER_MAPPING.keys())
        )


def upload_and_process_pdf() -> list:
    st.write('#### Upload a PDF file:')
    browse, url_link = st.tabs(
        ['Drag and drop file (Browse files)', 'Enter PDF URL link']
    )
    with browse:
        upload_file = st.file_uploader(
            'Browse file',
            type='pdf',
            label_visibility='hidden'
        )
        upload_file = upload_file.read() if upload_file else None

    with url_link:
        pdf_url = st.text_input(
            "Enter PDF URL Link",
            placeholder='https://www.xxx/uploads/file.pdf',
            label_visibility='hidden'
        )
        if pdf_url:
            upload_file = PDFLoader.crawl_pdf_file(pdf_url)

    if upload_file:
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        temp_file.write(upload_file)
        temp_file_path = temp_file.name

        docs = PDFLoader.load_documents(temp_file_path)
        docs = PDFLoader.split_documents(docs, chunk_size=2000, chunk_overlap=200)

        temp_file.close()
        if temp_file_path:
            os.remove(temp_file_path)

        return docs


@lru_cache(maxsize=20)
def get_response(query: str) -> str:
    try:
        if model is not None:
            response = model.run(query)
            return response
    except Exception as e:
        app_logger.info(f'{__file__}: {e}')
        return (
            'Something wrong in docGPT...\n'
            '1. If you are using gpt4free model, '
            'try to select the different provider.\n'
            '2. If you are using openai model, '
            'check your usage for openai api key.'
        )


theme()
load_api_key()

doc_container = st.container()

with doc_container:
    docs = upload_and_process_pdf()
    model = create_doc_gpt(docs)
    del docs
    st.write('---')

if 'response' not in st.session_state:
    st.session_state['response'] = ['How can I help you?']

if 'query' not in st.session_state:
    st.session_state['query'] = ['Hi']

user_container = st.container()
response_container = st.container()

with user_container:
    query = st.text_input(
        "#### Question:",
        placeholder='Enter your question'
    )

    if query and query != '':
        response = get_response(query)
        st.session_state.query.append(query)
        st.session_state.response.append(response) 

with response_container:
    if st.session_state['response']:
        for i in range(len(st.session_state['response'])-1, -1, -1):
            message(
                st.session_state["response"][i], key=str(i),
                logo=(
                    'https://api.dicebear.com/6.x/bottts/svg?'
                    'baseColor=fb8c00&eyes=bulging'
                )    
            )
            message(
                st.session_state['query'][i], is_user=True, key=str(i) + '_user',
                logo=(
                    'https://api.dicebear.com/6.x/adventurer/svg?'
                    'hair=short16&hairColor=85c2c6&'
                    'eyes=variant12&size=100&'
                    'mouth=variant26&skinColor=f2d3b1'
                )
            )
