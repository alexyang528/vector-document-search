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


def clean_search_results(dsg_client, results, prompt="clean_segment_prompt.md"):
    with open(prompt, "r") as f:
        prompt = f.read()
    
    prompt = prompt.format(results=results)
    
    cleaned_results = dsg_client.chat_completion(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return cleaned_results


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


def regular_result_card(result):
    name = result["data"]["name"]
    segment = result["data"].get("s_snippet", "")

    template = f"""
    <div style="border-radius: 5px; background-color: #f2f2f2; padding: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
        <div style="font-size: 18px; font-weight: bold;">{name}</div>
        <p style="margin: 10px 0;">{segment}</p>
    </div>
    """
    return st.write(template, unsafe_allow_html=True)


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

    if client == "vector_client":
        vertical_key = demo["vertical_key"]
        experience_key = demo["experience_key"]
        result_card = vector_result_card
        endpoint = None
    elif client == "current_client":
        vertical_key = demo["current_vertical_key"]
        experience_key = demo["experience_key"]
        result_card = regular_result_card
        endpoint = None
    elif client == "hybrid_client":
        vertical_key = "harry_potter"
        experience_key = "doc-search"
        result_card = vector_result_card
        endpoint = "https://funny-raptor-good.ngrok-free.app/v2/accounts/me/answers/vertical/query"

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
    # {
    #     "name": "CNO File",
    #     "api_key": st.secrets["cno"]["api_key"],
    #     "chat_api_key": st.secrets["cno"]["chat_api_key"],
    #     "hybrid_api_key": None,
    #     "chat_params": {
    #         "bot_id": "generic-question-answerer",
    #         "goal_id": "ANSWER_QUESTION",
    #         "step_indices": [0],
    #     },
    #     "experience_key": "answers",
    #     "vertical_key": "files",
    #     "current_vertical_key": "files_old",
    #     "default_search": "",
    #     "environment": "SANDBOX"
    # },
    {
        "name": "Harry Potter Books",
        "api_key": st.secrets["book-search"]["api_key"],
        "chat_api_key": st.secrets["book-search"]["chat_api_key"],
        "hybrid_api_key": "a1ed3828b792e4dbad4785c482c90e1b",
        "chat_params": {
            "bot_id": "book-search",
            "goal_id": "ANSWER_QUESTION",
            "step_indices": [1],
        },
        "experience_key": "book-search",
        "vertical_key": "books",
        "current_vertical_key": "books_current",
        "default_search": "",
        "environment": None,
    },
    # {
    #     "name": "Samsung Troubleshooting Guides",
    #     "api_key": st.secrets["samsung-troubleshooting-search"]["api_key"],
    #     "chat_api_key": st.secrets["samsung-troubleshooting-search"]["chat_api_key"],
    #     "hybrid_api_key": None,
    #     "chat_params": {
    #         "bot_id": "generic-question-answerer",
    #         "goal_id": "ANSWER_QUESTION",
    #         "step_indices": [0],
    #     },
    #     "experience_key": "samsung-troubleshooting-search",
    #     "vertical_key": "guides",
    #     "current_vertical_key": "guides_current",
    #     "default_search": "",
    #     "environment": None,
    # },
    # {
    #     "name": "Iceberg Reports",
    #     "api_key": st.secrets["iceberg-reports"]["api_key"],
    #     "chat_api_key": st.secrets["iceberg-reports"]["chat_api_key"],
    #     "hybrid_api_key": None,
    #     "chat_params": {
    #         "bot_id": "generic-question-answerer",
    #         "goal_id": "ANSWER_QUESTION",
    #         "step_indices": [0],
    #     },
    #     "experience_key": "iceberg-iq-report-search",
    #     "vertical_key": "reports",
    #     "current_vertical_key": None,
    #     "default_search": "",
    #     "environment": None,
    # },
    # {
    #     "name": "Cox Manuals",
    #     "api_key": st.secrets["cox-manuals"]["api_key"],
    #     "chat_api_key": st.secrets["cox-manuals"]["chat_api_key"],
    #     "hybrid_api_key": None,
    #     "chat_params": {
    #         "bot_id": "generic-question-answerer",
    #         "goal_id": "ANSWER_QUESTION",
    #         "step_indices": [0],
    #     },
    #     "experience_key": "cox-residential-answers-for-chat",
    #     "vertical_key": "manuals_doc_search",
    #     "current_vertical_key": None,
    #     "default_search": "",
    #     "environment": None,
    # },
    {
        "name": "Hitchhikers",
        "api_key": st.secrets["hitchhikers"]["api_key"],
        "chat_api_key": st.secrets["hitchhikers"]["chat_api_key"],
        "hybrid_api_key": None,
        "chat_params": {
            "bot_id": "generic-question-answerer",
            "goal_id": "ANSWER_QUESTION",
            "step_indices": [0],
        },
        "experience_key": "yext-help-hitchhikers-vector-search",
        "vertical_key": "content",
        "current_vertical_key": "content_current",
        "default_search": "",
        "environment": None,
    },
    {
        "name": "Telescope Knowledge Base",
        "api_key": st.secrets["telescope"]["api_key"],
        "chat_api_key": st.secrets["telescope"]["chat_api_key"],
        "hybrid_api_key": None,
        "chat_params": {
            "bot_id": "generic-question-answerer",
            "goal_id": "ANSWER_QUESTION",
            "step_indices": [0],
        },
        "experience_key": "yext-intranet",
        "vertical_key": "knowledge_base_vector",
        "current_vertical_key": "knowledge_base",
        "default_search": "",
        "environment": None,
    },
    # {
    #     "name": "Ski Warehouse",
    #     "api_key": st.secrets["ski-warehouse"]["api_key"],
    #     "chat_api_key": st.secrets["ski-warehouse"]["chat_api_key"],
    #     "hybrid_api_key": None,
    #     "chat_params": {
    #         "bot_id": "generic-question-answerer",
    #         "goal_id": "ANSWER_QUESTION",
    #         "step_indices": [0],
    #     },
    #     "experience_key": "yext-ski-warehouse-vector",
    #     "vertical_key": "content",
    #     "current_vertical_key": "content-current",
    #     "default_search": "What are the vibes like at Vail?",
    #     "environment": None,
    # },
    # {
    #     "name": "Healthcare DXP Demo",
    #     "api_key": st.secrets["healthcare-dxp-demo"]["api_key"],
    #     "chat_api_key": st.secrets["healthcare-dxp-demo"]["chat_api_key"],
    #     "hybrid_api_key": None,
    #     "chat_params": {
    #         "bot_id": "generic-question-answerer",
    #         "goal_id": "ANSWER_QUESTION",
    #         "step_indices": [0],
    #     },
    #     "experience_key": "handbook-search",
    #     "vertical_key": "handbooks",
    #     "current_vertical_key": "handbooks_nonvector",
    #     "default_search": "",
    #     "environment": None,
    # },
    # {
    #     "name": "Square Support Articles",
    #     "api_key": st.secrets["square-support"]["api_key"],
    #     "chat_api_key": st.secrets["square-support"]["chat_api_key"],
    #     "hybrid_api_key": None,
    #     "chat_params": {
    #         "bot_id": "generic-question-answerer",
    #         "goal_id": "ANSWER_QUESTION",
    #         "step_indices": [0],
    #     },
    #     "experience_key": "chat-backend-generative-answers",
    #     "vertical_key": "articles",
    #     "current_vertical_key": None,
    #     "default_search": "",
    #     "environment": None,
    # }
]


