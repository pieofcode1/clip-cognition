import os
import openai
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
import base64
from pathlib import Path
from io import StringIO, BytesIO
import requests
import dotenv



"""
This class is used to create an Embedding Agent that can be used to interact with Azure OpenAI.
The agent can be used to generate embeddings for text and images.
"""
class BaseEmbeddingAgent:
    
    def __init__(self):
        pass

    def get_text_embeddings(self, text):
        raise NotImplementedError("This method should be implemented in the derived class")
    
    def get_image_embeddings(self, blob_image_path):
        raise NotImplementedError("This method should be implemented in the derived class")
        

class AzureOpenAIEmbeddingsAgent(BaseEmbeddingAgent):
        
    def __init__(self):
        super().__init__()
        credential = DefaultAzureCredential(managed_identity_client_id=os.environ['USER_ASSIGNED_ID_CLIENT_ID'])
        # Use the credential to get an access token
        token = credential.get_token("https://cognitiveservices.azure.com/.default")
        self.AOAI_client = AzureOpenAI(
                            api_key=token.token, 
                            azure_endpoint=os.environ['AZURE_OPENAI_EMBEDDING_DEPLOYMENT_ENDPOINT'], 
                            api_version=os.environ['AZURE_OPENAI_API_VERSION']
                        )
    
    def get_text_embeddings(self, text):
        '''
        Generate embeddings from string of text.
        This will be used to vectorize data and user input for interactions with Azure OpenAI.
        '''
        response = self.AOAI_client.embeddings.create(input=text, model=os.environ['AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME'])
        embeddings =response.model_dump()
        return embeddings['data'][0]['embedding']
    
    def get_image_embeddings(self, blob_image_path):
        raise NotImplementedError("This method is not supported for this class")
        

class AIVisionEmbeddingsAgent(BaseEmbeddingAgent):
           
    def __init__(self):
        super().__init__()
    
    def get_text_embeddings(self, text):
        # Create a code snippet for calling post api using requests
        vision_ep = os.environ["COGNITIVE_MULTISVC_ENDPOINT"]
        vision_key = os.environ["COGNITIVE_MULTISVC_API_KEY"]

        operation_name = "vectorizeText"

        url = f"{vision_ep}/computervision/retrieval:{operation_name}?api-version=2024-02-01&model-version=2023-04-15"
        headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": vision_key
        }
        data = {
            "text": text
        }
        response = requests.post(url, headers=headers, json=data)
        # print(response.json())

        return response.json()["vector"]
    
    def get_image_embeddings(self, blob_image_path):
        # Create a code snippet for calling post api using requests
        vision_ep = os.environ["COGNITIVE_MULTISVC_ENDPOINT"]
        vision_key = os.environ["COGNITIVE_MULTISVC_API_KEY"]

        operation_name = "vectorizeImage"

        url = f"{vision_ep}/computervision/retrieval:{operation_name}?api-version=2024-02-01&model-version=2023-04-15"
        headers = {
            "Content-Type": "application/json",
            "Ocp-Apim-Subscription-Key": vision_key
        }
        data = {
            "url": blob_image_path
            # "url": "https://www.google.com/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png"
            # "url": f"data:image/jpeg;base64,{b64_encoded_image}"
        }
        response = requests.post(url, headers=headers, json=data)
        print(response.json())

        return response.json()["vector"]
        
