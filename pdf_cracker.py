import pikepdf
from tqdm import tqdm
import itertools
import string
import argparse
import logging
import sys
import os
import gzip
import zipfile
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterator, Optional, Dict
from colorama import Fore, Style, init

# Initialize colorama for colored output
init(autoreset=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pdf_cracker.log"),
        logging.StreamHandler(),
    ],
)

def is_pdf_file(file_path: str) -> bool:
    """Check if the file is a valid PDF."""
    if not file_path.lower().endswith('.pdf'):
        return False
    try:
        with open(file_path, "rb") as f:
            header = f.read(4)
            return header == b"%PDF"
    except Exception:
        return False

def is_pdf_encrypted(file_path: str) -> bool:
    """Check if the PDF is encrypted."""
    try:
        with pikepdf.open(file_path) as pdf:
            return False  # If it opens without a password, it's not encrypted
    except pikepdf.PasswordError:
        return True
    except Exception as e:
        logging.error(f"Error checking PDF encryption: {e}")
        return False

def generate_passwords(
    charset: str = string.ascii_letters + string.digits + string.punctuation,
    min_length: int = 1,
    max_length: int = 3,
    exclude_chars: Optional[str] = None,
) -> Iterator[str]:
    """Generate passwords of given lengths from a character set."""
    if exclude_chars:
        charset = "".join(c for c in charset if c not in exclude_chars)
    for length in range(min_length, max_length + 1):
        for password in itertools.product(charset, repeat=length):
            yield "".join(password)

def load_passwords(wordlist_file: str) -> Iterator[str]:
    """Load passwords from a wordlist file (supports plain, gzip, or zip)."""
    seen = set()
    try:
        if wordlist_file.endswith(".gz"):
            with gzip.open(wordlist_file, "rt") as file:
                for line in file:
                    password = line.strip()
                    if password and password not in seen:
                        seen.add(password)
                        yield password
        elif wordlist_file.endswith(".zip"):
            with zipfile.ZipFile(wordlist_file) as z:
                for name in z.namelist():
                    with z.open(name) as file:
                        for line in file:
                            password = line.decode().strip()
                            if password and password not in seen:
                                seen.add(password)
                                yield password
        else:
            with open(wordlist_file, "r", errors="ignore") as file:
                for line in file:
                    password = line.strip()
                    if password and password not in seen:
                        seen.add(password)
                        yield password
    except Exception as e:
        logging.error(f"Failed to load wordlist: {e}")
        raise

def try_password(pdf_file: str, password: str) -> Optional[str]:
    """Attempt to decrypt the PDF with a given password."""
    try:
        with pikepdf.open(pdf_file, password=password) as pdf:
            logging.info(f"[+] Password found for {pdf_file}: {password}")
            return password
    except pikepdf.PasswordError:
        return None
    except Exception as e:
        logging.error(f"Error testing password {password}: {e}")
        return None

def decrypt_pdf(
    pdf_file: str,
    passwords: Iterator[str],
    total_passwords: int,
    max_workers: int = 4,
    timeout: Optional[int] = None,
    progress_file: Optional[str] = None,
) -> Optional[str]:
    """Decrypt the PDF using parallel password attempts."""
    progress = {"attempted": 0, "last_password": None, "start_time": time.time()}
    if progress_file and os.path.exists(progress_file):
        with open(progress_file, "r") as f:
            progress = json.load(f)
            logging.info(f"Resuming from password: {progress['last_password']}")

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        passwords = itertools.islice(passwords, progress["attempted"], None)
        futures = {executor.submit(try_password, pdf_file, pwd): pwd for pwd in passwords}
        with tqdm(
            total=total_passwords - progress["attempted"],
            desc="Decrypting PDF",
            unit="password",
            initial=progress["attempted"],
        ) as pbar:
            for future in as_completed(futures, timeout=timeout):
                result = future.result()
                progress["attempted"] += 1
                progress["last_password"] = futures[future]
                if progress_file:
                    with open(progress_file, "w") as f:
                        json.dump(progress, f)
                if result:
                    executor.shutdown(wait=False, cancel_futures=True)
                    if progress_file and os.path.exists(progress_file):
                        os.remove(progress_file)
                    return result
                pbar.update(1)
    return None

def count_passwords(passwords: Iterator[str]) -> int:
    """Count the number of passwords in an iterator (for progress bar)."""
    return sum(1 for _ in passwords)

def estimate_password_strength(charset: str, min_length: int, max_length: int) -> str:
    """Estimate the strength of generated passwords."""
    total = sum(len(charset) ** length for length in range(min_length, max_length + 1))
    if total < 1e3:
        return "Very Weak"
    elif total < 1e6:
        return "Weak"
    elif total < 1e9:
        return "Moderate"
    else:
        return "Strong"

