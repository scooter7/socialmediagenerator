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
