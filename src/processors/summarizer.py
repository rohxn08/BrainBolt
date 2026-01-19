import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

logger = logging.getLogger(__name__)

class SummarizerProcessor:
    def __init__(self, model_name="gemini-2.0-flash"):
        """
        Initialize the Summarizer Processor.
        """
        self.llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.3)

    def summarize(self, rag_processor, summary_type: str = "concise"):
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
        # We query for a broad overview to capture the essence
        query = "comprehensive overview of the main content, key topics, and visual details"
        
        try:
            # Embed the broad query using the RAG processor's embedding method
            query_emb = rag_processor.embed_text(query)
            
            # Fetch top 15 chunks to get good coverage of the document
            # We use a higher 'k' here because we want a broad summary, not a specific answer
            results = rag_processor.vector_store.similarity_search_by_vector(query_emb, k=15)
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
        
        # System/Intro Prompt
        intro_prompt = f"""
You are BrainBolt's advanced AI summarization assistant. 
You are processing fragments retrieved from a larger document (containing text and images).

Your task is to generate a **{summary_type}** summary.

GUIDELINES:
{instructions}

GENERAL RULES:
- Synthesize information from both the text excerpts and the images provided below.
- Use professional yet accessible language.
- Format the output in clean Markdown.
- Do NOT start with phrases like "Here is the summary". Just dive straight into the content.
"""
        content.append({"type": "text", "text": intro_prompt})

        # Append Text and Images from Retrieval
        current_text_block = ""
        
        for doc in results:
            doc_type = doc.metadata.get("type", "text")
            page = doc.metadata.get("page", "?")
            
            if doc_type == "text":
                current_text_block += f"\n[Text Page {page}]: {doc.page_content}\n"
            
            elif doc_type == "image":
                # Flush pending text first so order is preserved relative to images
                if current_text_block:
                    content.append({"type": "text", "text": current_text_block})
                    current_text_block = ""
                
                # Add Image
                img_id = doc.metadata.get("image_id")
                # Ensure the image data exists in the RAG store
                if img_id and img_id in rag_processor.image_data_store:
                    b64_str = rag_processor.image_data_store[img_id]
                    content.append({"type": "text", "text": f"\n[Image from Page {page}]:\n"})
                    content.append({
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/png;base64,{b64_str}"}
                    })

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
