import subprocess
import sys
import os


def send_whatsapp(to: str, message: str, script_dir: str = ".") -> bool:
    """
    Send a WhatsApp message via Baileys (Node.js).

    Args:
        to:         Phone number with country code (e.g. "96170123456")
                    OR a group JID (e.g. "120363XXXXXXXXX@g.us")
        message:    The text message to send.
        script_dir: Directory where sender.js lives.

    Returns:
        True if sent successfully, False otherwise.
    """
    script_path = os.path.join(script_dir, "sender.js")

    if not os.path.isfile(script_path):
        print(f"[ERROR] sender.js not found at: {script_path}")
        return False

    try:
        result = subprocess.run(
            ["node", script_path, to, message],
            capture_output=False,
            text=True,
            cwd=script_dir,
        )

        if result.returncode == 0:
            print(f"[OK] Message sent to {to}")
            return True
        else:
            print(f"[ERROR] Node.js exited with code {result.returncode}")
            return False

    except FileNotFoundError:
        print("[ERROR] 'node' not found. Is Node.js installed?")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        return False


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))

    # ── Examples ─────────────────────────────────────────────────────────────
    # Send to an individual:
    # send_whatsapp("96170123456", "Hello!", script_dir=here)

    # Send to a group (get the JID by running: node list_groups.js)
    # send_whatsapp("120363XXXXXXXXX@g.us", "Hello group!", script_dir=here)
    # ─────────────────────────────────────────────────────────────────────────

    RECIPIENT = "96176412744"           # ← individual number OR group JID
    MESSAGE   = "Hello from Python!"

    send_whatsapp(RECIPIENT, MESSAGE, script_dir=here)