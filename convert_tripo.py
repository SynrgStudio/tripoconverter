import os
import sys
import subprocess
import time
import shutil
from urllib.parse import urlparse


def ensure_python_package(module_name, package_name=None):
    package_name = package_name or module_name

    try:
        __import__(module_name)
        return True
    except ImportError:
        print(f"[!] Missing Python dependency '{package_name}'. Trying to install it...")

    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", package_name],
            check=True,
            shell=False,
        )
        __import__(module_name)
        print(f"[OK] Dependency installed: {package_name}")
        return True
    except Exception as error:
        print(f"[ERROR] Could not install '{package_name}': {error}")
        return False


def ensure_playwright_browser():
    try:
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"],
            check=True,
            shell=False,
        )
        return True
    except Exception as error:
        print(f"[ERROR] Could not install Chromium for Playwright: {error}")
        return False


def check_and_install_dependencies():
    """Check whether gltf-transform is installed and install it if needed."""
    print("--- Checking system tools ---")

    # 1. Is gltf-transform already installed?
    if shutil.which("gltf-transform"):
        print("[OK] Conversion engine detected.")
        return True

    print("[!] Conversion engine not found. Trying to install it automatically...")

    # 2. Is npm installed?
    if not shutil.which("npm"):
        print("\n[CRITICAL ERROR] Node.js (npm) was not found on your system.")
        print("To use this script, please download and install Node.js from:")
        print("https://nodejs.org/")
        print("\nOnce installed, run the script again.")
        return False

    # 3. Try to install gltf-transform
    try:
        print("Installing @gltf-transform/cli... This can take a minute (only the first time).")
        subprocess.run(
            ["npm", "install", "-g", "@gltf-transform/cli"],
            check=True,
            shell=True,
            capture_output=True,
        )

        if shutil.which("gltf-transform"):
            print("[OK] Installation successful.")
            return True

        print("[!] Installed but not detected in the current PATH. Try reopening the folder or terminal.")
        return False
    except Exception as error:
        print(f"[ERROR] Automatic installation failed: {error}")
        print("Try opening the terminal as administrator and run: npm install -g @gltf-transform/cli")
        return False


def prompt_for_input_source():
    print("\nPaste a Tripo URL or a local .glb/.gltf path and press Enter.")
    print("Press Enter on an empty line to exit.")

    while True:
        user_input = input("> ").strip().strip('"')
        if not user_input:
            return None

        if user_input.lower() in {"exit", "quit"}:
            return None

        return user_input


def build_download_path(source_url):
    parsed_url = urlparse(source_url)
    file_name = os.path.basename(parsed_url.path)

    if not file_name.lower().endswith(".glb"):
        file_name = f"tripo_download_{int(time.time())}.glb"

    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, file_name)


def find_glb_url_from_tripo_page(page_url):
    if not ensure_python_package("playwright", "playwright"):
        return None

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("[ERROR] Playwright is missing. Run: python -m pip install playwright")
        print("Then run: python -m playwright install chromium")
        return None

    if not ensure_playwright_browser():
        return None

    print(f"\n--- Analyzing the Tripo page ---")
    print(f"URL: {page_url}")

    found_urls = []

    def remember_url(candidate_url):
        lowered_url = candidate_url.lower()
        if ".glb" in lowered_url and "tripo" in lowered_url:
            if candidate_url not in found_urls:
                found_urls.append(candidate_url)
                print(f"[+] GLB detected: {candidate_url}")

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            page.on("request", lambda request: remember_url(request.url))
            page.on("response", lambda response: remember_url(response.url))

            try:
                page.goto(page_url, wait_until="domcontentloaded", timeout=45000)
            except Exception as navigation_error:
                print(f"[!] Warning while opening the page: {navigation_error}")

            page.wait_for_timeout(8000)

            try:
                page.mouse.wheel(0, 2000)
                page.wait_for_timeout(3000)
            except Exception:
                pass

            page.wait_for_timeout(5000)
            browser.close()
    except Exception as error:
        print(f"[ERROR] Could not inspect the page: {error}")
        return None

    if not found_urls:
        print("[!] No .glb URL was found in the page network traffic.")
        return None

    prioritized = [candidate_url for candidate_url in found_urls if "meshopt" in candidate_url.lower()]
    if prioritized:
        return prioritized[0]

    prioritized = [candidate_url for candidate_url in found_urls if "tripo_pbr_model" in candidate_url.lower()]
    if prioritized:
        return prioritized[0]

    return found_urls[0]


