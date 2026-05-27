import flet as ft
import requests
import datetime
import time
import os
import random

# 你的專屬 Firebase 雲端資料庫網址
FIREBASE_URL = "https://pomodoroapp-73355-default-rtdb.firebaseio.com/"

def main(page: ft.Page):
    page.title = "備考番茄鐘 行動網頁版"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#f4f6f8"
    page.scroll = ft.ScrollMode.AUTO

    # 核心計時變數
    work_mins = 25
    time_left = work_mins * 60
    is_running = False

    # ---------------- 雲端資料讀取 ----------------
    def load_cloud_data():
        try:
            res = requests.get(f"{FIREBASE_URL}study_data.json", timeout=5).json() or {}
            streak_curr = res.get("streak_current", 0)
            streak_m = res.get("streak_max", 0)
            records = res.get("records", {})
            checkins = res.get("history_checkins", [])
            return streak_curr, streak_m, records, checkins
        except:
            return 0, 0, {}, []

    def save_cloud_data(streak_curr, streak_m, checkins, records):
        payload = {
            "streak_current": streak_curr,
            "streak_max": streak_m,
            "history_checkins": checkins,
            "records": records
        }
        try:
            requests.put(f"{FIREBASE_URL}study_data.json", json=payload, timeout=5)
        except:
            pass

    streak_current, streak_max, study_data, history_checkins = load_cloud_data()

    # ---------------- 簽到與計時邏輯 ----------------
    def trigger_checkin():
        nonlocal streak_current, streak_max, history_checkins
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        
        if today_str not in history_checkins:
            history_checkins.append(today_str)
            if yesterday_str in history_checkins or streak_current == 0:
                streak_current += 1
            else:
                streak_current = 1
            if streak_current > streak_max:
                streak_max = streak_current
            
            save_cloud_data(streak_current, streak_max, history_checkins, study_data)
            streak_text.value = f"🔥 連續備考：{streak_current} 天"
            record_title.value = f"今日明細 (已簽到 ✓)"
            page.update()

    def update_timer():
        nonlocal time_left
        mins, secs = divmod(time_left, 60)
        timer_text.value = f"{mins:02d}:{secs:02d}"
        page.update()

    def start_timer(e):
        nonlocal is_running
        if not is_running:
            is_running = True
            start_btn.disabled = True
            pause_btn.disabled = False
            page.update()
            countdown()

    def pause_timer(e):
        nonlocal is_running
        is_running = False
        start_btn.disabled = False
        pause_btn.disabled = True
        page.update()

    def reset_timer(e):
        nonlocal is_running, time_left
        is_running = False
        time_left = work_mins * 60
        start_btn.disabled = False
        pause_btn.disabled = True
        update_timer()

    def countdown():
        nonlocal time_left, is_running
        while time_left > 0 and is_running:
            time.sleep(1)
            time_left -= 1
            update_timer()
        if time_left == 0 and is_running:
            is_running = False
            start_btn.disabled = False
            pause_btn.disabled = True
            
            today_str = datetime.date.today().strftime("%Y-%m-%d")
            if today_str not in study_data:
                study_data[today_str] = []
            study_data[today_str].append({"id": random.randint(100, 999), "subject": "手機專注", "mins": work_mins})
            trigger_checkin()
            update_today_list()
            update_timer()

    def update_today_list():
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        list_views.controls.clear()
        day_records = study_data.get(today_str, [])
        if not day_records:
            list_views.controls.append(ft.Text("今日尚無專注紀錄", italic=True, color="grey600"))
        else:
            for idx, r in enumerate(day_records, 1):
                list_views.controls.append(ft.Text(f"{idx}. [{r['subject']}] {r['mins']} 分鐘", size=14))
        page.update()

    # ---------------- UI 元件建構 ----------------
    # 1. 簽到卡片
    streak_text = ft.Text(f"🔥 連續備考：{streak_current} 天", size=18, weight=ft.FontWeight.BOLD, color="#e53e3e")
    max_text = ft.Text(f"🏆 最高紀錄：{streak_max} 天", size=12, color="grey600")
    streak_card = ft.Container(
        content=ft.Column([streak_text, max_text], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor="white", padding=15, border_radius=12, alignment=ft.alignment.center, shadow=ft.BoxShadow(blur_radius=10, color="0x11000000")
    )

    # 2. 計時器卡片
    timer_text = ft.Text("25:00", size=64, weight=ft.FontWeight.BOLD, font_family="Arial", color="#1a202c")
    start_btn = ft.ElevatedButton("開始", bgcolor="#38a169", color="white", on_click=start_timer)
    pause_btn = ft.ElevatedButton("暫停", bgcolor="#dd6b20", color="white", disabled=True, on_click=pause_timer)
    reset_btn = ft.ElevatedButton("重設", bgcolor="#e53e3e", color="white", on_click=reset_timer)
    
    timer_card = ft.Container(
        content=ft.Column([
            ft.Text("專注倒數", size=14, weight=ft.FontWeight.BOLD, color="bluegrey400"),
            timer_text,
            ft.Row([start_btn, pause_btn, reset_btn], alignment=ft.MainAxisAlignment.CENTER)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
        bgcolor="white", padding=25, border_radius=16, shadow=ft.BoxShadow(blur_radius=15, color="0x15000000")
    )

    # 3. 今日明細卡片
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    is_checked = " (已簽到 ✓)" if today_str in history_checkins else " (未簽到)"
    record_title = ft.Text(f"今日明細{is_checked}", size=14, weight=ft.FontWeight.BOLD, color="#2d3748")
    list_views = ft.Column(spacing=8)
    update_today_list()
    
    record_card = ft.Container(
        content=ft.Column([record_title, ft.Divider(), list_views]),
        bgcolor="white", padding=20, border_radius=12, shadow=ft.BoxShadow(blur_radius=10, color="0x11000000")
    )

    # 將卡片排版到網頁上
    page.add(
        ft.Container(
            content=ft.Column([
                ft.Text("Premium 備考防線", size=22, weight=ft.FontWeight.BOLD, color="#3182ce"),
                ft.Text("行動端網頁同步系統", size=12, color="grey500"),
                ft.VerticalDivider(height=10),
                streak_card,
                timer_card,
                record_card
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            width=400,
            padding=10
        )
    )

if __name__ == "__main__":
    ft.run(main, port=int(os.environ.get("PORT", 8550)))
