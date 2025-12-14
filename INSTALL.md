# Installation Guide

## Method 1: Batch Script (Windows - Simplest) ⚡

### Step 1: Add to PATH
1. Copy the full path of this project folder (e.g., `C:\project\vidio-subtitle`)
2. Open System Environment Variables:
   - Press `Win + R`, type `sysdm.cpl`, press Enter
   - Go to "Advanced" tab → "Environment Variables"
   - Under "User variables", find "Path" → Click "Edit"
   - Click "New" → Paste your project path
   - Click "OK" on all windows

### Step 2: Usage
Now you can run from anywhere:
```bash
# From any folder
autosub -url "https://youtube.com/watch?v=..."

# Or with local file
autosub -l "C:\Videos\myvideo.mp4"

# With turbo mode
autosub -l "video.mp4" --turbo --model distil-large
```

---

## Method 2: Python Package Installation (Cross-Platform) 🐍

### Step 1: Install as Package
```bash
# Navigate to project folder
cd C:\project\vidio-subtitle

# Install in development mode (editable)
pip install -e .

# Or install normally
pip install .
```

### Step 2: Usage
Now you can run from anywhere:
```bash
# From any folder
autosub -url "https://youtube.com/watch?v=..."

# Or with local file
autosub -l "C:\Videos\myvideo.mp4"

# With options
autosub -l "video.mp4" --turbo --deepseek --model distil-large
```

### Step 3: Uninstall (if needed)
```bash
pip uninstall autosub-generator
```

---

## Method 3: PowerShell Alias (Windows) 💻

### Step 1: Create PowerShell Profile
```powershell
# Check if profile exists
Test-Path $PROFILE

# If false, create it
New-Item -Path $PROFILE -Type File -Force

# Open profile in notepad
notepad $PROFILE
```

### Step 2: Add Alias
Add this line to your profile:
```powershell
function autosub { python C:\project\vidio-subtitle\generate_subtitle.py $args }
```

### Step 3: Reload Profile
```powershell
. $PROFILE
```

### Step 4: Usage
```powershell
autosub -url "https://youtube.com/watch?v=..."
autosub -l "video.mp4" --turbo
```

---

## Method 4: Create Symlink (Advanced) 🔗

### Windows (Run as Administrator)
```bash
# Create symlink in a folder that's already in PATH
mklink "C:\Windows\System32\autosub.bat" "C:\project\vidio-subtitle\autosub.bat"
```

### Linux/Mac
```bash
# Create symlink
sudo ln -s /path/to/vidio-subtitle/generate_subtitle.py /usr/local/bin/autosub

# Make executable
chmod +x /path/to/vidio-subtitle/generate_subtitle.py
```

---

## Verification

Test if installation works:
```bash
# Should show help/run the script
autosub

# Should work from any folder
cd C:\Users\YourName\Desktop
autosub -url "https://youtube.com/watch?v=dQw4w9WgXcQ"
```

---

## Troubleshooting

### "autosub is not recognized"
- **Method 1**: Make sure project folder is in PATH and restart CMD/PowerShell
- **Method 2**: Run `pip install -e .` again
- **Method 3**: Reload PowerShell profile with `. $PROFILE`

### "Python not found"
- Make sure Python is installed and in PATH
- Try `python --version` or `py --version`

### "Module not found"
- Make sure you're in the project folder when running
- Or install as package with `pip install -e .`

### ".env file not found"
- Copy `.env.example` to `.env` in project folder
- Or set environment variables manually

---

## Recommended Method

**For Windows users**: Method 1 (Batch Script) - Simplest and most reliable
**For developers**: Method 2 (Python Package) - Professional and cross-platform
**For power users**: Method 3 (PowerShell Alias) - Flexible and customizable

Choose the method that fits your workflow best!
