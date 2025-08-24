import os
import discord
import docker
from discord.ext import commands, tasks
from dotenv import load_dotenv
import asyncio
from datetime import datetime, timedelta
import aiohttp
import json
import psutil
import time
import logging
from typing import Dict, List, Optional, Set

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
TOKEN = os.getenv('DISCORD_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
DEPLOY_CHANNEL_ID = int(os.getenv('DEPLOY_CHANNEL_ID', 0))  # ID do canal para notificações de deploy

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

class ContainerState:
    """Classe para armazenar estado dos containers"""
    def __init__(self):
        self.containers: Dict[str, dict] = {}
        self.last_update = datetime.now()
    
    def update_container(self, container_id: str, container_info: dict):
        """Atualiza informações de um container"""
        self.containers[container_id] = container_info
        self.last_update = datetime.now()
    
    def remove_container(self, container_id: str):
        """Remove um container do estado"""
        if container_id in self.containers:
            del self.containers[container_id]
            self.last_update = datetime.now()
    
    def get_container_changes(self, new_containers: Dict[str, dict]) -> Dict[str, List]:
        """Detecta mudanças nos containers"""
        changes = {
            'created': [],
            'removed': [],
            'restarted': [],
            'status_changed': []
        }
        
        current_ids = set(self.containers.keys())
        new_ids = set(new_containers.keys())
        
        # Containers criados
        for container_id in new_ids - current_ids:
            changes['created'].append(new_containers[container_id])
        
        # Containers removidos
        for container_id in current_ids - new_ids:
            changes['removed'].append(self.containers[container_id])
        
        # Containers com mudanças de estado
        for container_id in current_ids & new_ids:
            old_info = self.containers[container_id]
            new_info = new_containers[container_id]
            
            # Verificar se foi reiniciado (comparar timestamps de criação)
            old_started = old_info.get('started_at')
            new_started = new_info.get('started_at')
            
            if old_started != new_started and new_info['status'] == 'running':
                changes['restarted'].append(new_info)
            
            # Verificar mudança de status
            elif old_info['status'] != new_info['status']:
                changes['status_changed'].append({
                    'container': new_info,
                    'old_status': old_info['status'],
                    'new_status': new_info['status']
                })
        
        return changes

# Estado global dos containers
container_state = ContainerState()

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

def get_container_info(container) -> dict:
    """Obtém informações básicas de um container"""
    try:
        attrs = container.attrs
        return {
            'id': container.id[:12],
            'name': container.name,
            'image': container.image.tags[0] if container.image.tags else attrs['Config']['Image'],
            'status': container.status,
            'created_at': attrs['Created'],
            'started_at': attrs['State'].get('StartedAt', ''),
            'ports': attrs['NetworkSettings'].get('Ports', {}),
            'labels': attrs['Config'].get('Labels', {}),
            'full_id': container.id
        }
    except Exception as e:
        logger.error(f"Erro ao obter info do container {container.name}: {e}")
        return {}

def get_all_containers_info() -> Dict[str, dict]:
    """Obtém informações de todos os containers"""
    if not docker_client:
        return {}
    
    try:
        containers = docker_client.containers.list(all=True)
        containers_info = {}
        
        for container in containers:
            info = get_container_info(container)
            if info:
                containers_info[container.id] = info
        
        return containers_info
    except Exception as e:
        logger.error(f"Erro ao obter containers: {e}")
        return {}

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
        logger.error(f"Erro ao obter stats do container {container.name}: {e}")
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

async def send_deploy_notification(channel, changes: Dict[str, List]):
    """Envia notificação de deploy para o canal especificado"""
    if not channel:
        return
    
    embeds = []
    
    # Containers criados
    if changes['created']:
        embed = discord.Embed(
            title="🚀 Novos Containers Implantados",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        for container in changes['created']:
            ports_info = ""
            if container.get('ports'):
                ports = []
                for port, bindings in container['ports'].items():
                    if bindings:
                        for binding in bindings:
                            ports.append(f"{binding['HostPort']}:{port}")
                if ports:
                    ports_info = f"\nPortas: {', '.join(ports)}"
            
            embed.add_field(
                name=f"📦 {container['name']}",
                value=f"Imagem: `{container['image']}`\nStatus: {container['status']}{ports_info}",
                inline=False
            )
        
        embeds.append(embed)
    
    # Containers removidos
    if changes['removed']:
        embed = discord.Embed(
            title="🗑️ Containers Removidos",
            color=discord.Color.red(),
            timestamp=datetime.now()
        )
        
        for container in changes['removed']:
            embed.add_field(
                name=f"📦 {container['name']}",
                value=f"Imagem: `{container['image']}`\nID: `{container['id']}`",
                inline=False
            )
        
        embeds.append(embed)
    
    # Containers reiniciados
    if changes['restarted']:
        embed = discord.Embed(
            title="🔄 Containers Reiniciados",
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        
        for container in changes['restarted']:
            embed.add_field(
                name=f"📦 {container['name']}",
                value=f"Imagem: `{container['image']}`\nStatus: {container['status']}",
                inline=False
            )
        
        embeds.append(embed)
    
    # Mudanças de status
    if changes['status_changed']:
        embed = discord.Embed(
            title="⚡ Mudanças de Status",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        for change in changes['status_changed']:
            container = change['container']
            status_emoji = "✅" if change['new_status'] == 'running' else "❌"
            
            embed.add_field(
                name=f"{status_emoji} {container['name']}",
                value=f"Status: `{change['old_status']}` → `{change['new_status']}`\nImagem: `{container['image']}`",
                inline=False
            )
        
        embeds.append(embed)
    
    # Enviar embeds
    for embed in embeds:
        try:
            await channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Erro ao enviar notificação: {e}")

@tasks.loop(seconds=30)
async def monitor_containers():
    """Task que monitora mudanças nos containers"""
    global container_state
    
    if not docker_client:
        return
    
    try:
        current_containers = get_all_containers_info()
        changes = container_state.get_container_changes(current_containers)
        
        # Se há mudanças, enviar notificações
        if any(changes.values()):
            deploy_channel = bot.get_channel(DEPLOY_CHANNEL_ID) if DEPLOY_CHANNEL_ID else None
            
            if deploy_channel:
                await send_deploy_notification(deploy_channel, changes)
            
            logger.info(f"Mudanças detectadas: {sum(len(v) for v in changes.values())} alterações")
        
        # Atualizar estado
        for container_id, info in current_containers.items():
            container_state.update_container(container_id, info)
        
        # Remover containers que não existem mais
        for container_id in list(container_state.containers.keys()):
            if container_id not in current_containers:
                container_state.remove_container(container_id)
    
    except Exception as e:
        logger.error(f"Erro no monitoramento: {e}")

@monitor_containers.before_loop
async def before_monitor():
    """Aguarda o bot estar pronto antes de iniciar o monitoramento"""
    await bot.wait_until_ready()
    
    # Inicializar estado dos containers
    if docker_client:
        try:
            initial_containers = get_all_containers_info()
            for container_id, info in initial_containers.items():
                container_state.update_container(container_id, info)
            logger.info(f"Estado inicial: {len(initial_containers)} containers")
        except Exception as e:
            logger.error(f"Erro ao inicializar estado: {e}")

@bot.event
async def on_ready():
    print(f'🤖 Bot conectado como {bot.user}')
    
    # Testar conexão com Docker
    if docker_client:
        try:
            docker_client.ping()
            print('✅ Conexão com Docker confirmada!')
            
            # Iniciar monitoramento
            if not monitor_containers.is_running():
                monitor_containers.start()
                print('📡 Monitoramento de containers iniciado!')
        except Exception as e:
            print(f'❌ Erro na verificação do Docker: {e}')
    else:
        print('❌ Cliente Docker não disponível')
    
    # Verificar canal de deploy
    if DEPLOY_CHANNEL_ID:
        channel = bot.get_channel(DEPLOY_CHANNEL_ID)
        if channel:
            print(f'✅ Canal de deploy configurado: #{channel.name}')
        else:
            print(f'⚠️ Canal de deploy não encontrado (ID: {DEPLOY_CHANNEL_ID})')
    else:
        print('⚠️ Canal de deploy não configurado (DEPLOY_CHANNEL_ID)')

# ======= NOVOS COMANDOS DE MONITORAMENTO DE DEPLOY =======

@bot.command(name='deploy_status', aliases=['deploys'])
async def deploy_status(ctx):
    """Mostra status do monitoramento de deploy"""
    embed = discord.Embed(title="📡 Status do Monitoramento", color=discord.Color.blue())
    
    # Status do monitoramento
    monitor_status = "✅ Ativo" if monitor_containers.is_running() else "❌ Inativo"
    embed.add_field(name="Monitoramento", value=monitor_status, inline=True)
    
    # Canal de notificações
    if DEPLOY_CHANNEL_ID:
        channel = bot.get_channel(DEPLOY_CHANNEL_ID)
        channel_info = f"#{channel.name}" if channel else f"❌ Canal não encontrado (ID: {DEPLOY_CHANNEL_ID})"
    else:
        channel_info = "❌ Não configurado"
    embed.add_field(name="Canal de Notificações", value=channel_info, inline=True)
    
    # Estatísticas
    embed.add_field(name="Containers Monitorados", value=len(container_state.containers), inline=True)
    embed.add_field(name="Última Atualização", value=container_state.last_update.strftime("%H:%M:%S"), inline=True)
    
    # Docker status
    docker_status = "✅ Conectado" if docker_client else "❌ Desconectado"
    embed.add_field(name="Docker", value=docker_status, inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='recent_changes', aliases=['changes'])
async def recent_changes(ctx, minutes: int = 60):
    """Mostra mudanças recentes nos containers"""
    if not docker_client:
        await ctx.send("❌ Cliente Docker não disponível")
        return
    
    await ctx.send(f"🔍 Verificando mudanças dos últimos {minutes} minutos...")
    
    try:
        # Obter containers com filtro de tempo
        since_time = datetime.now() - timedelta(minutes=minutes)
        containers = docker_client.containers.list(all=True)
        
        recent_containers = []
        for container in containers:
            created_str = container.attrs['Created']
            created_time = datetime.fromisoformat(created_str.replace('Z', '+00:00')).replace(tzinfo=None)
            
            if created_time > since_time:
                recent_containers.append(get_container_info(container))
        
        if not recent_containers:
            await ctx.send(f"📭 Nenhuma mudança detectada nos últimos {minutes} minutos")
            return
        
        embed = discord.Embed(
            title=f"🕒 Mudanças dos Últimos {minutes} Minutos",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        
        for container in recent_containers:
            created_time = datetime.fromisoformat(container['created_at'].replace('Z', '+00:00')).replace(tzinfo=None)
            time_ago = datetime.now() - created_time
            
            embed.add_field(
                name=f"📦 {container['name']}",
                value=f"Status: {container['status']}\nImagem: `{container['image']}`\nCriado: {int(time_ago.total_seconds() / 60)} min atrás",
                inline=False
            )
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"❌ Erro ao verificar mudanças: {str(e)}")

@bot.command(name='set_deploy_channel')
async def set_deploy_channel(ctx, channel_id: int = None):
    """Define o canal para notificações de deploy (apenas administradores)"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Apenas administradores podem configurar o canal de deploy")
        return
    
    if channel_id is None:
        channel_id = ctx.channel.id
    
    channel = bot.get_channel(channel_id)
    if not channel:
        await ctx.send(f"❌ Canal com ID {channel_id} não encontrado")
        return
    
    # Aqui você deveria salvar o channel_id em um arquivo de configuração ou banco de dados
    # Por simplicidade, estou apenas informando como fazer
    await ctx.send(f"✅ Canal de deploy configurado para #{channel.name}\n"
                   f"💡 Adicione `DEPLOY_CHANNEL_ID={channel_id}` ao seu arquivo .env e reinicie o bot")

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
        value=f"✅ {len(running)} rodando | ℹ️ {len(stopped)} parados | 📦 {len(containers)} total",
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
        keywords = ['container', 'docker', 'cpu', 'ram', 'memoria', 'recurso', 'performance', 'deploy']
        
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
            value=f"🏃 {analysis_data['summary']['running']} rodando | ℹ️ {analysis_data['summary']['stopped']} parados\n🔥 CPU total: {analysis_data['summary']['total_cpu_usage']:.1f}% | 🧠 RAM total: {analysis_data['summary']['total_ram_usage_mb']:.0f} MB",
            inline=False
        )
        
        await ctx.send(embed=embed)

@bot.command(name='explain')
async def explain_container(ctx, container_name: str = None):
    """Explica o que faz um container específico usando IA"""
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
        container_info = get_container_info(container)
        stats = get_container_stats(container)
        
        async with ctx.typing():
            messages = [
                {
                    "role": "system",
                    "content": "Você é um especialista em Docker. Explique de forma didática o que faz um container baseado nas suas informações."
                },
                {
                    "role": "user",
                    "content": f"Explique o que faz este container: {json.dumps({**container_info, 'stats': stats}, indent=2, default=str)}"
                }
            ]
            
            response = await groq_client.chat_completion(messages, max_tokens=1000)
            
            embed = discord.Embed(
                title=f"🔍 Análise do Container: {container_name}",
                description=response,
                color=discord.Color.green() if container.status == 'running' else discord.Color.red(),
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="Status Atual",
                value=f"Status: {container.status}\nCPU: {stats['cpu_percent']}%\nRAM: {stats['memory_usage_mb']} MB",
                inline=False
            )
            
            await ctx.send(embed=embed)
            
    except docker.errors.NotFound:
        await ctx.send(f"❌ Container `{container_name}` não encontrado")
    except Exception as e:
        await ctx.send(f"❌ Erro: {str(e)}")

# ======= COMANDOS DE CONTROLE =======

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

@bot.command(name='start')
async def start_container(ctx, container_name: str = None):
    """Inicia um container específico"""
    if not container_name:
        await ctx.send("❌ Especifique o nome do container: `!start nome_do_container`")
        return
    
    if not docker_client:
        await ctx.send("❌ Cliente Docker não disponível")
        return
    
    try:
        container = docker_client.containers.get(container_name)
        
        if container.status == 'running':
            await ctx.send(f"ℹ️ Container `{container_name}` já está rodando")
            return
        
        await ctx.send(f"▶️ Iniciando container `{container_name}`...")
        container.start()
        await ctx.send(f"✅ Container `{container_name}` iniciado com sucesso!")
        
    except docker.errors.NotFound:
        await ctx.send(f"❌ Container `{container_name}` não encontrado")
    except Exception as e:
        await ctx.send(f"❌ Erro ao iniciar container: {str(e)}")

@bot.command(name='stop')
async def stop_container(ctx, container_name: str = None):
    """Para um container específico"""
    if not container_name:
        await ctx.send("❌ Especifique o nome do container: `!stop nome_do_container`")
        return
    
    if not docker_client:
        await ctx.send("❌ Cliente Docker não disponível")
        return
    
    try:
        container = docker_client.containers.get(container_name)
        
        if container.status != 'running':
            await ctx.send(f"ℹ️ Container `{container_name}` não está rodando")
            return
        
        await ctx.send(f"⏹️ Parando container `{container_name}`...")
        container.stop()
        await ctx.send(f"✅ Container `{container_name}` parado com sucesso!")
        
    except docker.errors.NotFound:
        await ctx.send(f"❌ Container `{container_name}` não encontrado")
    except Exception as e:
        await ctx.send(f"❌ Erro ao parar container: {str(e)}")

# ======= OUTROS COMANDOS =======

@bot.command(name='ping')
async def ping(ctx):
    """Testa se o bot está respondendo"""
    docker_status = "❌ Indisponível"
    groq_status = "❌ Indisponível"
    monitor_status = "❌ Inativo"
    
    if docker_client:
        try:
            docker_client.ping()
            docker_status = "✅ Conectado"
        except:
            docker_status = "❌ Erro"
    
    if groq_client:
        groq_status = "✅ Conectado"
    
    if monitor_containers.is_running():
        monitor_status = "✅ Ativo"
    
    embed = discord.Embed(title="🏓 Pong!", color=discord.Color.green())
    embed.add_field(name="Bot", value="✅ Online", inline=True)
    embed.add_field(name="Docker", value=docker_status, inline=True)
    embed.add_field(name="Groq AI", value=groq_status, inline=True)
    embed.add_field(name="Monitoramento", value=monitor_status, inline=True)
    embed.add_field(name="Latência", value=f"{round(bot.latency * 1000)}ms", inline=True)
    embed.add_field(name="Containers", value=len(container_state.containers), inline=True)
    
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
        value="`!status` - Status geral dos containers\n`!ping` - Testa conexão do bot\n`!system` / `!host` - Info do sistema host",
        inline=False
    )
    
    embed.add_field(
        name="📈 Monitoramento de Recursos",
        value="`!resources [container]` - CPU, RAM, rede detalhados\n`!res` / `!stats` - Aliases para resources\n`!top [limite]` - Top consumidores de recursos",
        inline=False
    )
    
    embed.add_field(
        name="🚀 Monitoramento de Deploy",
        value="`!deploy_status` - Status do monitoramento\n`!recent_changes [minutos]` - Mudanças recentes\n`!set_deploy_channel [id]` - Configurar canal (admin)",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Controle de Containers",
        value="`!start <nome>` - Iniciar container\n`!stop <nome>` - Parar container\n`!restart <nome>` - Reiniciar container",
        inline=False
    )
    
    embed.add_field(
        name="🧠 Inteligência Artificial",
        value="`!ask <pergunta>` - Perguntas com contexto\n`!ai` / `!chat` - Aliases para ask\n`!explain <container>` - Explica container\n`!analyze` - Análise completa do sistema",
        inline=False
    )
    
    embed.add_field(
        name="📖 Exemplos de Uso",
        value="`!resources nginx` - Recursos do nginx\n`!top 3` - Top 3 consumidores\n`!ask por que o postgres está lento?`\n`!recent_changes 30` - Mudanças dos últimos 30min",
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
        logger.error(f"Erro no comando: {error}")

# ======= COMANDO DE LIMPEZA =======

@bot.command(name='cleanup')
async def cleanup_containers(ctx):
    """Remove containers parados (apenas administradores)"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ Apenas administradores podem executar limpeza de containers")
        return
    
    if not docker_client:
        await ctx.send("❌ Cliente Docker não disponível")
        return
    
    try:
        # Confirmar ação
        embed = discord.Embed(
            title="⚠️ Confirmação de Limpeza",
            description="Isso removerá TODOS os containers parados. Tem certeza?",
            color=discord.Color.orange()
        )
        
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")
        
        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id
        
        try:
            reaction, user = await bot.wait_for("reaction_add", timeout=30.0, check=check)
            
            if str(reaction.emoji) == "❌":
                await ctx.send("❌ Limpeza cancelada")
                return
            
            # Executar limpeza
            await ctx.send("🧹 Executando limpeza...")
            result = docker_client.containers.prune()
            
            removed_count = len(result.get('ContainersDeleted', []))
            space_reclaimed = bytes_to_mb(result.get('SpaceReclaimed', 0))
            
            embed = discord.Embed(
                title="✅ Limpeza Concluída",
                color=discord.Color.green()
            )
            embed.add_field(name="Containers Removidos", value=removed_count, inline=True)
            embed.add_field(name="Espaço Liberado", value=f"{space_reclaimed} MB", inline=True)
            
            await ctx.send(embed=embed)
            
        except asyncio.TimeoutError:
            await ctx.send("⏰ Tempo esgotado. Limpeza cancelada.")
            
    except Exception as e:
        await ctx.send(f"❌ Erro durante limpeza: {str(e)}")

if __name__ == '__main__':
    if not TOKEN:
        print("❌ DISCORD_TOKEN não encontrado no arquivo .env")
        exit(1)
    
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY não encontrado - funcionalidades IA desabilitadas")
    
    if not DEPLOY_CHANNEL_ID:
        print("⚠️ DEPLOY_CHANNEL_ID não configurado - notificações de deploy desabilitadas")
    
    print("🚀 Iniciando bot...")
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Token do Discord inválido")
    except Exception as e:
        print(f"❌ Erro ao iniciar bot: {e}")