def download_glb_file(file_url, destination_path, referer=None):
    if not ensure_python_package("requests", "requests"):
        return False

    import requests

    print(f"\n--- Downloading GLB file ---")
    print(f"URL: {file_url}")

    headers = {
        "User-Agent": "Mozilla/5.0",
    }

    if referer:
        headers["Referer"] = referer

    try:
        with requests.get(file_url, stream=True, timeout=120, headers=headers) as response:
            response.raise_for_status()

            downloaded_bytes = 0
            with open(destination_path, "wb") as output_file:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output_file.write(chunk)
                        downloaded_bytes += len(chunk)

        size_mb = downloaded_bytes / (1024 * 1024)
        print(f"[OK] GLB downloaded to: {destination_path}")
        print(f"Downloaded size: {size_mb:.2f} MB")
        return True
    except Exception as error:
        print(f"[ERROR] Could not download the GLB: {error}")
        return False


def convert_tripo_to_standard(input_path, delete_input=False):
    # Output file name
    base, ext = os.path.splitext(input_path)
    output_path = f"{base}_ready.glb"

    print(f"\n--- Processing: {os.path.basename(input_path)} ---")

    try:
        # Use dequantize to clean the file.
        # This removes both KHR_mesh_quantization and EXT_meshopt_compression.
        result = subprocess.run(
            ["gltf-transform", "dequantize", input_path, output_path],
            capture_output=True,
            text=True,
            shell=True,
        )

        if result.returncode == 0:
            print(f"[OK] Compatible file generated at:\n{output_path}")
            new_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"Final size: {new_size:.2f} MB")

            if delete_input and os.path.isfile(input_path) and os.path.abspath(input_path) != os.path.abspath(output_path):
                try:
                    os.remove(input_path)
                    print(f"[OK] Original file deleted: {input_path}")
                except Exception as cleanup_error:
                    print(f"[!] Conversion succeeded, but the original file could not be deleted: {cleanup_error}")

            return True

        print("ERROR during conversion:")
        print(result.stderr)
        return False
    except Exception as error:
        print(f"ERROR: Could not run the converter.\nDetails: {str(error)}")
        return False


def process_source(source):
    source = source.strip().strip('"')

    if source.startswith(("http://", "https://")):
        glb_url = find_glb_url_from_tripo_page(source)
        if not glb_url:
            return False

        downloaded_path = build_download_path(glb_url)
        if download_glb_file(glb_url, downloaded_path, referer=source):
            return convert_tripo_to_standard(downloaded_path, delete_input=True)
        return False

    if source.lower().endswith((".glb", ".gltf")):
        return convert_tripo_to_standard(source, delete_input=True)

    print(f"[ERROR] The value you entered is neither a URL nor a glTF/GLB file: {source}")
    return False


if __name__ == "__main__":
    print("==========================================")
    print("   TRIPO 3D TO WINDOWS VIEWER CONVERTER   ")
    print("==========================================")

    if len(sys.argv) < 2:
        source = prompt_for_input_source()
        if source:
            if check_and_install_dependencies():
                process_source(source)
    else:
        if check_and_install_dependencies():
            for argument in sys.argv[1:]:
                process_source(argument)

    print("\nProcess finished. Press ENTER to exit...")
    input()