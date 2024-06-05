## Docker
- Docker build: `docker build --tag llm-chatbot .`
- Docker run: `docker run -d -p 5001:5001 --env-file ~/git/.env llm-chatbot`
#### Persistent data storage for chatbot in local data folder.
- Docker run: `docker run -d -p 80:5001 --env-file .env -v <<path to local data folder>>:/home/LLM-Chatbot/chat_data llm-chatbot`
