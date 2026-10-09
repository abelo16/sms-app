import flet as ft
from plyer import sms
import asyncio
import re
import sys
from datetime import datetime

# Android ላይ መሆኑን ማረጋገጫ (Android ላይ ብቻ True ይሆናል)
IS_ANDROID = hasattr(sys, "getandroidapilevel")

if IS_ANDROID:
    from flet_permission_handler import PermissionHandler, Permission
else:
    PermissionHandler = None  # Windows/Desktop ላይ import እንዳይደረግ

def main(page: ft.Page):
    page.title = "የትምህርት ክፍል መልዕክት መላኪያ"
    page.window_width = 450
    page.window_height = 800
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # Permission Handler Setup — Android ላይ ብቻ ይፈጠራል
    if IS_ANDROID:
        ph = PermissionHandler()
        page.overlay.append(ph)
    else:
        ph = None

    # Colors fallback
    blue_700 = getattr(ft, "Colors", getattr(ft, "colors", None)).BLUE_700 if hasattr(ft, "Colors") else "blue700"
    blue_400 = getattr(ft, "Colors", getattr(ft, "colors", None)).BLUE_400 if hasattr(ft, "Colors") else "blue400"
    blue_600 = getattr(ft, "Colors", getattr(ft, "colors", None)).BLUE_600 if hasattr(ft, "Colors") else "blue600"
    blue_800 = getattr(ft, "Colors", getattr(ft, "colors", None)).BLUE_800 if hasattr(ft, "Colors") else "blue800"
    blue_900 = getattr(ft, "Colors", getattr(ft, "colors", None)).BLUE_900 if hasattr(ft, "Colors") else "blue900"
    green_700 = getattr(ft, "Colors", getattr(ft, "colors", None)).GREEN_700 if hasattr(ft, "Colors") else "green700"
    red_700 = getattr(ft, "Colors", getattr(ft, "colors", None)).RED_700 if hasattr(ft, "Colors") else "red700"
    orange_700 = getattr(ft, "Colors", getattr(ft, "colors", None)).ORANGE_700 if hasattr(ft, "Colors") else "orange700"
    white_color = getattr(ft, "Colors", getattr(ft, "colors", None)).WHITE if hasattr(ft, "Colors") else "white"

    # Title
    title = ft.Text(
        "የትምህርት ክፍል መልዕክት መላኪያ", 
        size=22, 
        weight="bold", 
        color=blue_700
    )

    # Phone numbers input
    phone_input = ft.TextField(
        label="የስልክ ቁጥሮች (ከExcel/Word ኮፒ አድርገህ ወደታች ማስገባት ትችላለህ)",
        hint_text="ምሳሌ:\n0911223344\n0922334455",
        multiline=True,
        min_lines=5,
        border_color=blue_400
    )

    # Message input
    message_input = ft.TextField(
        label="የሚላከው መልእክት",
        hint_text="መልእክትህን እዚህ ፃፍ...",
        multiline=True,
        min_lines=4,
        border_color=blue_400
    )

    # Status Text
    status_text = ft.Text("", size=14, color=blue_700, weight="bold")
    
    # Report Container
    success_text = ft.Text("", size=13, color=green_700, selectable=True)
    failed_text = ft.Text("", size=13, color=red_700, selectable=True)

    # Global variable for failed numbers
    last_failed_numbers = []

    # History List View
    history_list = ft.Column()

    async def check_and_request_sms_permission():
        """Runtime Permission ጥያቄ የሚያቀርብ ተግባር"""
        if not IS_ANDROID or ph is None:
            return True  # PC ላይ — ፍቃድ ጥያቄ የለም
        try:
            if not ph.has_permission(Permission.SMS):
                return ph.request_permission(Permission.SMS)
            return True
        except Exception as e:
            print(f"Permission check error: {e}")
            return True

    async def send_process(numbers_list, message_text):
        nonlocal last_failed_numbers
        total = len(numbers_list)
        
        status_text.value = "የኤስኤምኤስ ፍቃድ በመፈተሽ ላይ..."
        status_text.color = blue_700
        page.update()

        # የRuntime permission ጥያቄ ማካሄድ
        await check_and_request_sms_permission()
        
        status_text.value = f"መልእክት መላክ ተጀምሯል... (0/{total})"
        success_text.value = ""
        failed_text.value = ""
        page.update()

        sent_list = []
        failed_list = []

        for idx, num in enumerate(numbers_list, 1):
            try:
                # መልእክት መላክ
                sms.send(recipient=num, message=message_text)
                sent_list.append(num)
            except Exception as ex:
                # እውነተኛውን የስህተት ምክንያት መያዝ
                err_msg = str(ex) if str(ex) else "የፍቃድ ወይም የሲም ካርድ ችግር"
                failed_list.append(f"{num} ({err_msg})")

            status_text.value = f"እየተላከ ነው: {idx}/{total} ተካሂዷል"
            page.update()
            await asyncio.sleep(0.3)

        sent_count = len(sent_list)
        failed_count = len(failed_list)
        
        # ያልተላከላቸውን ቁጥሮች ብቻ ለResend ማዘጋጀት
        last_failed_numbers = [item.split()[0] for item in failed_list]

        status_text.value = f"የመላክ ሂደቱ ተጠናቋል። አጠቃላይ: {total}"
        status_text.color = blue_900

        if sent_count > 0:
            success_text.value = f"ለ {sent_count} ሰዎች በተሳካ ሁኔታ ተልኳል!\nየተላከላቸው ቁጥሮች:\n" + ", ".join(sent_list)

        if failed_count > 0:
            failed_text.value = f"ለ {failed_count} ሰዎች አልተላከም!\nምክንያት እና ቁጥሮች:\n" + "\n".join(failed_list)

        # Add to History
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        history_item = ft.Container(
            content=ft.Column([
                ft.Text(f"📅 ቀንና ሰዓት: {now}", weight="bold", size=12),
                ft.Text(f"💬 መልእክት: {message_text}", size=12),
                ft.Text(f"📊 አጠቃላይ: {total} | ✅ የተላከ: {sent_count} | ❌ ያልተላከ: {failed_count}", size=12, color=blue_800),
                ft.Text(f"✅ የተላከላቸው: {', '.join(sent_list) if sent_list else 'ምንም'}", size=11, color=green_700, selectable=True),
                ft.Text(f"❌ ያልተላከላቸው: {', '.join(failed_list) if failed_list else 'ምንም'}", size=11, color=red_700, selectable=True),
                ft.Divider()
            ]),
            padding=10
        )
        history_list.controls.insert(0, history_item)
        page.update()

    # Main Send Action
    async def send_sms_click(e):
        numbers_raw = phone_input.value
        message = message_input.value

        if not numbers_raw or not message:
            status_text.value = "እባክህ ቁጥሮችን እና መልእክት አስገባ!"
            status_text.color = red_700
            page.update()
            return

        numbers = re.findall(r'09\d{8}|07\d{8}|\+251\d{9}', numbers_raw)
        if not numbers:
            numbers = [num.strip() for num in re.split(r'[\n,\s]+', numbers_raw) if num.strip()]

        if not numbers:
            status_text.value = "ምንም የሚሰራ የስልክ ቁጥር አልተገኘም!"
            status_text.color = red_700
            page.update()
            return

        await send_process(numbers, message)

    # Resend Failed Action
    async def resend_click(e):
        message = message_input.value
        if last_failed_numbers and message:
            await send_process(last_failed_numbers, message)
        else:
            status_text.value = "ምንም ያልተላከለት የስልክ ቁጥር የለም!"
            status_text.color = orange_700
            page.update()

    # Button compatibility layer
    ButtonClass = getattr(ft, "ElevatedButton", getattr(ft, "Button", None))

    send_btn = ButtonClass(
        "መልእክት ላክ (Send SMS)",
        on_click=send_sms_click,
        style=ft.ButtonStyle(
            color=white_color,
            bgcolor=blue_600,
            padding=15
        )
    )

    resend_btn = ButtonClass(
        "ያልተላከላቸውን በድጋሚ ላክ (Resend Failed)",
        on_click=resend_click,
        style=ft.ButtonStyle(
            color=white_color,
            bgcolor=orange_700,
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
        ft.Text("የመልእክት ታሪክ (History):", size=16, weight="bold", color=blue_800),
        history_list
    )

if __name__ == "__main__":
    app_runner = getattr(ft, "run", getattr(ft, "app", None))
    app_runner(main)