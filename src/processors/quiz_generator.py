import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List, Any

logger = logging.getLogger(__name__)

class QuizQuestion(BaseModel):
    question: str = Field(description="The question text")
    options: List[str] = Field(description="List of 4 options")
    correct_answer: str = Field(description="The correct option text")
    explanation: str = Field(description="Short explanation of why it is correct")

class QuizOutput(BaseModel):
    quiz: List[QuizQuestion]

class QuizProcessor:
    def __init__(self, model_name="gemini-2.5-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.3)
        self.parser = JsonOutputParser(pydantic_object=QuizOutput)

    def generate_quiz(self, rag_processor: Any, num_questions: int = 5, difficulty: str = "Medium"):
        logger.info(f"Generating {num_questions} {difficulty} questions using RAG...")
        
        if not rag_processor.vector_store:
            logger.error("No content ingested in RAG processor")
            return []

        # 1. Retrieve Context
        query = "important facts, key concepts, definitions, and details for examination"
        
        try:
            query_emb = rag_processor.embed_text(query)
            # Fetch context (Text + Images)
            results = rag_processor.vector_store.similarity_search_by_vector(query_emb, k=10)
        except Exception as e:
            logger.error(f"RAG Retrieval failed: {e}")
            return []

        # 2. Build Multimodal Context
        content = []
        
        intro_prompt = f"""
You are an expert exam setter. Your task is to create {num_questions} {difficulty} level multiple-choice questions based ONLY on the provided context (text and images).

{self.parser.get_format_instructions()}

RULES:
- Ensure questions are derived directly from the content.
- If images are provided, try to include at least one question related to the visual information.
- Provide a clear explanation for the correct answer.
- Return PURE JSON.
"""
        content.append({"type": "text", "text": intro_prompt})

        # Append Text and Images from Retrieval
        MAX_IMAGES = 3
        image_count = 0
        
        for doc in results:
             doc_type = doc.metadata.get("type", "text")
             page = doc.metadata.get("page", "?")
             
             if doc_type == "text":
                 content.append({"type": "text", "text": f"\n[Text Page {page}]: {doc.page_content}\n"})
             
             elif doc_type == "image":
                 if image_count < MAX_IMAGES:
                     img_id = doc.metadata.get("image_id")
                     if img_id and hasattr(rag_processor, 'image_data_store') and rag_processor.image_data_store and img_id in rag_processor.image_data_store:
                         b64_str = rag_processor.image_data_store[img_id]
                         content.append({"type": "text", "text": f"\n[Image from Page {page}]:\n"})
                         content.append({
                             "type": "image_url", 
                             "image_url": {"url": f"data:image/png;base64,{b64_str}"}
                         })
                         image_count += 1
        
        content.append({"type": "text", "text": "\n\nGenerate the quiz now."})

        # 3. Invoke LLM and Parse
        try:
            response = self.llm.invoke([HumanMessage(content=content)])
            
            # Helper to clean markdown json blocks if needed
            response_text = response.content
            if "```json" in response_text:
                response_text = response_text.replace("```json", "").replace("```", "")
            
            # Use the parser to extract JSON from the response
            parsed_result = self.parser.parse(response_text)
            
            # Handle potential wrapping keys
            if isinstance(parsed_result, dict) and 'quiz' in parsed_result:
                return parsed_result['quiz']
            return parsed_result
        
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            return []
