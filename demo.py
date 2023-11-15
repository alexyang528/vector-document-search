import time
import streamlit as st
from clients.yext_client import CustomYextClient
from clients.dsg_client import DSGClient

st.set_page_config(
    page_title="Demo: Yext Vector Search and Generative Answering",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("Demo: Yext Vector Search and Generative Answering")

@st.cache_resource
def init_yext_client(api_key, environment=None):
    return CustomYextClient(api_key, environment)


@st.cache_resource
def init_dsg_client(api_key):
    return DSGClient(api_key)


def search_request(client, query, experience_key, vertical_key, endpoint=None):
    response = client.search_answers_vertical(query, experience_key, vertical_key, endpoint=endpoint)
    return response


def vector_result_card(result):
    name = result["data"]["name"]
    segment = result["segment"]["text"].strip()
    score = result["segment"]["score"]

    # Drop name segments
    if result["segment"]["text"] == name:
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


def regular_direct_answer_card(direct_answer, element):
    
    snippet_value = direct_answer['answer']['snippet']['value']
    offset = direct_answer['answer']['snippet']['matchedSubstrings'][0]['offset']
    length = direct_answer['answer']['snippet']['matchedSubstrings'][0]['length']
    if "value" in direct_answer['answer']:
        answer_value = direct_answer['answer']['value']
    else:
        answer_value = snippet_value[offset:offset+length]
    answer_value = answer_value.replace('\n', ' ')
    book_name = direct_answer['relatedItem']['data']['fieldValues']['name']

    template = f"""
        <div style="border-radius: 5px; background-color: #ADD8E6; padding: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
            <div style="font-size: 18px; font-weight:bold;">{answer_value}</div>
            <div>
                <span>
                    ...{snippet_value[:offset]}<strong>{snippet_value[offset:offset+length]}</strong>{snippet_value[offset + length:]}...
                </span>
            </div>
            <div style="margin-top: 10px; font-size: 14px; color: #777;">
                From: <i>{book_name}</i>
            </div>
        </div>
    """

    return element.write(template, unsafe_allow_html=True)


def render_results(query, demo, client="vector_client"):

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

    # Write result count and time
    st.write(f"_{results_count} results ({response_time:.2f} seconds)_")

    # Direct answer placeholder
    placeholder = st.empty()
    
    # Render results
    st.write("---")
    for result in results:
        result_card(result)
    
    return response, placeholder


def render_direct_answer(response, element, demo):
    
    # Get direct answer
    if demo["chat_client"]:
        with element.container():
            with st.spinner("Generating Answer..."):
                direct_answer = demo["chat_client"].chat_message(
                    query,
                    response,
                    **demo["chat_params"]
                )
        chat_direct_answer_card(direct_answer, element)
    else:
        direct_answer = response["response"].get("directAnswer", None)
        if direct_answer:
            regular_direct_answer_card(direct_answer, element)

        # Logic to boost the direct answer result to the top
        # related_result = direct_answer["relatedItem"]["data"]["uid"]

        # for result in results:
        #     if result["data"]["uid"] == related_result and direct_answer["answer"]["snippet"]["value"] in result["segment"]["text"]:
        #         result_card(result, body_field, dsg_client)
        #         st.write("---")
        #         results.remove(result)
        #         break

    return


DEMOS = [
    {
        "name": "CNO Examples",
        "api_key": st.secrets["cno"]["api_key"],
        "chat_api_key": st.secrets["cno"]["chat_api_key"],
        "chat_params": {
            "bot_id": "generic-question-answerer",
            "goal_id": "ANSWER_QUESTION",
            "step_indices": [0],
        },
        "experience_key": "answers",
        "vertical_key": "files",

        "default_search": "",
        "environment": "SANDBOX"
    },
    {
        "name": "Harry Potter Books",
        "api_key": st.secrets["book-search"]["api_key"],
        "chat_api_key": st.secrets["book-search"]["chat_api_key"],
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
        "chat_params": {
            "bot_id": "generic-question-answerer",
            "goal_id": "ANSWER_QUESTION",
            "step_indices": [0],
        },
        "experience_key": "yext-help-hitchhikers-vector-search",
        "vertical_key": "content",
        "default_search": "",
        "environment": None,
    },
]


# Select demo
st.sidebar.write("## Select Demo")
demo = st.sidebar.selectbox(label="Select Demo", options=DEMOS, format_func=lambda x: x["name"])

# Populate other values
chat_direct_answer = st.checkbox("Generate Answer", value=False, disabled=not demo["chat_api_key"])

# Initialize clients
demo["vector_client"] = init_yext_client(demo["api_key"], environment=demo["environment"])
demo["chat_client"] = init_yext_client(demo["chat_api_key"]) if chat_direct_answer and demo["chat_api_key"] else None

# Query input
query = st.text_input(label=f"Search {demo['name']}:", value=demo["default_search"])

# Fetch and render results
if query:

    # Render results
    st.write("### Vector Search Results")
    vector_response, vector_placeholder = render_results(query, demo)

    # Render direct answers
    results = vector_response["response"].get("results", [])
    render_direct_answer(vector_response, vector_placeholder, demo)
    