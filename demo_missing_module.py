"""
demo_missing_module.py
======================
DEMO: ModuleNotFoundError → agent auto-installs the package

Run with:  agent> run demo_missing_module.py
"""
import qrcode  # NOT installed by default — agent will pip install qrcode

data = "https://github.com/self-healing-agent"
qr = qrcode.make(data)
qr.save("qrcode_demo.png")
print("✅ QR code saved to qrcode_demo.png")
