
import hashlib, json, os, re, tempfile
from datetime import datetime
from typing import Any, Dict, List, Optional
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
GEMINI_API_KEY=os.getenv('GEMINI_API_KEY','')
SUPABASE_URL=os.getenv('SUPABASE_URL','')
SUPABASE_KEY=os.getenv('SUPABASE_KEY','')
SUPABASE_SERVICE_ROLE_KEY=os.getenv('SUPABASE_SERVICE_ROLE_KEY','')
AUTH_SECRET=os.getenv('AUTH_SECRET','eumi-dev-secret-change-me')
SUPABASE_APP_KEY=SUPABASE_SERVICE_ROLE_KEY or SUPABASE_KEY
if not SUPABASE_URL or not SUPABASE_APP_KEY:
    st.error('⚠️ SUPABASE_URL과 SUPABASE_KEY를 Streamlit Secrets에 넣어주세요.')
    st.stop()
supabase=create_client(SUPABASE_URL, SUPABASE_APP_KEY)


def friendly_error_message(error: Exception) -> str:
    """개발자용 영어 오류를 사용자용 한글 안내로 바꿉니다."""
    msg = str(error)
    if "PGRST125" in msg or "Invalid path specified in request URL" in msg:
        return (
            "가족 연결 정보를 확인하는 중 문제가 생겼습니다. "
            "회원가입이 아직 안 되어 있다면 「처음 사용」 탭에서 먼저 가입해주세요. "
            "이미 가입한 번호라면 앱을 새로고침한 뒤 다시 시도해주세요."
        )
    if "JWT" in msg or "permission" in msg.lower() or "permission denied" in msg.lower():
        return "권한 설정을 확인해야 합니다. 관리자에게 알려주세요."
    if "relation" in msg.lower() and "does not exist" in msg.lower():
        return "데이터베이스 테이블이 아직 준비되지 않았습니다. 관리자에게 알려주세요."
    if "duplicate" in msg.lower() or "already" in msg.lower():
        return "이미 등록된 정보입니다."
    if "timeout" in msg.lower():
        return "응답 시간이 길어졌습니다. 잠시 후 다시 시도해주세요."
    if msg.strip():
        return msg
    return "알 수 없는 오류가 발생했습니다. 잠시 후 다시 시도해주세요."


def show_error(error: Exception, prefix: str = "") -> None:
    message = friendly_error_message(error)
    if prefix:
        st.error(f"{prefix}: {message}")
    else:
        st.error(message)



THEMES = {
    "parent": {
        "bg": "#FFF8F2",
        "primary": "#F05A28",
        "primary_dark": "#B63A16",
        "secondary": "#FFF0E7",
        "text": "#2A1A12",
        "muted": "#6B5C55",
        "badge": "#FF6B2C",
        "border": "#F0D8D0",
        "button2": "#FF9B5F",
        "button3": "#FFF1E6",
        "button3_text": "#3A2117",
    },
    "child": {
        "bg": "#F6FAFF",
        "primary": "#0A3D78",
        "primary_dark": "#062B55",
        "secondary": "#EAF4FF",
        "text": "#0F1C33",
        "muted": "#536273",
        "badge": "#0A3D78",
        "border": "#CFE0F2",
        "button2": "#2F7DB7",
        "button3": "#52B5BA",
        "button3_text": "#FFFFFF",
    },
}


