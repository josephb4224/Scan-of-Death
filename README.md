## OVERVIEW

**Scan of Death** is a full-featured graphical frontend for **Nmap**. It exposes every major Nmap option through a tabbed interface, builds the command in real time, and streams output live as the scan runs.

## REQUIREMENTS

Linux (Kali / Debian / Ubuntu):
   - Python 3.10 or newer
   - PyQt6 (`pip install PyQt6`)
   - Nmap (`apt install nmap`)

Windows:
   - Python 3.10 or newer
   - PyQt6 (`pip install PyQt6`)
   - Nmap installed via [official Windows installer](https://nmap.org)
      *(official installer bundles Npcap. Required for raw-socket scans such as SYN, UDP, OS detection, etc*)

## RUNNING THE APP

- `python scan_of_death.py`: Linux (unprivileged scans — TCP Connect, version, etc)
- `sudo python scan_of_death.py`: Linux (privileged scans — SYN, UDP, OS detection, etc)
- `python scan_of_death.py`: Windows PowerShell (Admin)

Place `icon.ico` and `splash.png` in same directory as `scan_of_death.py`.

## BUILDING A STANDALONE EXECUTABLE (PyInstaller)

Install PyInstaller: `pip install pyinstaller`

- Linux — single file:
```bash
pyinstaller --onefile --windowed \
	--add-data "splash.png:." \
	--add-data "icon.ico:." \
	--icon icon.ico \
	scan_of_death.py
```

- Linux — app bundle (recommended for distribution):
```bash
pyinstaller --windowed \
	--add-data "splash.png:." \
	--add-data "icon.ico:." \
	--icon icon.ico \
	scan_of_death.py
```

This produces `dist/scan_of_death.app` which you can drag to Applications.

### Windows — Batch version

Method 1: (single file) [WARNING: May not work without PyQt6]
```batch
pyinstaller --onefile --windowed ^
	--add-data "splash.png;." ^
	--add-data "icon.ico;." ^
	--icon icon.ico ^
	scan_of_death.py
```

### Windows — PowerShell versions

Method 1: PowerShell — Add hidden imports
```powershell
pyinstaller --onefile --windowed `
	--hidden-import=PyQt6 `
	--hidden-import=PyQt6.QtCore `
	--hidden-import=PyQt6.QtGui `
	--hidden-import=PyQt6.QtWidgets `
	--add-data "splash.png;." `
	--add-data "icon.ico;." `
	--icon icon.ico `
	scan_of_death.py
```

Method 2 — Use PyInstaller Qt hook (better):
```powershell
pyinstaller scan_of_death.py --onefile --windowed --collect-all PyQt6
```

Method 3 — Same as Method 2, but with images included:
```powershell
pyinstaller --onefile --windowed `
	--add-data "splash.png;." `
	--add-data "icon.ico;." `
	--icon icon.ico `
	--collect-all PyQt6 `
	scan_of_death.py
```

Method 4 — Including a cheatsheet: ('windowed' or 'console')
```powershell
#pyinstaller --onefile --console --icon "icon.ico" `
pyinstaller --onefile --windowed --icon "icon.ico" `
	--add-data "splash.png;." `
	--add-data "icon.ico;." `
	--add-data ".Nmap_Cheatsheet.md;." `
	--collect-all PyQt6 `
	"scan_of_death.py"
```

Method 5 — Clean??
```powershell
pyinstaller --clean --onefile --windowed --icon "icon.ico" `
	--add-data "splash.png;." `
	--add-data "icon.ico;." `
	--add-data ".Nmap_Cheatsheet.md;." `
	"scan_of_death.py"
```

- Note the separator difference: *Linux* uses `":"` between source & `dest` and *Windows* uses `";"`.
- The finished executable will be in the `dist/` folder.
- NOTE (Windows): Npcap can't be bundled into executable — it's a kernel driver & requires its own installer. End users **must install nmap via [official installer](https://nmap.org)** before running raw-socket scans. App detects missing Npcap on startup & disables incompatible options.

---

## PRIVILEGE REQUIREMENTS

Many Nmap scan types require **root** or **Administrator** access because they use *raw sockets*. The app displays orange warning bar when current options require elevated privileges.

- **Linux / macOS:**
  - Run the app with `sudo python scan_of_death.py`
  - Or for a PyInstaller build: `sudo ./dist/scan_of_death`
- **Windows:**
  - Run script or built executable from CMD (admin), or click `"Relaunch as Administrator"` button in warning bar.

Scan types that **DO NOT** require privileges (safe to run as normal user):
  - TCP Connect scan (`-sT`)
  - Version detection only (`-sV`) without raw scan types
  - List scan (`-sL`)
  - Ping scan with TCP probes disabled

Scan types that **DO** require privileges (root / Admin + Npcap on Windows):
  - SYN Stealth (`-sS`)               - UDP scan (`-sU`)
  - ACK scan (`-sA`)                  - FIN scan (`-sF`)
  - Window scan (`-sW`)             	- Xmas scan (`-sX`)
  - Null scan (`-sN`)                 - Maimon scan (`-sM`)
  - OS detection (`-O` / `-A`)  			- SCTP scans (`-sY`, `-sZ`)
  - IP protocol scan (`-sO`)         	- ICMP probes (`-PE`, `-PP`, `-PM`)
  - Fragmentation (`-f`)             	- Decoys / IP spoofing (`-D`, `-S`)

---

## INTERFACE OVERVIEW

### Target bar (top)
Enter 1+ targets: **hostname**, **IP address**, **CIDR range**, or **IP range**. 
Examples:
```sh
192.168.1.1
192.168.1.0/24
10.0.0.1-254
scanme.nmap.org
```

Click **"From File (`-iL`)"** to load targets from a text file (one per line).

### Command preview
Shows exact nmap command that will be run. Updates live as you change options. You can select and copy the text.

### Warning bar
Appears below  command preview when  current options:
  - Require root / Administrator privileges
  - Conflict with each other (e.g. `--unprivileged` + raw scan type)
  - Are known to cause crashes on Windows (e.g. `-T5` + OS detection)
  - Require Npcap (Windows only)

### Progress bar
- Shows scan progress as a percentage once nmap starts reporting it.
- Displays animated pulse while waiting for the first percentage update.
- Shows time remaining when available.

### Scan Output (bottom panel)
Live streaming output from nmap. Use **"Clear"** to reset & **"Save Output"** to write current output to a text file.

### SCAN / STOP buttons
- **SCANruns cmd. A pre-flight check warns about dangerous or contradictory option combinations before launching.
- **STOP** terminates the running nmap process.

---

## TABS — QUICK REFERENCE

### SCAN TYPE
Select scan technique. Raw-socket types require root/Administrator.

### Common choices:
- `-sS`  SYN stealth — fast, hard to log, requires root.
- `-sT`  TCP connect — slower, works without root, logged by target.
- `-sU`  UDP scan — slow, requires root.
- `-sA`  ACK scan — useful for mapping firewall rules.
- `-sN`/`-sF`/`-sX`  Null/FIN/Xmas — evade some firewalls, Unix targets only.

Idle Scan (`-sI`): requires a zombie host with predictable IP ID sequence.
FTP Bounce (`-b`): legacy technique, rarely works on modern servers.

### HOST DISCOVERY
Controls how Nmap determines whether hosts are alive before scanning ports.
- `-sn` Ping scan only - discover hosts without scanning ports.
- `-Pn` Skip discovery - assume all hosts are online (useful if ICMP is blocked by a firewall).
- `-n` Disable DNS resolution (faster).
- `-R` Always resolve DNS.
- `--traceroute` Trace the route to each host.

Probe types (`-PS`, `-PA`, `-PU`, etc.) allow custom discovery packets.
Optionally specify port numbers in the field next to each probe type.

### PORTS
- `-p`								Specify ports to scan. Examples:
	- `22,80,443`				individual ports
	- `1-1024`					range
	- `U:53,T:21-25`		protocol-specific (U=UDP, T=TCP)	
- `--exclude-ports`		Ports to skip.
- `-F`								Fast mode — scan only the top 100 ports.
- `--top-ports N`			Scan the N most common ports.
- `--port-ratio R`		Scan ports with frequency ratio above R (0.0 - 1.0).
- `-r`								Scan ports in sequential order instead of random.

### SERVICE / VERSION
- `-sV`             	Detect service versions on open ports.
- `--version-light`  	Fewer probes, faster but less accurate (intensity 2).
- `--version-all`   	Max probes — most accurate but very slow (intensity 9).
- `--version-intensity N`  Set probe intensity manually (0-9, default 7).
- `--version-trace`  	Show detailed version detection activity.

### SCRIPTS (NSE)
Nmap's Scripting Engine runs Lua scripts against discovered services.
- `-sC`             	Default scripts: Runs def script set (safe, informational)
- `--script <name/category>`:  Run specific scripts or categories. Examples:
	- `vuln`:         	Check for known vulnerabilities.
	- `auth`:         	Test for authentication bypasses.
	- `http-title`: 		Grab HTTP page titles.
	- `ssl-cert`:       Inspect SSL certificates.
	- `smb-vuln-*`:     SMB vulnerability checks.
- `--script-args`:    Pass arguments to scripts (key=value pairs).
- `--script-timeout`: Max time any script may run before being killed. ALWAYS set when using `vuln`, `auth`, `brute`, or intrusive categories. Recommended: `60s`.
- `--script-trace`		Show all data sent/received by scripts.
- `--script-updatedb`	Update the local script database.

### WARNING — CDN HOSTS (Akamai, Cloudflare, Fastly)

Heavy script categories (`vuln`, `auth`) can hang indefinitely against CDN-hosted targets. These CDNs return HTTP 400 instead of 404 for missing pages, which confuses http-enum into probing all 2000+ fingerprints forever. Always set `--script-timeout` 60s & `--host-timeout` 10m for these targets, or exclude `http-enum`: `--script "vuln and not http-enum"`.
[Full script reference:](https://nmap.org/nsedoc/)

### OS DETECTION
- `-A`:  						Aggressive: enables OS detection, version detection, 
										script scanning, & traceroute in 1 flag.
- `-O`:  						Attempt to identify the target operating system.
- `--osscan-limit`:	Only attempt OS detection on promising hosts.
- `--osscan-guess`:	Guess aggressively when a perfect match is not found.

NOTE (Windows):  OS detection requires Npcap & Admin privileges.
Avoid combining `-O` or `-A` with `-T5` on Windows — this causes nmap to crash (`0xC0000005 access violation`). Use `-T4` instead.

### TIMING
Templates (fastest to slowest):
  - `-T5`  Insane - very fast, unreliable, crashes on Windows w/`-O`/`-A`.
  - `-T4`  Aggressive — fast, good for reliable networks. Recommended def.
  - `-T3`  Normal — nmap default.
  - `-T2`  Polite — slower, less bandwidth.
  - `-T1`  Sneaky — slow, evades some IDS.
  - `-T0`  Paranoid — extremely slow, maximum IDS evasion.

Fine-grained controls allow setting exact timeouts, retry counts, & packet rates. Leave blank to use nmap's defaults.
`--host-timeout`  Maximum total time per host. Recommended when using heavy NSE scripts: 10m

### EVASION / SPOOFING
Options for evading firewalls and IDS systems. Use only on networks & systems you have authorization to test.
- `-f` / `-ff`: 			Fragment packets (8 or 16 bytes per fragment).
- `--mtu N`: 					Custom fragment size (must be a multiple of 8).
- `-D decoy1,decoy2`	Send packets from decoy addresses to obscure origin.
- `-S IP`							Spoof source IP address. NOTE: Linux requires source IP assigned to local interface. `-S` cannot forge arbitrary IPs — use `hping3` or `scapy` for true spoofing. Always pair w/`-e` (interface) & `-Pn`.
- `-e interface`			Specify the network interface to use.
- `-g` / `--source-port N`: Use a specific source port (e.g. 53 to mimic DNS).
- `--proxies`: 				Route scan through HTTP/SOCKS proxies.
- `--data-length N`: 	Append random data to packets to alter their size.
- `--ip-options`: 		Set IP header options.
- `--ttl N`: 					Set the IP time-to-live value.
- `--spoof-mac`: 			Spoof the source MAC address (0 = random).
- `--badsum`: 				Send packets w/invalid checksums (tests IDS behaviour).

### OUTPUT
Save scan results to files in various formats:
  - `-oN`  						Normal text (human-readable).
  - `-oX`  						XML (parseable by other tools).
  - `-oG` 						Greppable (one line per host/port).
  - `-oS`  						Script kiddie (l33tspeak — novelty only).
  - `-oA`  						All formats at once — provide a base filename.

Click `"..."` next to each format to choose a save location.
File dialogs default to your Desktop for convenience.
Relative filenames (e.g. output.txt) are resolved to your Desktop.

### Verbosity options:
- `-v` / `-vv`        Increase output verbosity.
- `-d` / `-dd`        Enable debug output.
- `--reason`        	Show why each port is in its state.
- `--open`          	Only show open ports.
- `--packet-trace`  	Print every packet sent and received.

### MISC
- `-6`               	Enable IPv6 scanning.
- `--privileged`     	Tell nmap to assume it has root (overrides detection).
- `--unprivileged`  	Tell nmap to assume it has NO root. Disables all raw-socket scan types.
	- `--send-eth`    	Send at the Ethernet layer (bypasses IP stack).
	- `--send-ip`     	Send at the IP layer.
	- `--exclude`   		Exclude specific hosts or ranges from the scan.
	- `--excludefile` 	Load exclusion list from a file.
	- `-iL`           	Load target list from a file.
	- `--iR N`        	Choose N random internet targets (use with care).

---

PRE-FLIGHT CHECKS
-----------------
Before each scan the app validates your options and warns about:

- `-T5` + OS detection (`-O` / `-A`) on Windows causes nmap to crash. 
	**Fix**: use `-T4`
- `-T5` + `--version-all` on Windows: extremely aggressive, unstable. 
	**Fix**: use `-T4` & `--version-intensity 7`.
- `--unprivileged` with raw-socket scan types: nmap will refuse to run. 
	**Fix**: uncheck `--unprivileged` or switch to `-sT`.
- UDP scan + `--version-all`: sends an enormous number of probes. 
	**Fix**: use a lower `--version-intensity`.
- Heavy NSE categories (vuln, auth, brute) without `--script-timeout` or
	`--host-timeout`: can hang indefinitely against CDN-hosted targets.
	**Fix**: set `--script-timeout 60s` &  `--host-timeout 10m`.
- `-S` (spoof IP) without `-e`: interface required for spoofing.
- `-S` (spoof IP) without `-Pn`: discovery ping will reveal your real IP.
  
You can choose to proceed past any of these warnings.

---

### STUCK SCAN DETECTION
If scan progress doesn't advance for 3 minutes, app will print a warning in output panel explaining likely cause (usually `http-enum` hanging against a CDN host) & suggest fixes. Detection resets automatically if progress resumes.

### PLATFORM-SPECIFIC NOTES
**Linux (Kali / Debian):**
- Run with sudo for privileged scans.
- File dialogs & output files default to Desktop even when running under sudo.
- libpcap is installed as a dependency of the nmap package — no separate Npcap installation needed.
- There's no sudo checkbox in the app — run the app itself with sudo.

**Windows:**
- Npcap is bundled with the official nmap Windows installer.
	Always install nmap from https://nmap.org, not third-party sources.
- Run from command prompt (admin) for privileged scans or use `"Relaunch as Administrator"` button in warning bar.
- `-T5` combined with OS detection (`-O` / `-A`) reliably crashes `nmap.exe` on Windows due to Npcap driver instability. Always use `-T4`.
- Source IP spoofing (`-S`) requires Npcap and Administrator privileges.

---

### KNOWN LIMITATIONS

- The app is a frontend — it requires nmap to be installed separately.
- Script output (`--script-trace`, `-dd`) can produce very large output volumes.
- UDP scans (`-sU`) are inherently slow regardless of timing settings.
- On Windows, `-T5` combined with OS detection (`-O`/`-A`) reliably crashes nmap. Always use `-T4` or lower on Windows when OS detection is enabled.
- The vuln script category can take a very long time on open networks,
  and can hang indefinitely against CDN-hosted targets. Always set timeouts.
- True arbitrary source-IP spoofing is not possible via `nmap -S` on Linux or macOS. Use `hping3` or `scapy` for this.
- Some NSE scripts require specific dependencies (e.g. ssl scripts need OpenSSL support compiled into nmap).

### LEGAL NOTICE

Scanning networks or hosts without explicit authorisation is illegal in most
jurisdictions and a violation of most terms of service agreements.

Use Scan of Death only on:
- Your own systems and networks.
- Systems and networks you have written permission to test.
- Deliberately vulnerable lab envs (e.g. HackTheBox, TryHackMe, your own VMs).

The authors accept no responsibility for misuse of this software.

---
