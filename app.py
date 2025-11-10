import chainlit as cl
from llm import LLMClient
from database import (
    log_message,
    start_conversation,
    list_conversations,
    get_conversation
)

@cl.on_chat_start
async def start():
    """Start a new chat session"""
    thread_id = start_conversation()
    cl.user_session.set("thread_id", thread_id)

    # Initialize Gemini LLM
    llm_client = LLMClient()
    system_prompt = "You are a helpful AI tutor assistant."
    llm_client.start_chat(system_prompt=system_prompt)
    cl.user_session.set("llm_client", llm_client)

    await cl.Message(
        content=f"🧠 New conversation started (Thread ID: {thread_id[:8]})\n"
                f"Type `/history` to view previous chats."
    ).send()


@cl.on_message
async def main(message: cl.Message):
    """Handle chat messages and commands"""
    text = message.content.strip()
    llm_client = cl.user_session.get("llm_client")
    thread_id = cl.user_session.get("thread_id")

    # --- /history command ---
    if text.lower() == "/history":
        convos = [c for c in list_conversations() if get_conversation(c["thread_id"]).get("messages")]
        if not convos:
            await cl.Message(content="No past conversations found.").send()
            return
        msg = "**🗂 Your past conversations:**\n"
        for convo in convos:
            msg += f"- `{convo['thread_id'][:8]}` → {convo['title']}\n"
        msg += "\nType `/resume <thread_id>` to reopen one."
        await cl.Message(content=msg).send()
        return

    # --- /resume command ---
    if text.lower().startswith("/resume"):
        parts = text.split()
        if len(parts) < 2:
            await cl.Message(content="Usage: `/resume <thread_id>`").send()
            return

        short_id = parts[1]
        convo = None
        for c in list_conversations():
            if c["thread_id"].startswith(short_id):
                convo = get_conversation(c["thread_id"])
                break

        if not convo:
            await cl.Message(content=f"No conversation found with ID `{short_id}`").send()
            return

        cl.user_session.set("thread_id", convo["thread_id"])

        # Recreate LLM with stored history
        llm_client = LLMClient()
        system_prompt = "You are a helpful AI tutor assistant."
        gemini_history = []
        if convo and convo.get("messages"):
            for m in convo["messages"]:
                gemini_history.append({
                    "role": m["role"],
                    "parts": [{"text": m["text"]}]
                })
        llm_client.start_chat(system_prompt=system_prompt, history=gemini_history)
        cl.user_session.set("llm_client", llm_client)

        await cl.Message(content=f"🔁 Resuming conversation `{convo['thread_id'][:8]}`...").send()

        # Display past messages visually
        if convo.get("messages"):
            for m in convo["messages"]:
                await cl.Message(
                    author="You" if m["role"] == "user" else "Tutor",
                    content=m["text"]
                ).send()
        else:
            await cl.Message(content="(No messages yet in this conversation.)").send()
        return

    # --- Regular chat flow ---
    if not isinstance(llm_client, LLMClient):
        await cl.Message(content="Error: LLM not initialized. Please refresh the chat.").send()
        return

    # Save user message
    log_message("user", text, thread_id)

    # Prepare Gemini-compatible conversation history
    convo = get_conversation(thread_id)
    gemini_history = []
    if convo and convo.get("messages"):
        for m in convo["messages"]:
            gemini_history.append({
                "role": m["role"],
                "parts": [{"text": m["text"]}]
            })

    # Restart Gemini chat with context
    llm_client.start_chat(
        system_prompt="You are a helpful AI tutor assistant.",
        history=gemini_history
    )

    # Get streamed reply
    msg = cl.Message(content="")
    async for chunk in stream_response(llm_client, text):
        await msg.stream_token(chunk)
    await msg.send()

    # Log the AI response
    log_message("assistant", msg.content, thread_id)


async def stream_response(llm_client: LLMClient, message: str):
    """Stream Gemini’s response"""
    for chunk in llm_client.send_message_stream(message):
        yield chunk
