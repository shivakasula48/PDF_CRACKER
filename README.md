# 🔐 PDF Password Cracker

A multithreaded Python tool to crack password-protected PDF files using either a wordlist or generated passwords.  
Supports resuming progress, colored output, and multiple input formats (`.txt`, `.gz`, `.zip`).

> ⚠️ **Educational Purpose Only**  
> Use this tool **only on PDF files you own or have permission to test**. Unauthorized usage may be illegal.

---

## 📦 Features

- 🔁 Resume password attempts via progress file
- 🔑 Brute-force or wordlist-based cracking
- 📂 Wordlist support: `.txt`, `.gz`, `.zip`
- 🎛 Configurable charset and length range
- ⏱ Progress tracking with `tqdm`
- ⚙️ Multithreaded using `ThreadPoolExecutor`
- 📋 Logging with both console and file output
- 🌈 Colorized terminal output using `colorama`

---

## 🚀 Requirements

Install the required packages using:

```bash
pip install -r requirements.txt
```
