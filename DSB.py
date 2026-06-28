import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import datetime
import requests
from aiohttp import web  # 🚨 Flask 대신 사용하는 아주 가벼운 부품입니다!

# --- Firebase 실시간 데이터베이스 설정 ---
FIREBASE_URL = "https://dailyscrumbot-110a2-default-rtdb.firebaseio.com/scrum_data.json"

def load_data():
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200:
            data = response.json()
            return data if data else {}
    except Exception as e:
        pass
    return {}

def save_data(data):
    try:
        requests.put(FIREBASE_URL, json=data)
    except Exception as e:
        pass

scrum_data = load_data()

# --- 디스코드 봇 기본 설정 ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- ⏰ 매일 낮 12시 알림 스케줄러 ---
KST = datetime.timezone(datetime.timedelta(hours=9))
target_time = datetime.time(hour=12, minute=0, tzinfo=KST)

@tasks.loop(time=target_time)
async def daily_reminder():
    # 🚨 알림을 보낼 디스코드 채널 ID 입력 (숫자만)
    CHANNEL_ID = 123456789012345678 
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("📢 팀원 여러분! 점심 식사 맛있게 하시고, 데일리 스크럼 내용(`/today`, `/to-do`)을 작성해 주세요!")

# --- 🌐 가짜 웹 서버 (디스코드 봇과 충돌 안 함!) ---
async def handle(request):
    return web.Response(text="봇이 쾌적하게 작동 중입니다!")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

@bot.event
async def setup_hook():
    # 봇이 준비될 때 웹 서버와 알람을 충돌 없이 안전하게 켭니다.
    await start_web_server()
    if not daily_reminder.is_running():
        daily_reminder.start()

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)}개의 명령어 동기화 완료!")
    except Exception as e:
        print(f"❌ 동기화 실패: {e}")
    print(f"🤖 로그인 성공: {bot.user}")


# --- 명령어 설정 ---
@bot.tree.command(name="to-do", description="앞으로 해야 할 일(전체 할 일)을 설정하거나 변경합니다.")
@app_commands.describe(task="변경할 할 일을 입력하세요.")
async def todo(interaction: discord.Interaction, task: str):
    user_id = str(interaction.user.id)
    if user_id not in scrum_data:
        scrum_data[user_id] = {'todo': '', 'today': ''}
    
    scrum_data[user_id]['todo'] = task
    save_data(scrum_data)
    await interaction.response.send_message(f"📝 **{interaction.user.display_name}**님의 [해야 할 일]이 수정되었습니다: {task}")

@bot.tree.command(name="today", description="오늘 집중해서 할 일을 설정하거나 변경합니다.")
@app_commands.describe(task="오늘 할 일을 입력하세요.")
async def today(interaction: discord.Interaction, task: str):
    user_id = str(interaction.user.id)
    if user_id not in scrum_data:
        scrum_data[user_id] = {'todo': '', 'today': ''}
    
    scrum_data[user_id]['today'] = task
    save_data(scrum_data)
    await interaction.response.send_message(f"🔥 **{interaction.user.display_name}**님의 [오늘 할 일]이 수정되었습니다: {task}")

@bot.tree.command(name="daily", description="모든 멤버의 데일리 스크럼 현황을 확인합니다.")
async def daily(interaction: discord.Interaction):
    global scrum_data
    scrum_data = load_data()
    
    if not scrum_data:
        await interaction.response.send_message("📋 아직 등록된 데일리 스크럼이 없습니다.")
        return

    embed = discord.Embed(title="📋 팀원들의 데일리 스크럼 현황", description="오늘도 파이팅입니다! 💪", color=0x3498db)
    
    for user_id, tasks_info in scrum_data.items():
        try:
            user = await bot.fetch_user(int(user_id))
            name = user.display_name
        except Exception:
            name = f"알 수 없는 유저({user_id})"
        
        todo_text = f"• {tasks_info['todo']}" if tasks_info.get('todo') else "• 등록된 일이 없습니다."
        today_text = f"• {tasks_info['today']}" if tasks_info.get('today') else "• 등록된 일이 없습니다."
        
        embed.add_field(name=f"👤 {name}", value=f"**[해야 할 일]**\n{todo_text}\n\n**[오늘 할 일]**\n{today_text}", inline=False)
        
    await interaction.response.send_message(embed=embed)

token = os.environ.get("BOT_TOKEN")
bot.run(token)