def apply_style(title, sub, theme="parent", badge=""):
    t = THEMES.get(theme, THEMES["parent"])
    st.markdown(f'''
<style>
html, body, [class*="css"] {{ font-size:24px !important; }}
[data-testid="stAppViewContainer"], [data-testid="stHeader"] {{ background:{t["bg"]}; }}
[data-testid="stMarkdownContainer"], p, li, label, div {{ line-height:1.75; }}
.block-container {{ padding-top: 2rem; }}
.title-area {{ text-align:center; padding:1.35rem 0 1.15rem; }}
.app-badge {{ display:inline-block; background:{t["badge"]}; color:white; border-radius:999px; padding:.45rem 1.05rem; font-size:1.05rem; font-weight:900; margin-bottom:.8rem; }}
.title-main {{ font-size:4.0rem; font-weight:900; color:{t["primary"]}; line-height:1.12; }}
.title-sub {{ font-size:1.65rem; color:{t["muted"]}; margin-top:.7rem; line-height:1.65; }}
.hero-card {{ background:white; border:2px solid {t["border"]}; border-radius:26px; padding:1.45rem 1.6rem; margin:1rem 0 1.25rem; box-shadow:0 8px 24px rgba(0,0,0,.05); }}
.guide-card,.folder-card,.log-card,.metric-card {{ background:#fff; border:2px solid {t["border"]}; border-radius:18px; padding:1.2rem 1.4rem; margin:.9rem 0; font-size:1.28rem; line-height:1.9; }}
.guide-card {{ background:{t["secondary"]}; }}
.answer-card {{ background:#fff; border-left:10px solid {t["primary"]}; border-radius:0 22px 22px 0; padding:1.8rem 2rem; font-size:1.6rem; line-height:2; box-shadow:0 4px 20px rgba(0,0,0,.08); }}
.small-note {{ color:{t["muted"]}; font-size:1.15rem; }}
.big-action {{ background:{t["primary"]}; color:white; border-radius:18px; padding:1rem 1.15rem; margin:.75rem 0; font-size:1.38rem; font-weight:900; }}
.big-action.secondary {{ background:{t["button2"]}; }}
.big-action.light {{ background:{t["button3"]}; color:{t["button3_text"]}; border:1px solid {t["border"]}; }}
.stButton > button {{ background:{t["primary"]} !important; color:#fff !important; font-size:1.35rem !important; font-weight:800 !important; border-radius:16px !important; min-height:4rem !important; width:100% !important; border:0 !important; }}
.stButton > button:hover {{ background:{t["primary_dark"]} !important; }}
.stTextInput > div > input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {{ font-size:1.3rem !important; border-radius:14px !important; min-height:3.3rem !important; }}
label, .stTextInput label, .stTextArea label, .stSelectbox label {{ font-size:1.25rem !important; font-weight:700 !important; }}
button[data-baseweb="tab"] {{ font-size:1.25rem !important; font-weight:800 !important; }}
[data-testid="stFileUploader"] {{ background:#fff; border-radius:18px; padding:1.5rem; border:3px dashed {t["border"]}; }}
[data-testid="stFileUploader"] * {{ font-size:1.25rem !important; }}
</style>
<div class="title-area">
    {f'<div class="app-badge">{badge}</div>' if badge else ''}
    <div class="title-main">🔗 {title}</div>
    <div class="title-sub">{sub}</div>
</div>
''', unsafe_allow_html=True)

def install_clear_cache_shortcut_guard() -> None:
    """Ctrl+C 복사 시 Streamlit의 Clear caches 팝업이 뜨지 않도록 막습니다."""
    components.html(
        r"""
<script>
(function () {
  function install() {
    const win = window.parent;
    const doc = win.document;

    if (win.__eumiClearCacheGuardInstalledV3) return;
    win.__eumiClearCacheGuardInstalledV3 = true;

    function isCopyShortcut(event) {
      const key = (event.key || "").toLowerCase();
      return (event.ctrlKey || event.metaKey) && key === "c";
    }

    function blockCopyPropagation(event) {
      if (!isCopyShortcut(event)) return;
      event.stopImmediatePropagation();
    }

    ["keydown", "keypress", "keyup"].forEach(function (type) {
      doc.addEventListener(type, blockCopyPropagation, true);
      win.addEventListener(type, blockCopyPropagation, true);
    });

    function closeClearCacheDialog() {
      const nodes = Array.from(doc.querySelectorAll('[role="dialog"], [data-testid="stModal"], div'));
      for (const node of nodes) {
        const text = node.innerText || "";
        if (text.includes("Clear caches") && text.includes("function caches")) {
          const buttons = Array.from(node.querySelectorAll("button"));
          const cancel = buttons.find(function (btn) {
            return (btn.innerText || "").trim().toLowerCase() === "cancel";
          });
          const xButton = buttons.find(function (btn) {
            const t = (btn.innerText || "").trim();
            const aria = (btn.getAttribute("aria-label") || "").toLowerCase();
            return t === "×" || aria.includes("close");
          });
          if (cancel) cancel.click();
          else if (xButton) xButton.click();
          node.style.display = "none";
        }
      }
    }

    closeClearCacheDialog();
    setInterval(closeClearCacheDialog, 200);
  }

  try { install(); } catch (e) {}
})();
</script>
        """,
        height=0,
        width=0,
    )


