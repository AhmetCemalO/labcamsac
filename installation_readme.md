# NeuCams   Build & Packaging Guide

This guide describes two ways to get **NeuCams** up and running:

1. **Run from source** (Conda + `python -m neucams`)
2. **Run the installer** (`NeuCams 1.0.0 windows x86_64.exe`)

   * Built with **PyInstaller** → `NeuCams.exe`
   * Wrapped inside a self contained **Conda Constructor** installer

> **Assumptions**
>
> * Windows 10 64-bit, PowerShell/git bash


---

## 1. Quick Start

### 1.1 Option A   Install the pre built offline package *(easiest)*

1. Download `NeuCams 1.0.0 windows x86_64.exe` from the latest GitHub release.
2. **Run as Administrator** and pick an **empty** install directory (e.g. `C:\NeuCams`).
   *Untick* “Register NeuCams as system Python” unless you *really* need it.
3. Launch NeuCams from the Start Menu shortcut, desktop shortcut **or** `C:Program Files\NeuCams\NeuCams.exe` (or whatever folder you choose to install it).

### 1.2 Option B   Run from source *(GitHub Repositoy)*

```powershell
# clone once
git clone https://github.com/AhmetCemalO/neucams.git
cd neucams

# create / activate env, the name is arbitrary.
conda env create -f environment.yml -n neucams_env
conda activate neucams_env

# to run the application, use the outer folder
python -m neucams
```

#### IMPORTANT: There are two nested folders, both are called neucams, run the commands from the outer neucams folder.

---

## 2. IP Configuration (Ethernet cameras)

Whether you installed NeuCams via the **installer** *or* you’re running from **source**, Ethernet cameras **won’t show up** until the NIC ↔ camera IPs match. Follow these two steps for *every* NIC camera pair:

### 2.1 Configure each Ethernet adapter

1. **Settings ▸ Network & Internet ▸ Advanced network settings ▸ Change adapter options**.
2. Double click each **Ethernet X**, hit **Properties ▸ Internet Protocol Version 4 (TCP/IPv4)**.
3. Select **Use the following IP address** and enter

   * **IP address**   `192.168.<x>.1`
   * **Subnet mask**   `255.255.255.0` (auto fills)
     Pick a unique `<x>` (1 254) per port.
4. **OK** to save.

### 2.2 Assign persistent IPs to cameras

1. Launch **mvIPConfigure** (Matrix Vision)   choose **Work as Administrator** if nothing appears.
2. Select a camera ▸ **Configure** ▸ tick **Use Persistent IP**.
3. Set

   * **IPv4 address**   `192.168.<x>.10` (same `<x>` as its NIC)
   * **Subnet mask**   `255.255.255.0`
4. In **Connected to IPv4 address** pick `192.168.<x>.1` (matching NIC).
5. **Apply changes**. Repeat for every camera.

Done! NeuCams should now list all devices automatically.

---

## 3. Troubleshooting

| Symptom                                        | Fix                                                                                                              |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| Installer shows **“post\_install.bat failed”** | Merely cosmetic   if `NeuCams.exe` exists, you’re fine.                                                          |
| NeuCams starts but **no cameras detected**     | Install/repair **mvIMPACT Acquire** (IDS) *and* **Vimba X** (Allied Vision). Double check the IP settings above. |
| **GENICAM\_GENTL64\_PATH** not persistent      | Run the installer **as Administrator** or set the env var manually (point to the `.cti` files).                  |

---

## 4. Appendix A   Building the Installer *(for maintainers only)*

*The stuff below is ****99 % irrelevant**** to end users. Don't worry about it unless you’re packaging a new release.*

### 4.1 Build a standalone **NeuCams.exe** with PyInstaller

```powershell
conda activate neucams_env        # your dev env
pip install pyinstaller==6.14.2   # one time

cd neucams\build_neucams
python -m PyInstaller neucams.spec --clean -y
# one file mode (  onefile) behaves badly → keep the _internal folder

# quick sanity check
dist\NeuCams\NeuCams.exe
```

Result: `dist\NeuCams\` containing `NeuCams.exe` plus `_internal\`.

### 4.2 Package **NeuCams.exe** into an offline installer (Constructor)

1. **Zip the payload** (run from repo root):

   ```powershell
   Compress-Archive -Path dist\NeuCams\NeuCams.exe, dist\NeuCams\_internal `
                   -DestinationPath build_neucams\payload.zip -Force
   ```

2. **Build with Constructor**

   ```powershell
   conda create -n ctorenv -c conda-forge python=3.11 constructor -y   # one time
   conda activate ctorenv

   cd build_neucams
   python -m constructor .
   ```

   Output: `NeuCams-1.0.0-windows-x86_64.exe` inside `build_neucams\`.

### 4.3 GitHub tip   ignore `build_neucams\files`

That folder is a *full copy* of the repo created by Constructor. It will blow up the repo size if committed.
Add this to `.gitignore` **or** delete the folder after building:

```
build_neucams/files/**
```

Re create it later by copying the repo back in.

### 4.4 Folder layout inside the installer

```
<install dir>\
│  NeuCams.exe
│  _internal\
│  gentl\        (optional CTI files added by post_install.bat)
│
├─ Library\      Conda packages
├─ Scripts\
└─ …             Standard Conda env dirs
```

---

## 5. Credits & Feedback


