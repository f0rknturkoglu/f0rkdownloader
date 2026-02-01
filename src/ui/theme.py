from questionary import Style

# Questionary (Menü) Stilleri
custom_style = Style(
    [
        ("qmark", "fg:#FF9D00 bold"),  # Soru işareti rengi
        ("question", "bold"),  # Soru metni
        ("answer", "fg:#FF9D00 bold"),  # Cevap rengi
        ("pointer", "fg:#FF9D00 bold"),  # Seçim oku rengi
        ("highlighted", "fg:#FF9D00 bold"),  # Seçili öğe
        ("selected", "fg:#FF9D00"),  # Seçilen
        ("separator", "fg:#cc5454"),
        ("instruction", ""),  # Talimat metni
        ("text", ""),  # Düz metin
        ("disabled", "fg:#858585 italic"),  # Devre dışı
    ]
)

# Rich (Konsol) Renkleri
COLORS = {
    "primary": "orange1",
    "success": "green",
    "error": "red",
    "warning": "yellow",
    "info": "cyan",
    "text": "white",
}

APP_TITLE = """
███████╗ ██████╗ ██████╗ ██╗  ██╗███╗   ██╗
██╔════╝██╔═████╗██╔══██╗██║ ██╔╝████╗  ██║
█████╗  ██║██╔██║██████╔╝█████╔╝ ██╔██╗ ██║
██╔══╝  ████╔╝██║██╔══██╗██╔═██╗ ██║╚██╗██║
██║     ╚██████╔╝██║  ██║██║  ██╗██║ ╚████║
╚═╝      ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
    D 0 W N L 0 A D E R   C L I
"""