def install_phone_input_guard():
    components.html(r'''
<script>
(function(){
function d(v){return (v||'').replace(/\D/g,'').slice(0,11)}
function f(v){const x=d(v); if(x.length<=3)return x; if(x.length<=7)return x.slice(0,3)+'-'+x.slice(3); return x.slice(0,3)+'-'+x.slice(3,7)+'-'+x.slice(7,11)}
function bind(){const doc=window.parent.document; doc.querySelectorAll('input[placeholder="010-0000-0000"]').forEach(function(i){
 if(i.dataset.eumiPhoneGuard==='1')return; i.dataset.eumiPhoneGuard='1'; i.setAttribute('inputmode','numeric'); i.setAttribute('maxlength','13');
 i.addEventListener('beforeinput',function(e){ if(e.inputType&&e.inputType.startsWith('delete'))return; if(e.ctrlKey||e.metaKey||e.altKey)return; const a=e.data||''; if(a&&/\D/.test(a))e.preventDefault(); if(a&&/\d/.test(a)&&d(i.value).length>=11)e.preventDefault(); });
 i.addEventListener('paste',function(e){e.preventDefault(); const p=(e.clipboardData||window.clipboardData).getData('text'); i.value=f(p); i.dispatchEvent(new Event('input',{bubbles:true})); i.dispatchEvent(new Event('change',{bubbles:true}));});
 i.addEventListener('input',function(){const y=f(i.value); if(i.value!==y){i.value=y; i.dispatchEvent(new Event('input',{bubbles:true}));}}); i.value=f(i.value);
});}
bind(); const t=setInterval(bind,500); setTimeout(function(){clearInterval(t)},10000);
})();
</script>
''', height=0, width=0)

def digits_only(v): return re.sub(r'\D','',v or '')[:11]
def format_phone(v):
    v=digits_only(v)
    if len(v)<=3: return v
    if len(v)<=7: return f'{v[:3]}-{v[3:]}'
    return f'{v[:3]}-{v[3:7]}-{v[7:11]}'
def normalize_phone_input(key):
    raw=st.session_state.get(key,''); val=format_phone(raw)
    if raw!=val: st.session_state[key]=val
def phone_input(label,key):
    val=st.text_input(label,key=key,placeholder='010-0000-0000',max_chars=13,help='숫자만 11자리까지 입력됩니다. - 는 자동으로 들어갑니다.',on_change=normalize_phone_input,args=(key,))
    return digits_only(val)
def hash_password(phone,pw): return hashlib.sha256(f'{AUTH_SECRET}:{phone}:{pw}'.encode()).hexdigest()

def create_user(phone,name,pw):
    if supabase.table('eumi_users').select('id').eq('phone',phone).limit(1).execute().data: raise ValueError('이미 가입된 휴대폰 번호입니다. 로그인해주세요.')
    res=supabase.table('eumi_users').insert({'phone':phone,'name':name.strip(),'password_hash':hash_password(phone,pw)}).execute()
    if not res.data: raise RuntimeError('계정을 만들지 못했습니다.')
    return res.data[0]
def login_user(phone,pw):
    res=supabase.table('eumi_users').select('*').eq('phone',phone).limit(1).execute()
    if not res.data: raise ValueError('아직 회원가입이 되어 있지 않은 번호입니다. 위의 「처음 사용」 탭에서 회원가입을 먼저 해주세요.')
    user=res.data[0]
    if user.get('password_hash')!=hash_password(phone,pw): raise ValueError('비밀번호가 틀렸습니다.')
    activate_pending_signup_links(user); return user

def get_user_by_phone(phone):
    res=supabase.table('eumi_users').select('*').eq('phone',phone).limit(1).execute()
    return res.data[0] if res.data else {}

def relation_input(prefix, opts):
    selected=st.selectbox('관계 선택',opts,key=f'{prefix}_relation')
    if selected=='기타': return st.text_input('관계명을 입력해주세요',key=f'{prefix}_relation_custom',placeholder='예: 장모님, 할머니, 보호자').strip()
    return selected

def upsert_family_link(caregiver_user_id,caree_user_id,caregiver_phone,caree_phone,relation_label,reverse_relation_label,requested_by_user_id,status):
    q=supabase.table('family_links').select('id')
    q=q.eq('caregiver_user_id',caregiver_user_id) if caregiver_user_id else q.eq('caregiver_phone',caregiver_phone)
    q=q.eq('caree_user_id',caree_user_id) if caree_user_id else q.eq('caree_phone',caree_phone)
    old=q.limit(1).execute().data
    payload={'caregiver_user_id':caregiver_user_id,'caree_user_id':caree_user_id,'caregiver_phone':caregiver_phone,'caree_phone':caree_phone,'relation_label':relation_label,'reverse_relation_label':reverse_relation_label,'requested_by_user_id':requested_by_user_id,'status':status,'updated_at':datetime.now().isoformat()}
    if old: supabase.table('family_links').update(payload).eq('id',old[0]['id']).execute()
    else: supabase.table('family_links').insert(payload).execute()

