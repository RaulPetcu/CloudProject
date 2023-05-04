from fastapi import FastAPI, File, UploadFile
from typing import Annotated
import json
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes, VisualFeatureTypes
from msrest.authentication import CognitiveServicesCredentials
from PIL import Image, ImageDraw, ImageFont
import time
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

credential = json.load(open('credentials.json'))
API_KEY = credential['API_KEY']
ENDPOINT = credential['ENDPOINT']
CONTAINER1 = credential['CONTAINER1']
CONTAINER2 = credential['CONTAINER2']
cv_client = ComputerVisionClient(ENDPOINT, CognitiveServicesCredentials(API_KEY))
max_description = 3

app = FastAPI()

@app.get('/')
async def root():
    return {'message': 'Hello World'}


@app.post("/uploadfile/handwriting/")
async def create_upload_file(file: UploadFile = File(...)):
    # return {"filename": str(type(file.read))}
    image_bytes = file.file
    # response = cv_client.read_in_stream(open(image_bytes, 'rb'), language='en',raw=True)
    response = cv_client.read_in_stream(image_bytes, language='en',raw=True)

    image_text = ""

    operationLocation = response.headers['Operation-Location']
    operation_id = operationLocation.split('/')[-1]
    time.sleep(5)
    result = cv_client.get_read_result(operation_id)

    if result.status == OperationStatusCodes.succeeded:
        read_results = result.analyze_result.read_results
        for analyzed_result in read_results:
            for line in analyzed_result.lines:
                image_text += line.text + " "
    else:
        return {"Error: ": "Statusc code bad"}
    
    account_url = "https://storageforcloudapp.blob.core.windows.net"
    default_credential = DefaultAzureCredential()
    print('eee1')
    blob_service_client = BlobServiceClient(account_url, credential=default_credential)
    print('eee2')
    container_name = CONTAINER1
    print('eee3')
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file.filename)
    print('eee4')
    image_bytes.seek(0)
    
    #blob_client.upload_blob(real_image_bytes)
    #with open(,mode="rb") as data:
    blob_client.upload_blob(image_bytes)

    return {"description:": image_text}


@app.post("/uploadfile/image/")
async def create_upload_file(file: UploadFile = File(...)):
    print("kk")
    # image_bytes = await file.file.read()
    # print(image_bytes)
    image_bytes = file.file
    response = cv_client.describe_image_in_stream(image_bytes, max_description)
    description = "No description"
    confidence = 0

    for caption in response.captions:
        description = caption.text
        confidence = caption.confidence * 100
        # print("Image description: {0}".format(caption.text))
        # print("Confidence: {0}".format(caption.confidence * 100))
    
    # incepem stocarea in blob-uri
 
    
    account_url = "https://storageforcloudapp.blob.core.windows.net"
    default_credential = DefaultAzureCredential()
    print('eee1')
    blob_service_client = BlobServiceClient(account_url, credential=default_credential)
    print('eee2')
    container_name = CONTAINER2
    print('eee3')
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=file.filename)
    print('eee4')
    image_bytes.seek(0)
    
    #blob_client.upload_blob(real_image_bytes)
    #with open(,mode="rb") as data:
    blob_client.upload_blob(image_bytes)


    return {"ImageDescription: ": description,
            "Confidence: ": confidence}


@app.post("/files/")
async def create_file(file: Annotated[bytes, File()]):
    return {"file_size": len(file)}