import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

logger = logging.getLogger(__name__)

class QuizQuestion(BaseModel):
    question: str = Field(description="The question text")
    options: List[str] = Field(description="List of 4 options")
    correct_answer: str = Field(description="The correct option text")
    explanation: str = Field(description="Short explanation of why it is correct")

class QuizOutput(BaseModel):
    quiz: List[QuizQuestion]



class QuizProcessor:
    def __init__(self, model_name="gemini-2.0-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.3)
        self.parser = JsonOutputParser(pydantic_object=QuizOutput)

    def generate_quiz(self, text: str, num_questions: int = 5, difficulty: str = "Medium"):
        logger.info(f"Generating {num_questions} {difficulty} questions...")
        
        # Define the prompt
        prompt = PromptTemplate(
            template="""
            You are an expert exam setter. Create {num_questions} {difficulty} level multiple-choice questions based on the following text.
            
            Text: "{text}"
            
            {format_instructions}
            """,
            input_variables=["num_questions", "difficulty", "text"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )
        
        chain = prompt | self.llm | self.parser
        
        
        try:
            response = chain.invoke({
                "num_questions": num_questions,
                "difficulty": difficulty,
                "text": text
            })
            return response['quiz'] if isinstance(response, dict) and 'quiz' in response else response
        
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            return []
