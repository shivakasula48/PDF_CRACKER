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


## 🧠 Usage

### 🔸 Interactive Mode

```bash
python pdf_cracker.py
```


- Prompts for PDF path  
- Choose between wordlist or generated passwords  
- Configure charset, length, threads, timeout, and save progress  


### 🔸 Command-Line Mode

```bash
# Using a wordlist
python pdf_cracker.py your_file.pdf --wordlist rockyou.txt

```
Or generate passwords on the fly:

```bash
python pdf_cracker.py your_file.pdf --generate --min_length 1 --max_length 3 --charset abc123 --max_workers 4
```


### 📝 Arguments

| Argument         | Description                                      |
|------------------|--------------------------------------------------|
| `pdf_file`       | Path to the encrypted PDF file                   |
| `--wordlist`     | Path to the wordlist file (.txt/.gz/.zip)        |
| `--generate`     | Use password generator instead of wordlist       |
| `--min_length`   | Minimum password length (default: 1)             |
| `--max_length`   | Maximum password length (default: 3)             |
| `--charset`      | Characters used for generation                   |
| `--exclude_chars`| Characters to exclude from charset               |
| `--max_workers`  | Number of threads (default: 4)                   |
| `--timeout`      | Timeout in seconds (optional)                    |
| `--progress_file`| Path to JSON file to save progress               |



### 📄 Example

Using a wordlist:

```bash
python pdf_cracker.py secret.pdf --wordlist common_passwords.txt --max_workers 8 --progress_file progress.json
```

Generating passwords:

```bash
python pdf_cracker.py secret.pdf --generate --min_length 2 --max_length 4 --charset abc123 --max_workers
```

### 📁 Project Structure

```bash
pdf_cracker/
├── pdf_cracker.py          # Main script
├── requirements.txt        # Dependencies
├── README.md               # Documentation
├── pdf_cracker.log         # Log file (generated during execution)
├── sample.pdf              # sample pdf with week password
├── sample2.pdf             # sample pdf with strong password
├── wordlist.txt            # password file with approx 1,00,000 common passwords




