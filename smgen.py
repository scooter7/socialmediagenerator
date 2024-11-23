import streamlit as st
from langchain.agents import initialize_agent, load_tools, Tool, AgentType
from langchain_openai import OpenAI
import os
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.DEBUG)

# Set environment variables
os.environ["SERPER_API_KEY"] = st.secrets["SERPER_API_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# Initialize OpenAI model
llm = OpenAI(temperature=0)

# Load Serper tool and rename it
tools = [
    Tool(
        name="Intermediate Answer",  # Rename tool to match agent expectations
        func=load_tools(["google-serper"])[0].run,
        description="Useful for answering questions using search."
    )
]

# Initialize self-ask-with-search agent
self_ask_with_search = initialize_agent(
    tools,
    llm,
    agent=AgentType.SELF_ASK_WITH_SEARCH,
    verbose=True,
    handle_parsing_errors=True  # Enable parsing error handling
)

# Function to manage post length limits
def limit_post_length(content, channel):
    """Limit the length of the content based on the channel."""
    limits = {
        "X": 280,  # Twitter character limit
        "Facebook": 2000,  # Facebook recommended limit
        "LinkedIn": 3000,  # LinkedIn recommended limit
        "Instagram": 2200,  # Instagram caption limit
        "TikTok": 150  # TikTok caption limit
    }
    max_length = limits.get(channel, 2000)  # Default limit if unspecified
    return content[:max_length]

# Function to search for college facts
def search_college_facts(college_name):
    """Search for interesting facts about the college/university."""
    query = f"Find some interesting and notable facts about {college_name}."
    try:
        response = self_ask_with_search.run(query)
        if response.strip().lower() in ["no", "none", "null"]:
            raise ValueError("No valid output was returned from the agent.")
        return response
    except ValueError as e:  # Catch parsing errors
        st.error("Output parsing error occurred. Retrying may help.")
        return ""
    except Exception as e:  # Catch all other errors
        st.error(f"Error fetching results: {e}")
        return ""

# Function to generate social media content
def generate_social_content_with_retry(main_content, selected_channels, retries=3, delay=5):
    """Generate social media content for multiple channels with retry logic."""
    generated_content = {}
    for channel in selected_channels:
        for i in range(retries):
            try:
                prompt = f"Generate a {channel.capitalize()} post based on this content:\n{main_content}\n"
                response = llm(prompt)
                if response:
                    limited_content = limit_post_length(response.strip(), channel)
                    generated_content[channel] = limited_content
                break
            except Exception as e:
                if i < retries - 1:
                    time.sleep(delay)
                else:
                    generated_content[channel] = f"Error generating content: {str(e)}"
    return generated_content

# Streamlit UI with state management
st.title("Social Media Post Creator for Colleges/Universities")

# Initialize session state
if "social_content" not in st.session_state:
    st.session_state["social_content"] = {}

# Inputs
college_name = st.text_input("Enter the name of the college/university:")
topic = st.text_input("Enter the topic for the social media posts:")
selected_channels = st.multiselect(
    "Select the social media channels:",
    ["Facebook", "X", "LinkedIn", "Instagram", "TikTok"]
)

if st.button("Generate Social Media Content"):
    if not college_name or not topic:
        st.error("Please fill out both fields.")
    else:
        st.info("Searching for interesting facts...")
        facts = search_college_facts(college_name)

        if facts:
            st.success("Interesting facts found. Generating posts...")
            main_content = f"Topic: {topic}\nInteresting Facts: {facts}"
            st.session_state["social_content"] = generate_social_content_with_retry(main_content, selected_channels)
        else:
            st.error("No facts found. Try a different college/university.")

# Display generated posts
if st.session_state["social_content"]:
    for channel, content in st.session_state["social_content"].items():
        st.subheader(f"{channel.capitalize()} Post")
        st.text_area(f"Generated Content for {channel}:", content, height=200)

        # Save content as text file
        filename = f"{channel}_post.txt"
        st.download_button(
            label=f"Download {channel.capitalize()} Post",
            data=content,
            file_name=filename,
            mime="text/plain"
        )