def activate_pending_signup_links(user):
    """가입 전 전화번호로 걸려 있던 가족 연결을 실제 사용자 ID와 연결합니다.

    기존 코드의 .is_('컬럼','null') 필터가 Streamlit/Supabase 환경에서
    PGRST125 Invalid path 오류를 만들 수 있어, status='pending_signup' 기준으로만
    안전하게 업데이트합니다.
    """
    try:
        now = datetime.now().isoformat()

        # 누군가 이 사용자를 '부모님'으로 추가해둔 경우:
        # 해당 사용자가 가입하면 승인 대기 상태로 바꿉니다.
        supabase.table('family_links').update({
            'caree_user_id': user['id'],
            'status': 'pending',
            'updated_at': now
        }).eq('caree_phone', user['phone']).eq('status', 'pending_signup').execute()

        # 이 사용자가 '자녀'로 등록되어 있었던 경우:
        # 부모가 먼저 자녀 번호를 등록한 것이므로 가입 시 자동 연결합니다.
        supabase.table('family_links').update({
            'caregiver_user_id': user['id'],
            'status': 'active',
            'updated_at': now
        }).eq('caregiver_phone', user['phone']).eq('status', 'pending_signup').execute()

    except Exception:
        # 로그인 자체를 막지 않기 위해 가족 연결 자동 업데이트 오류는 숨깁니다.
        pass

def add_parent_link(user,parent_phone,relation):
    if len(parent_phone)!=11: raise ValueError('부모님 휴대폰 번호 11자리를 입력해주세요.')
    if parent_phone==user.get('phone'): raise ValueError('본인 번호는 부모님으로 추가할 수 없습니다.')
    if not relation: raise ValueError('관계를 선택하거나 입력해주세요.')
    parent=get_user_by_phone(parent_phone)
    upsert_family_link(user['id'], parent.get('id') if parent else None, user['phone'], parent_phone, relation, '자녀', user['id'], 'pending' if parent else 'pending_signup')
    return '부모님께 연결 요청을 보냈습니다. 부모님이 앱에서 승인하면 기록을 볼 수 있어요.' if parent else '아직 가입하지 않은 번호입니다. 부모님이 이 번호로 가입하면 연결 요청이 표시됩니다.'
def add_child_link(user,child_phone,relation):
    if len(child_phone)!=11: raise ValueError('자녀 휴대폰 번호 11자리를 입력해주세요.')
    if child_phone==user.get('phone'): raise ValueError('본인 번호는 자녀로 추가할 수 없습니다.')
    if not relation: raise ValueError('관계를 선택하거나 입력해주세요.')
    child=get_user_by_phone(child_phone)
    upsert_family_link(child.get('id') if child else None, user['id'], child_phone, user['phone'], '부모님', relation, user['id'], 'active' if child else 'pending_signup')
    return '자녀를 연결했습니다. 이제 자녀가 내 기록을 볼 수 있습니다.' if child else '자녀 번호를 등록했습니다. 자녀가 이 번호로 가입하면 자동으로 연결됩니다.'
def load_pending_requests_for_me(uid): return supabase.table('family_links').select('*').eq('caree_user_id',uid).eq('status','pending').execute().data or []
def approve_link(lid): supabase.table('family_links').update({'status':'active','updated_at':datetime.now().isoformat()}).eq('id',lid).execute()
def reject_link(lid): supabase.table('family_links').update({'status':'rejected','updated_at':datetime.now().isoformat()}).eq('id',lid).execute()
def load_parents_i_help(uid): return supabase.table('family_links').select('*').eq('caregiver_user_id',uid).eq('status','active').order('created_at',desc=True).execute().data or []
def load_children_helping_me(uid): return supabase.table('family_links').select('*').eq('caree_user_id',uid).eq('status','active').order('created_at',desc=True).execute().data or []
def get_user_name(uid, fallback=''):
    if not uid: return format_phone(fallback) if fallback else '미가입 가족'
    res=supabase.table('eumi_users').select('name,phone').eq('id',uid).limit(1).execute()
    return (res.data[0].get('name') or format_phone(res.data[0].get('phone',''))) if res.data else (format_phone(fallback) if fallback else '가족')
def load_logs_for_user(uid):
    try: return supabase.table('usage_logs').select('*').eq('user_id',uid).order('created_at',desc=True).limit(500).execute().data or []
    except Exception as e: show_error(e, '사용 기록을 불러오지 못했습니다'); return []
def safe_dt(v):
    try: return datetime.fromisoformat((v or '').replace('Z','+00:00'))
    except Exception: return None

