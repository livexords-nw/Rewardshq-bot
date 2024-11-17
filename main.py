import os
import time
from datetime import datetime
from colorama import Fore
import requests
import json

class Auth:
    BASE_URL = "https://api-rewardshq.shards.tech/v1"
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9",
        "Origin": "https://rewardshq.shards.tech",
        "Referer": "https://rewardshq.shards.tech/"
    }

    def __init__(self, query_file="query.txt"):
        self.query_list = self.load_queries(query_file)
        self.token = None
        self.username = None

    @staticmethod
    def log(message, color=Fore.RESET):
        print(Fore.LIGHTBLACK_EX + datetime.now().strftime("[%Y:%m:%d:%H:%M:%S] |") + " " + color + message + Fore.RESET)

    def banner(self):
        print("     RewardsHQ Free Bot")
        print("     This Bot Created By LIVEXORDS\n")
        print("     Channel: t.me/livexordsscript")

    def load_config(self):
        try:
            with open('config.json') as config_file:
                config = json.load(config_file)
                required_keys = ["auto_farming", "auto_spin", "auto_task", "auto_campaign", "auto_achievements", "delay_iteration", "delay_change_account"]
                for key in required_keys:
                    if key not in config:
                        self.log(f"Missing config key: {key}. Please check your config.json.", Fore.RED)
                return config
        except FileNotFoundError:
            self.log("config.json not found. Please ensure the configuration file is available.", Fore.RED)
            return {}


    def load_queries(self, file_path):
        """Load queries from a text file."""
        self.banner()
        try:
            with open(file_path, 'r') as file:
                queries = [line.strip() for line in file if line.strip()]
            self.log(f"Data Load : {len(queries)}", Fore.GREEN)
            return queries
        except FileNotFoundError:
            self.log("File query.txt not found.", Fore.RED)
            return []

    def user(self):
        """Fetch user information and store username."""
        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}

        try:    
            response = requests.get(f"{self.BASE_URL}/users", headers=headers)
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred: {e}", Fore.RED)
            return

        if response.status_code == 200:
            data = response.json().get("data", {})
            self.username = data.get("firstName", "") + data.get("lastName", "")
        else:
            self.log("Failed to retrieve user data.", Fore.RED)

    def streakLogin(self):
        """Fetch user information Streak Login."""
        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(f"{self.BASE_URL}/users/streak-login", headers=headers)
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred: {e}", Fore.RED)
            return

        if response.status_code == 200:
            data = response.json().get("data", {})
            self.log(f"Streak: {data.get('streak', 0)}", Fore.YELLOW)
            self.log(f"pointBonus: {data.get('pointBonus', 'N/A')}", Fore.YELLOW)
        else:
            self.log("Failed to retrieve Login data.", Fore.RED)

    def point(self):
        """Fetch user information Point user."""
        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}

        try:
            response = requests.get(f"{self.BASE_URL}/point-logs", headers=headers)
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred: {e}", Fore.RED)
            return

        if response.status_code == 200:
            data = response.json().get("data", {})
            self.log(f"Point: {data.get('point', 0)}", Fore.YELLOW)
            self.log(f"referralPoint: {data.get('referralPoint', 0)}", Fore.YELLOW)
        else:
            self.log("Failed to retrieve Point data.", Fore.RED)

    def spinPoint(self):
        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.BASE_URL}/user-spin-logs", headers=headers)
        data = response.json().get("data", {})
        number_of_spins = data.get("numberSpin", 0)
        self.log(f"Spin: {number_of_spins}", Fore.GREEN)

    def login(self, index):
        """Login using a query index and save the access token."""
        if not (0 <= index < len(self.query_list)):
            self.log(f"Index {index} out of range.", Fore.RED)
            return None

        token_file = "token.json"

        # Step 1: Check token.json
        if os.path.exists(token_file):
            try:
                with open(token_file, "r") as file:
                    token_data = json.load(file)
            except (json.JSONDecodeError, IOError) as e:
                self.log(f"Error reading token.json: {e}", Fore.RED)
                token_data = {}
        else:
            token_data = {}

        # Step 2: Check for existing token
        query_key = self.query_list[index]
        saved_token = token_data.get(query_key)  # Ambil token untuk query ini

        if saved_token:  # Token ada, tetapi perlu divalidasi
            self.token = saved_token
            # Validasi token dengan API (misalnya panggil endpoint "validate token")
            try:
                response = requests.get(
                    f"{self.BASE_URL}/auth/validate",
                    headers={**self.headers, "Authorization": f"Bearer {self.token}"}
                )
                if response.status_code == 200:
                    self.log("Token is valid, using saved token.", Fore.GREEN)
                    self.user()
                    self.log(f"Username: {self.username}", Fore.CYAN)
                    self.spinPoint()
                    self.point()
                    self.streakLogin()
                    return
                else:
                    self.log("Token is invalid, fetching new token.", Fore.YELLOW)
            except requests.exceptions.RequestException as e:
                self.log(f"Network error during token validation: {e}", Fore.RED)
                return

        # Step 3: Fetch token from API
        try:
            response = requests.post(
                f"{self.BASE_URL}/auth/login",
                headers=self.headers,
                json={"telegramInitData": query_key}
            )
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred: {e}", Fore.RED)
            return

        if response.status_code == 201:
            data = response.json().get("data", {})
            self.token = data.get("accessToken")
            refresh_token = data.get("refreshToken")
            if self.token and refresh_token:
                self.log("Login successful, token saved.", Fore.GREEN)

                # Step 4: Update token.json
                token_data[query_key] = self.token
                try:
                    with open(token_file, "w") as file:
                        json.dump(token_data, file, indent=4)
                except IOError as e:
                    self.log(f"Error writing to token.json: {e}", Fore.RED)

                self.user()
                self.log(f"Username: {self.username}", Fore.CYAN)
                self.spinPoint()
                self.point()
                self.streakLogin()
            else:
                self.log("Incomplete token in API response.", Fore.RED)
        else:
            self.log("Query expired or invalid.", Fore.RED)

    def start_farming(self):
        """Initiate farming request if token is present."""
        if not self.token:
            self.log("No token available. Please log in first.", Fore.RED)
            return None
        
        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}
        try:
            requests.put(f"{self.BASE_URL}/user-earn-hour", headers=headers)
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred: {e}", Fore.RED)
            return
        
        try:
            response = requests.get(f"{self.BASE_URL}/user-earn-hour", headers=headers)
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred: {e}", Fore.RED)
            return

        if response.status_code == 200:
            self.log("Farming request successful.", Fore.GREEN)
            return response.json()
        else:
            self.log(f"Farming failed, status code: {response.status_code}", Fore.RED)
        return None

    def spin(self):
        """Perform spin actions in a loop until no spins are available."""
        if not self.token:
            self.log("No token available. Please log in first.", Fore.RED)
            return None

        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}
        spin_count = 1

        while True:
            try:
                # Fetch current spin status
                response = requests.get(f"{self.BASE_URL}/user-spin-logs", headers=headers)
                if response.status_code != 200:
                    self.log(f"Failed to retrieve spin logs, status code: {response.status_code}", Fore.RED)
                    break

                data = response.json().get("data", {})
                number_of_spins = data.get("numberSpin", 0)

                if number_of_spins == 0:
                    self.log("No spin points remaining.", Fore.YELLOW)
                    break

                # Perform spin action
                spin_response = requests.put(f"{self.BASE_URL}/user-spin-logs", headers=headers)
                if spin_response.status_code != 200:
                    self.log(f"Spin failed at spin {spin_count}, status code: {spin_response.status_code}", Fore.RED)
                    break

                spin_data = spin_response.json().get("data", {})
                if not spin_data:
                    self.log("Spin response data missing. Retrying...", Fore.RED)
                    continue

                # Extract and log results
                points = spin_data.get("point", 0)
                xp = spin_data.get("xp", 0)
                usdt = spin_data.get("usdt", 0)
                updated_spins = spin_data.get("numberSpin", number_of_spins - 1)  # Assume decrement

                self.log(
                    f"Spin {spin_count} successful! Points: {points}, XP: {xp}, USDT: {usdt}, Spins left: {updated_spins}",
                    Fore.GREEN,
                )
                spin_count += 1

            except requests.exceptions.RequestException as e:
                self.log(f"Network error occurred: {e}", Fore.RED)
                break

            # Delay before the next spin
            time.sleep(5)

    def task(self):
        """Claim tasks from all categories efficiently."""
        if not self.token:
            self.log("No token available. Please log in first.", Fore.RED)
            return None

        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}
        categories = [
            ("tasks", "Task"),
            ("tasks/basic-tasks", "Basic Task"),
            ("tasks/partner-tasks", "Partner Task")
        ]

        claimed_task_ids = []

        for endpoint, category_name in categories:
            self.log(f"{Fore.GREEN}Category: {category_name}")
            try:
                response = requests.get(f"{self.BASE_URL}/{endpoint}", headers=headers)
                if response.status_code != 200:
                    self.log(f"Failed to retrieve {category_name.lower()}s, status code: {response.status_code}", Fore.RED)
                    continue

                tasks = response.json().get("data", [])
                for task in tasks:
                    task_id = task.get("_id")
                    task_name = task.get("metadata", {}).get("name", "Unknown Task")
                    is_completed = task.get("isCompleted", False)
                    is_can_claim = task.get("isCanClaim", False)

                    if is_completed or not is_can_claim:
                        self.log(f"{category_name} '{task_name}' is either completed or cannot be claimed.", Fore.YELLOW)
                        continue

                    try:
                        do_task_response = requests.post(f"{self.BASE_URL}/{endpoint}/{task_id}", headers=headers)
                        if do_task_response.status_code in {200, 201}:
                            self.log(f"{category_name} '{task_name}' successfully claimed.", Fore.GREEN)
                            claimed_task_ids.append(task_id)
                            time.sleep(5)  # Delay only on success
                        else:
                            self.log(f"Failed to complete {category_name.lower()} '{task_name}', status code: {do_task_response.status_code}", Fore.RED)
                    except requests.exceptions.RequestException as e:
                        self.log(f"Network error occurred while claiming {category_name.lower()} '{task_name}': {e}", Fore.RED)

            except requests.exceptions.RequestException as e:
                self.log(f"Network error occurred while fetching {category_name.lower()}s: {e}", Fore.RED)

        self.log(f"{len(claimed_task_ids)} tasks have been successfully claimed.", Fore.CYAN)
        return claimed_task_ids
    
    def campain(self):
        if not self.token:
            self.log("No token available. Please log in first.", Fore.RED)
            return None

        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}

        payload = {
            "page": 1,
            "limit": 10,
            "keyword": ""
        }

        try:
            response = requests.get(f"{self.BASE_URL}/campaigns?page=1&limit=10&keyword=", headers=headers, json=payload)
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred: {e}", Fore.RED)
            return

        data = []

        if response.status_code != 200:
            self.log(f"Failed to retrieve partner tasks, status code: {response.status_code}", Fore.RED)
            return None
        else:
            campaigns = response.json().get("data", [])
            campaign = campaigns.get("data", [])
            for campaigns in campaign:
                _id = campaigns.get("_id")
                if _id:
                    data.append(_id) 
                self.log(f"Title: {campaigns.get('title')}", Fore.GREEN)

        if not data:
            self.log("No campaigns found.", Fore.YELLOW)
            return None

        campaign_ids_query = "&".join([f"campaignIds[]={_id}" for _id in data])

        user_quest_url = f"{self.BASE_URL}/user-quest/list?{campaign_ids_query}"

        try:
            user_quest_response = requests.get(user_quest_url, headers=headers)
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred: {e}", Fore.RED)
            return


        if user_quest_response.status_code != 200:
            self.log(f"Failed to retrieve user quests, status code: {user_quest_response.status_code}", Fore.RED)
            return None

        time.sleep(5)

        user_quests = user_quest_response.json()
        quest_ids = []  

        for quest in user_quests.get("data", []):
            for question in quest:
                quest_id = question.get("_id")  
                if quest_id:
                    quest_ids.append(quest_id)  
                self.log(f"{question.get('name')} | Status: {question.get('status')} | ID: {quest_id}", Fore.GREEN)

        time.sleep(5)
        
        for quest_id in quest_ids:
            put_url = f"{self.BASE_URL}/user-quest/{quest_id}"
            put_payload = {}  

            try:
                put_response = requests.put(put_url, headers=headers, json=put_payload)
            except requests.exceptions.RequestException as e:
                self.log(f"Network error occurred: {e}", Fore.RED)
                return

            
            if put_response.status_code == 200:
                try:
                    quest_data = put_response.json().get("data", {})
                    metadata = quest_data.get("metadata", {})
                    
                    quest_title = metadata.get("name", "Unknown Title")  
                    self.log(f"Completed quest: {quest_title}", Fore.GREEN)
                    
                except ValueError:
                    self.log("Failed to parse response JSON.", Fore.RED)
                time.sleep(5)
            else:
                try:
                    quest_data = put_response.json().get("data", {})
                    metadata = quest_data.get("metadata", {})
                    
                    quest_title = metadata.get("name", "Unknown Title")
                    self.log(f"Failed to complete quest: {quest_title}", Fore.RED)
                    
                except ValueError:
                    self.log("Failed to parse response JSON.", Fore.RED)
        return quest_ids 

    def reff(self):
        """Retrieve and boost referral users."""
        if not self.token:
            self.log("No token available. Please log in first.", Fore.RED)
            return None

        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}
        referral_ids = []

        try:
            # Fetch referral list
            response = requests.get(
                f"{self.BASE_URL}/user-referral/list",
                headers=headers,
                params={"page": 1, "limit": 10}
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred: {e}", Fore.RED)
            return

        referral_data = response.json().get("data", {}).get("data", [])
        if not referral_data:
            self.log("No referrals found.", Fore.YELLOW)
            return None

        # Process each referral
        for referral in referral_data:
            referral_id = referral.get("_id")
            if not referral_id:
                self.log("Invalid referral data received.", Fore.RED)
                continue

            referral_ids.append(referral_id)
            first_name = referral.get("user", {}).get("firstName", "Unknown")
            last_name = referral.get("user", {}).get("lastName", "Unknown")
            self.log(f"Referral: {first_name} {last_name} | ID: {referral_id}", Fore.GREEN)

        # Boost each referral
        for referral_id in referral_ids:
            try:
                response = requests.put(
                    f"{self.BASE_URL}/user-referral/boost/{referral_id}",
                    headers=headers
                )
                response.raise_for_status()
            except requests.exceptions.RequestException as e:
                self.log(f"Failed to boost referral ID {referral_id}: {e}", Fore.RED)
                continue

            boost_message = response.json().get("message", "Boost successful.")
            self.log(f"Boosted referral ID {referral_id}: {boost_message}", Fore.GREEN)

        return referral_ids

    def achievements(self):
        """Retrieve and claim one-time achievements."""
        if not self.token:
            self.log("No token available. Please log in first.", Fore.RED)
            return None

        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}

        try:
            # Get one-time tasks
            response = requests.get(f"{self.BASE_URL}/tasks/one-time", headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred while retrieving tasks: {e}", Fore.RED)
            return

        tasks = response.json().get("data", [])
        if not tasks:
            self.log("No one-time tasks found.", Fore.YELLOW)
            return None

        # Process each task
        for task in tasks:
            task_id = task.get("_id")
            name = task.get("metadata", {}).get("name", "Unknown Task")
            streaks = task.get("metadata", {}).get("streak", [])

            if not streaks:
                self.log(f"No streak targets found for task: {name} (ID: {task_id})", Fore.YELLOW)
                continue

            for streak in streaks:
                target = streak.get("target")
                if not target:
                    self.log(f"Invalid streak target for task: {name} (ID: {task_id})", Fore.RED)
                    continue

                claim_url = f"{self.BASE_URL}/tasks/one-time/{task_id}/{target}"
                try:
                    # Claim the achievement
                    post_response = requests.post(claim_url, headers=headers)
                    if post_response.status_code == 201:
                        self.log(f"Successfully claimed achievement: {name}, Target: {target}", Fore.GREEN)
                    else:
                        self.log(f"Failed to claim achievement: {name}, Target: {target}, Status: {post_response.status_code}", Fore.RED)
                except requests.exceptions.RequestException as e:
                    self.log(f"Error claiming achievement {name}, Target: {target}: {e}", Fore.RED)

                # Introduce a delay between requests to avoid rate-limiting
                time.sleep(5)

        return True


    def run(self):
        """Main loop to log in and process each query for up to 6 hours."""
        index = 0
        config = self.load_config()
        total_accounts = len(self.query_list)

        while True:
            # Log login process
            self.log(f"Login to User {index + 1}/{total_accounts}", Fore.CYAN)
            self.login(index)

            # Process tasks based on configuration
            tasks = [
                ("Farming", config["auto_farming"], self.start_farming),
                ("Reff", config["auto_reff"], self.reff),
                ("Spin", config["auto_spin"], self.spin),
                ("Tasks", config["auto_task"], self.task),
                ("Campaign", config["auto_campaign"], self.campain),
                ("Achievements", config["auto_achievements"], self.achievements),
            ]

            for task_name, is_enabled, task_func in tasks:
                if is_enabled:
                    self.log(f"{task_name}: On", Fore.GREEN)
                    try:
                        task_func()
                    except Exception as e:
                        self.log(f"Error in {task_name}: {e}", Fore.RED)
                else:
                    self.log(f"{task_name}: {Fore.RED}Off", Fore.GREEN)

            # Move to the next account
            index += 1
            if index >= total_accounts:
                index = 0
                self.log(f"Restarting in {config['delay_iteration']} seconds.", Fore.YELLOW)
                time.sleep(config["delay_iteration"])

            self.log(f"Moving to the next account in {config['delay_change_account']} seconds.", Fore.CYAN)
            time.sleep(config["delay_change_account"])

            self.log("---------------------------------------", Fore.MAGENTA)

if __name__ == "__main__":
    auth = Auth()
    auth.run()
