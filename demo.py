import time
import streamlit as st
from clients.yext_client import SuperYextClient
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
    return SuperYextClient(api_key)


@st.cache_resource
def init_dsg_client(api_key):
    return DSGClient(api_key)


def search_request(client, query, experience_key, vertical_key):
    return client.search_answers_vertical(query=query, experience_key=experience_key, vertical_key=vertical_key)


def clean_search_results(dsg_client, segment, prompt="clean_segment_prompt.md"):
    with open(prompt, "r") as f:
        prompt = f.read()
    
    prompt = prompt.format(segment=segment)
    
    cleaned_results = dsg_client.chat_completion(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return cleaned_results


def result_card(result, body_field=[], dsg_client=None):
    name = result["data"]["name"]

    # Get the body value (e.g., 'bodyV2.markdown')
    body_value = result["data"]
    for field in body_field:
        if field in body_value:
            body_value = body_value[field]

    # For vector search results
    if "segment" in result:
        segment = "... " + result["segment"]["text"].strip() + " ..."
        score = result["segment"]["score"]

        # If the name segment, replace it with the body field
        if name == segment:
            segment = body_value[:250] + " ..."
            score = str(result["segment"]["score"]) + " (matched on name)"
        
        # If recieved a DSG client, clean the segment
        if dsg_client:
            segment = clean_search_results(dsg_client, segment)

        template = f"""
        <div style="border-radius: 5px; background-color: #f2f2f2; padding: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
            <div style="font-size: 18px; font-weight: bold;">{name}</div>
            <p style="margin: 10px 0;">{segment}</p>
            <p style="text-align: right;"><i>Score: {score}</i></p>
        </div>
        """

        return st.write(template, unsafe_allow_html=True)
    
    # For current results, just use the body value
    else:
        if result["data"].get("s_snippet"):
            segment = result["data"].get("s_snippet")
        else:
            segment = body_value[:250] + " ..."

        # If recieved a DSG client, clean the segment
        if dsg_client:
            segment = clean_search_results(dsg_client, segment)

        template = f"""
        <div style="border-radius: 5px; background-color: #f2f2f2; padding: 10px; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
            <div style="font-size: 18px; font-weight: bold;">{name}</div>
            <p style="margin: 10px 0;">{segment}</p>
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
        "current_vertical_key": "books_current",
        "body_field": ["c_file", "s_content"],
        "default_search": "",
    },
    "samsung": {
        "name": "Samsung Troubleshooting Guides",
        "api_key": st.secrets["samsung-troubleshooting-search"]["api_key"],
        "experience_key": "samsung-troubleshooting-search",
        "vertical_key": "guides",
        "current_vertical_key": "guides_current",
        "body_field": ["bodyV2", "markdown"],
        "default_search": ""
    }
}

# Populate sidebar options
st.sidebar.write("## Demo Options")
demo = st.sidebar.selectbox("Select Demo", list(DEMOS.keys()))
show_current = st.sidebar.checkbox("Compare Non-Vector Results", value=False)
# Removing option, because very slow
# gpt_cleaning = st.sidebar.checkbox("Use GPT Cleaning", value=False)
chat_direct_answer = st.sidebar.checkbox("Generate Chat Direct Answer", value=False)

# Calculate values
client = init_yext_client(DEMOS[demo]["api_key"])
dsg_client = None
# if gpt_cleaning: # Only if the user wants to clean segments
#     dsg_client = init_dsg_client(DEMOS[demo]["api_key"])
experience_key = DEMOS[demo]["experience_key"]
vertical_key = DEMOS[demo]["vertical_key"]
body_field = DEMOS[demo]["body_field"]
query = st.text_input(label=f"Search {DEMOS[demo]['name']}:", value=DEMOS[demo]["default_search"])

# Fetch results for vector search
if query:
    start = time.time()
    response = search_request(client, query, experience_key, vertical_key)
    end = time.time()
    response_time = end - start
    results = response["response"].get("results", [])
    results_count = response["response"].get("resultsCount", 0)
    direct_answer = response["response"].get("directAnswer", None)

    # Get results for non-vector search
    if show_current:
        start = time.time()
        current_response = search_request(client, query, experience_key, DEMOS[demo]["current_vertical_key"])
        end = time.time()
        current_response_time = end - start
        current_results = current_response["response"].get("results", [])
        current_results_count = current_response["response"].get("resultsCount", 0)
        current_direct_answer = current_response["response"].get("directAnswer", None)

    # Write API response
    st.sidebar.write("## API Responses")
    with st.sidebar.expander("View Raw Response"):
        st.write(response)
    if show_current:
        with st.sidebar.expander("View Non-Vector Raw Response"):
            st.write(current_response)


    # Render results
    if show_current:
        vector, current = st.columns(2, gap="medium")

        with vector:
            st.write("### Vector Document Search")
            if query:
                st.write(f"_{results_count} results ({response_time:.2f} seconds)_")
            if direct_answer:
                direct_answer_card(direct_answer)
                st.write("---")

                related_result = direct_answer["relatedItem"]["data"]["uid"]

                for result in results:
                    if result["data"]["uid"] == related_result and direct_answer["answer"]["snippet"]["value"] in result["segment"]["text"]:
                        result_card(result, body_field, dsg_client)
                        st.write("---")
                        results.remove(result)
                        break

            for result in results:
                result_card(result, body_field, dsg_client)
                st.write("---")

        with current:
            st.write("### Non-Vector Search")
            if query:
                st.write(f"_{current_results_count} results ({current_response_time:.2f} seconds)_")
            if current_direct_answer:
                direct_answer_card(current_direct_answer)
                st.write("---")

                related_result = current_direct_answer["relatedItem"]["data"]["uid"]

                for result in current_results:
                    if result["data"]["uid"] == related_result:
                        result_card(result, body_field, dsg_client)
                        st.write("---")
                        current_results.remove(result)
                        break

            for result in current_results:
                result_card(result, body_field, dsg_client)
                st.write("---")        

    else:
        if query:
            st.write(f"_{results_count} results ({response_time:.2f} seconds)_")
        if direct_answer:
            direct_answer_card(direct_answer)
            st.write("---")

            related_result = direct_answer["relatedItem"]["data"]["uid"]

            for result in results:
                if result["data"]["uid"] == related_result and direct_answer["answer"]["snippet"]["value"] in result["segment"]["text"]:
                    result_card(result, body_field, dsg_client)
                    st.write("---")
                    results.remove(result)
                    break

        for result in results:
            result_card(result, body_field, dsg_client)
            st.write("---")
            