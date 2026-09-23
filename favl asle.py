import cv2
import subprocess
import time
import os

# لیست برنامه‌هایی که می‌خواهی قفل کنی (اسم فایل اجرایی آنها)
# مثال: 'notepad.exe', 'chrome.exe', 'spotify.exe'
blocked_apps = []

# ==========================================
# ۱. توابع کمکی با استفاده از دستورات ویندوز
# ==========================================

def is_app_running(app_name):
    """
    بررسی می‌کند آیا برنامه در حال اجراست یا خیر
    با استفاده از دستور tasklist ویندوز
    """
    # اجرای دستور tasklist در پس‌زمینه
    result = subprocess.run(['tasklist', '/FI', f'IMAGENAME eq {app_name}'], 
                            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
    # اگر اسم برنامه در خروجی بود، یعنی باز است
    return app_name.lower() in result.stdout.lower()

def suspend_app(app_name):
    """
    برنامه را فریز (Suspend) می‌کند
    با استفاده از دستور PowerShell ویندوز
    """
    # حذف پسوند .exe برای دستور PowerShell
    process_name = app_name.replace('.exe', '')
    command = f'Get-Process -Name "{process_name}" -ErrorAction SilentlyContinue | Suspend-Process'
    subprocess.run(['powershell', '-Command', command], 
                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)

def resume_app(app_name):
    """
    برنامه فریز شده را دوباره فعال (Resume) می‌کند
    """
    process_name = app_name.replace('.exe', '')
    command = f'Get-Process -Name "{process_name}" -ErrorAction SilentlyContinue | Resume-Process'
    subprocess.run(['powershell', '-Command', command], 
                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)

# ==========================================
# ۲. توابع اصلی برنامه
# ==========================================

def get_installed_apps():
    """دریافت لیست ساده از پوشه Program Files"""
    apps = []
    program_files = os.environ.get('PROGRAMFILES', 'C:\\Program Files')
    if os.path.exists(program_files):
        for item in os.listdir(program_files):
            if os.path.isdir(os.path.join(program_files, item)):
                apps.append(item + ".exe") # اضافه کردن پسوند برای تشخیص راحت‌تر
    return apps

def select_apps_to_block():
    """نمایش لیست و دریافت انتخاب کاربر"""
    print("\n=== لیست برنامه‌های نصب شده ===")
    apps = get_installed_apps()
    
    for i, app in enumerate(apps, 1):
        print(f"{i}. {app}")
    
    print("\nشماره برنامه‌هایی که می‌خواهی قفل کنی را وارد کن (با کاما جدا کن، مثلاً: 1,3)")
    print("یا 'q' برای خروج")
    
    choice = input("> ")
    if choice.lower() == 'q':
        return False
    
    try:
        indices = [int(x.strip()) - 1 for x in choice.split(',')]
        for idx in indices:
            if 0 <= idx < len(apps):
                blocked_apps.append(apps[idx])
        print(f"\n[OK] برنامه‌های قفل شده: {', '.join(blocked_apps)}")
        return True
    except:
        print("[ERROR] ورودی نامعتبر!")
        return False

def exercise_mode():
    """باز کردن دوربین و شمارش حرکت به عنوان شنا"""
    print("\n=== حالت ورزش ===")
    print("دوربین باز می‌شود. شروع به حرکت کن تا 10 شنا شمارش شود!")
    print("برای خروج اضطراری، کلید 'q' را روی کیبورد بزن")
    
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] دوربین باز نشد!")
        return False
    
    prev_frame = None
    pushup_count = 0
    pushup_threshold = 15000  # آستانه تشخیص حرکت
    movement_accumulator = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        if prev_frame is not None:
            frame_delta = cv2.absdiff(prev_frame, gray)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            
            # اینجا از متد sum خودِ آرایه (که از numpy می‌آید) استفاده می‌کنیم
            motion = thresh.sum()
            movement_accumulator += motion
            
            if movement_accumulator >= pushup_threshold:
                pushup_count += 1
                movement_accumulator = 0
                print(f"\n[OK] شنا شمارش شد! تعداد: {pushup_count}/10")
                
                if pushup_count >= 10:
                    print("\n[SUCCESS] آفرین! 10 شنا کامل شد!")
                    break
        
        prev_frame = gray.copy()
        
        cv2.putText(frame, f"Push-ups: {pushup_count}/10", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.imshow('Exercise Mode - Press q to quit', frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return pushup_count >= 10

def usage_timer():
    """تایمر 15 دقیقه‌ای"""
    print("\n=== تایمر استفاده 15 دقیقه‌ای ===")
    print("حالا می‌توانی از برنامه استفاده کنی. بعد از 15 دقیقه دوباره قفل می‌شود.")
    
    for remaining in range(900, 0, -1):
        mins, secs = divmod(remaining, 60)
        print(f"\rزمان باقی‌مانده: {mins:02d}:{secs:02d}", end="", flush=True)
        time.sleep(1)
    print("\n\n[WARNING] زمان 15 دقیقه تمام شد!")

def monitor_apps():
    """حلقه اصلی نظارت بر برنامه‌ها"""
    print("\n=== شروع نظارت ===")
    print("برای توقف کامل برنامه، کلیدهای Ctrl + C را بزن")
    
    while True:
        for app in blocked_apps:
            if is_app_running(app):
                print(f"\n[WARNING] برنامه قفل‌شده شناسایی شد: {app}")
                print("در حال فریز کردن برنامه...")
                
                # ۱. فریز کردن برنامه
                suspend_app(app)
                
                # ۲. درخواست ورزش
                if exercise_mode():
                    print("\n[OK] ورزش کامل شد! در حال آزادسازی برنامه...")
                    # ۳. آزاد کردن برنامه
                    resume_app(app)
                    
                    # ۴. شروع تایمر 15 دقیقه
                    usage_timer()
                else:
                    print("\n[ERROR] ورزش کامل نشد. برنامه همچنان فریز می‌ماند.")
        
        # هر 3 ثانیه چک کن
        time.sleep(3)

def main():
    print("=" * 40)
    print("برنامه قفل‌کننده ورزشی (نسخه سبک)")
    print("=" * 40)
    
    if not select_apps_to_block():
        print("خروج از برنامه...")
        return
    
    try:
        monitor_apps()
    except KeyboardInterrupt:
        print("\n\nبرنامه متوقف شد. خداحافظ!")

if __name__ == "__main__":
    main()
