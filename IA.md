# 🤖 Discord Bot Homelab & IA

Para usar IA junto ao Bot do Discord, estou ultilizando a API da Grok.

### Dependência para requisicoes
```bash
pip install aiohttp
```

### Criar API Key da Groq
* Acesse: https://console.groq.com/
* Crie uma conta
* Vá em "API Keys"
* Crie uma nova key

### Definir API Key no .env
```bash
GROQ_API_KEY=sua_key_groq_aqui
```

### Inteligência Artificial
```bash
!ask <pergunta> - Faz pergunta para IA
!explain <container> - Explica o que faz um container
!analyze - Análise inteligente do sistema
```