def interactive_mode() -> Dict:
    """Prompt the user for inputs interactively."""
    print("\n=== PDF Password Cracker (Interactive Mode) ===")
    args = {}
    while True:
        args["pdf_file"] = input("Enter the path to the PDF file: ").strip()
        if not os.path.exists(args["pdf_file"]):
            print(Fore.RED + "File not found. Please try again.")
            continue
        if not is_pdf_file(args["pdf_file"]):
            print(Fore.RED + "Error: The file is not a valid PDF. Only .pdf files are accepted.")
            continue
        break

    if not is_pdf_encrypted(args["pdf_file"]):
        print(Fore.GREEN + "The PDF is not encrypted. No need to crack.")
        sys.exit(0)

    method = input("Use a wordlist (W) or generate passwords (G)? [W/G]: ").strip().lower()
    if method == "w":
        while True:
            args["wordlist"] = input("Enter the path to the wordlist file: ").strip()
            if not os.path.exists(args["wordlist"]):
                print(Fore.RED + "Wordlist not found. Please try again.")
                continue
            break
        args["generate"] = False
    else:
        args["generate"] = True
        args["min_length"] = int(input("Minimum password length: ").strip())
        args["max_length"] = int(input("Maximum password length: ").strip())
        args["charset"] = input(
            f"Characters to use (default: {string.ascii_letters + string.digits + string.punctuation}): "
        ).strip() or (string.ascii_letters + string.digits + string.punctuation)
        args["exclude_chars"] = input("Characters to exclude (leave empty for none): ").strip() or None
        strength = estimate_password_strength(args["charset"], args["min_length"], args["max_length"])
        print(f"Estimated password strength: {strength}")

    args["max_workers"] = int(input("Number of threads to use (default: 4): ").strip() or 4)
    args["timeout"] = int(input("Timeout in seconds (leave empty for no timeout): ").strip() or 0) or None
    args["progress_file"] = input("Save progress to file (leave empty to disable): ").strip() or None
    return args

def main():
    parser = argparse.ArgumentParser(description="Decrypt a password-protected PDF.")
    parser.add_argument("pdf_file", nargs="?", help="Path to the PDF file")
    parser.add_argument("--wordlist", help="Path to a wordlist file")
    parser.add_argument("--generate", action="store_true", help="Generate passwords")
    parser.add_argument("--min_length", type=int, default=1, help="Minimum password length")
    parser.add_argument("--max_length", type=int, default=3, help="Maximum password length")
    parser.add_argument("--charset", type=str, default=string.ascii_letters + string.digits + string.punctuation, help="Characters for password generation")
    parser.add_argument("--exclude_chars", type=str, default=None, help="Characters to exclude")
    parser.add_argument("--max_workers", type=int, default=4, help="Number of parallel threads")
    parser.add_argument("--timeout", type=int, default=None, help="Timeout in seconds")
    parser.add_argument("--progress_file", type=str, default=None, help="File to save progress")
    args = parser.parse_args()

    if not args.pdf_file:
        args = argparse.Namespace(**interactive_mode())
    else:
        # Ensure generate is set if not using a wordlist
        if not args.wordlist and not args.generate:
            args.generate = True  # Default to generate if no wordlist is provided

    if not os.path.exists(args.pdf_file):
        print(Fore.RED + f"PDF file not found: {args.pdf_file}")
        sys.exit(1)

    if not is_pdf_file(args.pdf_file):
        print(Fore.RED + "The file is not a valid PDF. Only .pdf files are accepted.")
        sys.exit(1)

    if not is_pdf_encrypted(args.pdf_file):
        print(Fore.GREEN + "The PDF is not encrypted. No need to crack.")
        sys.exit(0)

    if hasattr(args, "wordlist") and args.wordlist:
        if not os.path.exists(args.wordlist):
            print(Fore.RED + f"Wordlist not found: {args.wordlist}")
            sys.exit(1)
        passwords = load_passwords(args.wordlist)
        total_passwords = count_passwords(load_passwords(args.wordlist))
    elif hasattr(args, "generate") and args.generate:
        passwords = generate_passwords(args.charset, args.min_length, args.max_length, args.exclude_chars)
        total_passwords = count_passwords(generate_passwords(args.charset, args.min_length, args.max_length, args.exclude_chars))
    else:
        print(Fore.RED + "Either --wordlist or --generate must be specified.")
        sys.exit(1)

    logging.info(f"Starting decryption with {total_passwords} passwords...")
    start_time = time.time()
    password = decrypt_pdf(
        args.pdf_file,
        passwords,
        total_passwords,
        args.max_workers,
        args.timeout,
        args.progress_file,
    )

    if password:
        print(Fore.GREEN + f"\n[+] Success! Password: {password}")
        logging.info(f"Password for {args.pdf_file}: {password}")
        logging.info(f"Time taken: {time.time() - start_time:.2f} seconds")
    else:
        print(Fore.RED + "\n[-] Password not found.")
        logging.info(f"Time taken: {time.time() - start_time:.2f} seconds")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n[!] Interrupted by user.")
        sys.exit(0)
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        sys.exit(1)
