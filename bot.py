import os
import discord
import docker
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# Configurações
TOKEN = os.getenv('DISCORD_TOKEN')

# Configurar intents
intents = discord.Intents.default()
intents.message_content = True

# Criar instância do bot
bot = commands.Bot(command_prefix='!', intents=intents)

# Cliente Docker - versão simples e funcional
print("🔧 Inicializando cliente Docker...")
try:
    docker_client = docker.from_env()
    docker_client.ping()
    print("✅ Cliente Docker conectado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao conectar Docker: {e}")
    docker_client = None

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
        result.append("🟢 **CONTAINERS RODANDO:** 🟢 ")
        for container in running:
            result.append(f"  • `{container['name']}` - {container['image']}")
    
    if stopped:
        result.append("\n🔴 **CONTAINERS PARADOS:**")
        for container in stopped:
            result.append(f"  • `{container['name']}` - {container['image']}")
    
    if others:
        result.append("\n🟡 **OUTROS STATUS:**")
        for container in others:
            result.append(f"  • `{container['name']}` - {container['status']}")
    
    # Adicionar resumo
    total = len(containers) if not filter_status else len(docker_client.containers.list(all=True))
    running_count = len(running)
    stopped_count = len(stopped)
    
    if not filter_status:
        result.insert(0, f"📊 **RESUMO:** {running_count} rodando, {stopped_count} parados, {total} total")
    
    return "\n".join(result)

@bot.command(name='status')
async def status(ctx):
    """Mostra o status de todos os containers"""
    await ctx.send("🔍 Verificando containers...")
    
    containers = get_container_info()
    message = format_container_status(containers)
    
    # Discord tem limite de 2000 caracteres por mensagem
    if len(message) > 1900:
        # Dividir mensagem se muito longa
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

@bot.command(name='count')
async def container_count(ctx):
    """Mostra contagem rápida dos containers"""
    containers = get_container_info()
    
    if isinstance(containers, str):
        await ctx.send(containers)
        return
    
    total = len(containers)
    running = len([c for c in containers if c['status'] == 'running'])
    stopped = len([c for c in containers if c['status'] in ['exited', 'stopped']])
    others = total - running - stopped
    
    embed = discord.Embed(
        title="📊 Resumo dos Containers",
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
    
    embed.add_field(name="🟢 Rodando", value=str(running), inline=True)
    embed.add_field(name="🔴 Parados", value=str(stopped), inline=True)
    embed.add_field(name="📦 Total", value=str(total), inline=True)
    
    if others > 0:
        embed.add_field(name="🟡 Outros", value=str(others), inline=True)
    
    await ctx.send(embed=embed)

@bot.command(name='ping')
async def ping(ctx):
    """Testa se o bot está respondendo"""
    docker_status = "❌ Indisponível"
    
    if docker_client:
        try:
            docker_client.ping()
            docker_status = "✅ Conectado"
        except Exception as e:
            docker_status = f"❌ Erro"
    
    embed = discord.Embed(title="🏓 Pong!", color=discord.Color.green())
    embed.add_field(name="Bot", value="✅ Online", inline=True)
    embed.add_field(name="Docker", value=docker_status, inline=True)
    embed.add_field(name="Latência", value=f"{round(bot.latency * 1000)}ms", inline=True)
    
    await ctx.send(embed=embed)

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

@bot.event
async def on_command_error(ctx, error):
    """Tratamento de erros"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando não encontrado. Use `!help` para ver os comandos disponíveis.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Argumento obrigatório faltando. Use `!help` para ver a sintaxe.")
    else:
        await ctx.send(f"❌ Erro: {str(error)}")
        print(f"Erro: {error}")

# Comando de ajuda customizado
@bot.remove_command('help')
@bot.command(name='help')
async def custom_help(ctx):
    """Mostra todos os comandos disponíveis"""
    embed = discord.Embed(
        title="🤖 Homelab Monitor - Comandos",
        description="Bot para monitorar containers Docker",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="📊 Monitoramento",
        value="`!status` - Todos os containers\n`!up` - Containers rodando\n`!down` - Containers parados\n`!count` - Resumo rápido",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Controle",
        value="`!restart <nome>` - Reiniciar container\n`!ping` - Testa conexão",
        inline=False
    )
    
    embed.add_field(
        name="❓ Ajuda",
        value="`!help` - Esta mensagem",
        inline=False
    )
    
    embed.set_footer(text="Use ! antes de cada comando • Exemplo: !restart portainer")
    
    await ctx.send(embed=embed)

if __name__ == '__main__':
    if not TOKEN:
        print("❌ DISCORD_TOKEN não encontrado no arquivo .env")
        exit(1)
    
    print("🚀 Iniciando bot...")
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ Token do Discord inválido")
    except Exception as e:
        print(f"❌ Erro ao iniciar bot: {e}")