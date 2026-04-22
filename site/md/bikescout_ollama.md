# Deploy and Use BikeScout with Ollama and Open WebUI

If you prefer a private and free experience without external API costs, use the `docker-compose-ollama.yml`
file to run BikeScout with Ollama (Llama 3/Mistral) instead of OpenAI.
Refer to this guide to setup a complete local installation with Ollama and Open WebUI.

Pre Requirements:

* **Docker Desktop:** [Download it here](https://www.docker.com/products/docker-desktop/).
* **OpenRouteService Key:** [Sign up here](https://openrouteservice.org/) for trail and surface data.

Deploy BikeScout:

1. **Download the repository:** Download this repository as a ZIP and extract it to a folder (e.g., `C:\BikeScout` or `/Users/YourName/BikeScout`).
2. Rename `.env.example` to `.env` and paste your API keys:
```bash
ORS_API_KEY=your_ors_key_here
OPENAI_API_KEY=your_llm_key_here
```
3. Launch: Open your terminal in the folder and run:
```bash
docker compose -f docker-compose-ollama.yml up -d
```
4. Download a LLM model for Ollama, example `llama3.1:8b` (or `gemma2:27b`):
```bash
   docker exec -it ollama ollama pull llama3.1:8b
```
5. Launch Open WebUI: connect to http://localhost:3000 and follow the instructions to create a first user.
6. Explore the Open API docs for BikeScout tools: http://localhost:8000/bikescout/docs


## Enable BikeScout using Open WebUI

To enable the tools within the Open WebUI interface, follow these steps:

- Navigate: Go to Admin Panel -> Settings -> Integrations. 
- Add Connection: Click the "+" button. 
  - Connection Details:
    - Type: OpenAPI 
    - URL: http://mcpo:8000/bikescout
    - OpenAPI Spec: Set to URL and use openapi.json. 
    - Auth: None. 
  - Identification:
    - ID: bikescout 
    - Name: bikescout
    - Description: bikescout

Once saved, you can enable this tool for your specific models in the New Chat, Workspace or Model settings, allowing the LLM to access real-time data through your MCP server.

Try a query, e.g. *"Use the **Dolomiti local guide** to plan a road cycling route starting from **Cortina**. I need at least **800m of elevation gain**. Also, recommend the correct tire pressure for high-altitude descents and a mountain hut for a strudel stop."*

## Teardown

Execute:
```bash
docker compose -f docker-compose-ollama.yml down -v
```
