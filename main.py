import time
from datetime import datetime
from colorama import Fore
import requests
import json

class RewardsHQ:
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

        response = requests.post(
            f"{self.BASE_URL}/auth/login",
            headers=self.headers,
            json={"telegramInitData": self.query_list[index]}
        )

        if response.status_code == 201:
            data = response.json().get("data", {})
            self.token = data.get("accessToken")
            refresh_token = data.get("refreshToken")
            if self.token and refresh_token:
                self.log("Login successful", Fore.GREEN)
                self.user()
                self.log(f"Username: {self.username}", Fore.CYAN)
            else:
                self.log("Incomplete token in API response.", Fore.RED)
        else:
            self.log(f"Login failed, status code: {response.status_code}", Fore.RED)

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
                response = requests.get(f"{self.BASE_URL}/user-spin-logs", headers=headers)
                if response.status_code != 200:
                    self.log(f"Failed to retrieve spin logs, status code: {response.status_code}", Fore.RED)
                    break

                data = response.json().get("data", {})
                number_of_spins = data.get("numberSpin", 0)

                if number_of_spins == 0:
                    self.log("No spin points remaining.", Fore.YELLOW)
                    break

                spin_response = requests.put(f"{self.BASE_URL}/user-spin-logs", headers=headers)
                if spin_response.status_code != 200:
                    self.log(f"Spin failed at spin {spin_count}, status code: {spin_response.status_code}", Fore.RED)
                    break

                spin_data = spin_response.json().get("data", {})
                if not spin_data:
                    self.log("Spin response data missing. Retrying...", Fore.RED)
                    continue

                points = spin_data.get("point", 0)
                xp = spin_data.get("xp", 0)
                usdt = spin_data.get("usdt", 0)
                updated_spins = spin_data.get("numberSpin", number_of_spins - 1)  

                self.log(
                    f"Spin {spin_count} successful! Points: {points}, XP: {xp}, USDT: {usdt}, Spins left: {updated_spins}",
                    Fore.GREEN,
                )
                spin_count += 1

            except requests.exceptions.RequestException as e:
                self.log(f"Network error occurred: {e}", Fore.RED)
                break

            time.sleep(5)

    def task(self):
        """Claim tasks from both basic-tasks and partner-tasks categories."""
        if not self.token:
            self.log("No token available. Please log in first.", Fore.RED)
            return None

        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}
        task_ids = [] 

        self.log(f"{Fore.GREEN}Category: Task")
        try:
            response = requests.get(f"{self.BASE_URL}/tasks", headers=headers)
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred: {e}", Fore.RED)
            return

        if response.status_code != 200:
            self.log(f"Failed to retrieve basic tasks, status code: {response.status_code}", Fore.RED)
        else:
            basic_tasks_data = response.json().get("data", [])
            for task in basic_tasks_data:
                task_id = task.get("_id")
                is_completed = task.get("isCompleted", False)
                is_can_claim = task.get("isCanClaim", False)
                task_name = task.get("metadata", {}).get("name", "Unknown Task")

                if not is_completed and is_can_claim:
                    task_ids.append(task_id)
                    
                    try:
                        do_task_response = requests.post(f"{self.BASE_URL}/tasks/do-task/{task_id}", headers=headers)
                    except requests.exceptions.RequestException as e:
                        self.log(f"Network error occurred: {e}", Fore.RED)
                        return

                    if do_task_response.status_code == 200 or do_task_response.status_code == 201:
                        self.log(f"Task '{task_name}' successfully claimed.", Fore.GREEN)
                    else:
                        self.log(f"Failed to complete task '{task_name}', status code: {do_task_response.status_code}", Fore.RED)
                    time.sleep(5)
                else:
                    self.log(f"Task '{task_name}' is either completed or cannot be claimed.", Fore.YELLOW)

        self.log(f"{Fore.GREEN}Category: Basic Task")
        try:
            response = requests.get(f"{self.BASE_URL}/tasks/basic-tasks", headers=headers)
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred: {e}", Fore.RED)
            return

        if response.status_code != 200:
            self.log(f"Failed to retrieve basic tasks, status code: {response.status_code}", Fore.RED)
        else:
            partner_tasks_data = response.json().get("data", [])
            for task in partner_tasks_data:
                task_id = task.get("_id")
                is_completed = task.get("isCompleted", False)
                is_can_claim = task.get("isCanClaim", False)
                task_name = task.get("metadata", {}).get("name", "Unknown Partner Task")

                if not is_completed and is_can_claim:
                    task_ids.append(task_id)
                    
                    try: 
                        do_task_response = requests.post(f"{self.BASE_URL}/tasks/basic-tasks/{task_id}", headers=headers)
                    except requests.exceptions.RequestException as e:
                        self.log(f"Network error occurred: {e}", Fore.RED)
                        return

                    if do_task_response.status_code == 200 or do_task_response.status_code == 201:
                        self.log(f"Basic Task '{task_name}' successfully claimed.", Fore.GREEN)
                    else:
                        self.log(f"Failed to complete basic task '{task_name}', status code: {do_task_response.status_code}", Fore.RED)
                    time.sleep(5)
                else:
                    self.log(f"Basic Task '{task_name}' is either completed or cannot be claimed.", Fore.YELLOW)

        self.log(f"{Fore.GREEN}Category: Partner Task")
        try:
            response = requests.get(f"{self.BASE_URL}/tasks/partner-tasks", headers=headers)
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred: {e}", Fore.RED)
            return

        if response.status_code != 200:
            self.log(f"Failed to retrieve partner tasks, status code: {response.status_code}", Fore.RED)
        else:
            partner_tasks_data = response.json().get("data", [])
            for task in partner_tasks_data:
                task_id = task.get("_id")
                is_completed = task.get("isCompleted", False)
                is_can_claim = task.get("isCanClaim", False)
                task_name = task.get("metadata", {}).get("name", "Unknown Partner Task")

                if not is_completed and is_can_claim:
                    task_ids.append(task_id)

                    try:
                        do_task_response = requests.post(f"{self.BASE_URL}/tasks/partner-tasks/{task_id}", headers=headers)
                    except requests.exceptions.RequestException as e:
                        self.log(f"Network error occurred: {e}", Fore.RED)
                        return

                    if do_task_response.status_code == 200 or do_task_response.status_code == 201:
                        self.log(f"Partner Task '{task_name}' successfully claimed.", Fore.GREEN)
                    else:
                        self.log(f"Failed to complete partner task '{task_name}', status code: {do_task_response.status_code}", Fore.RED)
                    time.sleep(5)
                else:
                    self.log(f"Partner Task '{task_name}' is either completed or cannot be claimed.", Fore.YELLOW)

        self.log(f"{len(task_ids)} tasks have been successfully claimed.")
        return task_ids
    
    def campain(self):
        if not self.token:
            self.log("No token available. Please log in first.", Fore.RED)
            return None

        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}

        payload = {
            "page": 1,
            "limit": 10,
            "filter": "going"
        }

        try:
            response = requests.get(f"{self.BASE_URL}/campaigns/filter?page=1&limit=10&filter=going", headers=headers, json=payload)
        except requests.excptions.RequestException as e:
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

        user_quests = user_quest_response.json()
        quest_ids = []  

        for quest in user_quests.get("data", []):
            for question in quest:
                quest_id = question.get("_id")
                quest_status = question.get("status", None)  
                quest_name = question.get("name", "Unknown Name")

                if quest_id:
                    quest_ids.append(quest_id)

                    if quest_status is None or quest_status.lower() != "completed":
                        self.log(f"{quest_name} | Status: {quest_status} | ID: {quest_id} - Claiming campaign", Fore.RED)
                        
                        claim_url = f"{self.BASE_URL}/user-quest/{quest_id}/claim"
                        claim_url2 = f"{self.BASE_URL}/user-quest/partner/{quest_id}"

                        claim_payload = {}
                        try:
                            claim_response = requests.put(claim_url, headers=headers, json=claim_payload)
                            requests.put(claim_url2, headers=headers)
                            if claim_response.status_code == 200:
                                self.log(f"Campaign successfully claimed for quest: {quest_name}", Fore.GREEN)
                            else:
                                self.log(f"Failed to claim campaign for quest: {quest_name}", Fore.RED)
                        except requests.exceptions.RequestException as e:
                            self.log(f"Network error occurred while claiming campaign: {e}", Fore.RED)
                    else:
                        self.log(f"{quest_name} | Status: {quest_status} | ID: {quest_id} - No action needed", Fore.YELLOW)
        return quest_ids 

    def reff(self):
        """Retrieve and boost referral users."""
        if not self.token:
            self.log("No token available. Please log in first.", Fore.RED)
            return None

        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}
        referral_ids = []

        try:
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

        for referral in referral_data:
            referral_id = referral.get("_id")
            if not referral_id:
                self.log("Invalid referral data received.", Fore.RED)
                continue

            referral_ids.append(referral_id)
            first_name = referral.get("user", {}).get("firstName", "Unknown")
            last_name = referral.get("user", {}).get("lastName", "Unknown")
            self.log(f"Referral: {first_name} {last_name} | ID: {referral_id}", Fore.GREEN)

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
            response = requests.get(f"{self.BASE_URL}/tasks/one-time", headers=headers)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            self.log(f"Network error occurred while retrieving tasks: {e}", Fore.RED)
            return

        tasks = response.json().get("data", [])
        if not tasks:
            self.log("No one-time tasks found.", Fore.YELLOW)
            return None

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
                    post_response = requests.post(claim_url, headers=headers)
                    if post_response.status_code == 201:
                        self.log(f"Successfully claimed achievement: {name}, Target: {target}", Fore.GREEN)
                    else:
                        self.log(f"Failed to claim achievement: {name}, Target: {target}, Status: {post_response.status_code}", Fore.RED)
                except requests.exceptions.RequestException as e:
                    self.log(f"Error claiming achievement {name}, Target: {target}: {e}", Fore.RED)

        return True

    def run(self):
        """Main loop to log in and process each query for up to 6 hours."""
        index = 0
        config = self.load_config()
        total_accounts = len(self.query_list)

        while True:
            self.log(f"Login to User {index + 1}/{total_accounts}", Fore.CYAN)
            self.login(index)

            tasks = [
                ("Farming", config["auto_farming"], self.start_farming),
                ("Reff", config["auto_reff"], self.reff),
                ("Tasks", config["auto_task"], self.task),
                ("Campaign", config["auto_campaign"], self.campain),
                ("Achievements", config["auto_achievements"], self.achievements),
                ("Spin", config["auto_spin"], self.spin),
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

            index += 1
            if index >= total_accounts:
                index = 0
                self.log(f"Restarting in {config['delay_iteration']} seconds.", Fore.YELLOW)
                time.sleep(config["delay_iteration"])

            self.log(f"Moving to the next account in {config['delay_change_account']} seconds.", Fore.CYAN)
            time.sleep(config["delay_change_account"])

            self.log("---------------------------------------", Fore.MAGENTA)

if __name__ == "__main__":
    Rewards = RewardsHQ()
    Rewards.run()
