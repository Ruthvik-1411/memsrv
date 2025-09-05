"""Module that interacts with backend agent using streamlit"""
# pylint: disable=line-too-long,invalid-name
import uuid
import asyncio
import streamlit as st
from adk_agent.response_manager import ResponseManager
from shared.memory_client import MemoryClient

st.set_page_config(page_title="Agent Response Manager", layout="wide")

SAMPLE_USERS = [
    "ruths@gmail.com",
    "rengoku@gmail.com",
    "jon@gmail.com",
    "jane@email.com",
    "user@email.com",
]

if "user_id" not in st.session_state:
    st.title("Hello there!")
    st.info("Choose a user id to continue.")

    selected_user = st.selectbox(
        "Choose your account",
        options=SAMPLE_USERS,
        index=0
    )

    if st.button("Start session with this user id", disabled=(not selected_user)):
        st.session_state.user_id = selected_user
        st.rerun()

    st.stop()

# --- Session State Initialization ---
if "response_manager" not in st.session_state:
    st.session_state.response_manager = ResponseManager(user_id=st.session_state.user_id)
if "memory_client" not in st.session_state:
    st.session_state.memory_client = MemoryClient()
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
    st.toast(f"New session created: {st.session_state.session_id}")
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Sidebar ---
with st.sidebar:
    st.markdown(f"Welcome: `{st.session_state.user_id}`")
    if st.button("Change User"):
        # delete all keys for now
        keys_to_delete = list(st.session_state.keys())
        for key in keys_to_delete:
            del st.session_state[key]
        st.toast("Select a new user id.")
        st.rerun()

    st.divider()
    st.title("Settings")
    st.markdown(f"**Session ID:**\n`{st.session_state.session_id}`")

    if st.button("New Session"):
        completed_session_events = asyncio.run(st.session_state.response_manager.dump_session_events(st.session_state.session_id))
        st.toast("Adding session to memory...")
        st.session_state.memory_client.add_to_memory(
            messages=completed_session_events,
            metadata={
                "user_id": st.session_state.user_id,
                "session_id": st.session_state.session_id,
                "app_id": st.session_state.response_manager.runner.app_name,
                "agent_name": st.session_state.response_manager.agent.name
        })
        st.toast(f"Successfully added {st.session_state.session_id} to memories. Memories updated.")
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.toast(f"New session started: {st.session_state.session_id}")
        st.rerun()

    st.divider()
    diagnostics_enabled = st.checkbox("Enable Diagnostics", value=True)

# --- Main Chat Interface ---
st.title("Agent Chat UI")

# Display chat history from session state
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if diagnostics_enabled and "diagnostics" in message and message["diagnostics"]:
            with st.expander("View Diagnostics for this response."):
                st.json(message["diagnostics"])

# --- Coroutine to handle agent invocation and UI updates ---
async def run_agent_and_display(prompt: str):
    """Add user message to session state and display it"""
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # --- Assistant's turn ---
    with st.chat_message("assistant"):
        final_response_text = ""
        diagnostic_events = []
        status_messages = {
            "tool_call": "Calling tool... 🛠️",
            "tool_response": "Processing tool result... ⚙️",
            "finished": "Response generation complete. ✅"
        }

        status_placeholder = st.empty()
        try:
            # Collect all events and the final response from the agent
            status_placeholder.text("Thinking... 🤔")
            async for event in st.session_state.response_manager.invoke_agent(
                session_id=st.session_state.session_id, query=prompt
            ):
                status_text = status_messages.get(event.get("status"), f"Processing: {event.get('status')}")
                status_placeholder.text(status_text)

                diagnostic_events.append(event.get("event"))
                if event.get("is_final_response"):
                    final_response_text = event.get("result", "Sorry, I couldn't generate a response.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
            final_response_text = "Sorry, I ran into an error."

        status_placeholder.empty()
        st.markdown(final_response_text)

    if diagnostics_enabled and diagnostic_events:
        with st.expander("View Diagnostics for this response."):
            st.json(diagnostic_events)

    st.session_state.messages.append({
        "role": "assistant",
        "content": final_response_text,
        "diagnostics": diagnostic_events
    })

# --- Handle User Input ---
if user_input := st.chat_input("What are some trending topics in AI?"):
    asyncio.run(run_agent_and_display(user_input))
