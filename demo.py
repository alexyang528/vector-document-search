import time
import streamlit as st
from clients.yext_client import CustomYextClient
from clients.dsg_client import DSGClient

st.set_page_config(
    page_title="Demo: Vector Document Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.title("Demo: Vector Document Search")

@st.cache_resource
def init_yext_client(api_key):
    return CustomYextClient(api_key)


@st.cache_resource
def init_dsg_client(api_key):
    return DSGClient(api_key)


def search_request(client, query, experience_key, vertical_key):
    return client.search_answers_vertical(
        query=query, experience_key=experience_key, vertical_key=vertical_key
    )


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
    segment = "... " + result["segment"]["text"].strip() + " ..."
    score = result["segment"]["score"]

    template = f"""
    <div style="border-radius: 5px; background-color: #f2f2f2; padding: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
        <div style="font-size: 18px; font-weight: bold;">{name}</div>
        <p style="margin: 10px 0;">{segment}</p>
        <p style="text-align: right;"><i>Score: {score}</i></p>
    </div>
    """

    return st.write(template, unsafe_allow_html=True)


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
    answer_value = answer_value.replace('\n', '')
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


def render_results(query, demo, vector=True):

    if vector:
        vertical_key = demo["vertical_key"]
        result_card = vector_result_card
    else:
        vertical_key = demo["current_vertical_key"]
        result_card = regular_result_card

    # Get search results
    start = time.time()
    response = search_request(demo["client"], query, demo["experience_key"], vertical_key)
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
        st.write("---")
    
    return response, placeholder


def render_direct_answer(response, element, demo):
    
    # Get direct answer
    if demo["chat_client"]:
        with element.container():
            with st.spinner("Generating Chat Direct Answer..."):
                direct_answer = demo["chat_client"].chat_message(query, response, bot_id=demo["bot_id"])
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
        "name": "Harry Potter Books",
        "api_key": st.secrets["book-search"]["api_key"],
        "chat_api_key": st.secrets["book-search"]["chat_api_key"],
        "bot_id": "book-search",
        "goal_id": "ANSWER_QUESTION",
        "experience_key": "book-search",
        "vertical_key": "books",
        "current_vertical_key": "books_current",
        "body_fields": [["c_file", "s_content"]],
        "default_search": "Who is Albus Dumbledore?",
    },
    {
        "name": "Samsung Troubleshooting Guides",
        "api_key": st.secrets["samsung-troubleshooting-search"]["api_key"],
        "chat_api_key": st.secrets["samsung-troubleshooting-search"]["chat_api_key"],
        "bot_id": "samsung-troubleshooting-search",
        "goal_id": "ANSWER_QUESTION",
        "experience_key": "samsung-troubleshooting-search",
        "vertical_key": "guides",
        "current_vertical_key": "guides_current",
        "body_fields": [["bodyV2", "markdown"]],
        "default_search": ""
    },
    {
        "name": "Iceberg Reports",
        "api_key": st.secrets["iceberg-reports"]["api_key"],
        "chat_api_key": None,
        "bot_id": None,
        "experience_key": "iceberg-iq-report-search",
        "vertical_key": "reports",
        "current_vertical_key": None,
        "body_fields": [],
        "default_search": "",
    },
    {
        "name": "Cox Manuals",
        "api_key": st.secrets["cox-manuals"]["api_key"],
        "chat_api_key": None,
        "bot_id": None,
        "experience_key": "cox-residential-answers-for-chat",
        "vertical_key": "manuals_doc_search",
        "current_vertical_key": None,
        "body_fields": [],
        "default_search": "",
    },
    {
        "name": "Hitchhikers",
        "api_key": st.secrets["hitchhikers"]["api_key"],
        "chat_api_key": None,
        "bot_id": None,
        "experience_key": "yext-help-hitchhikers-vector-search",
        "vertical_key": "content",
        "current_vertical_key": "content_current",
        "body_fields": [["body"], ["description"]],
        "default_search": "",
    }
]


# Select demo
st.sidebar.write("## Select Demo")
demo = st.sidebar.selectbox(label="Select Demo", options=DEMOS, format_func=lambda x: x["name"])

# Populate other values
show_current = st.sidebar.checkbox("Compare Non-Vector Results", value=False, disabled=not demo["current_vertical_key"])
chat_direct_answer = st.sidebar.checkbox("Generate Chat Direct Answer", value=False, disabled=not demo["chat_api_key"])
# gpt_cleaning = st.sidebar.checkbox("Use GPT Cleaning", value=False)

# Initialize clients
demo["client"] = init_yext_client(demo["api_key"])
# demo["dsg_client"] = init_dsg_client(demo["api_key"])
demo["chat_client"] = init_yext_client(demo["chat_api_key"]) if chat_direct_answer and demo["chat_api_key"] else None

# Query input
query = st.text_input(label=f"Search {demo['name']}:", value=demo["default_search"])

# Fetch and render results
if query:
    if show_current:
        vector, current = st.columns(2, gap="medium")

        # Render results
        with vector:
            st.write("### Vector Document Search")
            vector_response, vector_placeholder = render_results(query, demo, True)

        with current:
            st.write("### Non-Vector Search")
            current_response, current_placeholder = render_results(query, demo, False)

        # Render direct answers
        with vector:
            results = vector_response["response"].get("results", [])
            if len(results) > 0:
                render_direct_answer(vector_response, vector_placeholder, demo)
        
        with current:
            results = current_response["response"].get("results", [])
            if len(results) > 0:
                render_direct_answer(current_response, current_placeholder, demo)

        # Write API response
        st.sidebar.write("## API Responses")
        with st.sidebar.expander("View Vector Response"):
            st.write(vector_response)
        with st.sidebar.expander("View Non-Vector Response"):
            st.write(current_response)

    else:
        # Render results
        response, placeholder = render_results(query, demo, True)

        # Render direct answer
        render_direct_answer(response, placeholder, demo)

        # Write API response
        st.sidebar.write("## API Responses")
        with st.sidebar.expander("View Response"):
            st.write(response)
