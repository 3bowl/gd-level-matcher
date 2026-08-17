# GD Level Matcher
### A digital archaeology tool for cross-checking object data between Geometry Dash level IDs

## Features
* **Level ID Cross-Checking:** Scan and match level object data between two IDs
* **Level ID Range-Scanning:** Processes ranges of level IDs to brute-force matches
* **Logging:** Logs every level ID scanned, and puts matched level IDs in a special FOUND directory, containing metadata and object data
* **Notifications:** Includes notification support for when a match is found
* **Portable Execution:** Easily compile into a standalone `.exe` using the included `build.bat` script
* **Firewall-triggered shutdown:** Execution exits if it encounters a Cloudflare firewall block
* **Lost connection persistence:** If the connection is lost, it will try the request again one more time after five seconds

## Getting started
### Prerequisites
* Python 3.8+ installed on your machine (with pip)
* Modules in `requirements.txt` (install these in a virtual environment)
* Geometry Dash + an account

## Installation
1. Clone the repository or download the source code:
   ```bash
   git clone https://github.com/3bowl/gd-level-matcher.git
   ```
2. Navigate to the project root folder and create/activate a virtual environment
3. Run `pip install -r requirements.txt`
4. Run `build.bat` and compile the tool into an `.exe`.

## How to use
1. After compiling with `build.bat`, run `Match.exe` inside the `dist/` folder.
2. The program will ask that you supply a comparison level ID. This level ID will act as your fingerprint. The IDs that you're about to scan will attempt to match up with this very comparison level's object data, one object at a time.
3. Next, the program will have you supply a starting level ID. This will be the lower bound for the level ID range scan that you're about to do.
4. Lastly, the program will have you supply the amout of levels IDs to scrape through.
5. Let the magic happen! Every ID it comes by is logged to `LOGS/`.
6. If the comparison level matches up perfectly with another level, it will be a full match, and will be written to `LOGS/FOUND/`. But if the comparison only partially matches up with another level, it will be a partial match, and will be written to `LOGS/PARTIAL_FOUND/`.
7. If Cloudflare intercepts, the execution ends and the error log will be written to `LOGS/`.
8. If you wish to start fresh on a subsequent run, feel free to delete the log folders and/or the `comp_cache` folder.

## How to use the comparison level effectively
While you could technically attempt a match-up scan using an entire level as the comparison, it's better to instead make a copy of the level yourself and manually strip it down to a very small sample of objects unique to the level. That way, if the program encounters a copy level, it will be less susceptible to any modifications done by the copier.

(It may be best to match up with a small sample from a more niche part of the level, say, a middle section, which is less likely to be modified in the copy)

Once you make the stripped-down fingerprint of the level you're scanning for, upload it onto your GD account, preferably unlisted. Feed its level ID into the comparison level ID in the program.

## Notes and precautions
### Here are some things to be aware of when using the program:
* **"I uploaded a perfect copy of a level as a comparison, but when I try to match it up with the original, it won't detect it. Why?"** Note that some object IDs (including some older ones) have been remapped to different object IDs in later updates. When you save an old level in a modern version, the outdated IDs will remap to the new ones. This can and will affect the matching process, giving false negatives. You have to be careful with the objects present in your fingerprint--that is, only include objects whose IDs never changed since the original level's creation.
* **Please respect RobTop's servers.** Please do not nullify/mitigate the request cooldown, as that is there for safety purposes. It may seem inconvenient, but if you want to go faster, you'll need multiple devices connected to multiple separate IP addresses. You are responsible for any damage done to the servers when you use this program.
* **There exists a cutoff for partial matches and non-matches.** If at least 50% of the comparison level matches up with the other level, it will be considered a partial match, and will be written to `LOGS/PARTIAL_FOUND/`. But if it's under 50%, it gets treated as an ordinary non-matching level.
* **Patience is key!** This program will time to execute. Assuming that each request takes 5 seconds, `1000` IDs will take ~1.4 hours. Again, if you wish to go faster, you'll need to utilize separate devices running on separate IPs.

#
***Made with the help of AI.***