import os
import base64
import numpy as np
import logging
from PIL import Image
from typing import List, Dict, Any, Union
import torch
from transformers import CLIPProcessor, CLIPModel
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI

logger=logging.getLogger(__name__)

class MultiModalRAGProcessor:
    def __init__(self,model_name="gemini-2.5-flash",clip_model_id="openai/clip-vit-base-patch32"):
        self.llm=ChatGoogleGenerativeAI(model=model_name,temperature=0.3)
        try:
            self.clip_model=CLIPModel.from_pretrained(clip_model_id,use_safetensors=True)
            self.clip_processor=CLIPProcessor.from_pretrained(clip_model_id)
            logger.info("CLIP model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise e
        
        self.text_splitter=RecursiveCharacterTextSplitter(
            chunk_size=300, chunk_overlap=50)
        self.vector_store=None
        self.image_data_store=None
        self.all_docs=[]
        self.embeddings=[]

    def embed_image(self,image_data):
        if isinstance(image_data,str):
            image=Image.open(image_data).convert("RGB")
        else:
            image=image_data
        
        inputs=self.clip_processor(images=image,return_tensors="pt")
        with torch.no_grad():
            features=self.clip_model.get_image_features(**inputs)
            features=features/features.norm(p=2,dim=-1,keepdim=True)
            return features.squeeze().numpy()
        
    def embed_text(self,text):
        inputs=self.clip_processor(text=text,
        return_tensors="pt",
        padding=True,
        truncation=True,
        max_length=77)
        with torch.no_grad():
            features=self.clip_model.get_text_features(**inputs)
            features=features/features.norm(dim=-1,keepdim=True)
            return features.squeeze().numpy()
    
    def ingest_data(self,data:dict):
        if not data or (not data.get("text_pages") and not data.get('images')):
            return 'Error : No data to ingest'
        logger.info("Ingesting the given data")

        self.all_docs=[]
        self.embeddings=[]
        self.image_data_store={}

        #processing the text image
        for item in data.get("text_pages",[]):
            text=item.get("text","")
            page_num=item.get("page",0)

            if text.strip():
                temp_doc=Document(
                    page_content=text,
                    metadata={"type":"text","page":page_num}
                )

                chunks=self.text_splitter.split_documents([temp_doc])
                for chunk in chunks:
                    emb=self.embed_text(chunk.page_content)
                    self.all_docs.append(chunk)
                    self.embeddings.append(emb)
                    
        #processing for images
        for img_item in data.get("images",[]):
            try:
                pil_image=img_item.get("image")
                image_id=img_item.get("id","unknown")
                page_num=img_item.get("page",0)

                import io
                buffered=io.BytesIO()
                pil_image.save(buffered,format="PNG")
                img_base64=base64.b64encode(buffered.getvalue()).decode()
                self.image_data_store[image_id]=img_base64

                emb=self.embed_image(pil_image)
                self.embeddings.append(emb)

                image_doc=Document(
                    page_content=f"[Image: {image_id}]",
                    metadata={"page": page_num, "type": "image", "image_id": image_id}
                )
                self.all_docs.append(image_doc)
            except Exception as e:
                logger.warning(f"Failed to process image{image_id}:{e}")
                continue
        if not self.embeddings:
            return "No content to Index"

        embeddings_array=np.array(self.embeddings)
        self.vector_store=FAISS.from_embeddings(
            text_embeddings=[(doc.page_content, emb) for doc, emb in zip(self.all_docs, embeddings_array)],
            embedding=None,
            metadatas=[doc.metadata for doc in self.all_docs]
        )
        logger.info("Ingestion completed successfully")

        return f"Successfully ingested {len(self.all_docs)} documents"


    def query(self,user_query:str,k:int=5):
        if not self.vector_store:
            return "Error: No data ingested yet. Please ingest a PDF first."
        
        #Embed the query
        query_emb=self.embed_text(user_query)
        results=self.vector_store.similarity_search_by_vector(query_emb,k=k)        
        
        content=[]
        content.append({"type":"text","text":f"Question :{user_query}\n\n"})
        text_docs=[doc for doc in results if doc.metadata.get("type") == "text"]
        image_docs=[doc for doc in results if doc.metadata.get("type") == "image"]        
        
        if text_docs:
            text_context = "\n\n".join([f"[Page {doc.metadata['page']}]: {doc.page_content}" for doc in text_docs])
            content.append({"type": "text", "text": f"Text excerpts:\n{text_context}\n"})

        for doc in image_docs:
            image_id = doc.metadata.get("image_id")
            if image_id and image_id in self.image_data_store:
                content.append({"type": "text", "text": f"\n[Image from page {doc.metadata['page']}]:\n"})
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{self.image_data_store[image_id]}"}
                })
        
        content.append({"type": "text", "text": "\n\nPlease answer the question based on the provided text and images."})



        #INVOKING THE LLM 
        msg=HumanMessage(content=content)
        response=self.llm.invoke([msg])
        return response.content

