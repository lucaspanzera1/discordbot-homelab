import os
import discord
import docker
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from datetime import datetime
import aiohttp
import json
import psutil
import time

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
TOKEN = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

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

def bytes_to_mb(bytes_value):
    """Converte bytes para MB"""
    if bytes_value is None:
        return 0
    return round(bytes_value / 1024 / 1024, 2)

def bytes_to_gb(bytes_value):
    """Converte bytes para GB"""
    if bytes_value is None:
        return 0
    return round(bytes_value / 1024 / 1024 / 1024, 2)

def get_container_stats(container):
    """Obtém estatísticas de recursos de um container"""
    try:
        if container.status != 'running':
            return {
                'cpu_percent': 0,
                'memory_usage_mb': 0,
                'memory_limit_mb': 0,
                'memory_percent': 0,
                'network_rx_mb': 0,
                'network_tx_mb': 0,
                'status': container.status
            }
        
        stats = container.stats(stream=False)
        
        # CPU
        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
        system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats']['system_cpu_usage']
        cpu_count = stats['cpu_stats'].get('online_cpus', len(stats['cpu_stats']['cpu_usage'].get('percpu_usage', [1])))
        
        cpu_percent = 0
        if system_delta > 0 and cpu_delta > 0:
            cpu_percent = (cpu_delta / system_delta) * cpu_count * 100
        
        # Memória
        memory_usage = stats['memory_stats'].get('usage', 0)
        memory_limit = stats['memory_stats'].get('limit', 0)
        memory_percent = (memory_usage / memory_limit * 100) if memory_limit > 0 else 0
        
        # Rede
        network_stats = stats.get('networks', {})
        total_rx = sum(net.get('rx_bytes', 0) for net in network_stats.values())
        total_tx = sum(net.get('tx_bytes', 0) for net in network_stats.values())
        
        return {
            'cpu_percent': round(cpu_percent, 2),
            'memory_usage_mb': bytes_to_mb(memory_usage),
            'memory_limit_mb': bytes_to_mb(memory_limit),
            'memory_percent': round(memory_percent, 2),
            'network_rx_mb': bytes_to_mb(total_rx),
            'network_tx_mb': bytes_to_mb(total_tx),
            'status': 'running'
        }
        
    except Exception as e:
        print(f"Erro ao obter stats do container {container.name}: {e}")
        return {
            'cpu_percent': 0,
            'memory_usage_mb': 0,
            'memory_limit_mb': 0,
            'memory_percent': 0,
            'network_rx_mb': 0,
            'network_tx_mb': 0,
            'status': 'error',
            'error': str(e)
        }

def get_system_stats():
    """Obtém estatísticas do sistema host"""
    try:
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': psutil.virtual_memory(),
            'disk': psutil.disk_usage('/'),
            'uptime': time.time() - psutil.boot_time()
        }
    except Exception as e:
        return {'error': str(e)}

def get_detailed_container_info():
    """Obtém informações detalhadas dos containers com recursos"""
    if not docker_client:
        return "❌ Cliente Docker não disponível"
    
    try:
        containers = docker_client.containers.list(all=True)
        detailed_info = []
        
        for container in containers:
            stats = get_container_stats(container)
            
            info = {
                'name': container.name,
                'status': container.status,
                'image': container.image.tags[0] if container.image.tags else 'unknown',
                'created': container.attrs['Created'],
                'stats': stats
            }
            detailed_info.append(info)
        
        return detailed_info
    except Exception as e:
        return f"❌ Erro ao obter containers: {str(e)}"

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

# ======= COMANDOS DE MONITORAMENTO BÁSICO (mantidos) =======

