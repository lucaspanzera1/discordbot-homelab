# 🤖 Discord Bot Homelab

![Python](https://img.shields.io/badge/Python-3.8+-blue?style=for-the-badge&logo=python)
![Docker](https://img.shields.io/badge/Docker-Enabled-blue?style=for-the-badge&logo=docker)
![Discord](https://img.shields.io/badge/Discord-Bot-5865F2?style=for-the-badge&logo=discord)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

Um bot Discord para monitorar e gerenciar containers Docker do seu homelab diretamente do Discord!


## ✨ Funcionalidades

- 📊 **Monitoramento em tempo real** dos containers Docker
- 🟢 **Status detalhado** com containers rodando e parados
- 🔄 **Reiniciar containers** remotamente via Discord
- 📈 **Resumos rápidos** com contadores visuais
- 🏓 **Health check** do bot e conexão Docker
- 🎨 **Interface rica** com embeds coloridos e organizados
- ⚡ **Respostas rápidas** e informações bem estruturadas

## 🎮 Comandos Disponíveis

| Comando | Descrição | Exemplo |
|---------|-----------|---------|
| `!status` | 📋 Mostra todos os containers (rodando e parados) | `!status` |
| `!up` | 🟢 Lista apenas containers rodando | `!up` |
| `!down` | 🔴 Lista apenas containers parados | `!down` |
| `!count` | 📊 Resumo rápido com contadores visuais | `!count` |
| `!restart <nome>` | 🔄 Reinicia um container específico | `!restart portainer` |
| `!ping` | 🏓 Testa conexão do bot e Docker | `!ping` |
| `!help` | ❓ Mostra todos os comandos | `!help` |

## 📋 Pré-requisitos

- **Python 3.8+** instalado
- **Docker** instalado e rodando
- **Conta Discord** com permissões de desenvolvedor
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
pip install discord.py docker python-dotenv
```

## 🔧 Configuração do Bot Discord

### 1. Criar Bot no Discord

1. Acesse [Discord Developer Portal](https://discord.com/developers/applications)
2. Clique em **"New Application"**
3. Dê um nome ao seu bot (ex: "Homelab Monitor")
4. Vá na aba **"Bot"** → **"Add Bot"**
5. ✅ Habilite **"Message Content Intent"**
6. 📋 Copie o **Token** (mantenha em segurança!)

### 2. Adicionar Bot ao Servidor

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

### 2. Adicionar Token
```env
# Token do bot Discord (OBRIGATÓRIO)
DISCORD_TOKEN=seu_token_aqui
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

#### 1. Criar Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .

RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

CMD ["python", "bot.py"]
```

#### 2. Criar requirements.txt
```txt
discord.py==2.3.2
docker==6.1.3
python-dotenv==1.0.0
```

#### 3. Criar docker-compose.yml
```yaml
services:
  discord-bot:
    build: .
    container_name: discordbot-homelab
    restart: unless-stopped
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
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

### Verificar Status Geral
```
Usuário: !status
Bot: 📊 RESUMO: 5 rodando, 2 parados, 7 total

🟢 CONTAINERS RODANDO:
  • portainer - portainer/portainer-ce:latest
  • nginx - nginx:alpine
  • grafana - grafana/grafana:latest

🔴 CONTAINERS PARADOS:
  • old-app - ubuntu:20.04
  • backup - alpine:latest
```

### Reiniciar Container
```
Usuário: !restart portainer
Bot: 🔄 Reiniciando container portainer...
Bot: ✅ Container portainer reiniciado com sucesso!
```

### Verificar Conectividade
```
Usuário: !ping
Bot: 🏓 Pong!
     Bot: ✅ Online
     Docker: ✅ Conectado  
     Latência: 45ms
```

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
docker stats discordbot-homelab

# Containers do homelab
docker ps -a
```

## 🔮 Funcionalidades Futuras

- [ ] 📈 **Métricas de sistema** (CPU, RAM, Disk)
- [ ] 📢 **Alertas automáticos** quando containers caem
- [ ] 🗂️ **Logs de containers** em tempo real
- [ ] 📊 **Integração com Grafana/Prometheus**
- [ ] 🔐 **Sistema de autenticação** por roles Discord
- [ ] ⏰ **Agendamento de tarefas** (backups, updates)
- [ ] 💾 **Status de backups** e controle
- [ ] 🌡️ **Monitoramento de temperatura** dos servidores
- [ ] 🔄 **Auto-update** de containers
- [ ] 📱 **Notificações push** para eventos críticos

## 🤝 Contribuição

Contribuições são bem-vindas! Para contribuir:

1. 🍴 Fork o projeto
2. 🌿 Crie uma branch (`git checkout -b feature/MinhaFeature`)
3. 💾 Commit suas mudanças (`git commit -m 'Adiciona MinhaFeature'`)
4. 📤 Push para a branch (`git push origin feature/MinhaFeature`)  
5. 🔀 Abra um Pull Request

## 🌟 Screenshots


<div align="center">

**⭐ Se este projeto te ajudou, deixe uma estrela!**

**🔗 Links Úteis**
- [Discord Developer Portal](https://discord.com/developers/applications)
- [Docker Documentation](https://docs.docker.com/)
- [Python Virtual Environments](https://docs.python.org/3/tutorial/venv.html)