def show_log_summary(logs):
    if not logs: st.markdown("<div class='guide-card'>아직 저장된 기록이 없습니다.</div>",unsafe_allow_html=True); return
    counts={}
    for log in logs:
        label=f"{log.get('category') or '기타'} > {log.get('place_name') or '미분류'}"; counts[label]=counts.get(label,0)+1
    st.markdown('### 자주 어려워한 곳')
    for i,(label,count) in enumerate(sorted(counts.items(),key=lambda x:x[1],reverse=True)[:10],1): st.markdown(f"<div class='metric-card'><b>{i}. {label}</b><br>{count}회 질문</div>",unsafe_allow_html=True)
    st.markdown('### 장소별 기록')
    grouped={}
    for log in logs:
        label=f"{log.get('category') or '기타'} > {log.get('place_name') or '미분류'}"; grouped.setdefault(label,[]).append(log)
    for folder,items in grouped.items():
        with st.expander(f'📁 {folder} ({len(items)}회)',expanded=False):
            for log in items[:50]:
                dt=safe_dt(log.get('created_at','')); t=dt.strftime('%Y-%m-%d %H:%M') if dt else log.get('created_at','')
                q=log.get('question') or ''; a=log.get('answer') or ''; title=log.get('short_title') or log.get('task_name') or '질문 기록'
                st.markdown(f"<div class='log-card'><b>{title}</b><br><span class='small-note'>{t}</span><br><b>질문:</b> {q}<br><b>답변:</b> {a[:350]}{'...' if len(a)>350 else ''}</div>",unsafe_allow_html=True)

def norm(v,default):
    v=re.sub(r'\s+',' ',(v or '').strip())
    return v[:30] if v else default
def folder_key(c,p): return f"{norm(c,'기타')}__{norm(p,'미분류')}"
def safe_json_loads(text):
    cleaned=(text or '').strip(); cleaned=re.sub(r'^```(?:json)?','',cleaned).strip(); cleaned=re.sub(r'```$','',cleaned).strip(); m=re.search(r'\{.*\}',cleaned,flags=re.S)
    try: return json.loads(m.group(0) if m else cleaned)
    except Exception: return {}
def classify_and_answer(image,question,prev):
    if not GEMINI_API_KEY: raise RuntimeError('GEMINI_API_KEY가 설정되어 있지 않습니다.')
    try:
        from google import genai
    except Exception:
        raise RuntimeError('AI 분석 패키지(google-genai)가 설치되지 않았습니다. requirements.txt를 확인해주세요.')
    client=genai.Client(api_key=GEMINI_API_KEY); tmp_path=None
    try:
        with tempfile.NamedTemporaryFile(delete=False,suffix='.jpg') as tmp: image.convert('RGB').save(tmp.name,format='JPEG'); tmp_path=tmp.name
        up=client.files.upload(file=tmp_path)
        prev_text=''.join([f"이전 기록 {i}: {l.get('category')} > {l.get('place_name')}, {l.get('question')}, {(l.get('answer') or '')[:180]}\n" for i,l in enumerate(prev[:5],1)])
        prompt=f'''사용자 질문: {question}\n이전 기록:\n{prev_text}\n아래 JSON 형식으로만 답하세요.\n{{"category":"키오스크/병원 앱/은행 앱/기차/교통/배달/쇼핑/주민센터/공공/기타","place_name":"식당명 또는 앱명, 모르면 미분류","task_name":"하려는 일","short_title":"짧은 제목","answer":"어르신에게 쉬운 말로 다음 행동 안내. 비슷한 이전 기록이 있으면 짧게 언급"}}'''
        r=client.models.generate_content(model='gemini-2.5-flash',contents=[prompt,up],config={'system_instruction':'어르신에게 쉽고 짧게 안내하세요. 위치, 색깔, 버튼 이름을 구체적으로 말하세요.'})
        p=safe_json_loads(r.text)
        return {'category':norm(p.get('category',''),'기타'),'place_name':norm(p.get('place_name',''),'미분류'),'task_name':norm(p.get('task_name',''),'확인하기'),'short_title':norm(p.get('short_title',''),'화면 질문'),'answer':p.get('answer') or r.text or '답변을 만들지 못했습니다.'}
    finally:
        if tmp_path and os.path.exists(tmp_path): os.unlink(tmp_path)
def save_usage_log(uid,q,result,has_image=True):
    supabase.table('usage_logs').insert({'user_id':uid,'question':q,'answer':result.get('answer',''),'has_image':has_image,'category':result.get('category','기타'),'place_name':result.get('place_name','미분류'),'task_name':result.get('task_name','확인하기'),'short_title':result.get('short_title','화면 질문'),'folder_key':folder_key(result.get('category','기타'),result.get('place_name','미분류')),'created_at':datetime.now().isoformat()}).execute()
