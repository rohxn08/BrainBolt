import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Any
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

class SummarizerProcessor:
    def __init__(self, model_name="gemini-2.5-flash"):
        """
        Initialize the Summarizer Processor.
        """
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.3)

    def summarize(self, rag_processor: Any, summary_type: str = "concise"):
        """
        Generates a summary by retrieving context from the provided MultiModalRAGProcessor.
        
        Args:
            rag_processor: An instance of MultiModalRAGProcessor that has already ingested data.
            summary_type: The type of summary to generate (e.g., 'concise', 'detailed', 'visual').
        """
        logger.info(f"Generating {summary_type} summary using RAG backend...")

        # 1. Validation: Ensure we have a vector store to query
        if not rag_processor.vector_store:
            return "Error: No content ingested. Please ingest a file or link first."

        # 2. Retrieve Context
        # Dynamic 'k' selection based on summary type (Level 1 Optimization)
        # Concise/Executive = Less context needed (Focus on main points)
        # Detailed/Technical = More context needed
        k_map = {
            "concise": 5,
            "executive": 5,
            "bullet_points": 7,
            "educational": 7,
            "detailed": 10,
            "technical_deep_dive": 12,
            "exam_ready": 8
        }
        k_val = k_map.get(summary_type, 7) # Default to 7
        
        # Dynamic Query Selection (Level 2 Optimization)
        # Tailor the retrieval query to what matters for the summary type
        query_map = {
            "concise": "overview of the main content and core message",
            "executive": "key outcomes, risks, benefits, and strategic implications",
            "bullet_points": "list of key takeaways, main topics, and important facts",
            "educational": "definitions, step-by-step explanations, and fundamental concepts",
            "detailed": "comprehensive details, nuance, examples, and specifics",
            "technical_deep_dive": "technical specifications, implementation details, methodologies, and data",
            "exam_ready": "definitions, formulas, dates, and testable facts"
        }
        query = query_map.get(summary_type, "comprehensive overview of the main content, key topics, and visual details")
        
        try:
            # Embed the tailored query using the RAG processor's embedding method
            query_emb = rag_processor.embed_text(query)
            
            # Fetch top k chunks
            results = rag_processor.vector_store.similarity_search_by_vector(query_emb, k=k_val)
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return f"Error retrieving context: {str(e)}"

        # 3. Define Style Instructions
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
            "educational": (
                "Explain the content as if teaching a student. "
                "Define key terms clearly. "
                "Break down complex ideas step by step. "
                "Use examples only when they improve understanding. "
                "Maintain a logical learning flow from basics to advanced concepts."
            ),
            "exam_ready": (
                "Summarize the content with an exam-focused mindset. "
                "Highlight definitions, facts, formulas, and cause-effect relationships. "
                "Emphasize points likely to be asked as direct or conceptual questions. "
                "Avoid narrative explanations."
            ),
            "executive": (
                "Create a decision-oriented executive summary. "
                "Focus on outcomes, implications, risks, and benefits. "
                "Minimize background explanation unless it directly affects decisions. "
                "Keep the tone authoritative and concise."
            ),
            "technical_deep_dive": (
                "Provide a technically precise summary. "
                "Preserve domain-specific terminology. "
                "Explain mechanisms, workflows, and constraints. "
                "Avoid oversimplification."
            )
        }
        
        instructions = style_map.get(summary_type, style_map["concise"])

        # 4. Build Multimodal Message
        content = []
        
        # System/Intro Prompt (Level 3 Optimization: Simplified)
        intro_prompt = f"""
Task: Generate a {summary_type} summary from the retrieved context.

GUIDELINES:
{instructions}

RULES:
- Synthesize information from text and images.
- Use clean Markdown.
- No intro phrases like "Here is the summary".
"""
        content.append({"type": "text", "text": intro_prompt})

        # Append Text and Images from Retrieval
        # Level 5 Optimization: Token Budgeting via Image Capping
        MAX_IMAGES = 2 
        image_count = 0
        
        current_text_block = ""
        
        for doc in results:
            doc_type = doc.metadata.get("type", "text")
            page = doc.metadata.get("page", "?")
            
            if doc_type == "text":
                current_text_block += f"\n[Text Page {page}]: {doc.page_content}\n"
            
            elif doc_type == "image":
                # Only include image if budget allows
                if image_count >= MAX_IMAGES:
                    continue
                    
                # Flush pending text first so order is preserved relative to images
                if current_text_block:
                    content.append({"type": "text", "text": current_text_block})
                    current_text_block = ""
                
                # Add Image
                img_id = doc.metadata.get("image_id")
                # Ensure the image data exists in the RAG store
                if img_id and hasattr(rag_processor, 'image_data_store') and rag_processor.image_data_store and img_id in rag_processor.image_data_store:
                    b64_str = rag_processor.image_data_store[img_id]
                    content.append({"type": "text", "text": f"\n[Image from Page {page}]:\n"})
                    content.append({
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/png;base64,{b64_str}"}
                    })
                    image_count += 1

        # Flush any remaining text after the loop
        if current_text_block:
            content.append({"type": "text", "text": current_text_block})

        content.append({"type": "text", "text": "\n\nBased on the above retrieved context, generate the final summary now."})

        # 5. Invoke LLM
        try:
            msg = HumanMessage(content=content)
            response = self.llm.invoke([msg])
            return response.content
        except Exception as e:
            logger.error(f"Summarization processing failed: {e}")
            return f"Error generating summary: {str(e)}"
