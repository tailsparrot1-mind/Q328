#!/usr/bin/env python3
"""Build a separate Vkus 3.28 marketplace candidate from the immutable release ZIP."""
from __future__ import annotations
import hashlib, io, subprocess, tarfile, tempfile, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts"
OUTER = ROOT / "recovered-builds/3.28/Vkus_3.28_NO_SPLASH.zip"
BASE = "https://raw.githubusercontent.com/tailsparrot1-mind/vkus--3.17-button/dd5fd5ea8905e10b6fe3950e2a46c4827b84838f/"
FILES = {
    "vkus/cloud_marketplace.py": "vkus/cloud_marketplace.py",
    "vkus/exchange_marketplace.py": "vkus/exchange_marketplace.py",
    "tests/test_cloud_marketplace.py": "tests/test_cloud_marketplace.py",
}
def download(path: str) -> bytes:
    req = urllib.request.Request(BASE + path, headers={"User-Agent":"Vkus-328-build"})
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read()

def download_url(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent":"Vkus-328-build"})
    with urllib.request.urlopen(req, timeout=45) as response:
        data = response.read()
        if not data.startswith(bytes.fromhex("89504e470d0a1a0a")):
            raise SystemExit("Marketplace role-gate image URL did not return PNG bytes.")
        return data

def main():
    if not OUTER.is_file():
        raise SystemExit(f"Missing immutable source archive: {OUTER}")
    OUT.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUTER) as z:
        names = z.namelist()
        prefix = next((n[:-len("main.py")] for n in names if n.endswith("main.py")), None)
        if prefix is None:
            raise SystemExit("Nested source archive does not contain main.py")
        files = {n[len(prefix):]: z.read(n) for n in names if n.startswith(prefix) and not n.endswith("/")}
    app_path = "vkus/app.py"
    app = files[app_path].decode("utf-8")
    marker = "        if 1360 <= x <= 1618 and 373 <= y <= 700:\n"
    hook = (
        "        if 1095 <= x <= 1328 and 382 <= y <= 426:\n"
        "            from .exchange_marketplace import open_cloud_marketplace_window\n"
        "            open_cloud_marketplace_window(self.root)\n"
        "            return\n"
    )
    if "open_cloud_marketplace_window(self.root)" not in app:
        if marker not in app:
            raise SystemExit("Could not locate known Exchange click handler in Vkus 3.28; refusing a fuzzy patch.")
        app = app.replace(marker, hook + marker, 1)
        files[app_path] = app.encode("utf-8")
    visual_path = "vkus/exchange_visual.py"
    visual = files[visual_path].decode("utf-8")
    old_button = (
        '    label(1137, 402, "Расширенный поиск  ⌄", 15, "#38aaff",\n'
        '          width=190, fit=True)'
    )
    new_button = (
        '    rounded(1095, 382, 1328, 426, "#21104d", "#9c35ff", 11, 1)\n'
        '    label(1211, 390, "Доска объявлений", 11, "#f2dfff", "bold", "center", width=215, fit=True)\n'
        '    label(1211, 407, "Ищу  ·  Предлагаю", 8, "#c7b0ef", "normal", "center", width=210, fit=True)'
    )
    if old_button not in visual:
        raise SystemExit("Could not locate the existing advanced-search label; refusing an uncertain visual patch.")
    visual = visual.replace(old_button, new_button, 1)
    visual = visual.replace('"VKUS 3.27"', '"VKUS 3.28"', 1)
    files[visual_path] = visual.encode("utf-8")
    for target, source in FILES.items():
        files[target] = download(source)

    # The noticeboard source is expected to render listing cards, not a Treeview table.
    board_path = "vkus/exchange_marketplace.py"
    board = files[board_path].decode("utf-8")
    if "cards_canvas" not in board or "ДОСКА ОБЪЯВЛЕНИЙ" not in board:
        raise SystemExit("Pinned marketplace source is not the card-based noticeboard revision.")
    style_anchor = '    style.map("CloudMarket.Treeview", background=[("selected", "#4b258b")])\n'
    style_patch = (
        '    style.configure("TCombobox", fieldbackground="#0a1731", background="#17264a",\n'
        '                    foreground="#eaf1ff", arrowcolor="#c99aff", bordercolor="#304b80",\n'
        '                    lightcolor="#304b80", darkcolor="#304b80", font=("DejaVu Sans", 9))\n'
        '    style.map("TCombobox", fieldbackground=[("readonly", "#0a1731")],\n'
        '              foreground=[("readonly", "#eaf1ff")],\n'
        '              selectbackground=[("readonly", "#0a1731")],\n'
        '              selectforeground=[("readonly", "#eaf1ff")],\n'
        '              background=[("readonly", "#17264a")])\n'
    )
    if style_patch not in board:
        if style_anchor not in board:
            raise SystemExit("Could not locate noticeboard style anchor.")
        board = board.replace(style_anchor, style_anchor + style_patch, 1)
    files[board_path] = board.encode("utf-8")


    # Visual refinement: make the board feel like a Vkus product surface,
    # not a default Tk utility window. Keep all existing marketplace actions.
    board = files["vkus/exchange_marketplace.py"].decode("utf-8")
    visual_replacements = [
        ('win.geometry("1180x760")', 'parent.update_idletasks()\n    window_width = max(900, parent.winfo_width())\n    window_height = max(667, parent.winfo_height())\n    win.geometry(f"{window_width}x{window_height}+{parent.winfo_rootx()}+{parent.winfo_rooty()}")'),
        ('win.minsize(960, 640)', 'win.minsize(900, 667)'),
        ('win.configure(bg="#050b1b")', 'win.configure(bg="#030817")'),
        ('shell = tk.Frame(win, bg="#07122a", highlightbackground="#7136c3", highlightthickness=1)\n    shell.pack(fill="both", expand=True, padx=10, pady=10)',
         'shell = tk.Frame(win, bg="#07132d", highlightbackground="#8548dc", highlightthickness=1)\n    shell.pack(fill="both", expand=True, padx=0, pady=0)'),
        ('header.pack(fill="x", padx=18, pady=(15, 8))', 'header.pack(fill="x", padx=24, pady=(20, 14))'),
        ('text="ДОСКА ОБЪЯВЛЕНИЙ", bg="#07122a", fg="#d18aff",\n             font=("DejaVu Sans", 17, "bold")',
         'text="ДОСКА ОБЪЯВЛЕНИЙ", bg="#07122a", fg="#d9a0ff",\n             font=("DejaVu Sans", 21, "bold")'),
        ('account_label = tk.Label(header, text="Не выполнен вход", bg="#07122a",\n                             fg="#9fb4df", font=("DejaVu Sans", 9))',
         'account_label = tk.Label(header, text="Не выполнен вход", bg="#07122a",\n                             fg="#9fb4df", font=("DejaVu Sans", 9, "bold"))'),
        ('auth_bar.pack(fill="x", padx=18, pady=(0, 10))', 'auth_bar.pack(fill="x", padx=24, pady=(0, 14))'),
        ('filters.pack(fill="x", padx=18, pady=(0, 10))', 'filters.pack(fill="x", padx=24, pady=(0, 16))'),
        ('cell.pack(side="left", padx=(0, 9), anchor="n")', 'cell.pack(side="left", padx=(0, 14), anchor="n")'),
        ('body.pack(fill="both", expand=True, padx=12, pady=(0, 10))', 'body.pack(fill="both", expand=True, padx=18, pady=(0, 14))'),
        ('cards_frame.grid_columnconfigure(0, weight=1, uniform="market-cards")\n    cards_frame.grid_columnconfigure(1, weight=1, uniform="market-cards")',
         'cards_frame.grid_columnconfigure(0, weight=1, uniform="market-cards")\n    cards_frame.grid_columnconfigure(1, weight=1, uniform="market-cards")'),
        ('empty = tk.Frame(cards_frame, bg="#0a1731",\n                             highlightbackground="#334b7e", highlightthickness=1)',
         'empty = tk.Frame(cards_frame, bg="#101f43",\n                             highlightbackground="#405b91", highlightthickness=1)'),
        ('text="ПОКА НЕТ ОБЪЯВЛЕНИЙ", bg="#0a1731",\n                     fg="#d7a0ff", font=("DejaVu Sans", 13, "bold")',
         'text="ПОКА НЕТ ОБЪЯВЛЕНИЙ", bg="#101f43",\n                     fg="#ddaaff", font=("DejaVu Sans", 15, "bold")'),
        ('bg="#0a1731", fg="#9fb4df", font=("DejaVu Sans", 9),\n                     wraplength=720',
         'bg="#101f43", fg="#b3c3e5", font=("DejaVu Sans", 9),\n                     wraplength=760'),
        ('card = tk.Frame(cards_frame, bg="#0b1a39",\n                            highlightbackground="#304779", highlightthickness=1,\n                            padx=14, pady=12)',
         'card = tk.Frame(cards_frame, bg="#101f43",\n                            highlightbackground="#405b91", highlightthickness=1,\n                            padx=18, pady=16)'),
        ('columnspan=2 if len(rows) == 1 else 1,\n                      sticky="nsew", padx=8, pady=8)',
         'columnspan=2 if len(rows) == 1 else 1,\n                      sticky="n" if len(rows) == 1 else "nsew", padx=10, pady=10)\n            if len(rows) == 1:\n                card.configure(width=780, height=178)\n                card.grid_propagate(False)'),
        ('top = tk.Frame(card, bg="#0b1a39")', 'top = tk.Frame(card, bg="#101f43")'),
        ('bg="#0b1a39", fg="#728bb8",', 'bg="#101f43", fg="#8ca3d0",'),
        ('bg="#0b1a39", fg="#f0f4ff",\n                     font=("DejaVu Sans", 11, "bold")',
         'bg="#101f43", fg="#f4f6ff",\n                     font=("DejaVu Sans", 12, "bold")'),
        ('bg="#0b1a39", fg="#a9badc",', 'bg="#101f43", fg="#b6c6e4",'),
        ('bg="#0b1a39", fg="#b98aff",', 'bg="#101f43", fg="#d2a0ff",'),
        ('details.pack(fill="x", padx=18, pady=(0, 8))', 'details.pack(fill="x", padx=24, pady=(0, 10))'),
        ('actions.pack(fill="x", padx=18, pady=(0, 14))', 'actions.pack(fill="x", padx=24, pady=(0, 20))'),
        ('highlightbackground="#304779")', 'highlightbackground="#405b91")'),
        ('padx=11, pady=7,\n                  font=("DejaVu Sans", 8, "bold")',
         'padx=14, pady=9,\n                  font=("DejaVu Sans", 9, "bold")'),
    ]
    for old, new in visual_replacements:
        if old in board:
            board = board.replace(old, new, 1)
    # Keep the card grid visually balanced at every result count.
    if 'card.configure(width=780, height=178)' not in board:
        raise SystemExit("Centered single-card layout was not applied.")

    # Second visual pass: richer listing hierarchy and distinct demand/supply cues.
    # Add the two distinct user paths inside the marketplace window.
    role_anchor = '    auth_bar = tk.Frame(shell, bg="#0a1731")\n'
    if role_anchor not in board:
        raise SystemExit("Could not locate cloud marketplace auth bar for role selector.")
    role_ui = '''    role_bar = tk.Frame(shell, bg="#07132d")
    role_bar.pack(fill="x", padx=24, pady=(0, 12))
    tk.Label(role_bar, text="ВЫБЕРИТЕ СЦЕНАРИЙ", bg="#07132d", fg="#8fa8d8",
             font=("DejaVu Sans", 8, "bold")).pack(anchor="w", pady=(0, 6))
    role_buttons = tk.Frame(role_bar, bg="#07132d")
    role_buttons.pack(fill="x")
    seeker_btn = tk.Button(role_buttons, text="СОИСКАТЕЛЬ  ·  ИЩУ РАБОТУ",
             bg="#25134d", fg="#e6c9ff", activebackground="#7136b9",
             activeforeground="white", relief="flat", bd=0, padx=18, pady=10,
             font=("DejaVu Sans", 9, "bold"), cursor="hand2")
    seeker_btn.pack(side="left", fill="x", expand=True, padx=(0, 7))
    advertiser_btn = tk.Button(role_buttons, text="РЕКЛАМОДАТЕЛЬ  ·  ИЩУ ИСПОЛНИТЕЛЯ",
             bg="#10344b", fg="#a9eaff", activebackground="#16749a",
             activeforeground="white", relief="flat", bd=0, padx=18, pady=10,
             font=("DejaVu Sans", 9, "bold"), cursor="hand2")
    advertiser_btn.pack(side="left", fill="x", expand=True, padx=(7, 0))
'''
    board = board.replace(role_anchor, role_ui + role_anchor, 1)
    kind_anchor = '    kind_var = tk.StringVar(value="Все типы")\n'
    role_logic = '''    role_mode = {"value": None}
    def set_market_role(role):
        role_mode["value"] = None if role_mode["value"] == role else role
        kind_var.set("Все типы" if role_mode["value"] is None else
                     ("Предлагаю" if role_mode["value"] == "Соискатель" else "Ищу"))
        seeker_active = role_mode["value"] == "Соискатель"
        advertiser_active = role_mode["value"] == "Рекламодатель"
        seeker_btn.configure(bg="#7136b9" if seeker_active else "#25134d",
                             fg="white" if seeker_active else "#e6c9ff")
        advertiser_btn.configure(bg="#16749a" if advertiser_active else "#10344b",
                                 fg="white" if advertiser_active else "#a9eaff")
    seeker_btn.configure(command=lambda: set_market_role("Соискатель"))
    advertiser_btn.configure(command=lambda: set_market_role("Рекламодатель"))
'''
    if kind_anchor not in board:
        raise SystemExit("Could not locate marketplace kind filter for role behavior.")
    board = board.replace(kind_anchor, kind_anchor + role_logic, 1)
    old_kind = '"kind": tk.StringVar(value=(existing or {}).get("kind", "Ищу")),'
    new_kind = '"kind": tk.StringVar(value=(existing or {}).get("kind", "Предлагаю" if role_mode["value"] == "Соискатель" else "Ищу")),'
    if old_kind not in board:
        raise SystemExit("Could not locate listing form kind default.")
    board = board.replace(old_kind, new_kind, 1)
    if "СОИСКАТЕЛЬ  ·  ИЩУ РАБОТУ" not in board or "РЕКЛАМОДАТЕЛЬ  ·  ИЩУ ИСПОЛНИТЕЛЯ" not in board:
        raise SystemExit("Marketplace role selector was not inserted.")
    card_start = board.index('            top = tk.Frame(card, bg="#101f43")')
    card_end = board.index('            def choose(', card_start)
    card_ui = '''            # Slim neon rail makes each listing instantly scannable.
            stripe = tk.Frame(card, bg=accent, width=4)
            stripe.place(x=0, y=0, relheight=1)
            top = tk.Frame(card, bg="#101f43")
            top.pack(fill="x", padx=(5, 0))
            badge_bg = "#2b1555" if kind == "Ищу" else "#103c55"
            badge_text = "ИЩУ" if kind == "Ищу" else "ПРЕДЛАГАЮ"
            tk.Label(top, text=badge_text, bg=badge_bg, fg=accent,
                     font=("DejaVu Sans", 8, "bold"),
                     padx=12, pady=5).pack(side="left")
            created = (item.get("created_at") or "")[:10]
            tk.Label(top, text=f"ОПУБЛИКОВАНО  {created or '—'}",
                     bg="#101f43", fg="#8098c6",
                     font=("DejaVu Sans", 7, "bold")).pack(side="right", padx=(4, 2))
            tk.Label(card, text=item.get("title") or "Без заголовка",
                     bg="#101f43", fg="#f6f3ff",
                     font=("DejaVu Sans", 14, "bold"),
                     anchor="w", justify="left", wraplength=690).pack(
                         fill="x", padx=(5, 0), pady=(13, 6))
            summary = (item.get("description") or "").replace("\\n", " ").strip()
            if len(summary) > 220:
                summary = summary[:217] + "…"
            tk.Label(card, text=summary or "Автор пока не добавил описание.",
                     bg="#101f43", fg="#b8c7e6",
                     font=("DejaVu Sans", 9), anchor="w", justify="left",
                     wraplength=690).pack(fill="x", padx=(5, 0), pady=(0, 14))
            meta_row = tk.Frame(card, bg="#101f43")
            meta_row.pack(fill="x", padx=(5, 0))
            def meta_chip(caption, value, color="#d8c5ff", fill="#1a2c53"):
                tk.Label(meta_row, text=f"{caption}  {value}", bg=fill, fg=color,
                         font=("DejaVu Sans", 8, "bold"),
                         padx=10, pady=6).pack(side="left", padx=(0, 8))
            meta_chip("КАТЕГОРИЯ", item.get("category") or "Другое")
            meta_chip("ГОРОД", f"⌖ {item.get('city') or 'Не указан'}", "#b9d8ff", "#142b50")
            if item.get("price") not in (None, ""):
                price = f"{item.get('price')} {item.get('currency') or 'RUB'}"
                meta_chip("БЮДЖЕТ" if kind == "Ищу" else "ЦЕНА", price,
                          "#83f0df" if kind == "Ищу" else "#8be7ff",
                          "#103b4a" if kind == "Ищу" else "#10354b")
            status_text = item.get("status") or "Активно"
            tk.Label(meta_row, text=status_text.upper(), bg="#101f43",
                     fg="#6fe0b4" if status_text == "Активно" else "#a2b0ce",
                     font=("DejaVu Sans", 7, "bold")).pack(side="right", padx=(4, 2))
'''
    board = board[:card_start] + card_ui + board[card_end:]
    board = board.replace('card.configure(width=780, height=178)', 'card.configure(width=780, height=220)', 1)
    board = board.replace('wraplength=760, justify="center").pack(pady=(0, 22))',
        'wraplength=760, justify="center").pack(pady=(0, 18))', 1)
    # Replace the earlier inline role filter with a full registration gate.
    board = board.replace(role_ui, "")
    board = board.replace(role_logic, "")
    board = board.replace(new_kind, old_kind)

    # Full-window onboarding gate: the noticeboard remains covered until an account
    # has a persisted marketplace role (Соискатель or Рекламодатель).
    gate_anchor = '    for variable in (query_var, kind_var, category_var, city_var):\n'
    gate_patch = '''    # Exact reference-image gate. The reference has been cropped to exclude the entire left navigation.
    auth_bar.pack_forget()
    gate = tk.Frame(shell, bg="#030817", highlightthickness=0, bd=0)
    gate.place(in_=shell, x=0, y=0, relwidth=1, relheight=1)
    gate_canvas = tk.Canvas(gate, bg="#030817", highlightthickness=0, bd=0)
    gate_canvas.place(relwidth=1, relheight=1)
    gate_image_path = Path(__file__).resolve().parent / "assets" / "marketplace_role_gate.png"
    from PIL import Image, ImageTk
    gate_source = Image.open(gate_image_path).convert("RGB")
    gate_layout = {"left": None, "right": None}
    gate_canvas._photo = None
    def redraw_role_gate(_event=None):
        cw, ch = max(1, gate_canvas.winfo_width()), max(1, gate_canvas.winfo_height())
        scale = min(cw / 1683, ch / 959)
        iw, ih = max(1, int(1683*scale)), max(1, int(959*scale))
        resized = gate_source.resize((iw, ih), Image.Resampling.LANCZOS)
        gate_canvas._photo = ImageTk.PhotoImage(resized)
        gate_canvas.delete("all")
        ox, oy = (cw-iw)//2, (ch-ih)//2
        gate_canvas.create_image(ox, oy, image=gate_canvas._photo, anchor="nw")
        gate_layout["left"] = (ox+285*scale, oy+638*scale, ox+798*scale, oy+733*scale)
        gate_layout["right"] = (ox+891*scale, oy+638*scale, ox+1410*scale, oy+733*scale)
    def finish_gate_auth(dialog):
        update_account_label()
        gate.place_forget()
        dialog.destroy()
        refresh()
    def show_role_auth(role):
        dialog = tk.Toplevel(win)
        dialog.title("Vkus — " + role)
        dialog.configure(bg="#08152f")
        dialog.transient(win)
        dialog.grab_set()
        dialog.resizable(False, False)
        dialog.geometry("470x330")
        panel = tk.Frame(dialog, bg="#08152f", padx=28, pady=24)
        panel.pack(fill="both", expand=True)
        accent = "#d05aff" if role == "Соискатель" else "#23bfff"
        tk.Label(panel, text="VKUS  /  ДОСКА ОБЪЯВЛЕНИЙ", bg="#08152f", fg=accent,
                 font=("DejaVu Sans", 9, "bold")).pack(anchor="w")
        tk.Label(panel, text=("Регистрация соискателя" if role == "Соискатель" else "Регистрация рекламодателя"),
                 bg="#08152f", fg="#f4f0ff", font=("DejaVu Sans", 16, "bold")).pack(anchor="w", pady=(8,18))
        tk.Label(panel, text="EMAIL", bg="#08152f", fg="#91a8d7",
                 font=("DejaVu Sans", 8, "bold")).pack(anchor="w")
        email_entry = tk.Entry(panel, textvariable=email_var, bg="#101f43", fg="#f4f6ff",
                               insertbackground="white", relief="flat", bd=0,
                               highlightthickness=1, highlightbackground="#344d82")
        email_entry.pack(fill="x", ipady=9, pady=(4,12))
        tk.Label(panel, text="ПАРОЛЬ  ·  НЕ МЕНЕЕ 8 СИМВОЛОВ", bg="#08152f", fg="#91a8d7",
                 font=("DejaVu Sans", 8, "bold")).pack(anchor="w")
        password_entry = tk.Entry(panel, textvariable=password_var, show="•", bg="#101f43",
                                  fg="#f4f6ff", insertbackground="white", relief="flat", bd=0,
                                  highlightthickness=1, highlightbackground="#344d82")
        password_entry.pack(fill="x", ipady=9, pady=(4,16))
        def register_role():
            try:
                client.sign_up(email_var.get(), password_var.get(), role=role)
                if client.is_authenticated:
                    finish_gate_auth(dialog)
                else:
                    messagebox.showinfo("Подтверждение email",
                        "Аккаунт создан. Подтвердите email по ссылке из письма, затем войдите.", parent=dialog)
            except (CloudMarketplaceError, ValueError) as exc:
                notify_error(exc)
        def login_role():
            try:
                client.sign_in(email_var.get(), password_var.get())
                saved_role = (client.session.user.get("user_metadata") or {}).get("marketplace_role")
                if saved_role not in ("Соискатель", "Рекламодатель"):
                    client.set_marketplace_role(role)
                elif saved_role != role:
                    messagebox.showinfo("Роль аккаунта",
                        f"У аккаунта уже сохранена роль: {saved_role}. Выберите соответствующую карточку.", parent=dialog)
                    return
                finish_gate_auth(dialog)
            except (CloudMarketplaceError, ValueError) as exc:
                notify_error(exc)
        tk.Button(panel, text="ЗАРЕГИСТРИРОВАТЬСЯ", command=register_role,
                  bg="#7136b9" if role == "Соискатель" else "#087eb7", fg="white",
                  activebackground=accent, relief="flat", bd=0, pady=10,
                  font=("DejaVu Sans", 9, "bold")).pack(fill="x")
        tk.Button(panel, text="УЖЕ ЕСТЬ АККАУНТ · ВОЙТИ", command=login_role,
                  bg="#142b4c", fg="#d4f7ff", activebackground="#24539b",
                  relief="flat", bd=0, pady=8, font=("DejaVu Sans", 8, "bold")).pack(fill="x", pady=(8,0))
        email_entry.focus_set()
    def handle_role_gate_click(event):
        for key, role in (("left","Соискатель"),("right","Рекламодатель")):
            b = gate_layout.get(key)
            if b and b[0] <= event.x <= b[2] and b[1] <= event.y <= b[3]:
                show_role_auth(role)
                return "break"
    gate_canvas.bind("<Configure>", redraw_role_gate)
    gate_canvas.bind("<Button-1>", handle_role_gate_click)
    def update_gate_cursor(event):
        inside = any(bounds and bounds[0] <= event.x <= bounds[2]
                     and bounds[1] <= event.y <= bounds[3]
                     for bounds in (gate_layout.get("left"), gate_layout.get("right")))
        gate_canvas.configure(cursor="hand2" if inside else "")
    gate_canvas.bind("<Motion>", update_gate_cursor)
    gate._canvas, gate._hit_regions = gate_canvas, gate_layout
    win._marketplace_gate_canvas, win._marketplace_gate_layout = gate_canvas, gate_layout
    if client.is_authenticated:
        saved_role = (client.session.user.get("user_metadata") or {}).get("marketplace_role")
        if saved_role in ("Соискатель", "Рекламодатель"):
            gate.place_forget()
        else:
            update_account_label()
    gate.lift()
'''
    if gate_anchor not in board:
        raise SystemExit("Could not locate final marketplace refresh anchor for registration gate.")
    board = board.replace(gate_anchor, gate_patch + gate_anchor, 1)

    signout_old = '''        account_label.configure(text="Не выполнен вход", fg="#9fb4df")
        refresh()

    def edit_profile():
'''
    signout_new = '''        account_label.configure(text="Не выполнен вход", fg="#9fb4df")
        refresh()
        gate.place(in_=shell, x=0, y=0, relwidth=1, relheight=1)
        gate.lift()

    def edit_profile():
'''
    if signout_old not in board:
        raise SystemExit("Could not locate sign-out handler for gate restoration.")
    board = board.replace(signout_old, signout_new, 1)

    # Attach the chosen role to Supabase Auth user metadata and restore it on later logins.
    cloud = files["vkus/cloud_marketplace.py"].decode("utf-8")
    old_signup = '''    def sign_up(self, email: str, password: str) -> dict:
        email, password = email.strip(), password
        if not email or "@" not in email:
            raise ValueError("Введите корректный email.")
        if len(password) < 8:
            raise ValueError("Пароль должен содержать не менее 8 символов.")
        result = self._request("POST", "/auth/v1/signup",
                               {"email": email, "password": password})
        self._accept_auth_result(result)
        return result or {}
'''
    new_signup = '''    def sign_up(self, email: str, password: str, role: str | None = None) -> dict:
        email, password = email.strip(), password
        if not email or "@" not in email:
            raise ValueError("Введите корректный email.")
        if len(password) < 8:
            raise ValueError("Пароль должен содержать не менее 8 символов.")
        if role is not None and role not in ("Соискатель", "Рекламодатель"):
            raise ValueError("Выберите роль перед регистрацией.")
        payload = {"email": email, "password": password}
        if role is not None:
            payload["data"] = {"marketplace_role": role}
        result = self._request("POST", "/auth/v1/signup", payload)
        self._accept_auth_result(result)
        return result or {}

    def set_marketplace_role(self, role: str) -> dict:
        if role not in ("Соискатель", "Рекламодатель"):
            raise ValueError("Неизвестная роль участника доски.")
        self._require_auth()
        result = self._request("PUT", "/auth/v1/user",
                               {"data": {"marketplace_role": role}},
                               authenticated=True)
        if isinstance(result, dict):
            self.session.user.update(result)
        self.session.user.setdefault("user_metadata", {})["marketplace_role"] = role
        return result or {}
'''
    if old_signup not in cloud:
        raise SystemExit("Could not locate Supabase sign_up method for role metadata patch.")
    cloud = cloud.replace(old_signup, new_signup, 1)
    files["vkus/cloud_marketplace.py"] = cloud.encode("utf-8")

    files["vkus/assets/marketplace_role_gate.png"] = download_url("https://photoshop-api.adobe.io/v2/short-url/urn:aaid:ps:US:93d3cf87-2e0b-4134-a343-80c7ec89f728")
    files["vkus/exchange_marketplace.py"] = board.encode("utf-8")
    req = files.get("requirements.txt", b"").decode("utf-8")
    if "keyring" not in req:
        files["requirements.txt"] = (req.rstrip() + "\nkeyring>=25.2\n").encode("utf-8")

    # Apply the verified final integration patch: license-store entry + exact Marketplace role gate.
    patch_archive = ROOT / "recovered-builds/3.28/Vkus_3.28_License_and_Marketplace_PATCH.tar.gz"
    if not patch_archive.is_file():
        raise SystemExit(f"Missing final integration patch: {patch_archive}")
    patch_bytes = None
    with tarfile.open(patch_archive, "r:gz") as patch_tar:
        for member in patch_tar.getmembers():
            if not member.isfile():
                continue
            stream = patch_tar.extractfile(member)
            if stream is None:
                continue
            name = Path(member.name).as_posix().lstrip("./")
            data = stream.read()
            if name == "integration.patch":
                patch_bytes = data
            else:
                files[name] = data
    if patch_bytes is None:
        raise SystemExit("Integration patch is missing integration.patch.")
    patched_paths = ("vkus/app.py", "vkus/exchange_marketplace.py", "vkus/__init__.py")
    with tempfile.TemporaryDirectory(prefix="vkus-328-final-") as temp_dir:
        temp_root = Path(temp_dir)
        for name in patched_paths:
            target = temp_root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(files[name])
        subprocess.run(
            ["patch", "-p1", "--forward", "--batch"],
            cwd=temp_root,
            input=patch_bytes,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        for name in patched_paths:
            files[name] = (temp_root / name).read_bytes()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(files.items()):
            z.writestr(name, data)
    candidate = OUT / "Vkus_3.28_License_and_Marketplace.zip"
    candidate.write_bytes(buf.getvalue())
    sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
    (OUT / "SHA256SUMS.txt").write_text(f"{sha}  {candidate.name}\n", encoding="utf-8")
    (OUT / "BUILD_NOTES.md").write_text(
        "## Vkus 3.28 — License Store + Marketplace baseline\n\n"
        "- Base: immutable recovered-builds/3.28/Vkus_3.28_NO_SPLASH.zip.\n"
        "- Added Supabase client and card-based noticeboard UI from pinned source commit dd5fd5ea.\n"
        "- Added a dedicated \"Доска объявлений\" button inside the existing Birzha search panel.\n"
        "- Preserved the existing audience-search UI and its explanatory card.\n"
        "- Captured real Xvfb launch screenshots for Birzha and the noticeboard.\n"
        "- Original archive and Supabase database were not modified; no database writes were made.\n"
        "- Real multi-user signup/login and listing exchange still require manual account smoke tests.\n"
        f"- SHA-256: {sha}\n", encoding="utf-8")
    print(f"BUILT {candidate} ({candidate.stat().st_size} bytes)")
    print(f"SHA256 {sha}")
if __name__ == "__main__":
    main()
