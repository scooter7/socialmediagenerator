import streamlit as st
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_openai import OpenAI
from langchain.agents import initialize_agent, Tool
from langchain.agents import AgentType
import os

# Set environment variables
os.environ["SERPER_API_KEY"] = st.secrets["SERPER_API_KEY"]
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# Initialize LangChain components
llm = OpenAI(temperature=0)
search = GoogleSerperAPIWrapper()
tools = [
    Tool(
        name="Intermediate Answer",
        func=search.run,
        description="Useful for answering questions using search."
    )
]

# Initialize self-ask-with-search agent
self_ask_with_search = initialize_agent(
    tools,
    llm,
    agent=AgentType.SELF_ASK_WITH_SEARCH,
    verbose=True
)

# Helper function to search for facts about a college
def search_college_facts(college_name):
    """Search for interesting facts about the college/university."""
    query = f"Interesting facts about {college_name}"
    try:
        response = self_ask_with_search.run(query)
        return response
    except Exception as e:
        st.error(f"Error fetching results: {e}")
        return ""

# Helper function to generate social media posts
def generate_social_content_with_retry(main_content, selected_channels, retries=3, delay=5):
    """Generate social media content for multiple channels with retry logic."""
    generated_content = {}
    for channel in selected_channels:
        for i in range(retries):
            try:
                prompt = f"Generate a {channel.capitalize()} post based on this content:\n{main_content}\n"
                response = llm(prompt)
                if response:
                    generated_content[channel] = response.strip()
                break
            except Exception as e:
                if i < retries - 1:
                    time.sleep(delay)
                else:
                    generated_content[channel] = f"Error generating content: {str(e)}"
    return generated_content

# Streamlit UI
st.title("Social Media Post Creator for Colleges/Universities")

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
            social_content = generate_social_content_with_retry(main_content, selected_channels)

            for channel, content in social_content.items():
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
        else:
            st.error("No facts found. Try a different college/university.")
