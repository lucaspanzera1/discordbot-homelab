# 🤖 Discord Bot Homelab + AI

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue?style=for-the-badge&logo=docker)
![Discord](https://img.shields.io/badge/Discord-Bot-5865F2?style=for-the-badge&logo=discord)
![AI](https://img.shields.io/badge/AI-Groq%20LLaMA-orange?style=for-the-badge&logo=openai)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

Um bot Discord **inteligente** para monitorar e gerenciar containers Docker do seu homelab com **IA integrada** e **monitoramento avançado de recursos**!

## ✨ Funcionalidades

### 📈 **Monitoramento Clássico:**
- 📊 **Status em tempo real** dos containers Docker
- 🟢 **Containers rodando** e 🔴 **parados** organizados
- 🔄 **Reiniciar containers** remotamente via Discord
- 🏓 **Health check** do bot, Docker e IA
- 🎨 **Interface rica** com embeds coloridos
- ⚡ **Respostas rápidas** e bem estruturadas

### 🔥 **Funcionalidades com IA:**
- 🧠 **Assistente IA integrado** com contexto dos containers
- 📊 **Monitoramento avançado** de CPU, RAM e rede
- 🏆 **Top consumidores** de recursos em tempo real
- 🖥️ **Informações do sistema host** (CPU, RAM, disco, uptime)
- 🔬 **Análise completa** do sistema com insights da IA
- 💡 **Perguntas contextuais** - "Por que o Plex está lento?"

## 🎮 Comandos Disponíveis

### 📊 **Monitoramento Básico**
| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!status` | 📋 Status geral com recursos dos containers | `!status` |
| `!up` | 🟢 Lista containers rodando | `!up` |
| `!down` | 🔴 Lista containers parados | `!down` |
| `!ping` | 🏓 Testa bot, Docker e IA | `!ping` |

### 📈 **Monitoramento de Recursos**
| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!resources [container]` | 🔍 CPU, RAM, rede detalhados | `!resources plex` |
| `!res [container]` | 🔍 Alias para resources | `!res` |
| `!stats [container]` | 🔍 Alias para resources | `!stats nginx` |
| `!top [limite]` | 🏆 Top consumidores de recursos | `!top 5` |
| `!system` | 🖥️ Informações do sistema host | `!system` |
| `!host` | 🖥️ Alias para system | `!host` |

### 🔧 **Controle**
| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!restart <nome>` | 🔄 Reinicia container específico | `!restart portainer` |

### 🧠 **Inteligência Artificial**
| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!ask <pergunta>` | 🤖 Pergunta com contexto dos containers | `!ask por que o Plex está lento?` |
| `!ai <pergunta>` | 🤖 Alias para ask | `!ai como otimizar RAM?` |
| `!chat <pergunta>` | 🤖 Alias para ask | `!chat qual container usa mais CPU?` |
| `!explain <container>` | 📖 Explica o que faz um container | `!explain portainer` |
| `!analyze` | 🔬 Análise completa do sistema | `!analyze` |

### ❓ **Ajuda**
| Comando | Descrição |
|---------|-----------|
| `!help` | ❓ Lista todos os comandos com exemplos |

## 📋 Pré-requisitos

- **Python 3.8+** instalado
- **Docker** instalado e rodando
- **Conta Discord** com permissões de desenvolvedor
- **Conta Groq** (gratuita) para funcionalidades IA
- **Servidor Discord** onde você tenha permissões administrativas

## 🛠️ Instalação

### 1. Clone o Repositório
```bash
git clone https://github.com/lucaspanzera1/discordbot-homelab.git
cd discordbot-homelab
```

### 2. Configure o Ambiente Virtual
```bash
# Instalar dependências do sistema (Ubuntu/Debian)
sudo apt install python3-full python3-venv python3-pip

# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate     # Windows
```

### 3. Instalar Dependências
```bash
pip install discord.py docker python-dotenv psutil aiohttp
```

## 🔧 Configuração

### 1. Criar Bot no Discord

1. Acesse [Discord Developer Portal](https://discord.com/developers/applications)
2. Clique em **"New Application"**
3. Dê um nome ao seu bot (ex: "Homelab Monitor AI")
4. Vá na aba **"Bot"** → **"Add Bot"**
5. ✅ Habilite **"Message Content Intent"**
6. 📋 Copie o **Token** (mantenha em segurança!)

### 2. Criar Conta Groq (IA)

1. Acesse [Groq Console](https://console.groq.com)
2. Crie uma conta gratuita
3. Vá em **"API Keys"**
4. Gere uma nova API Key
5. 📋 Copie a key (gratuito: 30 req/min)

### 3. Adicionar Bot ao Servidor

1. Vá em **"OAuth2"** → **"URL Generator"**
2. Selecione:
   - **Scopes**: `bot`
   - **Bot Permissions**: 
     - `Send Messages`
     - `Use Slash Commands`
     - `Embed Links`
     - `Read Message History`
3. 🔗 Use o link gerado para adicionar o bot ao seu servidor

## ⚙️ Configuração do Ambiente

### 1. Criar Arquivo .env
```bash
nano .env
```

### 2. Adicionar Tokens
```env
# Token do bot Discord (OBRIGATÓRIO)
DISCORD_TOKEN=seu_token_discord_aqui

# Token da API Groq para IA (OBRIGATÓRIO para IA)
GROQ_API_KEY=sua_groq_api_key_aqui
```

### 3. Configurar Permissões Docker
```bash
# Adicionar usuário ao grupo docker
sudo usermod -aG docker $USER

# Reiniciar sessão ou executar:
newgrp docker

# Testar acesso
docker ps
```

## 🚀 Executando o Bot

### Método Local (Desenvolvimento)
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar bot
python bot.py
```

### Método Docker (Produção) 🐳

#### 1. Criar requirements.txt
```txt
discord.py==2.3.2
docker==6.1.3
python-dotenv==1.0.0
psutil==5.9.6
aiohttp==3.9.1
```

#### 2. Criar Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

CMD ["python", "bot.py"]
```

#### 3. Criar docker-compose.yml
```yaml
services:
  discord-bot:
    build: .
    container_name: discordbot-homelab-ai
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
    user: "1000:0"
    networks:
      - homelab

networks:
  homelab:
    driver: bridge
```

#### 4. Executar com Docker
```bash
# Build e executar
docker-compose up --build -d

# Ver logs
docker-compose logs -f discord-bot

# Parar
docker-compose down
```

## 📱 Exemplos de Uso

### 🔍 **Monitoramento de Recursos**
```
Usuário: !resources plex
Bot: 📈 Recursos - plex

Status: RUNNING
CPU: 45.2%
RAM: 2048 MB
RAM %: 12.5%
Limit RAM: 16384 MB
Rede RX: 1024 MB
Rede TX: 512 MB
```

### 🏆 **Top Consumidores**
```
Usuário: !top 3
Bot: 🏆 Top Consumidores de Recursos

🔥 CPU:
1. plex - 45.2%
2. nginx - 12.8%
3. grafana - 8.1%

🧠 RAM:
1. plex - 2048 MB
2. grafana - 512 MB
3. portainer - 128 MB
```

### 🤖 **Assistente IA**
```
Usuário: !ask por que o container plex está usando tanta CPU?
Bot: Com base nos dados atuais, o Plex está usando 45% de CPU, 
     o que pode indicar:

     1. 📺 Transcodificação ativa de vídeo
     2. 🔄 Scan de biblioteca em andamento  
     3. 👥 Múltiplos usuários simultâneos
     4. 🎬 Streaming de conteúdo 4K

     Recomendações:
     - Verificar atividade de transcodificação
     - Considerar hardware encoding
     - Monitorar usuários ativos
```

### 🔬 **Análise Completa**
```
Usuário: !analyze
Bot: 🔬 Análise Completa do Sistema

Sistema em bom estado geral. Observações:

🟢 Pontos Positivos:
- 85% dos containers rodando normalmente
- CPU do sistema em 23% (saudável)
- RAM com 68% de uso (aceitável)

🟡 Atenção:
- Container "plex" usando 45% CPU
- Disco com 78% de uso

💡 Recomendações:
- Monitorar crescimento do disco
- Considerar otimizar transcodificação do Plex
- Backup preventivo recomendado

Resumo Rápido:
🏃 7 rodando | ⏹️ 1 parados
🔥 CPU total: 89.4% | 🧠 RAM total: 4096 MB
```

### 🖥️ **Sistema Host**
```
Usuário: !system
Bot: 🖥️ Sistema Host

CPU: 23.4%
RAM: 11.2 GB / 16.0 GB (70%)
Disco: 180.5 GB / 250.0 GB (78%)
Uptime: 72.5 horas
RAM Livre: 4.8 GB
Disco Livre: 69.5 GB
```

### 📊 **Status Atualizado**
```
Usuário: !status
Bot: 📊 Status dos Containers

Containers Rodando:
🟢 plex
   CPU: 45.2% | RAM: 2048MB (12.5%)
🟢 nginx  
   CPU: 12.8% | RAM: 64MB (0.4%)
🟢 grafana
   CPU: 8.1% | RAM: 512MB (3.1%)

Containers Parados:
🔴 old-backup - exited

Resumo:
✅ 6 rodando | ⏹️ 1 parados | 📦 7 total
```

## 🔍 Funcionalidades da IA

### 🧠 **Contexto Inteligente**
- Quando você pergunta sobre containers, a IA tem acesso aos dados reais de CPU, RAM, rede
- Respostas baseadas no estado atual do seu sistema
- Sugestões personalizadas baseadas nos seus containers

### 💡 **Exemplos de Perguntas**
```
!ask por que o nginx está usando pouca CPU?
!ask como otimizar o uso de memória?  
!ask qual container devo reiniciar primeiro?
!ask meu sistema está com boa performance?
!ask preciso de mais RAM no servidor?
!explain portainer
!ask como fazer backup do grafana?
```

### 🎯 **Análises Inteligentes**
- Performance geral do sistema
- Identificação de gargalos
- Recomendações de otimização
- Alertas preventivos
- Sugestões de manutenção

## 📊 Monitoramento

### Logs do Bot
```bash
# Docker
docker-compose logs -f discord-bot

# Local  
python bot.py  # logs aparecem no terminal
```

### Verificar Recursos
```bash
# Uso de recursos do container
docker stats discordbot-homelab-ai

# Todos os containers
docker ps -a

# Recursos do sistema
htop
```

### 🔗 **Links Úteis**
- [Discord Developer Portal](https://discord.com/developers/applications)
- [Groq API Console](https://console.groq.com)
- [Docker Documentation](https://docs.docker.com/)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
