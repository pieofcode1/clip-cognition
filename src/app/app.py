import os
import streamlit as st
from pathlib import Path
import dotenv


# Load env settings if not already loaded
env_name = os.environ["AZURE_ENV_NAME"] if "AZURE_ENV_NAME" in os.environ else "dev"
# Load env settings
env_file_path = Path(f"./app/env/{env_name}/.env")
print(f"Loading environment from: {env_file_path}")
with open(env_file_path) as f:
    dotenv.load_dotenv(dotenv_path=env_file_path)


def main():

    st.set_page_config(page_title="RAG App Accelerator", page_icon=":books:")

    st.write(
        """
        ## Audio/Video RAG Accelerator ✨

        Welcome! 👋 Retrieval Augmented Generation (RAG) is a technique used in natural language processing to enhance the performance of chatbots and question-answering systems. It combines the power of retrieval-based models and generative models to provide more accurate and contextually relevant responses.

        In the context of Azure, Media RAG can be implemented using variety of Azure services such as Azure OpenAI, Azure Cosmos DB, and Azure Storage. Azure OpenAI provides the language model capabilities, Azure Cosmos enables storing audio/video metadata and efficient indexing and retrieval of information.

        This accelarator app utilizes RAG for chatbot functionality. It demonstrates the power of Azure OpenAI and Cosmos DB Vector search to extract the insights from audio/video and image data stored in the enterprise data lake.
        
        """
    )

    st.info(
        """
        Need to include a tpoic or a capability that's not on here?
        [Let me know by opening a GitHub issue!](https://github.com/pieofcode1/clip-cognition/issues)
        """,
        icon="👾",
    )


    st.write("\n\n")

    st.markdown("#### Reference Architecture")
    st.write(
        """
        This is a typical architecture of a RAG based app leveraging Azure Platform Services for structured data as well as for the media files. 
        """
    )
    tab_text2, tab_media, = st.tabs(["Structured", "Audio/Video"])
  
    with tab_text2:
        
        st.image("../media/arch_cosmos.png")

    with tab_media:
        st.image("../media/media_arch.png")


if __name__ == "__main__":
    main()
