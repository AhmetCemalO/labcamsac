# NeuCams – Build & Packaging Guide

This guide describes two ways to get **NeuCams** up and running:

1. **Run from source** (Conda + `python -m neucams`)
2. **Distribute an offline Windows installer** (`NeuCams‑<VERSION>‑windows‑x86_64.exe`)

   * Built with **PyInstaller** → `NeuCams.exe`
   * Wrapped inside a self‑contained **Conda Constructor** installer

> **Assumptions**
>
> * Windows 10 64-bit, PowerShell/git bash
> * Replace `<VERSION>` with the current release (currently **1.0.0**).

---

## 1. Clone the repository

```powershell
git clone https://github.com/AhmetCemalO/neucams.git
cd neucams
```

---

## 2. Run from source (development)

```powershell
conda env create -f environment.yml -n neucams_env
conda activate neucams_env
```

> There are two nested `neucams` folders in the repo.
> Run the module from the **outer** folder:

```powershell
python -m neucams
```

---

## 3. Build a standalone **NeuCams.exe** with PyInstaller

1. **Activate** the dev env:

   ```powershell
   conda activate neucams_env
   ```

2. **Install PyInstaller** (one‑time):

   ```powershell
   pip install pyinstaller==6.14.2
   ```

3. **Build** (must be inside the `build_neucams` folder):

   ```powershell
   cd neucams\build_neucams
   python -m PyInstaller neucams.spec --clean -y
   ```

   **Result**: `dist\NeuCams\`

   ```
   NeuCams.exe
   _internal\       ← support files bundled by the spec
   ```

   *One‑file mode (****`--onefile`**\*\*) caused trouble, so we keep ****`_internal`**** plus ****`NeuCams.exe`****.*

   **Quick test**

   ```powershell
   dist\NeuCams\NeuCams.exe
   ```

---

## 4. Package **NeuCams.exe** into an offline installer

### 4.1 Create **payload.zip**

Run from the repo root. (If the command fails, just zip `_internal` and `NeuCams.exe` manually and drop `payload.zip` into `build_neucams\` using the same folder structure. payload.zip should be in the same hierarchy as construct.yml and other files)

```powershell
Compress-Archive `
    -Path dist\NeuCams\NeuCams.exe, dist\NeuCams\_internal `
    -DestinationPath build_neucams\payload.zip `
    -Force
```

`build_neucams\` already contains:

```
construct.yaml
post_install.bat
icon.ico
LICENSE.txt
payload.zip   ← added by the command above
```

### 4.2 Build with Constructor

```powershell
# one‑time env for Constructor
conda create -n ctorenv -c conda-forge python=3.11 constructor -y
conda activate ctorenv

# build!
cd build_neucams
python -m constructor .
```

**Output**: `NeuCams-<VERSION>-windows-x86_64.exe` inside `build_neucams\`.

---

### 4.3 GitHub tip – ignore `build_neucams\files`

`build_neucams\files` is a *full copy* of the repo that Constructor needs during the build. It makes the working tree roughly twice as large and will easily exceed GitHub’s size limits if committed.

- Keep it locally while building, then **remove or add it to** `.gitignore` before pushing:

    ```
    # duplicated repo used by Constructor
    build_neucams/files/**
    ```

- If you later need to rebuild the installer, just recreate the folder by copying the current repo back into `build_neucams\files`.

---

## 5. Install on a fresh PC

Copy the installer to any Windows 10/11 64‑bit machine and **run as Administrator**.

1. Pick an **install directory** (e.g. `C:\NeuCams`). The folder must be empty.
2. **Un‑tick “Register NeuCams as system Python”.**
3. After installation, launch NeuCams from:

   * the Start‑Menu shortcut (if you kept `Menu\NeuCams.json`), **or**
   * directly: `C:\NeuCams\NeuCams.exe`

> **Camera drivers** – NeuCams still relies on **mvIMPACT Acquire** and **Vimba X**.
> Install/repair them separately (default options + *Next* spam are fine).
> For Ethernet cameras double‑check the IP addresses: both the NIC and the camera must be in the same subnet. See the *IP Configuration* section for details.

---

## 6. IP Configuration (Ethernet cameras)

Getting NIC–camera IPs right is mandatory; otherwise NeuCams will launch but list zero devices.

**Step 1 – Configure each Ethernet adapter**

1. Open **Settings ▸ Network & Internet ▸ Advanced network settings ▸ Change adapter options**.
2. For every port that will host a camera, double‑click the corresponding **Ethernet X** device, click **Properties**, then open **Internet Protocol Version 4 (TCP/IPv4)**.
3. Select **“Use the following IP address”** and enter
   • **IP address** – `192.168.<x>.1`
   • **Subnet mask** – `255.255.255.0` (auto‑fills)
   Pick a unique `<x>` (1‑254) per port/camera pair.
4. Click **OK**.

**Step 2 – Assign persistent IPs to each camera**

1. Launch **mvIPConfigure** (from Matrix Vision). If no devices appear, choose **“Work as Administrator”** and click **Update device list**.
2. Select a camera, click **Configure**, and check **“Use Persistent IP”**.
3. Fill in:
   • **IPv4 address** – `192.168.<x>.10` (use the same `<x>` you gave its NIC)
   • **Subnet mask** – `255.255.255.0`
4. In **Connected to IPv4 address** pick `192.168.<x>.1` (the matching NIC).
5. Hit **Apply changes** (the GUI may freeze for a few seconds). Repeat for every camera.

Done! NeuCams should now discover all cameras automatically.

## 7. Folder layout inside the installer

```
<install‑dir>\
│  NeuCams.exe
│  _internal\
│  gentl\        (optional CTI files added by post_install.bat)
│
├─ Library\      Conda packages
├─ Scripts\
└─ …             Standard Conda env directories
```

---

## 8. Troubleshooting

| Symptom                                        | Fix                                                                                                                                                      |
| ---------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Installer shows **“post\_install.bat failed”** | Merely cosmetic—`post_install.bat` returns a non‑zero exit code. If `NeuCams.exe` is in the folder, you’re good.                                         |
| NeuCams starts but **no cameras detected**     | Install/repair **mvIMPACT Acquire** (IDS) and **Vimba X** (Allied Vision). Ensure correct IP settings for both NIC and cameras (see *IP Configuration*). |
| **GENICAM\_GENTL64\_PATH** not persistent      | Run the installer **as Administrator** or set the environment variable manually (point it at the `.cti` files).                                          |

---

*Additions, typos, or salty comments? Ping me.*
