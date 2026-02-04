import streamlit as st
import requests
import time
import boto3
import os
import json
from botocore.exceptions import BotoCoreError, ClientError
import tempfile

st.set_page_config(page_title="Ask Agent Flow", page_icon="🤖", layout="centered")

st.title("Ask Adversarial AI 🤖")

st.markdown("""
Welcome! Ask Adversarial AI any question. Your question will be sent to an AWS agent and the response will appear below in a chat format.
""")

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []

def get_bedrock_agent_response(question):
    """
    Sends the user's question to the AWS Bedrock agent and returns the response.
    This function assumes AWS credentials are configured in the environment.
    """
    try:
        client = boto3.client(
            "bedrock-agent-runtime",
            region_name="us-east-1",
            aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
            verify=False
        )

        agent_arn = "arn:aws:bedrock:us-east-1:715841350584:agent/KXGEPEI2QE"

        # The API and payload may need to be adjusted based on Bedrock's latest SDK
        # response = client.invoke_agent(
        #     agentId="KXGEPEI2QE",
        #     agentAliasId="TSTALIASID",
        #     sessionId = "sidtest",
        #     inputText=question
        # )
        response = client.invoke_flow(
            flowIdentifier="DO83CXCB8D",
            flowAliasIdentifier="TXQS9G137Z",
            inputs=[
                {
                    "content": {
                        "document": "User input text or data here"
                    },
                    "nodeName": "FlowInputNode",       # Name of the starting node
                    "nodeOutputName": "document"       # Corresponding output name for that node
                }
            ]
            )

        # Assuming 'response' is the object returned from client.invoke_agent()
        # event_stream = response.get('completion')
        event_stream = response.get('responseStream')
        print(f"response {response}")
        print(f"event_stream {event_stream}")
        if event_stream:
            for event in event_stream:
                # Check if the event contains a 'chunk' with actual data
                print(event)
                if 'chunk' in event:
                    print(event['chunk'])
                    # Access the bytes and decode them
                    data_bytes = event['chunk']['bytes']
                    decoded_text = data_bytes.decode('utf8')
                    answer = decoded_text
                    chunk_size = 20
                    for i in range(chunk_size, len(answer) + chunk_size, chunk_size):
                        yield answer[:i]

                # 2. Check for specific event types
                if "flowOutputEvent" in event:
                    # Extract content from a specific node's output
                    output_data = event["flowOutputEvent"]["content"]["document"]
                    print(f"Node Output: {output_data}")

                    answer = output_data
                    chunk_size = 20
                    for i in range(chunk_size, len(answer) + chunk_size, chunk_size):
                        yield answer[:i]

                elif "flowCompletionEvent" in event:
                    # Check why the flow finished (e.g., SUCCESS)
                    reason = event["flowCompletionEvent"]["completionReason"]
                    print(f"Flow completed. Reason: {reason}")

                elif "internalServerException" in event:
                    # Handle errors directly within the stream
                    print(f"Error: {event['internalServerException']['message']}")
                    # yield decoded_text
                    # print(decoded_text)
                # elif 'trace' in event:
                #     # Handle trace events if enableTrace=True was set
                #     print(f"Trace event: {event['trace']}")
                # Other potential events like 'End', 'AccessDenied', etc., can also be handled


        # Simulate streaming by yielding chunks of the response
        # answer = response.get("outputText", "[No response from agent]")
        # for i in range(1, len(answer) + 1):
        #     yield answer[:i]
    except (BotoCoreError, ClientError) as e:
        yield f"[Error communicating with AWS Bedrock agent: {str(e)}]"


def generate_polly_mp3(text, voice_id="Joanna"):
    """
    Uses Amazon Polly to synthesize `text` to an MP3 and returns the bytes.
    Expects AWS credentials to be available via `st.secrets`.
    """
    try:
        polly = boto3.client(
            "polly",
            region_name="us-east-1",
            aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
            verify=False
        )

        resp = polly.synthesize_speech(
            Text=text,
            OutputFormat="mp3",
            VoiceId=voice_id
        )

        audio_stream = resp.get("AudioStream")
        if audio_stream:
            audio_bytes = audio_stream.read()
            return audio_bytes
        else:
            raise RuntimeError("No audio returned from Polly")

    except (BotoCoreError, ClientError, RuntimeError) as e:
        # Return the exception for the caller to show a message
        return e

with st.form("ask_form", clear_on_submit=True):
    user_question = st.text_input("Your question:", key="user_question")
    submitted = st.form_submit_button("Submit")

if submitted and user_question.strip():
    # st.session_state["chat_history"].append({"role": "user", "content": user_question})
    with st.spinner("Adversarial AI agents are collaborating..."):
        response = ""
        placeholder = st.empty()
        for partial in get_bedrock_agent_response(user_question):
            response = partial
            placeholder.markdown(f"**Agent Flow:** {response}")
            time.sleep(0.03)
        st.session_state["chat_history"].append({"role": "agent", "content": response})

# Display chat history
for msg in st.session_state["chat_history"]:
    if msg["role"] == "user":
        st.markdown(f"<div style='text-align: right; color: #1a73e8;'><b>You:</b> {msg['content']}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div style='text-align: left; color: #34a853;'><b>Adversarial AI:</b> {msg['content']}</div>", unsafe_allow_html=True)

# Show Polly button only when the last message is an agent response
if st.session_state.get("chat_history"):
    last_msg = st.session_state["chat_history"][-1]
    if last_msg.get("role") == "agent" and last_msg.get("content"):
        polly_button_key = f"polly_btn_{len(st.session_state['chat_history'])}"
        if st.button("Generate MP3 of last response", key=polly_button_key):
            with st.spinner("Generating MP3 via Amazon Polly..."):
                result = generate_polly_mp3(last_msg["content"])
                if isinstance(result, (bytes, bytearray)):
                    audio_bytes = result
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button("Download MP3", data=audio_bytes, file_name="agent_response.mp3", mime="audio/mpeg")
                else:
                    st.error(f"Error generating audio: {str(result)}")
