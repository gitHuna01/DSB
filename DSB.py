import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import datetime
import requests
from flask import Flask
from threading import Thread

# --- 가짜 웹 서버 설정 (Render 유지용) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "스크럼 봇이 무사히 살아있습니다!"

def run():
    # 렌더 포트 설정 (기본값 10000)
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
# ----------------------------------------

# --- Firebase 실시간 데이터베이스 설정 ---
# 🚨 아래 주소를 본인의 파이어베이스 Realtime Database 주소로 반드시 변경하세요! 
# (끝에 /scrum_data.json 이 꼭 붙어있어야 합니다.)
FIREBASE_URL = "https://dailyscrumbot-110a2-default-rtdb.firebaseio.com/scrum_data.json"

def load_data():
    try:
        response = requests.get(FIREBASE_URL)
        if response.status_code == 200:
            data = response.json()
            return data if data else {}
    except Exception as e:
        print(f"⚠️ Firebase 불러오기 오류: {e}")
    return {}

def save_data(data):
    try:
        requests.put(FIREBASE_URL, json=data)
    except Exception as e:
        print(f"⚠️ Firebase 저장 오류: {e}")

scrum_data = load_data()
# -----------------------------------------

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- ⏰ 매일 낮 12시 스크럼 알림 스케줄러 ---
KST = datetime.timezone(datetime.timedelta(hours=9))
target_time = datetime.time(hour=12, minute=0, tzinfo=KST)

@tasks.loop(time=target_time)
async def daily_reminder():
    # 🚨 아래 숫자를 봇이 알림을 보낼 디스코드 채널 ID로 반드시 변경하세요! (따옴표 없이 숫자만)
    CHANNEL_ID = 123456789012345678 
    
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("📢 팀원 여러분! 점심 식사 맛있게 하시고, 데일리 스크럼 내용(`/today`, `/to-do`)을 작성해 주세요!")
# ------------------------------------------

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)}개의 슬래시 명령어 동기화 완료!")
    except Exception as e:
        print(f"❌ 명령어 동기화 실패: {e}")
    
    # 봇이 켜질 때 스케줄러도 같이 시작합니다.
    if not daily_reminder.is_running():
        daily_reminder.start()
        
    print(f"🤖 로그인 성공: {bot.user}")


@bot.tree.command(name="to-do", description="앞으로 해야 할 일(전체 할 일)을 설정하거나 변경합니다.")
@app_commands.describe(task="변경할 할 일을 입력하세요.")
async def todo(interaction: discord.Interaction, task: str):
    user_id = str(interaction.user.id)
    
    if user_id not in scrum_data:
        scrum_data[user_id] = {'todo': '', 'today': ''}
    
    scrum_data[user_id]['todo'] = task
    save_data(scrum_data)  # 변경된 내용을 파이어베이스에 즉시 저장
    
    await interaction.response.send_message(f"📝 **{interaction.user.display_name}**님의 [해야 할 일]이 수정되었습니다: {task}")


@bot.tree.command(name="today", description="오늘 집중해서 할 일을 설정하거나 변경합니다.")
@app_commands.describe(task="오늘 할 일을 입력하세요.")
async def today(interaction: discord.Interaction, task: str):
    user_id = str(interaction.user.id)
    
    if user_id not in scrum_data:
        scrum_data[user_id] = {'todo': '', 'today': ''}
    
    scrum_data[user_id]['today'] = task
    save_data(scrum_data)  # 변경된 내용을 파이어베이스에 즉시 저장
    
    await interaction.response.send_message(f"🔥 **{interaction.user.display_name}**님의 [오늘 할 일]이 수정되었습니다: {task}")


@bot.tree.command(name="daily", description="모든 멤버의 데일리 스크럼 현황을 확인합니다.")
async def daily(interaction: discord.Interaction):
    # 조회할 때마다 파이어베이스에서 최신 데이터를 확실하게 가져옵니다.
    global scrum_data
    scrum_data = load_data()
    
    if not scrum_data:
        await interaction.response.send_message("📋 아직 등록된 데일리 스크럼이 없습니다.")
        return

    embed = discord.Embed(
        title="📋 팀원들의 데일리 스크럼 현황", 
        description="오늘도 파이팅입니다! 💪",
        color=0x3498db
    )
    
    for user_id, tasks_info in scrum_data.items():
        try:
            user = await bot.fetch_user(int(user_id))
            name = user.display_name
        except Exception:
            name = f"알 수 없는 유저({user_id})"
        
        todo_text = f"• {tasks_info['todo']}" if tasks_info.get('todo') else "• 등록된 일이 없습니다."
        today_text = f"• {tasks_info['today']}" if tasks_info.get('today') else "• 등록된 일이 없습니다."
        
        embed.add_field(
            name=f"👤 {name}",
            value=f"**[해야 할 일]**\n{todo_text}\n\n**[오늘 할 일]**\n{today_text}",
            inline=False
        )
        
    await interaction.response.send_message(embed=embed)


# --- 봇 실행 ---
keep_alive() 
token = os.environ.get("BOT_TOKEN")
bot.run(token)