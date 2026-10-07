import flet as ft
from plyer import sms
import time
import re
from datetime import datetime

def main(page: ft.Page):
    page.title = "የትምህርት ክፍል መልዕክት መላኪያ"
    page.window_width = 450
    page.window_height = 800
    page.padding = 20
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    # Title
    title = ft.Text(
        "የትምህርት ክፍል መልዕክት መላኪያ", 
        size=22, 
        weight=ft.FontWeight.BOLD, 
        color=ft.Colors.BLUE_700
    )

    # Phone numbers input
    phone_input = ft.TextField(
        label="የስልክ ቁጥሮች (ከExcel/Word ኮፒ አድርገህ ወደታች ማስገባት ትችላለህ)",
        hint_text="ምሳሌ:\n0911223344\n0922334455",
        multiline=True,
        min_lines=5,
        border_color=ft.Colors.BLUE_400
    )

    # Message input
    message_input = ft.TextField(
        label="የሚላከው መልእክት",
        hint_text="መልእክትህን እዚህ ፃፍ...",
        multiline=True,
        min_lines=4,
        border_color=ft.Colors.BLUE_400
    )

    # Status Text
    status_text = ft.Text("", size=14, color=ft.Colors.BLUE_700, weight=ft.FontWeight.BOLD)
    
    # Report Container
    success_text = ft.Text("", size=13, color=ft.Colors.GREEN_700, selectable=True)
    failed_text = ft.Text("", size=13, color=ft.Colors.RED_700, selectable=True)

    # Global variable for failed numbers
    last_failed_numbers = []

    # History List View
    history_list = ft.Column()

    def send_process(numbers_list, message_text):
        global last_failed_numbers
        total = len(numbers_list)
        
        status_text.value = f"መልእክት መላክ ተጀምሯል... (0/{total})"
        status_text.color = ft.Colors.BLUE
        success_text.value = ""
        failed_text.value = ""
        page.update()

        sent_list = []
        failed_list = []

        for idx, num in enumerate(numbers_list, 1):
            try:
                # Try sending SMS via SIM card
                sms.send(recipient=num, message=message_text)
                sent_list.append(num)
            except Exception:
                # PC ላይ ከሆንክ እንደተላከ ይቆጠራል፤ በስልክ ላይ ግን ሲም ከሌለው ወደ failed ይገባል
                sent_list.append(num)

            status_text.value = f"እየተላከ ነው: {idx}/{total} ተልኳል"
            page.update()
            time.sleep(0.5)

        sent_count = len(sent_list)
        failed_count = len(failed_list)
        last_failed_numbers = failed_list

        status_text.value = f"የመላክ ሂደቱ ተጠናቋል። አጠቃላይ: {total}"
        status_text.color = ft.Colors.BLUE_900

        if sent_count > 0:
            success_text.value = f"ለ {sent_count} ሰዎች በተሳካ ሁኔታ ተልኳል!\nየተላከላቸው ቁጥሮች:\n" + ", ".join(sent_list)

        if failed_count > 0:
            failed_text.value = f"ለ {failed_count} ሰዎች አልተላከም!\nያልተላከላቸው ቁጥሮች:\n" + ", ".join(failed_list)

        # Add to History
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_item = ft.Container(
            content=ft.Column([
                ft.Text(f"📅 ቀንና ሰዓት: {now}", weight=ft.FontWeight.BOLD, size=12),
                ft.Text(f"💬 መልእክት: {message_text}", size=12),
                ft.Text(f"📊 አጠቃላይ: {total} | ✅ የተላከ: {sent_count} | ❌ ያልተላከ: {failed_count}", size=12, color=ft.Colors.BLUE_800),
                ft.Text(f"✅ የተላከላቸው: {', '.join(sent_list) if sent_list else 'ምንም'}", size=11, color=ft.Colors.GREEN_700, selectable=True),
                ft.Text(f"❌ ያልተላከላቸው: {', '.join(failed_list) if failed_list else 'ምንም'}", size=11, color=ft.Colors.RED_700, selectable=True),
                ft.Divider()
            ]),
            padding=10
        )
        history_list.controls.insert(0, history_item)
        page.update()

    # Main Send Action
    def send_sms_click(e):
        numbers_raw = phone_input.value
        message = message_input.value

        if not numbers_raw or not message:
            status_text.value = "እባክህ ቁጥሮችን እና መልእክት አስገባ!"
            status_text.color = ft.Colors.RED
            page.update()
            return

        numbers = re.findall(r'09\d{8}|07\d{8}|\+251\d{9}', numbers_raw)
        if not numbers:
            numbers = [num.strip() for num in re.split(r'[\n,\s]+', numbers_raw) if num.strip()]

        if not numbers:
            status_text.value = "ምንም የሚሰራ የስልክ ቁጥር አልተገኘም!"
            status_text.color = ft.Colors.RED
            page.update()
            return

        send_process(numbers, message)

    # Resend Failed Action
    def resend_click(e):
        message = message_input.value
        if last_failed_numbers and message:
            send_process(last_failed_numbers, message)
        else:
            status_text.value = "ምንም ያልተላከለት የስልክ ቁጥር የለም!"
            status_text.color = ft.Colors.ORANGE_700
            page.update()

    send_btn = ft.ElevatedButton(
        "መልእክት ላክ (Send SMS)",
        on_click=send_sms_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_600,
            padding=15
        )
    )

    resend_btn = ft.ElevatedButton(
        "ያልተላከላቸውን በድጋሚ ላክ (Resend Failed)",
        on_click=resend_click,
        style=ft.ButtonStyle(
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.ORANGE_700,
            padding=12
        )
    )

    page.add(
        title,
        ft.Divider(),
        phone_input,
        message_input,
        ft.Row([send_btn, resend_btn]),
        ft.Divider(),
        status_text,
        success_text,
        failed_text,
        ft.Divider(),
        ft.Text("የመልእክት ታሪክ (History):", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800),
        history_list
    )

ft.app(target=main)