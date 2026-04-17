from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import select, func
from datetime import datetime
import secrets

from bot.database.crud import async_session
from bot.database.models import User, TourRequest, TourvisorOrder, HotTourSubscription, Review
from bot.config import settings

app = FastAPI(title="Green Travel Admin")

ADMIN_LOGIN = "anna"
ADMIN_PASSWORD = "greentravel2024"
SESSIONS = {}

CSS = """<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#0f0f0f;color:#e0e0e0;display:flex;min-height:100vh}
.sidebar{width:220px;background:#1a1a1a;border-right:1px solid #2a2a2a;padding:24px 0;position:fixed;height:100vh;display:flex;flex-direction:column}
.logo{padding:0 20px 24px;border-bottom:1px solid #2a2a2a;margin-bottom:12px}
.logo h2{color:#4ade80;font-size:16px;font-weight:700}
.logo p{color:#666;font-size:12px;margin-top:2px}
.nav a{display:flex;align-items:center;gap:10px;padding:11px 20px;color:#999;text-decoration:none;font-size:14px;border-left:3px solid transparent}
.nav a:hover{color:#e0e0e0;background:#222}
.nav a.active{color:#4ade80;background:#1f2e24;border-left-color:#4ade80}
.sidebar-footer{margin-top:auto;padding:16px 20px;border-top:1px solid #2a2a2a}
.sidebar-footer a{color:#666;text-decoration:none;font-size:13px}
.main{margin-left:220px;flex:1;padding:32px}
.title{font-size:22px;font-weight:700;color:#fff;margin-bottom:24px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:16px;margin-bottom:32px}
.card{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;padding:20px}
.card-label{color:#666;font-size:12px;text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px}
.card-value{color:#fff;font-size:28px;font-weight:700}
.green{color:#4ade80}.yellow{color:#fbbf24}
.table-wrap{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:12px;overflow:hidden;margin-bottom:24px}
.table-header{padding:16px 20px;border-bottom:1px solid #2a2a2a;display:flex;align-items:center;justify-content:space-between}
.table-header h3{font-size:15px;color:#fff}
table{width:100%;border-collapse:collapse}
th{padding:12px 16px;text-align:left;font-size:11px;color:#666;text-transform:uppercase;border-bottom:1px solid #2a2a2a}
td{padding:13px 16px;font-size:13px;color:#ccc;border-bottom:1px solid #1f1f1f}
tr:last-child td{border-bottom:none}
tr:hover td{background:#1f1f1f}
.badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600}
.badge-new{background:#1f3a2a;color:#4ade80}
.badge-progress{background:#2a2a1a;color:#fbbf24}
.badge-done{background:#1a2a3a;color:#60a5fa}
.btn{display:inline-flex;align-items:center;padding:8px 16px;border-radius:8px;font-size:13px;font-weight:500;border:none;cursor:pointer;text-decoration:none}
.btn-primary{background:#4ade80;color:#0f0f0f}
.btn-secondary{background:#2a2a2a;color:#ccc}
.btn-sm{padding:5px 12px;font-size:12px}
.filters{display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap}
.filter-btn{padding:6px 14px;border-radius:20px;font-size:12px;border:1px solid #2a2a2a;background:transparent;color:#999;cursor:pointer;text-decoration:none}
.filter-btn.active,.filter-btn:hover{background:#4ade80;color:#0f0f0f;border-color:#4ade80}
.form-group{margin-bottom:16px}
.form-group label{display:block;font-size:12px;color:#666;margin-bottom:6px;text-transform:uppercase}
.fc{width:100%;background:#222;border:1px solid #333;border-radius:8px;padding:10px 14px;color:#e0e0e0;font-size:14px;outline:none}
.fc:focus{border-color:#4ade80}
textarea.fc{resize:vertical;min-height:120px}
.alert-success{background:#1f3a2a;border:1px solid #4ade80;color:#4ade80;padding:14px;border-radius:10px;margin-bottom:20px;font-size:14px}
a{color:#4ade80;text-decoration:none}
strong.white{color:#fff}
</style>"""


