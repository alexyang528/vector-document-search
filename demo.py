import streamlit as st
from clients.yext_client import SuperYextClient
from clients.dsg_client import DSGClient

st.set_page_config(
    page_title="Demo: Vector Document Search",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

@st.cache_resource
def init_yext_client(api_key):
    return SuperYextClient(api_key)

@st.cache_resource
def init_dsg_client(api_key):
    return DSGClient(api_key)


def search_request(client, query, experience_key, vertical_key):
    return client.search_answers_vertical(query=query, experience_key=experience_key, vertical_key=vertical_key)


def result_card(result, body_field=None):
    name = result["data"]["name"]
    segment = result["segment"]["text"].strip()

    # IF the name segment, replace it with the body field
    if name == segment and body_field:
        segment = result["data"][body_field]["markdown"][:250] + " ..."
        score = str(result["segment"]["score"]) + " (matched on name)"
    else:
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


def direct_answer_card(direct_answer):
    snippet_value = direct_answer['answer']['snippet']['value']
    offset = direct_answer['answer']['snippet']['matchedSubstrings'][0]['offset']
    length = direct_answer['answer']['snippet']['matchedSubstrings'][0]['length']
    if "value" in direct_answer['answer']:
        answer_value = direct_answer['answer']['value']
    else:
        answer_value = snippet_value[offset:offset+length]
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

    return st.write(template, unsafe_allow_html=True)


DEMOS = {
    "harry_potter": {
        "name": "Harry Potter Books",
        "api_key": st.secrets["book-search"]["api_key"],
        "experience_key": "book-search",
        "vertical_key": "books",
        "body_field": None,
        "default_search": "Who is Albus Dumbledore?",
    },
    "samsung": {
        "name": "Samsung Troubleshooting Guides",
        "api_key": st.secrets["samsung-troubleshooting-search"]["api_key"],
        "experience_key": "samsung-troubleshooting-search",
        "vertical_key": "guides",
        "body_field": "bodyV2",
        "default_search": "How do I reset my ice maker?"
    }
}

demo = st.sidebar.selectbox("Select Demo", list(DEMOS.keys()))

client = init_yext_client(DEMOS[demo]["api_key"])
experience_key = DEMOS[demo]["experience_key"]
vertical_key = DEMOS[demo]["vertical_key"]
body_field = DEMOS[demo]["body_field"]

query = st.text_input(label="Search Query", value=DEMOS[demo]["default_search"])
response = search_request(client, query, experience_key, vertical_key)

with st.sidebar.expander("View Raw Response"):
    st.write(response)


try:
    direct_answer = response["response"]["directAnswer"]
except:
    direct_answer = None
results = response["response"]["results"]

st.write("")

if direct_answer:
    direct_answer_card(direct_answer)
    st.write("---")

    related_result = direct_answer["relatedItem"]["data"]["uid"]

    for result in results:
        if result["data"]["uid"] == related_result and direct_answer["answer"]["snippet"]["value"] in result["segment"]["text"]:
            result_card(result, body_field)
            st.write("---")
            results.remove(result)
            break

for result in results:
    result_card(result, body_field)
    st.write("---")
    