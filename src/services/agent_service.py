import json

from openai.types.chat import (
    ChatCompletionAssistantMessageParam,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionToolMessageParam,
    ChatCompletionToolParam,
    ChatCompletionUserMessageParam,
)

from core.config import settings
from core.openai_client import openai_client
from core.structlog_logs import logger
from services.rag_service import RAGService

RAG_TOOL: ChatCompletionToolParam = {
    "type": "function",
    "function": {
        "name": "retrieve_knowledge_from_rag",
        "description": 
        """Search for relevant information, context, 
        and documents in the local RAG knowledge 
        base to answer the user question.""",
        "parameters": {
            "type": "object",
            "properties": {
                "search_query": {
                    "type": "string",
                    "description": 
                    """The search query or question to perform 
                       semantic search against the embeddings database.""",
                }
            },
            "required": ["search_query"],
        },
    },
}

class ReActAgentService:
    def __init__(self, rag_service: RAGService) -> None:
        self.rag_service: RAGService = rag_service
        self.system_prompt = (
            "You are an assistant with access to a local knowledge base (RAG).\n"
            "CRITICAL RULE 1: For any question, you MUST first call the "
            "'retrieve_knowledge_from_rag' tool. Do not answer from memory "
            "until you receive context from the tool.\n"
            "CRITICAL RULE 2: Your final answer must be based ONLY on the facts "
            "directly mentioned in the retrieved context. If the context does "
            "not contain the answer, state that you cannot find it in the "
            "provided documents. Do not use external knowledge to invent quotes."
        )

    async def run(self, user_question: str) -> str:
        logger.info("Initializing ReAct Agent run", user_question=user_question)
        
        sys_msg = ChatCompletionSystemMessageParam(role="system", 
                                                   content=self.system_prompt)
        user_msg = ChatCompletionUserMessageParam(role="user", content=user_question)
        messages: list[ChatCompletionMessageParam] = [sys_msg, user_msg]

        logger.info("Sending initial request to LLM with RAG tool enabled")
        response = await openai_client.chat.completions.create(
            model=settings.MODEL_ID,
            messages=messages,
            tools=[RAG_TOOL],
            tool_choice={"type": "function", 
                         "function": {"name": "retrieve_knowledge_from_rag"}}
        )

        response_message = response.choices[0].message
        logger.info(
            "Received initial LLM response", 
            content=response_message.content, 
            has_tool_calls=bool(response_message.tool_calls)
        )
        
        tool_calls_list: list[ChatCompletionMessageToolCallParam] = []
        if response_message.tool_calls:
            for tc in response_message.tool_calls:
                tc_dict = tc.model_dump()
                tool_call_param = ChatCompletionMessageToolCallParam(
                    id=str(tc_dict.get("id")),
                    type="function",
                    function={
                        "name": str(tc_dict.get("function", {}).get("name")),
                        "arguments": str(tc_dict.get("function", {}).get("arguments"))
                    }
                )
                tool_calls_list.append(tool_call_param)

        assistant_msg = ChatCompletionAssistantMessageParam(
            role="assistant",
            content=response_message.content if response_message.content else ""
        )
        if tool_calls_list:
            assistant_msg["tool_calls"] = tool_calls_list
            
        messages.append(assistant_msg)

        if response_message.tool_calls:
            for tc in response_message.tool_calls:
                tc_dict = tc.model_dump()
                tc_name = tc_dict.get("function", {}).get("name")
                
                if tc_name == "retrieve_knowledge_from_rag":
                    tc_args_str = tc_dict.get("function", {}).get("arguments", "{}")
                    arguments = json.loads(tc_args_str)
                    search_query = arguments.get("search_query", user_question)

                    logger.info("Executing RAG semantic search tool", 
                                search_query=search_query)
                    _, t_ch = await self.rag_service.answer_question(search_query)
                    
                    context = " ".join(t_ch) if t_ch else "No information found"
                    logger.info("RAG search completed", 
                                chunks_found=len(t_ch) if t_ch else 0)

                    tool_msg = ChatCompletionToolMessageParam(
                        role="tool",
                        tool_call_id=str(tc_dict.get("id")),
                        content=f"Retrieved context from knowledge base: {context}"
                    )
                    messages.append(tool_msg)

            logger.info("Sending final request to LLM with retrieved context")
            final_response = await openai_client.chat.completions.create(
                model=settings.MODEL_ID,
                messages=messages
            )
            
            final_content = final_response.choices[0].message.content
            logger.info("Received final answer from LLM")
            return final_content or "Failed to generate response."
            
        logger.warn("Agent execution finished without triggering the RAG tool")
        return response_message.content or "Agent failed to trigger the RAG tool."