def layout(content, page):
    nav_items = [
        ("/admin", "📊", "Дашборд", "dashboard"),
        ("/admin/requests", "📋", "Заявки (бот)", "requests"),
        ("/admin/tourvisor", "🌐", "Заявки (сайт)", "tourvisor"),
        ("/admin/clients", "👥", "Клиенты", "clients"),
        ("/admin/reviews", "⭐", "Отзывы", "reviews"),
        ("/admin/broadcast", "📢", "Рассылка", "broadcast"),
    ]
    links = ""
    for url, icon, label, p in nav_items:
        cls = "active" if p == page else ""
        links += f'<a href="{url}" class="{cls}">{icon} {label}</a>'

    return f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Green Travel Admin</title>{CSS}</head>
<body>
<div class="sidebar">
  <div class="logo"><h2>🌴 Green Travel</h2><p>Панель управления</p></div>
  <nav class="nav">{links}</nav>
  <div class="sidebar-footer"><a href="/admin/logout">🚪 Выйти</a></div>
</div>
<div class="main">{content}</div>
</body></html>"""


def badge(status):
    if status == "new":
        return '<span class="badge badge-new">Новая</span>'
    elif status == "in_progress":
        return '<span class="badge badge-progress">В работе</span>'
    return '<span class="badge badge-done">Закрыта</span>'


def is_auth(request):
    return request.cookies.get("admin_token") in SESSIONS


LOGIN_PAGE = """<!DOCTYPE html>
<html lang="ru">
<head><meta charset="UTF-8"><title>Вход</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#0f0f0f;color:#e0e0e0;display:flex;align-items:center;justify-content:center;min-height:100vh}
.box{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:16px;padding:40px;width:360px}
.logo{text-align:center;margin-bottom:32px}
.logo h1{color:#4ade80;font-size:32px}
.logo p{color:#666;font-size:14px;margin-top:6px}
label{display:block;font-size:12px;color:#666;margin-bottom:6px;text-transform:uppercase}
input{width:100%;background:#222;border:1px solid #333;border-radius:8px;padding:12px 14px;color:#e0e0e0;font-size:14px;outline:none;margin-bottom:16px}
input:focus{border-color:#4ade80}
button{width:100%;padding:13px;background:#4ade80;color:#0f0f0f;border:none;border-radius:8px;font-size:15px;font-weight:700;cursor:pointer}
.err{background:#3a1a1a;border:1px solid #f87171;color:#f87171;padding:12px;border-radius:8px;margin-bottom:16px;font-size:13px}
</style></head>
<body><div class="box">
<div class="logo"><h1>🌴</h1><p>Green Travel — Панель управления</p></div>
{err}
<form method="post" action="/admin/login">
<label>Логин</label><input type="text" name="username" placeholder="anna" autofocus required>
<label>Пароль</label><input type="password" name="password" placeholder="••••••••" required>
<button type="submit">Войти →</button>
</form>
</div></body></html>"""


@app.get("/admin/login", response_class=HTMLResponse)
async def login_page(request: Request, error: str = ""):
    err = f'<div class="err">⚠️ {error}</div>' if error else ""
    return HTMLResponse(LOGIN_PAGE.replace("{err}", err))


@app.post("/admin/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_LOGIN and password == ADMIN_PASSWORD:
        token = secrets.token_hex(32)
        SESSIONS[token] = username
        resp = RedirectResponse(url="/admin", status_code=302)
        resp.set_cookie("admin_token", token, max_age=86400 * 7)
        return resp
    err = '<div class="err">⚠️ Неверный логин или пароль</div>'
    return HTMLResponse(LOGIN_PAGE.replace("{err}", err))


@app.get("/admin/logout")
async def logout(request: Request):
    token = request.cookies.get("admin_token")
    SESSIONS.pop(token, None)
    resp = RedirectResponse(url="/admin/login", status_code=302)
    resp.delete_cookie("admin_token")
    return resp


@app.get("/admin", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not is_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    async with async_session() as s:
        total_users = (await s.execute(select(func.count(User.id)))).scalar() or 0
        total_req = (await s.execute(select(func.count(TourRequest.id)))).scalar() or 0
        new_req = (await s.execute(select(func.count(TourRequest.id)).where(TourRequest.status == "new"))).scalar() or 0
        total_subs = (await s.execute(select(func.count(HotTourSubscription.id)).where(HotTourSubscription.is_active == True))).scalar() or 0
        tv_new = (await s.execute(select(func.count(TourvisorOrder.id)).where(TourvisorOrder.status == "new"))).scalar() or 0
        recent = (await s.execute(select(TourRequest).order_by(TourRequest.created_at.desc()).limit(5))).scalars().all()

    rows = ""
    for r in recent:
        dt = r.created_at.strftime("%d.%m %H:%M") if r.created_at else "—"
        rows += f"<tr><td>#{r.id}</td><td><strong class='white'>{r.destination or '—'}</strong></td><td>{r.adults} взр</td><td>{r.budget or '—'}</td><td>{dt}</td><td>{badge(r.status)}</td></tr>"

    if not rows:
        rows = "<tr><td colspan='6' style='text-align:center;color:#444;padding:30px'>Заявок пока нет</td></tr>"

    content = f"""
<div class="title">📊 Дашборд</div>
<div class="cards">
  <div class="card"><div class="card-label">Пользователей</div><div class="card-value">{total_users}</div></div>
  <div class="card"><div class="card-label">Новых заявок (бот)</div><div class="card-value green">{new_req}</div></div>
  <div class="card"><div class="card-label">Новых заявок (сайт)</div><div class="card-value yellow">{tv_new}</div></div>
  <div class="card"><div class="card-label">Подписок</div><div class="card-value">{total_subs}</div></div>
  <div class="card"><div class="card-label">Всего заявок</div><div class="card-value">{total_req}</div></div>
</div>
<div class="table-wrap">
  <div class="table-header"><h3>Последние заявки из бота</h3><a href="/admin/requests" class="btn btn-secondary btn-sm">Все →</a></div>
  <table><thead><tr><th>#</th><th>Направление</th><th>Туристов</th><th>Бюджет</th><th>Дата</th><th>Статус</th></tr></thead>
  <tbody>{rows}</tbody></table>
</div>"""
    return HTMLResponse(layout(content, "dashboard"))


@app.get("/admin/requests", response_class=HTMLResponse)
async def requests_page(request: Request, status: str = ""):
    if not is_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    async with async_session() as s:
        q = select(TourRequest).order_by(TourRequest.created_at.desc())
        if status:
            q = q.where(TourRequest.status == status)
        reqs = (await s.execute(q)).scalars().all()

    rows = ""
    for r in reqs:
        dt = r.created_at.strftime("%d.%m %H:%M") if r.created_at else "—"
        children_info = f"+ {r.children} дет" if r.children else ""
        sel_new = "selected" if r.status == "new" else ""
        sel_prog = "selected" if r.status == "in_progress" else ""
        sel_done = "selected" if r.status == "done" else ""
        rows += f"""<tr>
<td>#{r.id}</td>
<td><a href="tg://user?id={r.telegram_id}">{r.telegram_id}</a></td>
<td><strong class="white">{r.destination or "—"}</strong></td>
<td>{r.departure_date or "—"}</td>
<td>{r.adults} взр {children_info}</td>
<td>{r.nights or "—"}</td>
<td>{r.budget or "—"}</td>
<td>{r.comment or "—"}</td>
<td>{dt}</td>
<td>
<form method="post" action="/admin/requests/{r.id}/status" style="display:flex;gap:4px">
<select name="status" class="fc" style="padding:4px 8px;font-size:12px;width:auto">
<option value="new" {sel_new}>🟢 Новая</option>
<option value="in_progress" {sel_prog}>🟡 В работе</option>
<option value="done" {sel_done}>🔵 Закрыта</option>
</select>
<button type="submit" class="btn btn-secondary btn-sm">✓</button>
</form>
</td></tr>"""

    if not rows:
        rows = "<tr><td colspan='10' style='text-align:center;color:#444;padding:30px'>Заявок нет</td></tr>"

    fa = "active" if not status else ""
    fn = "active" if status == "new" else ""
    fp = "active" if status == "in_progress" else ""
    fd = "active" if status == "done" else ""

    content = f"""
<div class="title">📋 Заявки из бота</div>
<div class="filters">
<a href="/admin/requests" class="filter-btn {fa}">Все</a>
<a href="/admin/requests?status=new" class="filter-btn {fn}">🟢 Новые</a>
<a href="/admin/requests?status=in_progress" class="filter-btn {fp}">🟡 В работе</a>
<a href="/admin/requests?status=done" class="filter-btn {fd}">🔵 Закрытые</a>
</div>
<div class="table-wrap"><table>
<thead><tr><th>#</th><th>TG ID</th><th>Направление</th><th>Вылет</th><th>Туристов</th><th>Ночей</th><th>Бюджет</th><th>Телефон</th><th>Дата</th><th>Статус</th></tr></thead>
<tbody>{rows}</tbody></table></div>"""
    return HTMLResponse(layout(content, "requests"))


@app.post("/admin/requests/{req_id}/status")
async def update_req_status(req_id: int, request: Request, status: str = Form(...)):
    if not is_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    from sqlalchemy import update
    async with async_session() as s:
        await s.execute(update(TourRequest).where(TourRequest.id == req_id).values(status=status))
        await s.commit()
    return RedirectResponse(url="/admin/requests", status_code=302)


@app.get("/admin/tourvisor", response_class=HTMLResponse)
async def tourvisor_page(request: Request):
    if not is_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    async with async_session() as s:
        orders = (await s.execute(select(TourvisorOrder).order_by(TourvisorOrder.created_at.desc()))).scalars().all()

    rows = ""
    for o in orders:
        price_str = f"<strong class='green'>{o.price} {o.currency}</strong>" if o.price else "—"
        rows += f"""<tr>
<td>#{o.tourvisor_id}</td>
<td><strong class="white">{o.client_name or "—"}</strong></td>
<td>{o.client_phone or "—"}</td>
<td><strong class="white">{o.country or "—"}</strong><br><small style="color:#666">{o.hotel or ""}</small></td>
<td>{o.fly_date or "—"}</td>
<td>{o.nights or "—"}</td>
<td>{o.placement or "—"}</td>
<td>{price_str}</td>
<td>{badge(o.status)}</td></tr>"""

    if not rows:
        rows = "<tr><td colspan='9' style='text-align:center;color:#444;padding:30px'>Заявок нет</td></tr>"

    content = f"""
<div class="title">🌐 Заявки с сайта (Tourvisor)</div>
<div class="table-wrap"><table>
<thead><tr><th>ID</th><th>Клиент</th><th>Телефон</th><th>Страна/Отель</th><th>Вылет</th><th>Ночей</th><th>Туристов</th><th>Цена</th><th>Статус</th></tr></thead>
<tbody>{rows}</tbody></table></div>"""
    return HTMLResponse(layout(content, "tourvisor"))


@app.get("/admin/clients", response_class=HTMLResponse)
async def clients_page(request: Request):
    if not is_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    async with async_session() as s:
        users = (await s.execute(select(User).order_by(User.created_at.desc()))).scalars().all()
        subs = (await s.execute(select(HotTourSubscription).where(HotTourSubscription.is_active == True))).scalars().all()

    urows = ""
    for u in users:
        uname = f"@{u.username}" if u.username else str(u.telegram_id)
        dt = u.created_at.strftime("%d.%m.%Y") if u.created_at else "—"
        urows += f"<tr><td>{u.id}</td><td><a href='tg://user?id={u.telegram_id}'>{uname}</a></td><td>{u.full_name or '—'}</td><td>{dt}</td></tr>"

    srows = ""
    for sub in subs:
        budget = f"до ${sub.budget_max}" if sub.budget_max else "Любой"
        dt = sub.created_at.strftime("%d.%m.%Y") if sub.created_at else "—"
        srows += f"<tr><td><a href='tg://user?id={sub.telegram_id}'>{sub.telegram_id}</a></td><td><strong class='white'>{sub.destination}</strong></td><td>{budget}</td><td>{sub.adults} взр</td><td>{dt}</td></tr>"

    if not urows:
        urows = "<tr><td colspan='4' style='text-align:center;color:#444;padding:30px'>Нет пользователей</td></tr>"
    if not srows:
        srows = "<tr><td colspan='5' style='text-align:center;color:#444;padding:30px'>Нет подписок</td></tr>"

    content = f"""
<div class="title">👥 Клиенты</div>
<div class="cards" style="margin-bottom:24px">
  <div class="card"><div class="card-label">Пользователей</div><div class="card-value">{len(users)}</div></div>
  <div class="card"><div class="card-label">Подписок</div><div class="card-value green">{len(subs)}</div></div>
</div>
<div class="table-wrap" style="margin-bottom:24px">
  <div class="table-header"><h3>Пользователи</h3></div>
  <table><thead><tr><th>#</th><th>Telegram</th><th>Имя</th><th>Дата</th></tr></thead><tbody>{urows}</tbody></table>
</div>
<div class="table-wrap">
  <div class="table-header"><h3>Подписки на горящие</h3></div>
  <table><thead><tr><th>TG ID</th><th>Направление</th><th>Бюджет</th><th>Туристов</th><th>Дата</th></tr></thead><tbody>{srows}</tbody></table>
</div>"""
    return HTMLResponse(layout(content, "clients"))


@app.get("/admin/reviews", response_class=HTMLResponse)
async def reviews_page(request: Request, msg: str = ""):
    if not is_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    async with async_session() as s:
        reviews = (await s.execute(select(Review).order_by(Review.created_at.desc()))).scalars().all()

    rows = ""
    for r in reviews:
        stars = "⭐" * r.rating
        st = '<span class="badge badge-new">Активен</span>' if r.is_active else '<span class="badge" style="background:#2a2a2a;color:#666">Скрыт</span>'
        btn = "Скрыть" if r.is_active else "Показать"
        txt = r.text[:80] + "..." if len(r.text) > 80 else r.text
        rows += f"""<tr>
<td>{r.id}</td>
<td><strong class="white">{r.author_name}</strong></td>
<td>{r.destination or "—"}</td>
<td>{stars}</td>
<td style="color:#aaa;font-size:12px">{txt}</td>
<td>{st}</td>
<td><form method="post" action="/admin/reviews/{r.id}/toggle"><button type="submit" class="btn btn-secondary btn-sm">{btn}</button></form></td>
</tr>"""

    if not rows:
        rows = "<tr><td colspan='7' style='text-align:center;color:#444;padding:30px'>Отзывов нет</td></tr>"

    alert = '<div class="alert-success">✅ Отзыв добавлен!</div>' if msg == "ok" else ""

    content = f"""
<div class="title">⭐ Отзывы</div>
{alert}
<div style="display:grid;grid-template-columns:1fr 380px;gap:24px;align-items:start">
<div class="table-wrap">
  <div class="table-header"><h3>Все отзывы</h3></div>
  <table><thead><tr><th>#</th><th>Автор</th><th>Направление</th><th>Рейтинг</th><th>Текст</th><th>Статус</th><th></th></tr></thead>
  <tbody>{rows}</tbody></table>
</div>
<div class="card">
  <h3 style="color:#fff;margin-bottom:20px;font-size:15px">➕ Добавить отзыв</h3>
  <form method="post" action="/admin/reviews/add">
    <div class="form-group"><label>Имя автора</label><input type="text" name="author" class="fc" placeholder="Мария К." required></div>
    <div class="form-group"><label>Направление</label><input type="text" name="destination" class="fc" placeholder="Турция"></div>
    <div class="form-group"><label>Рейтинг</label>
    <select name="rating" class="fc"><option value="5">⭐⭐⭐⭐⭐</option><option value="4">⭐⭐⭐⭐</option><option value="3">⭐⭐⭐</option></select></div>
    <div class="form-group"><label>Текст</label><textarea name="text" class="fc" required></textarea></div>
    <button type="submit" class="btn btn-primary" style="width:100%">Добавить</button>
  </form>
</div>
</div>"""
    return HTMLResponse(layout(content, "reviews"))


@app.post("/admin/reviews/add")
async def add_review(request: Request, author: str = Form(...), text: str = Form(...), rating: int = Form(5), destination: str = Form("")):
    if not is_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    async with async_session() as s:
        s.add(Review(author_name=author, text=text, rating=rating, destination=destination or None))
        await s.commit()
    return RedirectResponse(url="/admin/reviews?msg=ok", status_code=302)


@app.post("/admin/reviews/{review_id}/toggle")
async def toggle_review(review_id: int, request: Request):
    if not is_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    from sqlalchemy import update
    async with async_session() as s:
        r = (await s.execute(select(Review).where(Review.id == review_id))).scalar_one_or_none()
        if r:
            await s.execute(update(Review).where(Review.id == review_id).values(is_active=not r.is_active))
            await s.commit()
    return RedirectResponse(url="/admin/reviews", status_code=302)


@app.get("/admin/broadcast", response_class=HTMLResponse)
async def broadcast_page(request: Request, sent: int = 0, failed: int = 0, success: str = ""):
    if not is_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)

    async with async_session() as s:
        total = (await s.execute(select(func.count(User.id)))).scalar() or 0

    alert = f'<div class="alert-success">✅ Отправлено: {sent}, не доставлено: {failed}</div>' if success else ""

    content = f"""
<div class="title">📢 Рассылка</div>
{alert}
<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;align-items:start">
<div class="card">
  <h3 style="color:#fff;margin-bottom:8px;font-size:15px">📢 Рассылка всем пользователям</h3>
  <p style="color:#666;font-size:13px;margin-bottom:20px">Получат все {total} пользователей. Поддерживается *жирный* и _курсив_.</p>
  <form method="post" action="/admin/broadcast/send">
    <div class="form-group"><label>Текст сообщения</label>
    <textarea name="text" class="fc" style="min-height:200px" placeholder="🔥 *Горящий тур!*" required></textarea></div>
    <button type="submit" class="btn btn-primary" onclick="return confirm('Отправить {total} пользователям?')">📢 Отправить</button>
  </form>
</div>
<div class="card">
  <h3 style="color:#fff;margin-bottom:16px;font-size:15px">💡 Подсказки</h3>
  <div style="color:#999;font-size:13px;line-height:1.8">
    <p>*жирный* → <strong>жирный</strong></p>
    <p>_курсив_ → <em>курсив</em></p>
    <br>
    <p style="color:#4ade80;margin-bottom:8px">Пример:</p>
    <div style="background:#222;padding:14px;border-radius:8px;font-size:12px;color:#ccc;line-height:1.7">
      🔥 *Горящий тур в Египет!*<br><br>
      📍 Хургада, отель 5⭐<br>
      ✈️ Вылет 28 апреля из Минска<br>
      🌙 7 ночей, всё включено<br>
      💰 от $580 на человека
    </div>
  </div>
</div>
</div>"""
    return HTMLResponse(layout(content, "broadcast"))


@app.post("/admin/broadcast/send")
async def send_broadcast(request: Request, text: str = Form(...)):
    if not is_auth(request):
        return RedirectResponse(url="/admin/login", status_code=302)
    from aiogram import Bot
    bot = Bot(token=settings.BOT_TOKEN)
    async with async_session() as s:
        users = (await s.execute(select(User).where(User.is_blocked == False))).scalars().all()
    sent = failed = 0
    for u in users:
        try:
            await bot.send_message(u.telegram_id, text, parse_mode="Markdown")
            sent += 1
        except Exception:
            failed += 1
    await bot.session.close()
    return RedirectResponse(url=f"/admin/broadcast?success=1&sent={sent}&failed={failed}", status_code=302)
