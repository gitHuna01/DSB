import discord
from discord import app_commands
from discord.ext import commands
import json
import os

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
    
    # 처음 등록하는 유저라면 빈 문자열('')로 초기화합니다.
    if user_id not in scrum_data:
        scrum_data[user_id] = {'todo': '', 'today': ''}
    
    # .append() 대신 = 을 사용하여 새로운 내용으로 덮어씁니다.
    scrum_data[user_id]['todo'] = task
    save_data(scrum_data)
    
    await interaction.response.send_message(f"📝 **{interaction.user.display_name}**님의 [해야 할 일]이 수정되었습니다: {task}")


@bot.tree.command(name="today", description="오늘 집중해서 할 일을 설정하거나 변경합니다.")
@app_commands.describe(task="오늘 할 일을 입력하세요.")
async def today(interaction: discord.Interaction, task: str):
    user_id = str(interaction.user.id)
    
    if user_id not in scrum_data:
        scrum_data[user_id] = {'todo': '', 'today': ''}
    
    # 새로운 내용으로 덮어씁니다.
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
        
        # 리스트가 아니라 단일 문자열이므로 바로 출력합니다. 내용이 비어있을 때만 예외 처리합니다.
        todo_text = f"• {tasks['todo']}" if tasks.get('todo') else "• 등록된 일이 없습니다."
        today_text = f"• {tasks['today']}" if tasks.get('today') else "• 등록된 일이 없습니다."
        
        embed.add_field(
            name=f"👤 {name}",
            value=f"**[해야 할 일]**\n{todo_text}\n\n**[오늘 할 일]**\n{today_text}",
            inline=False
        )
        
    await interaction.response.send_message(embed=embed)


# 렌더(Render) 구동을 위한 환경 변수 토큰 불러오기 코드
token = os.environ.get("BOT_TOKEN")
bot.run(token)