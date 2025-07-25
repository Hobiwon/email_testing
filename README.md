# email_testing

# 🧠 Remote Ollama Python Client

This repository demonstrates how to use the [`ollama`](https://pypi.org/project/ollama/) Python package to interact with an Ollama server running in a container on a **remote host**.

> Ollama lets you run open-source large language models locally or remotely. This project focuses on accessing those models over the network using Python.

---

## 📦 Requirements

- Python 3.8+
- A remote machine running the Ollama server with networking exposed
- Models pulled and available on the remote server (e.g. `llama3`, `mistral`, etc.)

---

## ⚙️ Quick Setup

### 1. Install the `ollama` Python package

```bash
pip install ollama
```

2. Set your remote host environment variable (or pass it programmatically)
Option A: Set environment variable
```bash
export OLLAMA_BASE_URL=http://<REMOTE_IP>:11434
```
Option B: Use the base URL directly in code
```python
from ollama import Client

client = Client(host='http://<REMOTE_IP>:11434')
```
  
🚀 Example Usage  
🔹 Basic Prompt Completion
```python
from ollama import Client

client = Client(host='http://<REMOTE_IP>:11434')

response = client.chat(model='llama3', messages=[
    {'role': 'user', 'content': 'What is the capital of France?'}
])

print(response['message']['content'])
```
🔹 Streaming Response
```python
for chunk in client.chat(model='llama3', messages=[
    {'role': 'user', 'content': 'Write a haiku about the stars.'}
], stream=True):
    print(chunk['message']['content'], end='', flush=True)
```
🔹 Multi-Turn Conversation
```python
messages = [
    {'role': 'system', 'content': 'You are a helpful assistant.'},
    {'role': 'user', 'content': 'Who is Ada Lovelace?'},
    {'role': 'user', 'content': 'Why is she important?'}
]

response = client.chat(model='llama3', messages=messages)
print(response['message']['content'])
```
🛠️ Utility Functions
🔸 List Available Models on the Server
```python
models = client.list()
for m in models['models']:
    print(f"{m['name']} (size: {m['size']} bytes)")
```

This will download the model to the remote server running Ollama. Make sure it has access to the internet.
🔸 Check Model Information
```python
info = client.show(model='llama3')
print(f"Model: {info['name']}")
print(f"Parameters: {info.get('parameters', 'N/A')}")
```

🔸 Generate Embeddings
```python
result = client.embeddings(model='nomic-embed-text', prompt='The quick brown fox jumps over the lazy dog.')
embedding = result['embedding']

print(f'Got embedding with {len(embedding)} dimensions')
```
🐳 Running Ollama Remotely via Docker

On the remote machine:
```bash
docker run -d -p 11434:11434 --name ollama-server ollama/ollama
```
