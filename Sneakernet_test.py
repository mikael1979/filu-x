#!/usr/bin/env python3
"""
Sneakernet test - Simuloi USB-tikulla tapahtuvaa tiedostojen siirtoa
Käyttö: python3 sneakernet_test.py
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Testikansiot
BASE_DIR = Path("./test_data/sneakernet")
USB_DIR = BASE_DIR / "usb"
ALICE_DIR = BASE_DIR / "alice"
BOB_DIR = BASE_DIR / "bob"

# Värit tulostukseen
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(msg):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{msg}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}")

def run_cmd(cmd, env=None):
    """Suorita komento ja palauta (stdout, stderr, returncode)"""
    print(f"{Colors.YELLOW}$ {cmd}{Colors.END}")
    process = subprocess.run(cmd, shell=True, capture_output=True, text=True, env=env)
    if process.stdout:
        print(process.stdout)
    if process.stderr:
        print(f"{Colors.RED}{process.stderr}{Colors.END}")
    return process.stdout, process.stderr, process.returncode

def check_file_exists(path, description):
    if path.exists():
        print(f"{Colors.GREEN}✓ {description} löytyy: {path}{Colors.END}")
        return True
    else:
        print(f"{Colors.RED}✗ {description} puuttuu: {path}{Colors.END}")
        return False

def main():
    print_step("LENKKARIPROTOKOLLAN TESTAUS")
    print("Tämä testi simuloi kahden käyttäjän välistä tiedostonsiirtoa USB-tikulla.")
    print("Alice luo postauksia, kopioidaan ne USB:lle, ja Bob lukee ne välimuistiin.")
    
    # Siivotaan vanhat testidatat
    if BASE_DIR.exists():
        shutil.rmtree(BASE_DIR)
    BASE_DIR.mkdir(parents=True)
    USB_DIR.mkdir()
    
    # 1. Alustetaan Alice
    print_step("1. Alustetaan Alice")
    env = os.environ.copy()
    env["FILU_X_DATA_DIR"] = str(ALICE_DIR)
    out, err, ret = run_cmd("filu-x init alice --no-password", env=env)
    if ret != 0:
        print(f"{Colors.RED}Virhe Alicen alustuksessa{Colors.END}")
        sys.exit(1)
    
    # 2. Alice luo postauksia
    print_step("2. Alice luo postauksia")
    posts = []
    for msg in ["Ensimmäinen postaus USB-testiin", "Toinen postaus USB-testiin"]:
        out, err, ret = run_cmd(f'filu-x post "{msg}"', env=env)
        if ret != 0:
            print(f"{Colors.RED}Virhe postauksen luonnissa{Colors.END}")
            sys.exit(1)
        # Poimi postauksen ID tulosteesta
        for line in out.splitlines():
            if "Post created:" in line:
                post_id = line.split()[3].replace(":", "")
                posts.append(post_id)
                print(f"   → Postaus ID: {post_id}")
    
    # 3. Alice synkronoi IPFS:ään (jotta manifestiin tulee IPFS-CID:t)
    print_step("3. Alice synkronoi IPFS:ään")
    run_cmd("filu-x sync -v", env=env)
    
    # 4. Kopioidaan Alicen public-kansio USB:lle
    print_step("4. Kopioidaan Alicen public-tiedostot USB-tikulle")
    alice_public = ALICE_DIR / "data" / "public"
    usb_alice = USB_DIR / "alice"
    shutil.copytree(alice_public, usb_alice)
    print(f"{Colors.GREEN}✓ Kopioitu {alice_public} → {usb_alice}{Colors.END}")
    
    # Tarkistetaan että tärkeät tiedostot ovat mukana
    check_file_exists(usb_alice / "profile.json", "Profiili")
    check_file_exists(usb_alice / "Filu-X.json", "Manifesti")
    check_file_exists(usb_alice / "posts", "Posts-kansio")
    
    # 5. Alustetaan Bob
    print_step("5. Alustetaan Bob")
    env["FILU_X_DATA_DIR"] = str(BOB_DIR)
    run_cmd("filu-x init bob --no-password", env=env)
    
    # 6. Bob "liittää" USB-tikun ja kopioi Alicen tiedostot välimuistiinsa
    print_step("6. Bob kopioi Alicen tiedostot välimuistiinsa (USB → cache)")
    bob_cache_follows = BOB_DIR / "data" / "cached" / "follows" / "alice"
    bob_cache_follows.mkdir(parents=True, exist_ok=True)
    
    # Kopioidaan kaikki USB:ltä Bobin cacheen
    shutil.copytree(usb_alice, bob_cache_follows, dirs_exist_ok=True)
    print(f"{Colors.GREEN}✓ Kopioitu {usb_alice} → {bob_cache_follows}{Colors.END}")
    
    # Tarkistetaan että postaukset ovat nyt Bobin cachessa
    bob_posts_cache = bob_cache_follows / "posts"
    if bob_posts_cache.exists():
        post_files = list(bob_posts_cache.glob("*.json"))
        print(f"{Colors.GREEN}✓ Bobin cachessa {len(post_files)} postausta{Colors.END}")
    else:
        print(f"{Colors.RED}✗ Posts-kansiota ei löydy cachesta{Colors.END}")
    
    # 7. Bob katsoo feediä (pitäisi nähdä Alicen postaukset)
    print_step("7. Bobin feed USB-tikulta tuonnin jälkeen")
    out, err, ret = run_cmd("filu-x feed", env=env)
    
    # Tarkistetaan että Alicen postaukset näkyvät
    alice_seen = 0
    for line in out.splitlines():
        if "@alice" in line:
            alice_seen += 1
            print(f"{Colors.GREEN}   → Löytyi: {line.strip()}{Colors.END}")
    
    if alice_seen >= len(posts):
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ TESTI ONNISTUI! Bob näkee {alice_seen} Alicen postausta.{Colors.END}")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ TESTI EPÄONNISTUI! Bob näkee vain {alice_seen} postausta, pitäisi nähdä {len(posts)}.{Colors.END}")
        sys.exit(1)
    
    # 8. Lisätesti: Bob seuraa Alicea (vaikka ei verkkoa) ja sync-followed käyttää välimuistia
    print_step("8. Bob seuraa Alicea (ilman verkkoa) ja ajaa sync-followed")
    # Haetaan Alicen profiilin CID USB:ltä
    profile_path = usb_alice / "profile.json"
    if profile_path.exists():
        import json
        with open(profile_path) as f:
            profile = json.load(f)
        profile_cid = None
        # Profiilin CID ei ole tiedostossa, mutta meillä on kopio. Seuraaminen vaatii CID:n tai IPNS:n.
        # Tässä vaiheessa emme voi saada CID:tä helposti, joten ohitetaan.
        print("   (Profiilin CID:tä ei saada suoraan, ohitetaan)")
    else:
        print("   Profiilia ei löydy USB:ltä")
    
    # 9. Yritetään resolvata Alicen manifesti suoraan cachesta
    print_step("9. Resolvataan Alicen manifesti cachesta (ilman IPFS:ää)")
    manifest_path = bob_cache_follows / "Filu-X.json"
    if manifest_path.exists():
        print(f"{Colors.GREEN}✓ Manifesti löytyy cachesta: {manifest_path}{Colors.END}")
        with open(manifest_path) as f:
            manifest = json.load(f)
        entries = manifest.get("entries", [])
        print(f"   Manifestissa {len(entries)} postausta:")
        for e in entries[:3]:
            print(f"   - {e.get('cid', '')[:16]}... ({e.get('type', 'unknown')})")
    else:
        print(f"{Colors.RED}✗ Manifestia ei löydy cachesta{Colors.END}")
    
    print_step("TESTI PÄÄTTYI")

if __name__ == "__main__":
    main()