# Select demo
st.sidebar.write("## Select Demo")
demo = st.sidebar.selectbox(label="Select Demo", options=DEMOS, format_func=lambda x: x["name"])

# Populate other values
show_current = st.sidebar.checkbox("Compare Non-Vector Results", value=False, disabled=not demo["current_vertical_key"])
# show_hybrid = st.sidebar.checkbox("Compare Hybrid Results", value=False, disabled=not demo["hybrid_api_key"])
show_hybrid = False
chat_direct_answer = st.checkbox("Generate Answer", value=False, disabled=not demo["chat_api_key"])
# gpt_cleaning = st.sidebar.checkbox("Use GPT Cleaning", value=False)

# Initialize clients
demo["vector_client"] = init_yext_client(demo["api_key"], environment=demo["environment"])
demo["current_client"] = init_yext_client(demo["api_key"], environment=demo["environment"])
demo["hybrid_client"] = init_yext_client(demo["hybrid_api_key"])
demo["dsg_client"] = init_dsg_client(demo["api_key"])
demo["chat_client"] = init_yext_client(demo["chat_api_key"], environment=demo["environment"]) if chat_direct_answer and demo["chat_api_key"] else None

# Query input
query = st.text_input(label=f"Search {demo['name']}:", value=demo["default_search"])

# Define columns
if show_current:
    if show_hybrid:
        vector, current, hybrid = st.columns(3, gap="medium")
    else:
        vector, current = st.columns(2, gap="medium")
else:
    if show_hybrid:
        vector, hybrid = st.columns(2, gap="medium")
    else:
        vector,_ = st.columns([1, 0.001], gap="small")

# Fetch and render results
if query:

    # Render results
    with vector:
        st.write("### Vector Search Results")
        vector_response, vector_placeholder = render_results(query, demo)

    if show_current:
        with current:
            st.write("### Non-Vector Search Results")
            current_response, current_placeholder = render_results(query, demo, client="current_client")
    
    if show_hybrid:
        with hybrid:
            st.write("### Hybrid Search Results")
            hybrid_response, hybrid_placeholder = render_results(query, demo, client="hybrid_client")

    # Render direct answers
    with vector:
        results = vector_response["response"].get("results", [])
        render_direct_answer(vector_response, vector_placeholder, demo)
    
    if show_current:
        with current:
            results = current_response["response"].get("results", [])
            render_direct_answer(current_response, current_placeholder, demo)
        
    if show_hybrid:
        with hybrid:
            results = hybrid_response["response"].get("results", [])
            render_direct_answer(hybrid_response, hybrid_placeholder, demo)

    # Write API response
    st.sidebar.write("## API Responses")

    with st.sidebar.expander("View Vector Response"):
        st.write(vector_response)
    
    if show_current:
        with st.sidebar.expander("View Non-Vector Response"):
            st.write(current_response)
    
    if show_hybrid:
        with st.sidebar.expander("View Hybrid Response"):
            st.write(hybrid_response)
    