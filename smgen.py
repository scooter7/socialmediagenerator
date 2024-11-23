import os
import streamlit as st
import serpapi
import openai
import time

# Configure API Keys
SERP_API_KEY = st.secrets["SERPER_API_KEY"]
openai.api_key = st.secrets["OPENAI_API_KEY"]

import requests

def search_college_facts(college_name):
    """Search for interesting facts about the college/university using SerpAPI."""
    url = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": f"Interesting facts about {college_name}",
        "api_key": SERPER_API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 401:
        raise ValueError("Invalid or unauthorized SerpAPI key.")
    response.raise_for_status()  # Raise an error for other HTTP issues
    results = response.json()
    facts = [result['snippet'] for result in results.get('organic_results', []) if 'snippet' in result]
    return facts

def generate_social_content_with_retry(main_content, selected_channels, retries=3, delay=5):
    """Generate social media content for multiple channels with retry logic."""
    generated_content = {}
    for channel in selected_channels:
        for i in range(retries):
            try:
                prompt = f"Generate a {channel.capitalize()} post based on this content:\n{main_content}\n"
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a social media content generator."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500
                )
                content = response['choices'][0]['message']['content']
                if content:
                    generated_content[channel] = content.strip()
                break
            except Exception as e:
                if 'overloaded' in str(e).lower() and i < retries - 1:
                    time.sleep(delay)
                else:
                    generated_content[channel] = "Error generating content."
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
            main_content = f"Topic: {topic}\nInteresting Facts: {' '.join(facts)}"
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
