from datetime import datetime
import time
from colorama import Fore
import requests
import random
from fake_useragent import UserAgent
import asyncio
import json
import gzip
import brotli
import zlib
import chardet
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class RewardsHQ:
    BASE_URL = "https://api-rewardshq.shards.tech/v1/"
    HEADERS = {
        "accept": "application/json",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "en-GB,en;q=0.9,en-US;q=0.8",
        "content-type": "application/json",
        "origin": "https://rewardshq.shards.tech",
        "priority": "u=1, i",
        "referer": "https://rewardshq.shards.tech/",
        "sec-ch-ua": '"Microsoft Edge WebView2";v="135", "Chromium";v="135", "Not-A.Brand";v="8", "Microsoft Edge";v="135"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36 Edg/135.0.0.0",
    }

    def __init__(self):
        self.query_list = self.load_query("query.txt")
        self.token = None
        self.config = self.load_config()
        self.session = self.sessions()
        self._original_requests = {
            "get": requests.get,
            "post": requests.post,
            "put": requests.put,
            "delete": requests.delete,
        }
        self.proxy_session = None

    def log(self, message, color=Fore.RESET):
        safe_message = message.encode("utf-8", "backslashreplace").decode("utf-8")
        print(
            Fore.LIGHTBLACK_EX
            + datetime.now().strftime("[%Y:%m:%d ~ %H:%M:%S] |")
            + " "
            + color
            + safe_message
            + Fore.RESET
        )

    def banner(self) -> None:
        """Displays the banner for the bot."""
        self.log("🎉 RewardsHQ Bot", Fore.CYAN)
        self.log("🚀 Created by LIVEXORDS", Fore.CYAN)
        self.log("📢 Channel: t.me/livexordsscript\n", Fore.CYAN)

    def sessions(self):
        session = requests.Session()
        retries = Retry(
            total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504, 520]
        )
        session.mount("https://", HTTPAdapter(max_retries=retries))
        return session

    def decode_response(self, response):
        """
        Mendekode response dari server secara umum.

        Parameter:
            response: objek requests.Response

        Mengembalikan:
            - Jika Content-Type mengandung 'application/json', maka mengembalikan objek Python (dict atau list) hasil parsing JSON.
            - Jika bukan JSON, maka mengembalikan string hasil decode.
        """
        # Ambil header
        content_encoding = response.headers.get("Content-Encoding", "").lower()
        content_type = response.headers.get("Content-Type", "").lower()

        # Tentukan charset dari Content-Type, default ke utf-8
        charset = "utf-8"
        if "charset=" in content_type:
            charset = content_type.split("charset=")[-1].split(";")[0].strip()

        # Ambil data mentah
        data = response.content

        # Dekompresi jika perlu
        try:
            if content_encoding == "gzip":
                data = gzip.decompress(data)
            elif content_encoding in ["br", "brotli"]:
                data = brotli.decompress(data)
            elif content_encoding in ["deflate", "zlib"]:
                data = zlib.decompress(data)
        except Exception:
            # Jika dekompresi gagal, lanjutkan dengan data asli
            pass

        # Coba decode menggunakan charset yang didapat
        try:
            text = data.decode(charset)
        except Exception:
            # Fallback: deteksi encoding dengan chardet
            detection = chardet.detect(data)
            detected_encoding = detection.get("encoding", "utf-8")
            text = data.decode(detected_encoding, errors="replace")

        # Jika konten berupa JSON, kembalikan hasil parsing JSON
        if "application/json" in content_type:
            try:
                return json.loads(text)
            except Exception:
                # Jika parsing JSON gagal, kembalikan string hasil decode
                return text
        else:
            return text

    def load_config(self) -> dict:
        """
        Loads configuration from config.json.

        Returns:
            dict: Configuration data or an empty dictionary if an error occurs.
        """
        try:
            with open("config.json", "r") as config_file:
                config = json.load(config_file)
                self.log("✅ Configuration loaded successfully.", Fore.GREEN)
                return config
        except FileNotFoundError:
            self.log("❌ File not found: config.json", Fore.RED)
            return {}
        except json.JSONDecodeError:
            self.log(
                "❌ Failed to parse config.json. Please check the file format.",
                Fore.RED,
            )
            return {}

    def load_query(self, path_file: str = "query.txt") -> list:
        """
        Loads a list of queries from the specified file.

        Args:
            path_file (str): The path to the query file. Defaults to "query.txt".

        Returns:
            list: A list of queries or an empty list if an error occurs.
        """
        self.banner()

        try:
            with open(path_file, "r") as file:
                queries = [line.strip() for line in file if line.strip()]

            if not queries:
                self.log(f"⚠️ Warning: {path_file} is empty.", Fore.YELLOW)

            self.log(f"✅ Loaded {len(queries)} queries from {path_file}.", Fore.GREEN)
            return queries

        except FileNotFoundError:
            self.log(f"❌ File not found: {path_file}", Fore.RED)
            return []
        except Exception as e:
            self.log(f"❌ Unexpected error loading queries: {e}", Fore.RED)
            return []

    def login(self, index: int) -> None:
        self.log("🔐 Attempting to log in...", Fore.GREEN)
        if index >= len(self.query_list):
            self.log("❌ Invalid login index. Please check again.", Fore.RED)
            return

        token = self.query_list[index]
        self.log(f"📋 Using token: {token[:10]}... (truncated for security)", Fore.CYAN)

        # API: Login via auth/login
        login_url = f"{self.BASE_URL}auth/login"
        payload = json.dumps(
            {"telegramInitData": token, "appId": "b3edf262-0aa7-4ebb-954a-887a24cb09f1"}
        )
        login_headers = self.HEADERS

        try:
            self.log("📡 Sending login request...", Fore.CYAN)
            login_response = requests.post(
                login_url, headers=login_headers, data=payload
            )
            login_response.raise_for_status()
            login_data = self.decode_response(login_response)
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to send login request: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {login_response.text}", Fore.RED)
            except Exception:
                pass
            return
        except Exception as e:
            self.log(f"❌ Unexpected error during login: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {login_response.text}", Fore.RED)
            except Exception:
                pass
            return

        try:
            # Simpan accessToken dari respons
            data = login_data.get("data", {})
            self.token = data.get("accessToken", "")
            if not self.token:
                self.log("❌ Access token not found in response.", Fore.RED)
                return
            self.log("✅ Login successful! Access token stored.", Fore.GREEN)
        except Exception as e:
            self.log(f"❌ Error processing login response: {e}", Fore.RED)
            return

        # API: Request point logs
        point_logs_url = f"{self.BASE_URL}point-logs"
        headers_with_auth = {**self.HEADERS, "authorization": f"Bearer {self.token}"}
        try:
            self.log("📡 Sending point logs request...", Fore.CYAN)
            point_logs_response = requests.get(
                point_logs_url, headers=headers_with_auth
            )
            point_logs_response.raise_for_status()
            point_logs_data = self.decode_response(point_logs_response)
            points = point_logs_data.get("data", {})
            self.log("💰 Point Logs:", Fore.GREEN)
            self.log(f"    - Points: {points.get('point', 'N/A')}", Fore.CYAN)
            self.log(
                f"    - Referral Point: {points.get('referralPoint', 'N/A')}", Fore.CYAN
            )
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to fetch point logs: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {point_logs_response.text}", Fore.RED)
            except Exception:
                pass
        except Exception as e:
            self.log(f"❌ Unexpected error in point logs request: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {point_logs_response.text}", Fore.RED)
            except Exception:
                pass

        # API: Request task level (tanpa menampilkan roadmap)
        tasks_level_url = f"{self.BASE_URL}tasks/level"
        try:
            self.log("📡 Sending task level request...", Fore.CYAN)
            tasks_level_response = requests.get(
                tasks_level_url, headers=headers_with_auth
            )
            tasks_level_response.raise_for_status()
            tasks_level_data = self.decode_response(tasks_level_response)
            level_data = tasks_level_data.get("data", {})
            self.log("📊 Task Level:", Fore.GREEN)
            self.log(f"    - XP: {level_data.get('xp', 'N/A')}", Fore.CYAN)
            self.log(f"    - Level: {level_data.get('level', 'N/A')}", Fore.CYAN)
            self.log(
                f"    - XP to Next Level: {level_data.get('xpToNextLevel', 'N/A')}",
                Fore.CYAN,
            )
            self.log(
                f"    - Multiplier: {level_data.get('multiplier', 'N/A')}", Fore.CYAN
            )
            self.log(f"    - Diff XP: {level_data.get('diffXp', 'N/A')}", Fore.CYAN)
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to fetch task level: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {tasks_level_response.text}", Fore.RED)
            except Exception:
                pass
        except Exception as e:
            self.log(f"❌ Unexpected error in task level request: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {tasks_level_response.text}", Fore.RED)
            except Exception:
                pass

        # API: Request streak login
        streak_login_url = f"{self.BASE_URL}users/streak-login"
        try:
            self.log("📡 Sending streak login request...", Fore.CYAN)
            streak_login_response = requests.get(
                streak_login_url, headers=headers_with_auth
            )
            streak_login_response.raise_for_status()
            streak_login_data = self.decode_response(streak_login_response)
            streak_data = streak_login_data.get("data", {})
            self.log("🔥 Streak Login:", Fore.GREEN)
            self.log(f"    - Streak: {streak_data.get('streak', 'N/A')}", Fore.CYAN)
            self.log(
                f"    - Point Bonus: {streak_data.get('pointBonus', 'N/A')}", Fore.CYAN
            )
            self.log(
                f"    - Prev Point Bonus: {streak_data.get('prevPointBonus', 'N/A')}",
                Fore.CYAN,
            )
            self.log(
                f"    - Next Point Bonus: {streak_data.get('nextPointBonus', 'N/A')}",
                Fore.CYAN,
            )
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to fetch streak login: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {streak_login_response.text}", Fore.RED)
            except Exception:
                pass
        except Exception as e:
            self.log(f"❌ Unexpected error in streak login request: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {streak_login_response.text}", Fore.RED)
            except Exception:
                pass

        # API: Request user info
        user_info_url = f"{self.BASE_URL}users"
        try:
            self.log("📡 Sending user info request...", Fore.CYAN)
            user_info_response = requests.get(user_info_url, headers=headers_with_auth)
            user_info_response.raise_for_status()
            user_info_data = self.decode_response(user_info_response)
            user_info = user_info_data.get("data", {})
            self.log("👤 User Info:", Fore.GREEN)
            self.log(f"    - ID: {user_info.get('_id', 'N/A')}", Fore.CYAN)
            self.log(f"    - Username: {user_info.get('userName', 'N/A')}", Fore.CYAN)
            self.log(
                f"    - First Name: {user_info.get('firstName', 'N/A')}", Fore.CYAN
            )
            self.log(f"    - Last Name: {user_info.get('lastName', 'N/A')}", Fore.CYAN)
            self.log(
                f"    - Created At: {user_info.get('createdAt', 'N/A')}", Fore.CYAN
            )
            self.log(
                f"    - Updated At: {user_info.get('updatedAt', 'N/A')}", Fore.CYAN
            )
            self.log(f"    - Address: {user_info.get('address', 'N/A')}", Fore.CYAN)
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Failed to fetch user info: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {user_info_response.text}", Fore.RED)
            except Exception:
                pass
        except Exception as e:
            self.log(f"❌ Unexpected error in user info request: {e}", Fore.RED)
            try:
                self.log(f"📄 Response content: {user_info_response.text}", Fore.RED)
            except Exception:
                pass

    def farming(self):
        """Automatically perform farming for abundant harvest 🌾."""
        if not self.token:
            self.log("❌ No token available. Please log in first.", Fore.RED)
            return None

        headers = {**self.HEADERS, "Authorization": f"Bearer {self.token}"}

        # ====================================================
        # Phase 1: Initiate Farming
        # ====================================================
        self.log("📡 Initiating farming...", Fore.CYAN)
        try:
            put_response = requests.put(
                f"{self.BASE_URL}user-earn-hour", headers=headers
            )
            put_response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Network error during farming initiation: {e}", Fore.RED)
            return None
        except Exception as e:
            self.log(f"❌ Unexpected error during farming initiation: {e}", Fore.RED)
            return None

        # ====================================================
        # Phase 2: Check Farming Status
        # ====================================================
        self.log("📡 Checking farming status...", Fore.CYAN)
        try:
            response = requests.get(f"{self.BASE_URL}user-earn-hour", headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Network error during farming status check: {e}", Fore.RED)
            return None
        except Exception as e:
            self.log(f"❌ Unexpected error during farming status check: {e}", Fore.RED)
            return None

        if response.status_code == 200:
            self.log("✅ Farming request successful.", Fore.GREEN)
            return self.decode_response(response)
        else:
            self.log(
                f"❌ Farming failed, status code: {response.status_code}", Fore.RED
            )
            return None

    def spin(self) -> None:
        """Perform spin actions repeatedly based solely on API response."""
        if not self.token:
            self.log("❌ No token available. Please log in first.", Fore.RED)
            return

        headers = {**self.HEADERS, "Authorization": f"Bearer {self.token}"}

        while True:
            try:
                self.log("📡 Checking available spins...", Fore.CYAN)
                spin_logs_response = requests.get(
                    f"{self.BASE_URL}user-spin-logs", headers=headers
                )
                spin_logs_response.raise_for_status()
                spin_logs_data = self.decode_response(spin_logs_response)
                available_spins = spin_logs_data.get("data", {}).get("numberSpin", 0)
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Failed to retrieve spin logs: {e}", Fore.RED)
                break
            except Exception as e:
                self.log(
                    f"❌ Unexpected error while retrieving spin logs: {e}", Fore.RED
                )
                break

            if available_spins == 0:
                self.log("⚠️ No spin points remaining.", Fore.YELLOW)
                break

            try:
                self.log("📡 Initiating spin...", Fore.CYAN)
                spin_response = requests.put(
                    f"{self.BASE_URL}user-spin-logs", headers=headers
                )
                spin_response.raise_for_status()
                spin_data = self.decode_response(spin_response).get("data", {})
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Spin failed: {e}", Fore.RED)
                break
            except Exception as e:
                self.log(f"❌ Unexpected error during spin: {e}", Fore.RED)
                break

            if not spin_data:
                self.log("❌ Spin response data missing. Retrying...", Fore.RED)
                continue

            points = spin_data.get("point", 0)
            xp = spin_data.get("xp", 0)
            usdt = spin_data.get("usdt", 0)
            remaining_spins = spin_data.get("numberSpin", available_spins - 1)

            self.log(
                f"✅ Spin successful! Points: {points}, XP: {xp}, USDT: {usdt}, Spins left: {remaining_spins}",
                Fore.GREEN,
            )

            time.sleep(5)

    def task(self) -> dict:
        """
        Execute multiple phases:
        Phase 1: Claim regular tasks (tasks, basic-tasks, partner-tasks)
        Phase 2: Claim campaigns via user quests
        Phase 3: Claim one-time achievements

        Returns:
            A dictionary with claimed task IDs, quest statuses, and achievement claim status.
        """
        if not self.token:
            self.log("❌ No token available. Please log in first.", Fore.RED)
            return {}

        headers = {**self.HEADERS, "Authorization": f"Bearer {self.token}"}
        claimed_task_ids = []
        claimed_quest_ids = {}
        achievements_claimed = []

        # ====================================================
        # Phase 1: Claiming Regular Tasks
        # ====================================================
        self.log("🔰 Phase 1: Claiming Regular Tasks", Fore.GREEN)

        # 1.1. Tasks from /tasks
        self.log("📡 Retrieving tasks from /tasks...", Fore.CYAN)
        try:
            response = requests.get(f"{self.BASE_URL}tasks", headers=headers)
            response.raise_for_status()
            tasks = self.decode_response(response).get("data", [])
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Network error while retrieving tasks: {e}", Fore.RED)
            tasks = []
        except Exception as e:
            self.log(f"❌ Unexpected error while retrieving tasks: {e}", Fore.RED)
            tasks = []

        for task in tasks:
            task_id = task.get("_id")
            is_completed = task.get("isCompleted", False)
            is_can_claim = task.get("isCanClaim", False)
            task_name = task.get("metadata", {}).get("name", "Unknown Task")
            if not is_completed and is_can_claim:
                try:
                    do_response = requests.post(
                        f"{self.BASE_URL}tasks/do-task/{task_id}", headers=headers
                    )
                    do_response.raise_for_status()
                    self.log(f"✅ Task '{task_name}' successfully claimed.", Fore.GREEN)
                    claimed_task_ids.append(task_id)
                except requests.exceptions.RequestException as e:
                    self.log(f"❌ Failed to claim task '{task_name}': {e}", Fore.RED)
                except Exception as e:
                    self.log(
                        f"❌ Unexpected error for task '{task_name}': {e}", Fore.RED
                    )
                time.sleep(5)
            else:
                self.log(
                    f"⚠️ Task '{task_name}' is either completed or cannot be claimed.",
                    Fore.YELLOW,
                )

        # 1.2. Basic Tasks from /tasks/basic-tasks
        self.log("📡 Retrieving basic tasks from /tasks/basic-tasks...", Fore.CYAN)
        try:
            response = requests.get(
                f"{self.BASE_URL}tasks/basic-tasks", headers=headers
            )
            response.raise_for_status()
            basic_tasks = self.decode_response(response).get("data", [])
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Network error while retrieving basic tasks: {e}", Fore.RED)
            basic_tasks = []
        except Exception as e:
            self.log(f"❌ Unexpected error while retrieving basic tasks: {e}", Fore.RED)
            basic_tasks = []

        for task in basic_tasks:
            task_id = task.get("_id")
            is_completed = task.get("isCompleted", False)
            is_can_claim = task.get("isCanClaim", False)
            task_name = task.get("metadata", {}).get("name", "Unknown Basic Task")
            if not is_completed and is_can_claim:
                try:
                    do_response = requests.post(
                        f"{self.BASE_URL}tasks/basic-tasks/{task_id}", headers=headers
                    )
                    do_response.raise_for_status()
                    self.log(
                        f"✅ Basic Task '{task_name}' successfully claimed.", Fore.GREEN
                    )
                    claimed_task_ids.append(task_id)
                except requests.exceptions.RequestException as e:
                    self.log(
                        f"❌ Failed to claim basic task '{task_name}': {e}", Fore.RED
                    )
                except Exception as e:
                    self.log(
                        f"❌ Unexpected error for basic task '{task_name}': {e}",
                        Fore.RED,
                    )
                time.sleep(5)
            else:
                self.log(
                    f"⚠️ Basic Task '{task_name}' is either completed or cannot be claimed.",
                    Fore.YELLOW,
                )

        # 1.3. Partner Tasks from /tasks/partner-tasks
        self.log("📡 Retrieving partner tasks from /tasks/partner-tasks...", Fore.CYAN)
        try:
            response = requests.get(
                f"{self.BASE_URL}tasks/partner-tasks", headers=headers
            )
            response.raise_for_status()
            partner_tasks = self.decode_response(response).get("data", [])
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Network error while retrieving partner tasks: {e}", Fore.RED)
            partner_tasks = []
        except Exception as e:
            self.log(
                f"❌ Unexpected error while retrieving partner tasks: {e}", Fore.RED
            )
            partner_tasks = []

        for task in partner_tasks:
            task_id = task.get("_id")
            is_completed = task.get("isCompleted", False)
            is_can_claim = task.get("isCanClaim", False)
            task_name = task.get("metadata", {}).get("name", "Unknown Partner Task")
            if not is_completed and is_can_claim:
                try:
                    do_response = requests.post(
                        f"{self.BASE_URL}tasks/partner-tasks/{task_id}", headers=headers
                    )
                    do_response.raise_for_status()
                    self.log(
                        f"✅ Partner Task '{task_name}' successfully claimed.",
                        Fore.GREEN,
                    )
                    claimed_task_ids.append(task_id)
                except requests.exceptions.RequestException as e:
                    self.log(
                        f"❌ Failed to claim partner task '{task_name}': {e}", Fore.RED
                    )
                except Exception as e:
                    self.log(
                        f"❌ Unexpected error for partner task '{task_name}': {e}",
                        Fore.RED,
                    )
                time.sleep(5)
            else:
                self.log(
                    f"⚠️ Partner Task '{task_name}' is either completed or cannot be claimed.",
                    Fore.YELLOW,
                )

        # ====================================================
        # Phase 2: Claiming Campaigns via User Quests
        # ====================================================
        self.log("🔰 Phase 2: Claiming Campaigns", Fore.GREEN)

        try:
            payload = {"page": 1, "limit": 10, "filter": "going"}
            self.log("📡 Retrieving campaigns...", Fore.CYAN)
            response = requests.get(
                f"{self.BASE_URL}campaigns/filter?page=1&limit=10&filter=going",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            campaigns_response = self.decode_response(response)
            campaigns_list = campaigns_response.get("data", {}).get("data", [])
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Network error while retrieving campaigns: {e}", Fore.RED)
            campaigns_list = []
        except Exception as e:
            self.log(f"❌ Unexpected error while retrieving campaigns: {e}", Fore.RED)
            campaigns_list = []

        campaign_ids = []
        for campaign in campaigns_list:
            _id = campaign.get("_id")
            title = campaign.get("title", "Unknown Campaign")
            if _id:
                campaign_ids.append(_id)
            self.log(f"🎯 Campaign: {title}", Fore.GREEN)

        if not campaign_ids:
            self.log("⚠️ No campaigns found.", Fore.YELLOW)
        else:
            campaign_ids_query = "&".join(
                [f"campaignIds[]={_id}" for _id in campaign_ids]
            )
            user_quest_url = f"{self.BASE_URL}user-quest/list?{campaign_ids_query}"
            self.log("📡 Retrieving user quests...", Fore.CYAN)
            try:
                user_quest_response = requests.get(user_quest_url, headers=headers)
                user_quest_response.raise_for_status()
                user_quest_data = self.decode_response(user_quest_response)
            except requests.exceptions.RequestException as e:
                self.log(
                    f"❌ Network error while retrieving user quests: {e}", Fore.RED
                )
                user_quest_data = {}
            except Exception as e:
                self.log(
                    f"❌ Unexpected error while retrieving user quests: {e}", Fore.RED
                )
                user_quest_data = {}

            quests = user_quest_data.get("data", [])
            for quest in quests:
                # Jika struktur quest berupa dictionary
                if isinstance(quest, dict):
                    quest_id = quest.get("_id")
                    quest_status = quest.get("status", "")
                    quest_name = quest.get("name", "Unknown Quest")
                    if quest_id:
                        claimed_quest_ids[quest_id] = quest_status
                        if quest_status.lower() != "completed":
                            self.log(
                                f"📡 Claiming campaign for quest: {quest_name} (ID: {quest_id})",
                                Fore.CYAN,
                            )
                            claim_url = f"{self.BASE_URL}user-quest/{quest_id}/claim"
                            claim_url2 = f"{self.BASE_URL}user-quest/partner/{quest_id}"
                            try:
                                claim_response = requests.put(
                                    claim_url, headers=headers, json={}
                                )
                                claim_response.raise_for_status()
                                self.log(
                                    f"✅ Campaign claimed for quest: {quest_name}",
                                    Fore.GREEN,
                                )
                                # Jika diperlukan, kirim juga request kedua
                                requests.put(claim_url2, headers=headers)
                            except requests.exceptions.RequestException as e:
                                self.log(
                                    f"❌ Failed to claim campaign for quest '{quest_name}': {e}",
                                    Fore.RED,
                                )
                            except Exception as e:
                                self.log(
                                    f"❌ Unexpected error while claiming quest '{quest_name}': {e}",
                                    Fore.RED,
                                )
                            time.sleep(5)
                        else:
                            self.log(
                                f"⚠️ Quest '{quest_name}' already completed. No action needed.",
                                Fore.YELLOW,
                            )
                else:
                    # Jika data quest berbentuk nested list
                    for question in quest:
                        quest_id = question.get("_id")
                        quest_status = question.get("status", "")
                        quest_name = question.get("name", "Unknown Quest")
                        if quest_id:
                            claimed_quest_ids[quest_id] = quest_status
                            if quest_status.lower() != "completed":
                                self.log(
                                    f"📡 Claiming campaign for quest: {quest_name} (ID: {quest_id})",
                                    Fore.CYAN,
                                )
                                claim_url = (
                                    f"{self.BASE_URL}user-quest/{quest_id}/claim"
                                )
                                claim_url2 = (
                                    f"{self.BASE_URL}user-quest/partner/{quest_id}"
                                )
                                try:
                                    claim_response = requests.put(
                                        claim_url, headers=headers, json={}
                                    )
                                    claim_response.raise_for_status()
                                    self.log(
                                        f"✅ Campaign claimed for quest: {quest_name}",
                                        Fore.GREEN,
                                    )
                                    requests.put(claim_url2, headers=headers)
                                except requests.exceptions.RequestException as e:
                                    self.log(
                                        f"❌ Failed to claim campaign for quest '{quest_name}': {e}",
                                        Fore.RED,
                                    )
                                except Exception as e:
                                    self.log(
                                        f"❌ Unexpected error while claiming quest '{quest_name}': {e}",
                                        Fore.RED,
                                    )
                                time.sleep(5)
                            else:
                                self.log(
                                    f"⚠️ Quest '{quest_name}' already completed. No action needed.",
                                    Fore.YELLOW,
                                )

        # ====================================================
        # Phase 3: Claiming One-Time Achievements (Optimized)
        # ====================================================
        self.log("🔰 Phase 3: Claiming One-Time Achievements", Fore.GREEN)
        try:
            response = requests.get(f"{self.BASE_URL}tasks/one-time", headers=headers)
            response.raise_for_status()
            one_time_tasks = self.decode_response(response).get("data", [])
        except requests.exceptions.RequestException as e:
            self.log(
                f"❌ Network error occurred while retrieving one-time tasks: {e}",
                Fore.RED,
            )
            one_time_tasks = []
        except Exception as e:
            self.log(
                f"❌ Unexpected error while retrieving one-time tasks: {e}", Fore.RED
            )
            one_time_tasks = []

        achievements_claimed = []

        if not one_time_tasks:
            self.log("⚠️ No one-time achievements found.", Fore.YELLOW)
        else:
            for achievement in one_time_tasks:
                task_id = achievement.get("_id")
                name = achievement.get("metadata", {}).get(
                    "name", "Unknown Achievement"
                )
                progress = achievement.get("progress", 0)
                streaks = achievement.get("metadata", {}).get("streak", [])
                logs = achievement.get("logs", [])

                # Buat set target yang sudah diklaim berdasarkan logs
                claimed_targets = set()
                for log_entry in logs:
                    meta = log_entry.get("metadata", {})
                    if "target" in meta:
                        claimed_targets.add(meta["target"])

                # Iterasi tiap streak target dan klaim jika progress sudah mencapai target dan belum diklaim
                for streak in streaks:
                    target = streak.get("target")
                    if target is None:
                        self.log(
                            f"❌ Invalid streak target for achievement: {name} (ID: {task_id})",
                            Fore.RED,
                        )
                        continue

                    if progress >= target:
                        if target in claimed_targets:
                            self.log(
                                f"⚠️ Achievement '{name}' target {target} already claimed.",
                                Fore.YELLOW,
                            )
                            continue

                        claim_url = f"{self.BASE_URL}tasks/one-time/{task_id}/{target}"
                        try:
                            post_response = requests.post(claim_url, headers=headers)
                            if post_response.status_code == 201:
                                self.log(
                                    f"✅ Successfully claimed achievement: {name}, Target: {target}",
                                    Fore.GREEN,
                                )
                                achievements_claimed.append(f"{task_id}:{target}")
                            else:
                                self.log(
                                    f"❌ Failed to claim achievement: {name}, Target: {target}, Status: {post_response.status_code}",
                                    Fore.RED,
                                )
                        except requests.exceptions.RequestException as e:
                            self.log(
                                f"❌ Error claiming achievement {name}, Target: {target}: {e}",
                                Fore.RED,
                            )
                        except Exception as e:
                            self.log(
                                f"❌ Unexpected error claiming achievement {name}, Target: {target}: {e}",
                                Fore.RED,
                            )
                        time.sleep(5)
                    else:
                        self.log(
                            f"ℹ️ Achievement '{name}' target {target} not reached yet (Progress: {progress}).",
                            Fore.CYAN,
                        )

        # ====================================================
        # Summary
        # ====================================================
        self.log("🎉 Phase Summary:", Fore.MAGENTA)
        self.log(f"   Total tasks claimed: {len(claimed_task_ids)}", Fore.GREEN)
        self.log(f"   Total quests processed: {len(claimed_quest_ids)}", Fore.GREEN)
        self.log(
            f"   Total achievements claimed: {len(achievements_claimed)}", Fore.GREEN
        )

        return {
            "task_ids": claimed_task_ids,
            "quest_ids": claimed_quest_ids,
            "achievements": achievements_claimed,
        }

    def reff(self) -> list:
        """
        Retrieve referral users and boost them.

        Returns:
            A list of referral IDs that have been processed.
        """
        if not self.token:
            self.log("❌ No token available. Please log in first.", Fore.RED)
            return []

        headers = {**self.HEADERS, "Authorization": f"Bearer {self.token}"}
        referral_ids = []

        # ====================================================
        # Retrieve referral users
        # ====================================================
        self.log("📡 Retrieving referral users...", Fore.CYAN)
        try:
            response = requests.get(
                f"{self.BASE_URL}user-referral/list",
                headers=headers,
                params={"page": 1, "limit": 10},
            )
            response.raise_for_status()
            referral_data = (
                self.decode_response(response).get("data", {}).get("data", [])
            )
        except requests.exceptions.RequestException as e:
            self.log(
                f"❌ Network error occurred while retrieving referrals: {e}", Fore.RED
            )
            return referral_ids
        except Exception as e:
            self.log(f"❌ Unexpected error while retrieving referrals: {e}", Fore.RED)
            return referral_ids

        if not referral_data:
            self.log("⚠️ No referrals found.", Fore.YELLOW)
            return referral_ids

        for referral in referral_data:
            referral_id = referral.get("_id")
            if not referral_id:
                self.log("❌ Invalid referral data received.", Fore.RED)
                continue

            referral_ids.append(referral_id)
            first_name = referral.get("user", {}).get("firstName", "Unknown")
            last_name = referral.get("user", {}).get("lastName", "Unknown")
            self.log(
                f"👥 Referral: {first_name} {last_name} | ID: {referral_id}", Fore.GREEN
            )

        # ====================================================
        # Boost each referral
        # ====================================================
        for referral_id in referral_ids:
            try:
                boost_response = requests.put(
                    f"{self.BASE_URL}user-referral/boost/{referral_id}", headers=headers
                )
                boost_response.raise_for_status()
                boost_message = self.decode_response(boost_response).get(
                    "message", "Boost successful."
                )
                self.log(
                    f"🚀 Boosted referral ID {referral_id}: {boost_message}", Fore.GREEN
                )
            except requests.exceptions.RequestException as e:
                self.log(f"❌ Failed to boost referral ID {referral_id}: {e}", Fore.RED)
            except Exception as e:
                self.log(
                    f"❌ Unexpected error while boosting referral ID {referral_id}: {e}",
                    Fore.RED,
                )

        return referral_ids

    def load_proxies(self, filename="proxy.txt"):
        """
        Reads proxies from a file and returns them as a list.

        Args:
            filename (str): The path to the proxy file.

        Returns:
            list: A list of proxy addresses.
        """
        try:
            with open(filename, "r", encoding="utf-8") as file:
                proxies = [line.strip() for line in file if line.strip()]
            if not proxies:
                raise ValueError("Proxy file is empty.")
            return proxies
        except Exception as e:
            self.log(f"❌ Failed to load proxies: {e}", Fore.RED)
            return []

    def set_proxy_session(self, proxies: list) -> requests.Session:
        """
        Creates a requests session with a working proxy from the given list.

        If a chosen proxy fails the connectivity test, it will try another proxy
        until a working one is found. If no proxies work or the list is empty, it
        will return a session with a direct connection.

        Args:
            proxies (list): A list of proxy addresses (e.g., "http://proxy_address:port").

        Returns:
            requests.Session: A session object configured with a working proxy,
                            or a direct connection if none are available.
        """
        # If no proxies are provided, use a direct connection.
        if not proxies:
            self.log("⚠️ No proxies available. Using direct connection.", Fore.YELLOW)
            self.proxy_session = requests.Session()
            return self.proxy_session

        # Copy the list so that we can modify it without affecting the original.
        available_proxies = proxies.copy()

        while available_proxies:
            proxy_url = random.choice(available_proxies)
            self.proxy_session = requests.Session()
            self.proxy_session.proxies = {"http": proxy_url, "https": proxy_url}

            try:
                test_url = "https://httpbin.org/ip"
                response = self.proxy_session.get(test_url, timeout=5)
                response.raise_for_status()
                origin_ip = response.json().get("origin", "Unknown IP")
                self.log(
                    f"✅ Using Proxy: {proxy_url} | Your IP: {origin_ip}", Fore.GREEN
                )
                return self.proxy_session
            except requests.RequestException as e:
                self.log(f"❌ Proxy failed: {proxy_url} | Error: {e}", Fore.RED)
                # Remove the failed proxy and try again.
                available_proxies.remove(proxy_url)

        # If none of the proxies worked, use a direct connection.
        self.log("⚠️ All proxies failed. Using direct connection.", Fore.YELLOW)
        self.proxy_session = requests.Session()
        return self.proxy_session

    def override_requests(self):
        import random

        """Override requests functions globally when proxy is enabled."""
        if self.config.get("proxy", False):
            self.log("[CONFIG] 🛡️ Proxy: ✅ Enabled", Fore.YELLOW)
            proxies = self.load_proxies()
            self.set_proxy_session(proxies)

            # Override request methods
            requests.get = self.proxy_session.get
            requests.post = self.proxy_session.post
            requests.put = self.proxy_session.put
            requests.delete = self.proxy_session.delete
        else:
            self.log("[CONFIG] proxy: ❌ Disabled", Fore.RED)
            # Restore original functions if proxy is disabled
            requests.get = self._original_requests["get"]
            requests.post = self._original_requests["post"]
            requests.put = self._original_requests["put"]
            requests.delete = self._original_requests["delete"]


async def process_account(account, original_index, account_label, rewards, config):

    ua = UserAgent()
    rewards.HEADERS["user-agent"] = ua.random

    # Menampilkan informasi akun
    display_account = account[:10] + "..." if len(account) > 10 else account
    rewards.log(f"👤 Processing {account_label}: {display_account}", Fore.YELLOW)

    # Override proxy jika diaktifkan
    if config.get("proxy", False):
        rewards.override_requests()
    else:
        rewards.log("[CONFIG] Proxy: ❌ Disabled", Fore.RED)

    # Login (fungsi blocking, dijalankan di thread terpisah) dengan menggunakan index asli (integer)
    await asyncio.to_thread(rewards.login, original_index)

    rewards.log("🛠️ Starting task execution...", Fore.CYAN)
    tasks_config = {
        "task": "Automatically solving tasks 🤖",
        "farming": "Automatic farming for abundant harvest 🌾",
        "spin": "Automatically spinning for rewarding outcomes 🎰",
        "reff": "Automatically boosting referrals for bonus points 🚀",
    }

    for task_key, task_name in tasks_config.items():
        task_status = config.get(task_key, False)
        color = Fore.YELLOW if task_status else Fore.RED
        rewards.log(
            f"[CONFIG] {task_name}: {'✅ Enabled' if task_status else '❌ Disabled'}",
            color,
        )
        if task_status:
            rewards.log(f"🔄 Executing {task_name}...", Fore.CYAN)
            await asyncio.to_thread(getattr(rewards, task_key))

    delay_switch = config.get("delay_account_switch", 10)
    rewards.log(
        f"➡️ Finished processing {account_label}. Waiting {Fore.WHITE}{delay_switch}{Fore.CYAN} seconds before next account.",
        Fore.CYAN,
    )
    await asyncio.sleep(delay_switch)


async def worker(worker_id, rewards, config, queue):
    """
    Setiap worker akan mengambil satu akun dari antrian dan memprosesnya secara berurutan.
    Worker tidak akan mengambil akun baru sebelum akun sebelumnya selesai diproses.
    """
    while True:
        try:
            original_index, account = queue.get_nowait()
        except asyncio.QueueEmpty:
            break
        account_label = f"Worker-{worker_id} Account-{original_index+1}"
        await process_account(account, original_index, account_label, rewards, config)
        queue.task_done()
    rewards.log(
        f"Worker-{worker_id} finished processing all assigned accounts.", Fore.CYAN
    )


async def main():
    rewards = RewardsHQ()
    config = rewards.load_config()
    all_accounts = rewards.query_list
    num_threads = config.get("thread", 1)  # Jumlah worker sesuai konfigurasi

    if config.get("proxy", False):
        proxies = rewards.load_proxies()

    rewards.log(
        "🎉 [LIVEXORDS] === Welcome to RewardsHQ Automation === [LIVEXORDS]",
        Fore.YELLOW,
    )
    rewards.log(f"📂 Loaded {len(all_accounts)} accounts from query list.", Fore.YELLOW)

    while True:
        # Buat queue baru dan masukkan semua akun (dengan index asli)
        queue = asyncio.Queue()
        for idx, account in enumerate(all_accounts):
            queue.put_nowait((idx, account))

        # Buat task worker sesuai dengan jumlah thread yang diinginkan
        workers = [
            asyncio.create_task(worker(i + 1, rewards, config, queue))
            for i in range(num_threads)
        ]

        # Tunggu hingga semua akun di queue telah diproses
        await queue.join()

        # Opsional: batalkan task worker (agar tidak terjadi tumpang tindih)
        for w in workers:
            w.cancel()

        rewards.log("🔁 All accounts processed. Restarting loop.", Fore.CYAN)
        delay_loop = config.get("delay_loop", 30)
        rewards.log(
            f"⏳ Sleeping for {Fore.WHITE}{delay_loop}{Fore.CYAN} seconds before restarting.",
            Fore.CYAN,
        )
        await asyncio.sleep(delay_loop)


if __name__ == "__main__":
    asyncio.run(main())
