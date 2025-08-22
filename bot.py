import os
import discord
import docker
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from datetime import datetime
import aiohttp
import json

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
TOKEN = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')  # Adicione no seu .env

# Configurar intents
intents = discord.Intents.default()
intents.message_content = True

# Criar instância do bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Cliente Docker
print("🔧 Inicializando cliente Docker...")
try:
    docker_client = docker.from_env()
    docker_client.ping()
    print("✅ Cliente Docker conectado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao conectar Docker: {e}")
    docker_client = None

class GroqClient:
    """Cliente para API Groq"""
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def chat_completion(self, messages: list, model: str = "llama-3.3-70b-versatile", max_tokens: int = 1000):
        """Faz uma requisição para o modelo de chat da Groq"""
        payload = {
            "messages": messages,
            "model": model,
            "max_tokens": max_tokens,
            "temperature": 0.7,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.base_url, headers=self.headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        return f"Erro na API Groq: {response.status} - {error_text}"
            except Exception as e:
                return f"Erro de conexão com Groq: {str(e)}"

# Inicializar cliente Groq
groq_client = None
if GROQ_API_KEY:
    groq_client = GroqClient(GROQ_API_KEY)
    print("✅ Cliente Groq inicializado!")
else:
    print("❌ GROQ_API_KEY não encontrada")

@bot.event
async def on_ready():
    print(f'🤖 Bot conectado como {bot.user}')
    
    # Testar conexão com Docker
    if docker_client:
        try:
            docker_client.ping()
            print('✅ Conexão com Docker confirmada!')
        except Exception as e:
            print(f'❌ Erro na verificação do Docker: {e}')
    else:
        print('❌ Cliente Docker não disponível')

def get_container_info():
    """Obtém informações dos containers"""
    if not docker_client:
        return "❌ Cliente Docker não disponível"
    
    try:
        containers = docker_client.containers.list(all=True)
        container_info = []
        
        for container in containers:
            info = {
                'name': container.name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'created': container.attrs['Created']
            }
            container_info.append(info)
        
        return container_info
    except Exception as e:
        return f"❌ Erro ao obter containers: {str(e)}"

def format_container_status(containers, filter_status=None):
    """Formata a lista de containers para exibição"""
    if isinstance(containers, str):
        return containers
    
    if not containers:
        return "🔭 Nenhum container encontrado"
    
    # Filtrar por status se especificado
    if filter_status:
        containers = [c for c in containers if c['status'] == filter_status]
        if not containers:
            return f"🔭 Nenhum container {filter_status} encontrado"
    
    # Organizar por status
    running = [c for c in containers if c['status'] == 'running']
    stopped = [c for c in containers if c['status'] in ['exited', 'stopped']]
    others = [c for c in containers if c not in running + stopped]
    
    result = []
    
    if running:
        result.append("🟢🟢 **CONTAINERS RODANDO:**")
        for container in running:
            result.append(f"  • `{container['name']}` - {container['image']}")
    
    if stopped:
        result.append("\n🔴🔴 **CONTAINERS PARADOS:**")
        for container in stopped:
            result.append(f"  • `{container['name']}` - {container['image']}")
    
    if others:
        result.append("\n🟡🟡 **OUTROS STATUS:**")
        for container in others:
            result.append(f"  • `{container['name']}` - {container['status']}")
    
    # Adicionar resumo
    total = len(containers) if not filter_status else len(docker_client.containers.list(all=True))
    running_count = len(running)
    stopped_count = len(stopped)
    
    if not filter_status:
        result.insert(0, f"📊 **RESUMO:** {running_count} rodando, {stopped_count} parados, {total} total")
    
    return "\n".join(result)

# Comandos Docker existentes (mantendo os mesmos)
@bot.command(name='status')
async def status(ctx):
    """Mostra o status de todos os containers"""
    await ctx.send("🔍 Verificando containers...")
    
    containers = get_container_info()
    message = format_container_status(containers)
    
    if len(message) > 1900:
        parts = message.split('\n')
        current_message = ""
        
        for part in parts:
            if len(current_message + part + '\n') > 1900:
                await ctx.send(current_message)
                current_message = part + '\n'
            else:
                current_message += part + '\n'
        
        if current_message:
            await ctx.send(current_message)
    else:
        await ctx.send(message)

@bot.command(name='up')
async def containers_up(ctx):
    """Mostra apenas containers que estão rodando"""
    await ctx.send("🔍 Verificando containers rodando...")
    containers = get_container_info()
    message = format_container_status(containers, filter_status='running')
    await ctx.send(message)

@bot.command(name='down')
async def containers_down(ctx):
    """Mostra apenas containers parados"""
    await ctx.send("🔍 Verificando containers parados...")
    containers = get_container_info()
    
    if isinstance(containers, str):
        await ctx.send(containers)
        return
    
    stopped_containers = [c for c in containers if c['status'] in ['exited', 'stopped']]
    
    if not stopped_containers:
        await ctx.send("🟢 Nenhum container parado encontrado!")
        return
        
    message = format_container_status(stopped_containers)
    await ctx.send(message)

@bot.command(name='restart')
async def restart_container(ctx, container_name: str = None):
    """Reinicia um container específico"""
    if not container_name:
        await ctx.send("❌ Especifique o nome do container: `!restart nome_do_container`")
        return
    
    if not docker_client:
        await ctx.send("❌ Cliente Docker não disponível")
        return
    
    try:
        container = docker_client.containers.get(container_name)
        await ctx.send(f"🔄 Reiniciando container `{container_name}`...")
        
        container.restart()
        await ctx.send(f"✅ Container `{container_name}` reiniciado com sucesso!")
        
    except docker.errors.NotFound:
        await ctx.send(f"❌ Container `{container_name}` não encontrado")
    except Exception as e:
        await ctx.send(f"❌ Erro ao reiniciar container: {str(e)}")

# ======= NOVOS COMANDOS COM IA =======

@bot.command(name='ask', aliases=['ai', 'chat'])
async def ask_ai(ctx, *, question: str = None):
    """Faz uma pergunta para a IA"""
    if not groq_client:
        await ctx.send("❌ Cliente Groq não disponível. Verifique a API key.")
        return
    
    if not question:
        await ctx.send("❌ Faça uma pergunta: `!ask sua pergunta aqui`")
        return
    
    # Indicar que está processando
    async with ctx.typing():
        messages = [
            {
                "role": "system", 
                "content": "Você é um assistente prestativo para um bot Discord de monitoramento de homelab. Responda de forma concisa e útil."
            },
            {
                "role": "user", 
                "content": question
            }
        ]
        
        response = await groq_client.chat_completion(messages)
        
        # Dividir resposta se muito longa
        if len(response) > 2000:
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(response)

@bot.command(name='explain')
async def explain_container(ctx, container_name: str = None):
    """Explica o que faz um container específico"""
    if not groq_client:
        await ctx.send("❌ Cliente Groq não disponível. Verifique a API key.")
        return
    
    if not container_name:
        await ctx.send("❌ Especifique o nome do container: `!explain nome_do_container`")
        return
    
    if not docker_client:
        await ctx.send("❌ Cliente Docker não disponível")
        return
    
    try:
        container = docker_client.containers.get(container_name)
        image_name = container.image.tags[0] if container.image.tags else container.image.id
        
        async with ctx.typing():
            messages = [
                {
                    "role": "system",
                    "content": "Você é um expert em Docker e containers. Explique de forma clara e concisa o que faz cada aplicação."
                },
                {
                    "role": "user",
                    "content": f"Explique o que faz o container/aplicação: {image_name}. Seja conciso mas informativo."
                }
            ]
            
            response = await groq_client.chat_completion(messages)
            
            embed = discord.Embed(
                title=f"📦 {container_name}",
                description=response,
                color=discord.Color.blue()
            )
            embed.add_field(name="Imagem", value=image_name, inline=True)
            embed.add_field(name="Status", value=container.status, inline=True)
            
            await ctx.send(embed=embed)
            
    except docker.errors.NotFound:
        await ctx.send(f"❌ Container `{container_name}` não encontrado")
    except Exception as e:
        await ctx.send(f"❌ Erro: {str(e)}")

@bot.command(name='analyze')
async def analyze_system(ctx):
    """Analisa o status geral do sistema com IA"""
    if not groq_client:
        await ctx.send("❌ Cliente Groq não disponível. Verifique a API key.")
        return
    
    containers = get_container_info()
    
    if isinstance(containers, str):
        await ctx.send(containers)
        return
    
    async with ctx.typing():
        # Preparar dados para análise
        system_info = {
            "total_containers": len(containers),
            "running": len([c for c in containers if c['status'] == 'running']),
            "stopped": len([c for c in containers if c['status'] in ['exited', 'stopped']]),
            "containers": [{"name": c['name'], "status": c['status'], "image": c['image']} for c in containers]
        }
        
        messages = [
            {
                "role": "system",
                "content": "Você é um analista de sistemas especializado em Docker. Analise o status dos containers e dê insights úteis sobre o homelab."
            },
            {
                "role": "user",
                "content": f"Analise este sistema Docker: {json.dumps(system_info, indent=2)}. Dê insights sobre saúde do sistema, possíveis problemas e recomendações."
            }
        ]
        
        response = await groq_client.chat_completion(messages, max_tokens=1500)
        
        embed = discord.Embed(
            title="🔍 Análise do Sistema",
            description=response,
            color=discord.Color.green() if system_info["stopped"] == 0 else discord.Color.yellow(),
            timestamp=datetime.now()
        )
        
        await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    """Testa se o bot está respondendo"""
    docker_status = "❌ Indisponível"
    groq_status = "❌ Indisponível"
    
    if docker_client:
        try:
            docker_client.ping()
            docker_status = "✅ Conectado"
        except:
            docker_status = "❌ Erro"
    
    if groq_client:
        groq_status = "✅ Conectado"
    
    embed = discord.Embed(title="🏓 Pong!", color=discord.Color.green())
    embed.add_field(name="Bot", value="✅ Online", inline=True)
    embed.add_field(name="Docker", value=docker_status, inline=True)
    embed.add_field(name="Groq AI", value=groq_status, inline=True)
    embed.add_field(name="Latência", value=f"{round(bot.latency * 1000)}ms", inline=True)
    
    await ctx.send(embed=embed)

@bot.event
async def on_command_error(ctx, error):
    """Tratamento de erros"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando não encontrado. Use `!help` para ver os comandos disponíveis.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ Argumento obrigatório faltando. Use `!help` para ver a sintaxe.")
    else:
        await ctx.send(f"❌ Erro: {str(error)}")
        print(f"Erro: {error}")

# Comando de ajuda customizado
@bot.remove_command('help')
@bot.command(name='help')
async def custom_help(ctx):
    """Mostra todos os comandos disponíveis"""
    embed = discord.Embed(
        title="🤖 Homelab Monitor + AI - Comandos",
        description="Bot para monitorar containers Docker com IA integrada",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📊 Monitoramento",
        value="`!status` - Todos os containers\n`!up` - Containers rodando\n`!down` - Containers parados",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Controle",
        value="`!restart <nome>` - Reiniciar container\n`!ping` - Testa conexão",
        inline=False
    )
    
    embed.add_field(
        name="🧠 Inteligência Artificial",
        value="`!ask <pergunta>` - Pergunte qualquer coisa\n`!explain <container>` - Explica um container\n`!analyze` - Análise do sistema",
        inline=False
    )
    
    embed.add_field(
        name="❓ Ajuda",
        value="`!help` - Esta mensagem",
        inline=False
    )
    
    embed.set_footer(text="Use ! antes de cada comando • Exemplo: !ask como otimizar Docker?")
    
    await ctx.send(embed=embed)

if __name__ == '__main__':
    if not TOKEN:
        print("❌ DISCORD_TOKEN não encontrado no arquivo .env")
        exit(1)
    
    if not GROQ_API_KEY:
        print("⚠️  GROQ_API_KEY não encontrado - funcionalidades IA desabilitadas")
    
    print("🚀 Iniciando bot...")
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Token do Discord inválido")
    except Exception as e:
        print(f"❌ Erro ao iniciar bot: {e}")