@bot.command(name='status')
async def status(ctx):
    """Mostra o status de todos os containers"""
    await ctx.send("🔍 Verificando containers...")
    
    containers = get_detailed_container_info()
    
    if isinstance(containers, str):
        await ctx.send(containers)
        return
    
    if not containers:
        await ctx.send("🔭 Nenhum container encontrado")
        return
    
    # Organizar por status
    running = [c for c in containers if c['status'] == 'running']
    stopped = [c for c in containers if c['status'] in ['exited', 'stopped']]
    
    embed = discord.Embed(title="📊 Status dos Containers", color=discord.Color.blue())
    
    if running:
        running_text = ""
        for container in running:
            stats = container['stats']
            running_text += f"🟢 `{container['name']}`\n"
            running_text += f"   CPU: {stats['cpu_percent']}% | RAM: {stats['memory_usage_mb']}MB ({stats['memory_percent']:.1f}%)\n"
        embed.add_field(name="Containers Rodando", value=running_text, inline=False)
    
    if stopped:
        stopped_text = "\n".join([f"🔴 `{c['name']}` - {c['status']}" for c in stopped])
        embed.add_field(name="Containers Parados", value=stopped_text, inline=False)
    
    embed.add_field(
        name="Resumo", 
        value=f"✅ {len(running)} rodando | ⏹️ {len(stopped)} parados | 📦 {len(containers)} total",
        inline=False
    )
    
    await ctx.send(embed=embed)

# ======= NOVOS COMANDOS DE MONITORAMENTO AVANÇADO =======

@bot.command(name='resources', aliases=['res', 'stats'])
async def resources(ctx, container_name: str = None):
    """Mostra recursos detalhados de um container específico ou todos"""
    if container_name:
        # Mostrar recursos de um container específico
        if not docker_client:
            await ctx.send("❌ Cliente Docker não disponível")
            return
        
        try:
            container = docker_client.containers.get(container_name)
            stats = get_container_stats(container)
            
            embed = discord.Embed(
                title=f"📈 Recursos - {container_name}",
                color=discord.Color.green() if container.status == 'running' else discord.Color.red()
            )
            
            embed.add_field(name="Status", value=container.status.upper(), inline=True)
            embed.add_field(name="CPU", value=f"{stats['cpu_percent']}%", inline=True)
            embed.add_field(name="RAM", value=f"{stats['memory_usage_mb']} MB", inline=True)
            embed.add_field(name="RAM %", value=f"{stats['memory_percent']:.1f}%", inline=True)
            embed.add_field(name="Limit RAM", value=f"{stats['memory_limit_mb']} MB", inline=True)
            embed.add_field(name="Rede RX", value=f"{stats['network_rx_mb']} MB", inline=True)
            embed.add_field(name="Rede TX", value=f"{stats['network_tx_mb']} MB", inline=True)
            
            embed.set_footer(text=f"Atualizado em {datetime.now().strftime('%H:%M:%S')}")
            
            await ctx.send(embed=embed)
            
        except docker.errors.NotFound:
            await ctx.send(f"❌ Container `{container_name}` não encontrado")
        except Exception as e:
            await ctx.send(f"❌ Erro: {str(e)}")
    else:
        # Mostrar resumo de recursos de todos os containers
        await ctx.send("📊 Coletando estatísticas...")
        
        containers = get_detailed_container_info()
        
        if isinstance(containers, str):
            await ctx.send(containers)
            return
        
        running_containers = [c for c in containers if c['status'] == 'running']
        
        if not running_containers:
            await ctx.send("🔭 Nenhum container rodando para mostrar recursos")
            return
        
        # Calcular totais
        total_cpu = sum(c['stats']['cpu_percent'] for c in running_containers)
        total_ram_mb = sum(c['stats']['memory_usage_mb'] for c in running_containers)
        
        embed = discord.Embed(title="📈 Recursos dos Containers", color=discord.Color.blue())
        
        resources_text = ""
        for container in sorted(running_containers, key=lambda x: x['stats']['cpu_percent'], reverse=True):
            stats = container['stats']
            resources_text += f"🔹 **{container['name']}**\n"
            resources_text += f"   CPU: {stats['cpu_percent']}% | RAM: {stats['memory_usage_mb']}MB ({stats['memory_percent']:.1f}%)\n"
        
        embed.add_field(name="Por Container", value=resources_text, inline=False)
        embed.add_field(name="Total", value=f"CPU: {total_cpu:.1f}% | RAM: {total_ram_mb:.0f} MB", inline=False)
        
        await ctx.send(embed=embed)

