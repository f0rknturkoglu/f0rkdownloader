from questionary import Style

# Tema tanımları
# hex: Questionary (menü) için
# primary: Rich (konsol) ana renk
# secondary: Rich (konsol) ikincil renk (ör. info, başlıklar)
THEMES = {
    "ubuntu": {
        "primary": "orange1",        # Ubuntu Orange
        "secondary": "bright_magenta", # Accessible Canonical Aubergine/Violet
        "hex": "#E95420",
        "success": "green",
        "error": "red",
        "warning": "yellow"
    },
    "macintosh": {
        "primary": "white",          # Classic Black/White look (inverted for dark terminals)
        "secondary": "grey70",       # Retro Grey
        "hex": "#FFFFFF",
        "success": "green",
        "error": "red",
        "warning": "yellow"
    },
    "fedora": {
        "primary": "bright_blue",    # Fedora Clear Blue (High contrast)
        "secondary": "cyan",         # Accent Cyan
        "hex": "#5180D8",            # Accessible Fedora Blue
        "success": "green",
        "error": "red",
        "warning": "yellow"
    }
}

def get_style(theme_name="ubuntu"):
    """Seçilen temaya göre questionary stili döndür."""
    theme = THEMES.get(theme_name, THEMES.get("ubuntu"))
    if not theme:
        # Fallback if somehow theme is missing, defaulting to ubuntu values manually
        theme = THEMES["ubuntu"]
        
    color = theme["hex"]
    
    return Style([
        ("qmark", f"fg:{color} bold"),
        ("question", "bold"),
        ("answer", f"fg:{color} bold"),
        ("pointer", f"fg:{color} bold"),
        ("highlighted", f"fg:{color} bold"),
        ("selected", f"fg:{color}"),
        ("separator", "fg:#6C6C6C"),
        ("instruction", "fg:#8A8A8A italic"),
        ("text", ""),
        ("disabled", "fg:#858585 italic"),
    ])

def get_colors(theme_name="ubuntu"):
    """Seçilen temaya göre Rich renklerini döndür."""
    theme = THEMES.get(theme_name, THEMES.get("ubuntu"))
    if not theme:
        theme = THEMES["ubuntu"]

    return {
        "primary": theme["primary"],
        "secondary": theme["secondary"],
        "success": theme["success"],
        "error": theme["error"],
        "warning": theme["warning"],
        "info": theme["secondary"],
        "text": "white",
    }
