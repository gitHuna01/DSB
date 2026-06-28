import discord
from discord import app_commands
from discord.ext import commands, tasks
import json
import os
import datetime

# --- 여기부터 웹 서버 설정 (Render 속이기용) ---
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "스크럼 봇이 무사히 살아있습니다!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()
# --- 여기까지 웹 서버 설정 ---


intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "scrum_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 데이터를 불러오는 중 오류 발생: {e}")
            return {}
    return {}

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"⚠️ 데이터를 저장하는 중 오류 발생: {e}")

scrum_data = load_data()

# ⏰ 매일 낮 12시 알림 스케줄러 설정
# 한국 시간(KST) 기준으로 낮 12시 0분 설정
KST = datetime.timezone(datetime.timedelta(hours=9))
target_time = datetime.time(hour=12, minute=0, tzinfo=KST)

@tasks.loop(time=target_time)
async def daily_reminder():
    # 🚨 여기에 아까 복사한 채널 ID 숫자를 넣어주세요! (따옴표 없이 숫자만)
    CHANNEL_ID = 1502690601802535086
    
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send("📢 팀원 여러분! 점심 식사 맛있게 하시고, 데일리 스크럼 내용(`/today`, `/to-do`)을 작성해 주세요!")

@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)}개의 슬래시 명령어 동기화 완료!")
    except Exception as e:
        print(f"❌ 명령어 동기화 실패: {e}")
    print(f"🤖 로그인 성공: {bot.user}")


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
    if not scrum_data:
        await interaction.response.send_message("📋 아직 등록된 데일리 스크럼이 없습니다.")
        return

    embed = discord.Embed(
        title="📋 팀원들의 데일리 스크럼 현황", 
        description="오늘도 파이팅입니다! 💪",
        color=0x3498db
    )
    
    for user_id, tasks in scrum_data.items():
        try:
            user = await bot.fetch_user(int(user_id))
            name = user.display_name
        except Exception:
            name = f"알 수 없는 유저({user_id})"
        
        todo_text = f"• {tasks['todo']}" if tasks.get('todo') else "• 등록된 일이 없습니다."
        today_text = f"• {tasks['today']}" if tasks.get('today') else "• 등록된 일이 없습니다."
        
        embed.add_field(
            name=f"👤 {name}",
            value=f"**[해야 할 일]**\n{todo_text}\n\n**[오늘 할 일]**\n{today_text}",
            inline=False
        )
        
    await interaction.response.send_message(embed=embed)


# 실행 부분: 가짜 웹사이트를 켜서 렌더를 안심시킨 뒤, 봇을 실행합니다.
keep_alive() 
token = os.environ.get("BOT_TOKEN")
bot.run(token)