@bot.command(name='top')
async def top_resources(ctx, limit: int = 5):
    """Mostra os containers que mais consomem recursos"""
    await ctx.send("🔍 Analisando consumo de recursos...")
    
    containers = get_detailed_container_info()
    
    if isinstance(containers, str):
        await ctx.send(containers)
        return
    
    running_containers = [c for c in containers if c['status'] == 'running']
    
    if not running_containers:
        await ctx.send("🔭 Nenhum container rodando")
        return
    
    # Ordenar por CPU
    top_cpu = sorted(running_containers, key=lambda x: x['stats']['cpu_percent'], reverse=True)[:limit]
    # Ordenar por RAM
    top_ram = sorted(running_containers, key=lambda x: x['stats']['memory_usage_mb'], reverse=True)[:limit]
    
    embed = discord.Embed(title="🏆 Top Consumidores de Recursos", color=discord.Color.orange())
    
    cpu_text = ""
    for i, container in enumerate(top_cpu, 1):
        cpu_text += f"{i}. **{container['name']}** - {container['stats']['cpu_percent']}%\n"
    embed.add_field(name="🔥 CPU", value=cpu_text, inline=True)
    
    ram_text = ""
    for i, container in enumerate(top_ram, 1):
        ram_text += f"{i}. **{container['name']}** - {container['stats']['memory_usage_mb']} MB\n"
    embed.add_field(name="🧠 RAM", value=ram_text, inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='system', aliases=['host'])
async def system_info(ctx):
    """Mostra informações do sistema host"""
    await ctx.send("🖥️ Coletando informações do sistema...")
    
    try:
        system_stats = get_system_stats()
        
        if 'error' in system_stats:
            await ctx.send(f"❌ Erro ao obter stats do sistema: {system_stats['error']}")
            return
        
        memory = system_stats['memory']
        disk = system_stats['disk']
        uptime_hours = system_stats['uptime'] / 3600
        
        embed = discord.Embed(title="🖥️ Sistema Host", color=discord.Color.purple())
        
        embed.add_field(name="CPU", value=f"{system_stats['cpu_percent']}%", inline=True)
        embed.add_field(name="RAM", value=f"{bytes_to_gb(memory.used):.1f} GB / {bytes_to_gb(memory.total):.1f} GB ({memory.percent}%)", inline=True)
        embed.add_field(name="Disco", value=f"{bytes_to_gb(disk.used):.1f} GB / {bytes_to_gb(disk.total):.1f} GB ({disk.percent}%)", inline=True)
        embed.add_field(name="Uptime", value=f"{uptime_hours:.1f} horas", inline=True)
        embed.add_field(name="RAM Livre", value=f"{bytes_to_gb(memory.available):.1f} GB", inline=True)
        embed.add_field(name="Disco Livre", value=f"{bytes_to_gb(disk.free):.1f} GB", inline=True)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Erro ao obter informações do sistema: {str(e)}")

# ======= COMANDOS DE IA APRIMORADOS =======

@bot.command(name='ask', aliases=['ai', 'chat'])
async def ask_ai(ctx, *, question: str = None):
    """Faz uma pergunta para a IA com contexto dos containers"""
    if not groq_client:
        await ctx.send("❌ Cliente Groq não disponível. Verifique a API key.")
        return
    
    if not question:
        await ctx.send("❌ Faça uma pergunta: `!ask sua pergunta aqui`")
        return
    
    async with ctx.typing():
        # Obter contexto dos containers se a pergunta mencionar containers/recursos
        context = ""
        keywords = ['container', 'docker', 'cpu', 'ram', 'memoria', 'recurso', 'performance']
        
        if any(keyword in question.lower() for keyword in keywords):
            containers = get_detailed_container_info()
            if not isinstance(containers, str) and containers:
                context = f"\n\nContexto atual dos containers:\n{json.dumps(containers, indent=2, default=str)}"
        
        messages = [
            {
                "role": "system", 
                "content": f"Você é um assistente especializado em Docker, containers e monitoramento de sistemas. Responda de forma técnica mas acessível.{context}"
            },
            {
                "role": "user", 
                "content": question
            }
        ]
        
        response = await groq_client.chat_completion(messages, max_tokens=1500)
        
        # Dividir resposta se muito longa
        if len(response) > 2000:
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(response)

