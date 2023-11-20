import time
import streamlit as st
from clients.yext_client import CustomYextClient
from clients.dsg_client import DSGClient
from clients.google_client import GoogleClient

st.set_page_config(
    page_title="デモ: Yext ベクトル検索と生成応答",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("デモ: Yext ベクトル検索と生成応答")

@st.cache_resource
def init_yext_client(api_key, environment=None):
    return CustomYextClient(api_key, environment)


@st.cache_resource
def init_dsg_client(api_key):
    return DSGClient(api_key)


@st.cache_resource
def init_google_client(api_key):
    return GoogleClient(api_key)

@st.cache_data
def translate_text(_client, text):
    return _client.translate_text(text)

@st.cache_data
def search_request(_client, query, experience_key, vertical_key, endpoint=None):
    response = _client.search_answers_vertical(query, experience_key, vertical_key, endpoint=endpoint)
    return response


def vector_result_card(name, segment, score):

    # Indicator for name segments
    if segment == name:
        template = f"""
        <div style="border-radius: 5px; background-color: #f2f2f2; padding: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
            <p style="font-size: 18px; font-weight: bold;">{name}</p>
            <p style="margin: 10px 0;">(Title) {segment}</p>
            <p style="text-align: right;"><i>Score: {score}</i></p>
        </div>
        """
        st.write(template, unsafe_allow_html=True)
        st.write("---")
        return 

    template = f"""
    <div style="border-radius: 5px; background-color: #f2f2f2; padding: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
        <p style="font-size: 18px; font-weight: bold;">{name}</p>
        <p style="margin: 10px 0;">{segment}</p>
        <p style="text-align: right;"><i>Score: {score}</i></p>
    </div>
    """

    st.write(template, unsafe_allow_html=True)
    st.write("---")
    return 

def chat_direct_answer_card(direct_answer, element):
    template = f"""
        <div style="border-radius: 5px; background-color: #ADD8E6; padding: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
            <div style="font-size: 18px; font-weight:bold;">{direct_answer}</div>
                <div style="margin-top: 10px; font-size: 14px; color: #777;">
                    <i>Generated using Yext Chat</i>
                </div>
        </div>
    """
    return element.write(template, unsafe_allow_html=True)


def regular_direct_answer_card(snippet_value, answer_value, offset, length, item_name, element):

    template = f"""
        <div style="border-radius: 5px; background-color: #ADD8E6; padding: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
            <div style="font-size: 18px; font-weight:bold;">{answer_value}</div>
            <div>
                <span>
                    ...{snippet_value[:offset]}<strong>{snippet_value[offset:offset+length]}</strong>{snippet_value[offset + length:]}...
                </span>
            </div>
            <div style="margin-top: 10px; font-size: 14px; color: #777;">
                From: <i>{item_name}</i>
            </div>
        </div>
    """

    return element.write(template, unsafe_allow_html=True)


def render_results(query, demo, limit=10, client="vector_client", translation_client=None):

    vertical_key = demo["vertical_key"]
    experience_key = demo["experience_key"]
    result_card = vector_result_card
    endpoint = None

    # Get search results
    start = time.time()
    response = search_request(demo[client], query, experience_key, vertical_key, endpoint=endpoint)
    end = time.time()
    response_time = end - start

    # Parse results
    results = response["response"].get("results", [])
    results_count = response["response"].get("resultsCount", 0)

    if limit:
        results = results[:min(results_count, limit)]
        results_count = min(results_count, limit)

    # Write result count and time
    st.write(f"_{results_count} results ({response_time:.2f} seconds)_")

    # Direct answer placeholder
    placeholder = st.empty()
    
    # Render results
    st.write("---")
    for result in results:
        name = result["data"]["name"]
        segment = result["segment"]["text"].strip()
        score = result["segment"]["score"]

        if translation_client:
            name = translate_text(demo[translation_client], name)
            segment = translate_text(demo[translation_client], segment)

        result_card(name, segment, score)
    
    return response, placeholder


def render_direct_answer(response, element, demo, translation_client=None):
    
    # Get direct answer
    if demo["chat_client"]:
        with element.container():
            with st.spinner("Generating Answer..."):
                direct_answer = demo["chat_client"].chat_message(
                    query,
                    response,
                    **demo["chat_params"]
                )

                if translation_client:
                    direct_answer = translate_text(demo[translation_client], direct_answer)

        chat_direct_answer_card(direct_answer, element)
    else:
        direct_answer = response["response"].get("directAnswer", None)
        if direct_answer:
            snippet_value = direct_answer['answer']['snippet']['value']
            offset = direct_answer['answer']['snippet']['matchedSubstrings'][0]['offset']
            length = direct_answer['answer']['snippet']['matchedSubstrings'][0]['length']
            if "value" in direct_answer['answer']:
                answer_value = direct_answer['answer']['value']
            else:
                answer_value = snippet_value[offset:offset+length]
            answer_value = answer_value.replace('\n', ' ')
            item_name = direct_answer['relatedItem']['data']['fieldValues']['name']

            if translation_client:
                snippet_value = translate_text(demo[translation_client], snippet_value)
                answer_value = translate_text(demo[translation_client], answer_value)
                item_name = translate_text(demo[translation_client], item_name)

            regular_direct_answer_card(snippet_value, answer_value, offset, length, item_name, element)
    return


DEMOS = [
    {
        "name": "Harry Potter Books",
        "api_key": st.secrets["book-search"]["api_key"],
        "chat_api_key": st.secrets["book-search"]["chat_api_key"],
        "google_api_key": st.secrets["hitchhikers"]["google_api_key"],
        "chat_params": {
            "bot_id": "book-search",
            "goal_id": "ANSWER_QUESTION",
            "step_indices": [1],
        },
        "experience_key": "book-search",
        "vertical_key": "books",
        "default_search": "",
        "environment": None,
    },
    {
        "name": "Hitchhikers",
        "api_key": st.secrets["hitchhikers"]["api_key"],
        "chat_api_key": st.secrets["hitchhikers"]["chat_api_key"],
        "google_api_key": st.secrets["hitchhikers"]["google_api_key"],
        "chat_params": {
            "bot_id": "generic-question-answerer",
            "goal_id": "ANSWER_QUESTION",
            "step_indices": [0],
        },
        "experience_key": "yext-help-hitchhikers-vector-search",
        "vertical_key": "content",
        "default_search": "",
    },
]


# Select demo
st.sidebar.write("## Select Demo")
demo = st.sidebar.selectbox(label="Select Demo", options=DEMOS, format_func=lambda x: x["name"])

# Populate other values
chat_direct_answer = st.checkbox("Generate Answer", value=False, disabled=not demo["chat_api_key"])

# Initialize clients
demo["vector_client"] = init_yext_client(demo["api_key"], environment=demo["environment"])
demo["dsg_client"] = init_dsg_client(demo["api_key"])
demo["chat_client"] = init_yext_client(demo["chat_api_key"], environment=demo["environment"]) if chat_direct_answer and demo["chat_api_key"] else None
demo["google_client"] = init_google_client(demo["google_api_key"])

# Query input
query = st.text_input(label=f"Search {demo['name']}:", value=demo["default_search"])

# Define columns
original, translation = st.columns(2, gap="medium")

# Fetch and render results
if query:

    # Render results
    with original:
        st.write("### Vector Search Results")
        response, placeholder = render_results(query, demo)
    
    with translation:
        st.write("### ベクトルの検索結果")
        translated_response, translated_placeholder = render_results(query, demo, translation_client="google_client")

    # Render direct answers
    with original:
        results = response["response"].get("results", [])
        render_direct_answer(response, placeholder, demo)

    with translation:
        results = translated_response["response"].get("results", [])
        render_direct_answer(translated_response, translated_placeholder, demo, translation_client="google_client")