def show_auth(session_key, title='이음이', subtitle='사진으로 도움받고, 기록을 가족과 함께 확인하세요', theme='parent', badge=''):
    install_phone_input_guard(); install_clear_cache_shortcut_guard(); apply_style(title, subtitle, theme=theme, badge=badge)
    _,col,_=st.columns([.3,4.4,.3])
    with col:
        t1,t2=st.tabs(['🔐 로그인','📝 처음 사용'])
        with t1:
            st.markdown('### 로그인'); st.markdown("<div class='small-note'>처음 오신 분은 옆의 <b>처음 사용</b> 탭에서 회원가입을 먼저 해주세요.</div>", unsafe_allow_html=True); phone=phone_input('휴대폰 번호',f'{session_key}_login_phone'); pw=st.text_input('비밀번호',key=f'{session_key}_login_pw',placeholder='예: 123456')
            if st.button('로그인',key=f'{session_key}_login_submit'):
                try:
                    if len(phone)!=11: raise ValueError('휴대폰 번호 11자리를 입력해주세요.')
                    pw_clean=(st.session_state.get(f'{session_key}_login_pw') or pw or '').strip()
                    if not pw_clean: raise ValueError('비밀번호를 입력해주세요.')
                    st.session_state[session_key]=login_user(phone,pw_clean); st.rerun()
                except Exception as e: show_error(e)
        with t2:
            st.markdown('### 처음 사용하는 분'); st.markdown("<div class='small-note'>테스트 단계에서는 비밀번호가 보이게 입력됩니다. 숫자 6자리 예: 123456</div>", unsafe_allow_html=True); phone=phone_input('휴대폰 번호',f'{session_key}_join_phone'); name=st.text_input('이름',key=f'{session_key}_join_name'); pw=st.text_input('비밀번호',key=f'{session_key}_join_pw',placeholder='예: 123456'); pw2=st.text_input('비밀번호 확인',key=f'{session_key}_join_pw2',placeholder='같은 비밀번호를 다시 입력')
            if st.button('계정 만들기',key=f'{session_key}_join_submit'):
                try:
                    if len(phone)!=11: raise ValueError('휴대폰 번호 11자리를 입력해주세요.')
                    if not name.strip(): raise ValueError('이름을 입력해주세요.')
                    pw_clean=(st.session_state.get(f'{session_key}_join_pw') or pw or '').strip()
                    pw2_clean=(st.session_state.get(f'{session_key}_join_pw2') or pw2 or '').strip()
                    if not pw_clean: raise ValueError('비밀번호를 입력해주세요.')
                    if not pw2_clean: raise ValueError('비밀번호 확인을 입력해주세요.')
                    if pw_clean!=pw2_clean: raise ValueError('비밀번호가 일치하지 않아요.')
                    # 테스트 단계에서는 Streamlit 입력값 유실 오류를 막기 위해 길이 검사는 완화하고,
                    # 실제 운영 전 결제/문자인증 단계에서 6자리 이상 정책을 다시 강화합니다.
                    st.session_state[session_key]=create_user(phone,name,pw_clean); st.rerun()
                except Exception as e: show_error(e, '회원가입 실패')
def family_management_ui(user,prefix='family'):
    install_phone_input_guard(); st.markdown('### 가족 관리'); st.markdown("<div class='guide-card'><b>부모님</b>은 내가 도와드릴 가족입니다.<br><b>자녀</b>는 내 기록을 함께 볼 가족입니다.</div>",unsafe_allow_html=True)
    ptab,ctab,rtab=st.tabs(['👵 부모님','👨‍👩‍👧 자녀','✅ 연결 요청'])
    with ptab:
        st.markdown('#### 부모님 추가'); ph=phone_input('부모님 휴대폰 번호',f'{prefix}_parent_phone'); rel=relation_input(f'{prefix}_parent',['엄마','아빠','배우자','기타'])
        if st.button('부모님 연결 요청',key=f'{prefix}_add_parent'):
            try: st.success(add_parent_link(user,ph,rel)); st.rerun()
            except Exception as e: show_error(e)
        st.markdown('#### 내가 도와주는 부모님')
        links=load_parents_i_help(user['id'])
        if not links: st.info('아직 연결된 부모님이 없습니다.')
        for l in links: st.markdown(f"<div class='folder-card'>👵 <b>{l.get('relation_label') or '부모님'}</b> — {get_user_name(l.get('caree_user_id'),l.get('caree_phone',''))}</div>",unsafe_allow_html=True)
    with ctab:
        st.markdown('#### 자녀 추가'); ph=phone_input('자녀 휴대폰 번호',f'{prefix}_child_phone'); rel=relation_input(f'{prefix}_child',['아들','딸','배우자','기타'])
        if st.button('자녀 연결',key=f'{prefix}_add_child'):
            try: st.success(add_child_link(user,ph,rel)); st.rerun()
            except Exception as e: show_error(e)
        st.markdown('#### 나를 도와주는 자녀')
        links=load_children_helping_me(user['id'])
        if not links: st.info('아직 연결된 자녀가 없습니다.')
        for l in links: st.markdown(f"<div class='folder-card'>👨‍👩‍👧 <b>{l.get('reverse_relation_label') or '자녀'}</b> — {get_user_name(l.get('caregiver_user_id'),l.get('caregiver_phone',''))}</div>",unsafe_allow_html=True)
    with rtab:
        pending=load_pending_requests_for_me(user['id'])
        if not pending: st.info('승인할 요청이 없습니다.')
        for l in pending:
            st.markdown(f"<div class='folder-card'><b>{get_user_name(l.get('caregiver_user_id'),l.get('caregiver_phone',''))}</b>님이 내 기록 연결을 요청했습니다.<br>관계: {l.get('relation_label') or '가족'}</div>",unsafe_allow_html=True)
            a,b=st.columns(2)
            with a:
                if st.button('허용',key=f"approve_{l['id']}"): approve_link(l['id']); st.rerun()
            with b:
                if st.button('거절',key=f"reject_{l['id']}"): reject_link(l['id']); st.rerun()