@bot.command(name='analyze')
async def analyze_system(ctx):
    """Análise completa do sistema com recursos"""
    if not groq_client:
        await ctx.send("❌ Cliente Groq não disponível. Verifique a API key.")
        return
    
    await ctx.send("🔍 Analisando sistema completo...")
    
    containers = get_detailed_container_info()
    system_stats = get_system_stats()
    
    if isinstance(containers, str):
        await ctx.send(containers)
        return
    
    async with ctx.typing():
        # Preparar dados para análise
        analysis_data = {
            "containers": containers,
            "system": system_stats,
            "summary": {
                "total_containers": len(containers),
                "running": len([c for c in containers if c['status'] == 'running']),
                "stopped": len([c for c in containers if c['status'] != 'running']),
                "total_cpu_usage": sum(c['stats']['cpu_percent'] for c in containers if c['status'] == 'running'),
                "total_ram_usage_mb": sum(c['stats']['memory_usage_mb'] for c in containers if c['status'] == 'running')
            }
        }
        
        messages = [
            {
                "role": "system",
                "content": "Você é um especialista em análise de performance de sistemas Docker. Analise os dados e forneça insights sobre performance, problemas potenciais e recomendações."
            },
            {
                "role": "user",
                "content": f"Analise este sistema Docker completo com recursos: {json.dumps(analysis_data, indent=2, default=str)}. Foque em performance, saúde dos containers e recomendações."
            }
        ]
        
        response = await groq_client.chat_completion(messages, max_tokens=2000)
        
        embed = discord.Embed(
            title="🔬 Análise Completa do Sistema",
            description=response,
            color=discord.Color.green() if analysis_data["summary"]["stopped"] == 0 else discord.Color.yellow(),
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name="Resumo Rápido",
            value=f"🏃 {analysis_data['summary']['running']} rodando | ⏹️ {analysis_data['summary']['stopped']} parados\n🔥 CPU total: {analysis_data['summary']['total_cpu_usage']:.1f}% | 🧠 RAM total: {analysis_data['summary']['total_ram_usage_mb']:.0f} MB",
            inline=False
        )
        
        await ctx.send(embed=embed)

# ======= OUTROS COMANDOS MANTIDOS =======

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

@bot.remove_command('help')
@bot.command(name='help')
async def custom_help(ctx):
    """Mostra todos os comandos disponíveis"""
    embed = discord.Embed(
        title="🤖 Homelab Monitor + AI - Comandos",
        description="Bot para monitorar containers Docker com IA e recursos detalhados",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📊 Monitoramento Básico",
        value="`!status` - Status geral dos containers\n`!up` - Containers rodando\n`!down` - Containers parados\n`!ping` - Testa conexão",
        inline=False
    )
    
    embed.add_field(
        name="📈 Monitoramento de Recursos",
        value="`!resources [container]` - CPU, RAM, rede detalhados\n`!res [container]` - Alias para resources\n`!stats [container]` - Alias para resources\n`!top [limite]` - Top consumidores de recursos\n`!system` - Informações do sistema host\n`!host` - Alias para system",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Controle",
        value="`!restart <nome>` - Reiniciar container específico",
        inline=False
    )
    
    embed.add_field(
        name="🧠 Inteligência Artificial",
        value="`!ask <pergunta>` - Perguntas com contexto dos containers\n`!ai <pergunta>` - Alias para ask\n`!chat <pergunta>` - Alias para ask\n`!explain <container>` - Explica o que faz um container\n`!analyze` - Análise completa do sistema",
        inline=False
    )
    
    embed.add_field(
        name="📖 Exemplos de Uso",
        value="`!resources plex` - Recursos do Plex\n`!top 3` - Top 3 consumidores\n`!ask por que o nginx está lento?`\n`!explain portainer`",
        inline=False
    )
    
    embed.set_footer(text="Use ! antes de cada comando • <obrigatório> [opcional]")
    
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

if __name__ == '__main__':
    if not TOKEN:
        print("❌ DISCORD_TOKEN não encontrado no arquivo .env")
        exit(1)
    
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY não encontrado - funcionalidades IA desabilitadas")
    
    print("🚀 Iniciando bot...")
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Token do Discord inválido")
    except Exception as e:
        print(f"❌ Erro ao iniciar bot: {e}")