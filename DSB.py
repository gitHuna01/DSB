import discord
from discord import app_commands
from discord.ext import commands
import json
import os

# 봇의 권한(Intents) 설정
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# 데이터가 저장될 JSON 파일 이름
DATA_FILE = "scrum_data.json"

# 1. 파일에서 기존 스크럼 데이터를 불러오는 함수
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ 데이터를 불러오는 중 오류 발생: {e}")
            return {}
    return {}

# 2. 데이터를 파일에 저장하는 함수
def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            # 한글이 깨지지 않도록 ensure_ascii=False 설정
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"⚠️ 데이터를 저장하는 중 오류 발생: {e}")

# 실행 시점에 데이터 로드
scrum_data = load_data()


@bot.event
async def on_ready():
    # 서버에 슬래시 명령어를 동기화 (등록)
    try:
        synced = await bot.tree.sync()
        print(f"✅ {len(synced)}개의 슬래시 명령어 동기화 완료!")
    except Exception as e:
        print(f"❌ 명령어 동기화 실패: {e}")
    print(f"🤖 로그인 성공: {bot.user}")


@bot.tree.command(name="to-do", description="앞으로 해야 할 일(전체 할 일)을 추가합니다.")
@app_commands.describe(task="추가할 할 일을 입력하세요.")
async def todo(interaction: discord.Interaction, task: str):
    user_id = str(interaction.user.id)  # JSON 키는 반드시 문자열이어야 합니다.
    
    if user_id not in scrum_data:
        scrum_data[user_id] = {'todo': [], 'today': []}
    
    scrum_data[user_id]['todo'].append(task)
    save_data(scrum_data)  # 파일에 바로 저장
    
    await interaction.response.send_message(f"📝 **{interaction.user.display_name}**님의 [해야 할 일]이 추가되었습니다: {task}")


@bot.tree.command(name="today", description="오늘 집중해서 할 일을 추가합니다.")
@app_commands.describe(task="오늘 할 일을 입력하세요.")
async def today(interaction: discord.Interaction, task: str):
    user_id = str(interaction.user.id)
    
    if user_id not in scrum_data:
        scrum_data[user_id] = {'todo': [], 'today': []}
    
    scrum_data[user_id]['today'].append(task)
    save_data(scrum_data)  # 파일에 바로 저장
    
    await interaction.response.send_message(f"🔥 **{interaction.user.display_name}**님의 [오늘 할 일]이 추가되었습니다: {task}")


@bot.tree.command(name="daily", description="모든 멤버의 데일리 스크럼 현황을 확인합니다.")
async def daily(interaction: discord.Interaction):
    if not scrum_data:
        await interaction.response.send_message("📋 아직 등록된 데일리 스크럼이 없습니다.")
        return

    # 디스코드 임베드(Embed) 형태로 깔끔하게 출력
    embed = discord.Embed(
        title="📋 팀원들의 데일리 스크럼 현황", 
        description="오늘도 파이팅입니다! 💪",
        color=0x3498db
    )
    
    for user_id, tasks in scrum_data.items():
        try:
            # user_id로 서버에서 유저 정보 가져오기
            user = await bot.fetch_user(int(user_id))
            name = user.display_name
        except Exception:
            name = f"알 수 없는 유저({user_id})"
        
        # 목록 생성 (비어있으면 '없음' 처리)
        todo_list = "\n".join([f"• {t}" for t in tasks['todo']]) if tasks['todo'] else "• 등록된 일이 없습니다."
        today_list = "\n".join([f"• {t}" for t in tasks['today']]) if tasks['today'] else "• 등록된 일이 없습니다."
        
        embed.add_field(
            name=f"👤 {name}",
            value=f"**[해야 할 일]**\n{todo_list}\n\n**[오늘 할 일]**\n{today_list}",
            inline=False  # 한 줄에 하나씩 배치하여 가독성 높임
        )
        
    await interaction.response.send_message(embed=embed)


# ⚠️ 주의: 토큰은 절대 외부에 노출되면 안 됩니다!
# 디스코드 개발자 포털에서 발급받은 본인의 봇 토큰을 아래에 입력하세요.
bot.run("BOT_TOKEN")