import undetected_chromedriver as uc
import time

print("Starting stealth Chrome test...")

options = uc.ChromeOptions()
options.add_argument('--start-maximized')

print("Launching Chrome...")

# Force use Chrome v150
driver = uc.Chrome(
    options=options,
    version_main=150
)

print("Chrome launched!")

driver.get("https://bot.sannysoft.com")
input("Press Enter to close...")
driver.quit()