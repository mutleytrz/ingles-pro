# icons.py — Icones SVG Premium (Filled/Gradient Style — 48px)
# Cada módulo tem sua cor de destaque única

def get_svg(name: str, color: str = "#06b6d4") -> str:
    _icons_map = {
        "ESCOLA": """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="ge" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#818cf8"/><stop offset="100%" stop-color="#6366f1"/></linearGradient></defs>
<path d="M24 4L4 16l20 12 16-9.6V32h4V16L24 4z" fill="url(#ge)"/>
<path d="M8 18.4V30c0 2 2 4 4 5.2l12 7.2 12-7.2c2-1.2 4-3.2 4-5.2V18.4L24 28 8 18.4z" fill="url(#ge)" opacity="0.7"/>
<circle cx="24" cy="16" r="3" fill="#fff" opacity="0.9"/>
</svg>""",
        "AEROPORTO": """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="ga" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#38bdf8"/><stop offset="100%" stop-color="#0284c7"/></linearGradient></defs>
<path d="M42 22l-16-4-4-14h-4l2 14H8l-3-4H2l2 6-2 6h3l3-4h12l-2 14h4l4-14 16-4v-4z" fill="url(#ga)"/>
<ellipse cx="24" cy="42" rx="16" ry="2" fill="#0284c7" opacity="0.2"/>
</svg>""",
        "HOTEL": """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="gh" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#f59e0b"/><stop offset="100%" stop-color="#d97706"/></linearGradient></defs>
<rect x="8" y="8" width="32" height="36" rx="4" fill="url(#gh)"/>
<rect x="12" y="14" width="6" height="6" rx="1" fill="#fef3c7"/>
<rect x="21" y="14" width="6" height="6" rx="1" fill="#fef3c7"/>
<rect x="30" y="14" width="6" height="6" rx="1" fill="#fef3c7"/>
<rect x="12" y="24" width="6" height="6" rx="1" fill="#fef3c7"/>
<rect x="21" y="24" width="6" height="6" rx="1" fill="#fef3c7"/>
<rect x="30" y="24" width="6" height="6" rx="1" fill="#fef3c7"/>
<rect x="19" y="34" width="10" height="10" rx="2" fill="#92400e"/>
<circle cx="27" cy="39" r="1" fill="#fbbf24"/>
</svg>""",
        "PALAVRAS": """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="gp" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#a78bfa"/><stop offset="100%" stop-color="#7c3aed"/></linearGradient></defs>
<path d="M6 8a4 4 0 014-4h10a4 4 0 014 4v32a3 3 0 00-3-3H6V8z" fill="url(#gp)"/>
<path d="M42 8a4 4 0 00-4-4H28a4 4 0 00-4 4v32a3 3 0 013-3h15V8z" fill="url(#gp)" opacity="0.75"/>
<path d="M12 14h6M12 20h6M12 26h4" stroke="#ede9fe" stroke-width="2" stroke-linecap="round"/>
<path d="M30 14h6M30 20h6M30 26h4" stroke="#ede9fe" stroke-width="2" stroke-linecap="round"/>
</svg>""",
        "TRABALHO": """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="gt" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#34d399"/><stop offset="100%" stop-color="#059669"/></linearGradient></defs>
<rect x="4" y="16" width="40" height="28" rx="4" fill="url(#gt)"/>
<path d="M16 16V12a4 4 0 014-4h8a4 4 0 014 4v4" stroke="#065f46" stroke-width="3" fill="none"/>
<rect x="20" y="26" width="8" height="6" rx="2" fill="#ecfdf5"/>
<path d="M4 28h40" stroke="#065f46" stroke-width="1" opacity="0.3"/>
</svg>""",
        "COMPRAS": """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="gc" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#fb923c"/><stop offset="100%" stop-color="#ea580c"/></linearGradient></defs>
<path d="M12 6h24l4 10H8l4-10z" fill="url(#gc)" opacity="0.8"/>
<rect x="8" y="16" width="32" height="24" rx="4" fill="url(#gc)"/>
<path d="M18 4v6M30 4v6" stroke="#fed7aa" stroke-width="2.5" stroke-linecap="round"/>
<path d="M20 26l4 4 6-8" stroke="#fff7ed" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",
        "SAUDE": """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="gs" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#fb7185"/><stop offset="100%" stop-color="#e11d48"/></linearGradient></defs>
<path d="M24 42s-16-10.4-16-22A10 10 0 0124 12.8 10 10 0 0140 20c0 11.6-16 22-16 22z" fill="url(#gs)"/>
<path d="M14 22h6l3-6 4 12 3-6h6" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
</svg>""",
        "CASUAL": """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="gca" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#a3e635"/><stop offset="100%" stop-color="#65a30d"/></linearGradient></defs>
<path d="M10 16h22a8 8 0 010 16H10V16z" fill="url(#gca)"/>
<path d="M10 16a6 6 0 016-6h10a6 6 0 016 6" fill="url(#gca)" opacity="0.6"/>
<rect x="8" y="32" width="26" height="4" rx="2" fill="#4d7c0f"/>
<path d="M34 18c2 0 4 1.6 4 3.6s-2 3.6-4 3.6" stroke="#65a30d" stroke-width="2.5" stroke-linecap="round"/>
<path d="M14 8v3M20 6v5M26 8v3" stroke="#ecfccb" stroke-width="2" stroke-linecap="round" opacity="0.8"/>
</svg>""",
        "TRANSPORTE": """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="gtr" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#22d3ee"/><stop offset="100%" stop-color="#0891b2"/></linearGradient></defs>
<rect x="4" y="12" width="40" height="24" rx="6" fill="url(#gtr)"/>
<rect x="8" y="16" width="14" height="10" rx="2" fill="#cffafe"/>
<rect x="26" y="16" width="14" height="10" rx="2" fill="#cffafe"/>
<circle cx="14" cy="38" r="4" fill="#164e63"/>
<circle cx="14" cy="38" r="2" fill="#67e8f9"/>
<circle cx="34" cy="38" r="4" fill="#164e63"/>
<circle cx="34" cy="38" r="2" fill="#67e8f9"/>
<rect x="2" y="30" width="8" height="4" rx="2" fill="#fbbf24"/>
</svg>""",
        "TECNOLOGIA": """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="gte" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#c084fc"/><stop offset="100%" stop-color="#9333ea"/></linearGradient></defs>
<rect x="6" y="6" width="36" height="26" rx="4" fill="url(#gte)"/>
<rect x="10" y="10" width="28" height="18" rx="2" fill="#f3e8ff"/>
<path d="M18 36h12v4H18z" fill="url(#gte)" opacity="0.7"/>
<rect x="14" y="40" width="20" height="3" rx="1.5" fill="url(#gte)"/>
<circle cx="24" cy="19" r="4" fill="#9333ea" opacity="0.3"/>
<path d="M22 18l4 2-4 2z" fill="#7e22ce"/>
</svg>""",
        "COTIDIANO": """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="gco" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#fbbf24"/><stop offset="100%" stop-color="#f59e0b"/></linearGradient></defs>
<path d="M6 22L24 6l18 16v20a2 2 0 01-2 2H8a2 2 0 01-2-2V22z" fill="url(#gco)"/>
<rect x="18" y="28" width="12" height="16" rx="2" fill="#92400e"/>
<rect x="12" y="20" width="8" height="8" rx="1" fill="#fef3c7"/>
<rect x="28" y="20" width="8" height="8" rx="1" fill="#fef3c7"/>
<circle cx="27" cy="36" r="1.5" fill="#fbbf24"/>
<path d="M22 4l2-2 2 2" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" opacity="0.5"/>
</svg>""",
        "LAZER": """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="gl" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#f472b6"/><stop offset="100%" stop-color="#db2777"/></linearGradient></defs>
<rect x="2" y="12" width="44" height="24" rx="12" fill="url(#gl)"/>
<circle cx="15" cy="24" r="6" fill="#fce7f3" opacity="0.3"/>
<path d="M13 24h4M15 22v4" stroke="#fff" stroke-width="2.5" stroke-linecap="round"/>
<circle cx="33" cy="22" r="2.5" fill="#fff" opacity="0.9"/>
<circle cx="37" cy="26" r="2.5" fill="#fff" opacity="0.6"/>
<circle cx="33" cy="26" r="0.8" fill="#fff" opacity="0.4"/>
</svg>""",
        "RELACIONAMENTO": """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="gr" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#f87171"/><stop offset="100%" stop-color="#dc2626"/></linearGradient></defs>
<path d="M16 38s-12-7.8-12-16.5A7.5 7.5 0 0116 15.6a7.5 7.5 0 0112 5.9c0 8.7-12 16.5-12 16.5z" fill="url(#gr)" opacity="0.7"/>
<path d="M32 34s-10-6.5-10-13.8A6.2 6.2 0 0132 14.8a6.2 6.2 0 0110 5.4c0 7.3-10 13.8-10 13.8z" fill="url(#gr)"/>
<circle cx="16" cy="22" r="2" fill="#fff" opacity="0.5"/>
<circle cx="32" cy="20" r="2" fill="#fff" opacity="0.6"/>
</svg>""",
    }
    # Fallback icon
    svg = _icons_map.get(name, """<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 48 48" fill="none">
<defs><linearGradient id="gf" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#94a3b8"/><stop offset="100%" stop-color="#64748b"/></linearGradient></defs>
<rect x="4" y="4" width="40" height="40" rx="8" fill="url(#gf)"/>
<path d="M18 18h12v12H18z" fill="#fff" opacity="0.3" rx="2"/>
</svg>""")
    return svg.replace("{color}", color)
