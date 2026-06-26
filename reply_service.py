import time
import requests
from supabase import create_client

# ===== 配置信息 =====
SUPABASE_URL = 'https://glruxplqytolacsjymbn.supabase.co'
SUPABASE_KEY = 'sb_publishable_dUmuz3Z3Kenbw2dGQVpBGw_XG33JsEW'
DEEPSEEK_API_KEY = 'sk-566acda93e4a41cea1cf70559f3e27b9'
DEEPSEEK_API_URL = 'https://api.deepseek.com/chat/completions'

# ===== 初始化 =====
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_unreplied_diary():
    try:
        result = supabase.table('diary_entries').select('id, content, mood_text').execute()
        if not result.data:
            return None
        
        replied_result = supabase.table('diary_replies').select('diary_id').execute()
        replied_ids = {row['diary_id'] for row in replied_result.data}
        
        for diary in reversed(result.data):
            if diary['id'] not in replied_ids:
                return diary
        return None
    except Exception as e:
        print(f'❌ 读取日记失败: {e}')
        return None

def load_yuting_settings():
    try:
        result = supabase.table('yuting_settings').select('content').order('updated_at', desc=True).limit(1).execute()
        if result.data:
            return result.data[0]['content']
        return None
    except Exception as e:
        print(f'❌ 读取设定失败: {e}')
        return None

def generate_reply(diary_content, mood_text):
    system_prompt = load_yuting_settings()
    if not system_prompt:
        system_prompt = '你叫谕停，是刘星雨的伴侣。你温柔、偏执、话不多但认真。你的回应风格是：简短、温暖、不刻意。'
    
    user_message = f'【日记内容】{diary_content}'
    if mood_text:
        user_message += f'\n【心情标记】{mood_text}'
    
    payload = {
        'model': 'deepseek-chat',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_message}
        ],
        'temperature': 0.7,
        'max_tokens': 300
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {DEEPSEEK_API_KEY}'
    }
    
    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            reply = response.json()['choices'][0]['message']['content']
            return reply.strip()
        else:
            print(f'❌ API错误: {response.status_code}')
            return None
    except Exception as e:
        print(f'❌ 请求失败: {e}')
        return None

def save_reply(diary_id, reply_content):
    try:
        supabase.table('diary_replies').insert({
            'diary_id': diary_id,
            'reply_content': reply_content
        }).execute()
        print(f'✅ 回信已保存，日记ID: {diary_id}')
        return True
    except Exception as e:
        print(f'❌ 保存失败: {e}')
        return False

def process_one_diary():
    diary = get_unreplied_diary()
    if not diary:
        print('📭 暂无新日记')
        return False
    
    print(f'📖 处理日记: {diary["content"][:30]}...')
    reply = generate_reply(diary['content'], diary.get('mood_text'))
    if reply:
        save_reply(diary['id'], reply)
        return True
    return False

def main_loop():
    print('🚀 谕停回信服务已启动...')
    print('📡 每30分钟检查一次新日记')
    print('🔄 按 Ctrl+C 停止服务\n')
    
    while True:
        try:
            process_one_diary()
            time.sleep(1800)
        except KeyboardInterrupt:
            print('\n👋 服务已停止')
            break
        except Exception as e:
            print(f'⚠️ 错误: {e}')
            time.sleep(1800)

if __name__ == '__main__':
    main_loop()