def render_landing_preview(theme="parent"):
    """시안에 최대한 가깝게 보이는 부모용/자녀용 첫 화면 카드."""
    if theme == "child":
        css = """
<style>
.block-container{max-width:1180px!important;}
.eumi-main-card{background:linear-gradient(135deg,#FDFEFF 0%,#EEF7FF 56%,#DFF1FF 100%);border:2px solid #CFE0F2;border-radius:28px;padding:1.5rem 1.6rem;margin:1rem auto 1.4rem;box-shadow:0 18px 45px rgba(9,61,120,.12);position:relative;overflow:hidden;}
.eumi-main-card:before{content:"";position:absolute;width:260px;height:260px;right:-90px;bottom:-90px;border-radius:50%;background:rgba(255,255,255,.45)}
.eumi-main-grid{display:grid;grid-template-columns:1.28fr .82fr;gap:1.1rem;align-items:center;position:relative;z-index:1}
.eumi-badge{display:inline-flex;background:#0A3D78;color:#fff;border-radius:14px;padding:.35rem .75rem;font-size:1rem;font-weight:900;margin-bottom:.7rem}
.eumi-card-title{font-size:2.45rem;font-weight:900;color:#0A3D78;letter-spacing:-.04em;margin:.15rem 0 .3rem}
.eumi-headline{font-size:1.68rem;font-weight:900;color:#0F1C33;line-height:1.34;margin:.35rem 0}.eumi-copy{font-size:1.05rem;color:#536273;font-weight:650;line-height:1.65;margin:.3rem 0 1rem}.eumi-ill{background:#DCEFFF;border-radius:26px;min-height:215px;display:flex;align-items:center;justify-content:center;font-size:4.2rem}.eumi-note{text-align:center;color:#536273;font-size:1.02rem;font-weight:800;margin-top:.45rem}.eumi-action{display:flex;align-items:center;justify-content:space-between;border-radius:18px;padding:.82rem 1rem;margin:.62rem 0;font-size:1.25rem;font-weight:900;color:#fff;box-shadow:0 8px 18px rgba(0,0,0,.10)}.eumi-action .left{display:flex;gap:.75rem;align-items:center}.eumi-action .ico{width:2.4rem;height:2.4rem;display:flex;align-items:center;justify-content:center;border-radius:13px;background:rgba(255,255,255,.23)}.eumi-action.one{background:#0A3D78}.eumi-action.two{background:#2F7DB7}.eumi-action.three{background:#52B5BA}.eumi-arrow{font-size:1.8rem}@media(max-width:900px){.eumi-main-grid{grid-template-columns:1fr}.eumi-ill{min-height:130px;font-size:3rem}.eumi-card-title{font-size:2rem}}
</style>
"""
        html = css + """
<div class='eumi-main-card'>
  <div class='eumi-main-grid'>
    <div>
      <div class='eumi-badge'>👤 자녀용</div>
      <div class='eumi-card-title'>🔗 이음이 자녀 대시보드</div>
      <div class='eumi-headline'>부모님의 디지털 사용 기록을<br>함께 확인하세요</div>
      <div class='eumi-copy'>어디에서 자주 어려워하시는지 보고,<br>가족 연결도 관리할 수 있어요</div>
      <div class='eumi-action one'><span class='left'><span class='ico'>📋</span>부모님 기록 보기</span><span class='eumi-arrow'>›</span></div>
      <div class='eumi-action two'><span class='left'><span class='ico'>👨‍👩‍👧</span>가족 연결 관리</span><span class='eumi-arrow'>›</span></div>
      <div class='eumi-action three'><span class='left'><span class='ico'>👤</span>내 기록 보기</span><span class='eumi-arrow'>›</span></div>
    </div>
    <div><div class='eumi-ill'>👨‍💻📊</div><div class='eumi-note'>기록 확인 · 가족 관리</div></div>
  </div>
</div>
"""
    else:
        css = """
<style>
.block-container{max-width:1180px!important;}
.eumi-main-card{background:linear-gradient(135deg,#FFFDF9 0%,#FFF4EA 54%,#FFE6D2 100%);border:2px solid #F2D6C7;border-radius:28px;padding:1.5rem 1.6rem;margin:1rem auto 1.4rem;box-shadow:0 18px 45px rgba(240,90,40,.13);position:relative;overflow:hidden;}
.eumi-main-card:before{content:"";position:absolute;width:260px;height:260px;right:-90px;bottom:-90px;border-radius:50%;background:rgba(255,255,255,.45)}
.eumi-main-card:after{content:"";position:absolute;width:190px;height:190px;left:-70px;top:110px;border-radius:50%;background:rgba(255,255,255,.35)}
.eumi-main-grid{display:grid;grid-template-columns:1.28fr .82fr;gap:1.1rem;align-items:center;position:relative;z-index:1}
.eumi-badge{display:inline-flex;background:#FF6B2C;color:#fff;border-radius:14px;padding:.35rem .75rem;font-size:1rem;font-weight:900;margin-bottom:.7rem}.eumi-card-title{font-size:2.45rem;font-weight:900;color:#F05A28;letter-spacing:-.04em;margin:.15rem 0 .3rem}.eumi-headline{font-size:1.68rem;font-weight:900;color:#2A1A12;line-height:1.34;margin:.35rem 0}.eumi-copy{font-size:1.05rem;color:#6B5C55;font-weight:650;line-height:1.65;margin:.3rem 0 1rem}.eumi-ill{background:#FFE6D7;border-radius:26px;min-height:215px;display:flex;align-items:center;justify-content:center;font-size:4.2rem}.eumi-note{text-align:center;color:#6B5C55;font-size:1.02rem;font-weight:800;margin-top:.45rem}.eumi-action{display:flex;align-items:center;justify-content:space-between;border-radius:18px;padding:.82rem 1rem;margin:.62rem 0;font-size:1.25rem;font-weight:900;color:#fff;box-shadow:0 8px 18px rgba(0,0,0,.10)}.eumi-action .left{display:flex;gap:.75rem;align-items:center}.eumi-action .ico{width:2.4rem;height:2.4rem;display:flex;align-items:center;justify-content:center;border-radius:13px;background:rgba(255,255,255,.25)}.eumi-action.one{background:#F05A28}.eumi-action.two{background:#FF9B5F}.eumi-action.three{background:#FFF1E6;color:#3A2117;border:1px solid #F2D6C7}.eumi-arrow{font-size:1.8rem}@media(max-width:900px){.eumi-main-grid{grid-template-columns:1fr}.eumi-ill{min-height:130px;font-size:3rem}.eumi-card-title{font-size:2rem}}
</style>
"""
        html = css + """
<div class='eumi-main-card'>
  <div class='eumi-main-grid'>
    <div>
      <div class='eumi-badge'>👥 부모님용</div>
      <div class='eumi-card-title'>🔗 이음이 부모님용</div>
      <div class='eumi-headline'>어려운 화면,<br>사진 찍어서 물어보세요</div>
      <div class='eumi-copy'>키오스크 · 병원 앱 · 은행 앱 · 예매 화면을 쉽게 도와드려요</div>
      <div class='eumi-action one'><span class='left'><span class='ico'>📷</span>사진으로 물어보기</span><span class='eumi-arrow'>›</span></div>
      <div class='eumi-action two'><span class='left'><span class='ico'>🕘</span>지난 기록 보기</span><span class='eumi-arrow'>›</span></div>
      <div class='eumi-action three'><span class='left'><span class='ico'>👨‍👩‍👧</span>가족 연결하기</span><span class='eumi-arrow'>›</span></div>
    </div>
    <div><div class='eumi-ill'>👵👴📱</div><div class='eumi-note'>사진으로 도움받기</div></div>
  </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# =========================================================
# 화면 전환 버튼 설명
# =========================================================
def render_action_button_note() -> None:
    st.markdown(
        "<div class='small-note'>아래 큰 버튼을 누르면 해당 기능 화면으로 이동합니다.</div>",
        unsafe_allow_html=True,
    )
