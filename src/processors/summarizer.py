import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

class SummarizerProcessor:
    def __init__(self, model_name="gemini-2.0-flash"):
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.3)
        self.output_parser = StrOutputParser()

    def summarize(self, text: str, summary_type: str = "concise"):
        logger.info(f"Generating {summary_type} summary...")

       
        template_string = """
You are BrainBolt's advanced AI summarization assistant. Your role is to distill complex information into clear, readable, and educational content.
You are processing the following text:

<SOURCE_TEXT>
{text}
</SOURCE_TEXT>

Your task is to generate a **{summary_type}** summary. 

Follow these specific guidelines for the requested style:
{style_instructions}

GENERAL RULES:
- Use professional yet accessible language.
- Maintain the original meaning and accuracy of the source.
- Format the output in clean Markdown (using bolding for key terms).
- Do NOT start with phrases like "Here is the summary" or "In this text". Just dive straight into the content.

Output:
"""
        
        style_map = {
            "concise": (
                "Create a brief, high-level abstract (approx. 3-5 sentences). "
                "Focus ONLY on the 'big picture' core message. "
                "Ignore minor details and examples."
            ),
            "detailed": (
                "Create a comprehensive, structured summary. "
                "Use H3 headers (###) to separate key sections. "
                "Include important details, examples, and nuance from the original text. "
                "The length should be proportional to the depth of the source material."
            ),
            "bullet_points": (
                "Create a list of key takeaways. "
                "Use bullet points for readability. "
                "Ensure each bullet point is self-contained and impactful. "
                "Group related points under bold headers if there are many topics."
            ),
            "educational":(
                "Explain the content as if teaching a student. "
                "Define key terms clearly. "
                "Break down complex ideas step by step. "
                "Use examples only when they improve understanding. "
                "Maintain a logical learning flow from basics to advanced concepts."
            ),
            "exam_ready":(
                "Summarize the content with an exam-focused mindset. "
                "Highlight definitions, facts, formulas, and cause-effect relationships. "
                "Emphasize points likely to be asked as direct or conceptual questions. "
                "Avoid narrative explanations."),
            
            "executive": (
                "Create a decision-oriented executive summary. "
                "Focus on outcomes, implications, risks, and benefits. "
                "Minimize background explanation unless it directly affects decisions. "
                "Keep the tone authoritative and concise."),

            "technical_deep_dive": (
    "Provide a technically precise summary. "
    "Preserve domain-specific terminology. "
    "Explain mechanisms, workflows, and constraints. "
    "Avoid oversimplification."
)

                
                
                
                }
        
        
        
        instructions = style_map.get(summary_type, style_map["concise"])

        prompt_template = PromptTemplate(
            input_variables=["text", "summary_type", "style_instructions"],
            template=template_string
        )

        chain = prompt_template | self.llm | self.output_parser

        try:
            
            response = chain.invoke({
                "text": text,
                "summary_type": summary_type,
                "style_instructions": instructions
            })
            return response
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return f"Error generating summary: {e}"
