# 🤖 Discord Bot Homelab + AI

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue?style=for-the-badge&logo=docker)
![Discord](https://img.shields.io/badge/Discord-Bot-5865F2?style=for-the-badge&logo=discord)
![AI](https://img.shields.io/badge/AI-Groq%20LLaMA-orange?style=for-the-badge&logo=openai)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

Um bot Discord **inteligente** para monitorar e gerenciar containers Docker do seu homelab com **IA integrada**, **monitoramento avançado de recursos** e **notificações automáticas de deploy**!

## ✨ Funcionalidades

### 🚀 **NOVO: Monitoramento Automático de Deploy**
- 📡 **Detecção automática** de novos containers, remoções e restarts
- 🔔 **Notificações em tempo real** no Discord quando algo muda
- 📊 **Histórico de mudanças** com timestamps precisos
- 🎯 **Monitoramento contínuo** a cada 30 segundos
- 🚨 **Alertas inteligentes** para mudanças de status

### 📈 **Monitoramento Clássico:**
- 📊 **Status em tempo real** dos containers Docker
- 🟢 **Containers rodando** e 🔴 **parados** organizados
- 🔄 **Controle completo** - start, stop, restart remotamente
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
- 🔍 **Explicações detalhadas** de containers específicos

## 🎮 Comandos Disponíveis

### 📊 **Monitoramento Básico**
| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!status` | 📋 Status geral com recursos dos containers | `!status` |
| `!ping` | 🏓 Testa bot, Docker, IA e monitoramento | `!ping` |

### 🚀 **Monitoramento de Deploy (NOVO)**
| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!deploy_status` | 📡 Status do monitoramento automático | `!deploy_status` |
| `!recent_changes [min]` | 🕒 Mudanças recentes nos containers | `!recent_changes 60` |
| `!set_deploy_channel [id]` | 🔧 Configurar canal para notificações | `!set_deploy_channel` |

### 📈 **Monitoramento de Recursos**
| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!resources [container]` | 🔍 CPU, RAM, rede detalhados | `!resources plex` |
| `!res [container]` | 🔍 Alias para resources | `!res` |
| `!stats [container]` | 🔍 Alias para resources | `!stats nginx` |
| `!top [limite]` | 🏆 Top consumidores de recursos | `!top 5` |
| `!system` | 🖥️ Informações do sistema host | `!system` |
| `!host` | 🖥️ Alias para system | `!host` |

### 🔧 **Controle de Containers (NOVO)**
| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!start <nome>` | ▶️ Iniciar container específico | `!start nginx` |
| `!stop <nome>` | ⏹️ Parar container específico | `!stop nginx` |
| `!restart <nome>` | 🔄 Reiniciar container específico | `!restart portainer` |
| `!cleanup` | 🧹 Remover containers parados (admin) | `!cleanup` |

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
5. ✅ **IMPORTANTE**: Habilite **"Message Content Intent"**
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
     - `Add Reactions`
     - `Attach Files`
3. 🔗 Use o link gerado para adicionar o bot ao seu servidor

### 4. Configurar Canal de Notificações (NOVO)

1. **Crie um canal** no seu servidor (ex: `#homelab-deploys`)
2. **Ative Modo Desenvolvedor**: Discord → Configurações → Avançado → Modo Desenvolvedor
3. **Clique com botão direito** no canal → "Copiar ID do Canal"
4. **Guarde o ID** para usar no arquivo `.env`

## ⚙️ Configuração do Ambiente

### 1. Criar Arquivo .env
```bash
nano .env
```

### 2. Adicionar Configurações
```env
# Token do bot Discord (OBRIGATÓRIO)
DISCORD_TOKEN=seu_token_discord_aqui

# Token da API Groq para IA (OBRIGATÓRIO para IA)
GROQ_API_KEY=sua_groq_api_key_aqui

# ID do canal para notificações de deploy (NOVO - OPCIONAL)
DEPLOY_CHANNEL_ID=123456789012345678
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

Você deve ver algo como:
```
🔧 Inicializando cliente Docker...
✅ Cliente Docker conectado com sucesso!
✅ Cliente Groq inicializado!
🤖 Bot conectado como SeuBot#1234
✅ Conexão com Docker confirmada!
📡 Monitoramento de containers iniciado!
✅ Canal de deploy configurado: #homelab-deploys
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
      - DEPLOY_CHANNEL_ID=${DEPLOY_CHANNEL_ID}
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

## 🔔 Notificações Automáticas de Deploy (NOVO)

### Como Funciona:
- 🕰️ **A cada 30 segundos** o bot verifica todos os containers
- 🔍 **Compara** com o estado anterior
- 🚨 **Detecta mudanças**: criação, remoção, restart, mudança de status
- 📢 **Envia notificações** automaticamente no canal configurado

### Exemplos de Notificações:

#### 🚀 Novo Container
```
🚀 Novos Containers Implantados

📦 nginx-proxy
Imagem: nginx:latest
Status: running
Portas: 80:80, 443:443
```

#### 🔄 Container Reiniciado
```
🔄 Containers Reiniciados

📦 portainer
Imagem: portainer/portainer-ce:latest
Status: running
```

#### ⚡ Mudança de Status
```
⚡ Mudanças de Status

✅ grafana
Status: exited → running
Imagem: grafana/grafana:latest
```

## 📱 Exemplos de Uso

### 🚀 **Monitoramento de Deploy (NOVO)**
```
Usuário: !deploy_status
Bot: 📡 Status do Monitoramento

Monitoramento: ✅ Ativo
Canal de Notificações: #homelab-deploys
Containers Monitorados: 12
Última Atualização: 14:32:15
Docker: ✅ Conectado
```

```
Usuário: !recent_changes 120
Bot: 🕒 Mudanças dos Últimos 120 Minutos

📦 nginx-test
Status: running
Imagem: nginx:latest
Criado: 15 min atrás

📦 redis-cache
Status: running  
Imagem: redis:7-alpine
Criado: 45 min atrás
```

### 🔧 **Controle de Containers (NOVO)**
```
Usuário: !start nginx
Bot: ▶️ Iniciando container nginx...
     ✅ Container nginx iniciado com sucesso!

Usuário: !stop nginx  
Bot: ⏹️ Parando container nginx...
     ✅ Container nginx parado com sucesso!

Usuário: !cleanup
Bot: ⚠️ Confirmação de Limpeza
     Isso removerá TODOS os containers parados. Tem certeza?
     [Reações: ✅ ❌]
```

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

Atualizado em 14:25:30
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

### 🤖 **Assistente IA Melhorado**
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

Usuário: !explain nginx
Bot: 🔍 Análise do Container: nginx

O nginx é um servidor web de alta performance que atua como:

🌐 **Servidor Web**: Serve conteúdo estático (HTML, CSS, JS)
🔄 **Reverse Proxy**: Redireciona requisições para outros serviços
⚖️ **Load Balancer**: Distribui carga entre múltiplos backends
🔒 **SSL Termination**: Gerencia certificados HTTPS

Status Atual:
Status: running
CPU: 12.8%
RAM: 64 MB
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
- Monitoramento ativo há 2.5 horas

🟡 Atenção:
- Container "plex" usando 45% CPU
- Disco com 78% de uso
- 2 containers foram reiniciados na última hora

💡 Recomendações:
- Monitorar crescimento do disco
- Considerar otimizar transcodificação do Plex
- Backup preventivo recomendado
- Investigar cause dos restarts recentes

Resumo Rápido:
🏃 7 rodando | ℹ️ 1 parados
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

### 📊 **Status Completo**
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
🟢 portainer
   CPU: 2.3% | RAM: 128MB (0.8%)

Containers Parados:
🔴 old-backup - exited

Resumo:
✅ 6 rodando | ℹ️ 1 parados | 📦 7 total
```

## 🔍 Funcionalidades da IA

### 🧠 **Contexto Inteligente**
- Quando você pergunta sobre containers, a IA tem acesso aos dados reais de CPU, RAM, rede
- Respostas baseadas no estado atual do seu sistema
- Sugestões personalizadas baseadas nos seus containers
- **NOVO**: Contexto sobre mudanças recentes de deploy

### 💡 **Exemplos de Perguntas**
```
!ask por que o nginx está usando pouca CPU?
!ask como otimizar o uso de memória?  
!ask qual container devo reiniciar primeiro?
!ask meu sistema está com boa performance?
!ask preciso de mais RAM no servidor?
!ask por que tantos containers foram reiniciados hoje?
!explain portainer
!ask como fazer backup do grafana?
!ask o que significa quando um container fica "exited"?
```

### 🎯 **Análises Inteligentes**
- Performance geral do sistema
- Identificação de gargalos
- Recomendações de otimização
- Alertas preventivos
- Sugestões de manutenção
- **NOVO**: Análise de padrões de deploy
- **NOVO**: Detecção de problemas recorrentes

## 🏓 Teste Rápido

Após configurar tudo, teste com:

```bash
# Teste básico
!ping                    # Deve mostrar todos os status ✅

# Teste monitoramento
!status                  # Lista containers atuais
!deploy_status          # Status do monitoramento automático

# Teste deploy (crie um container teste)
docker run --name teste-deploy -d nginx
# O bot deve notificar automaticamente no canal!

# Teste IA
!ask como está meu sistema?
!explain teste-deploy

# Limpeza
!stop teste-deploy
docker rm teste-deploy
```

## 📊 Monitoramento e Logs

### Logs do Bot
```bash
# Docker
docker-compose logs -f discord-bot

# Local  
python bot.py  # logs aparecem no terminal
```

### Verificar Recursos
```bash
# Uso de recursos do container do bot
docker stats discordbot-homelab-ai

# Todos os containers
docker ps -a

# Recursos do sistema
htop
```

### Status do Bot
```bash
# No Discord
!ping                    # Status geral
!deploy_status          # Status do monitoramento
!system                 # Status do host
```

## 🔧 Solução de Problemas

### ❌ "Message Content Intent não ativado"
- Vá no Discord Developer Portal
- Aba "Bot" → Privileged Gateway Intents
- ✅ Ative "Message Content Intent"

### ❌ "Canal de deploy não encontrado"
- Verifique se o DEPLOY_CHANNEL_ID está correto
- Use `!set_deploy_channel` no canal desejado
- Certifique-se que o bot tem permissões no canal

### ❌ "Monitoramento inativo"
- Verifique logs do bot
- Certifique-se que Docker está acessível
- Reinicie o bot: `!restart` (se aplicável)

### ❌ Bot não detecta mudanças
- Verifique se o bot tem acesso ao Docker socket
- Confirme que o monitoramento está ativo: `!deploy_status`
- Teste com: `docker run --name teste -d nginx`

### 🆘 **Comandos de Emergência**
```bash
# Reiniciar monitoramento
!deploy_status           # Verificar status
# Se inativo, reinicie o bot

# Ver mudanças recentes
!recent_changes 1440     # Últimas 24 horas

# Status completo
!ping                    # Ver todos os componentes
```

## 🔗 Links Úteis

- [Discord Developer Portal](https://discord.com/developers/applications)
- [Groq API Console](https://console.groq.com)
- [Docker Documentation](https://docs.docker.com/)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request