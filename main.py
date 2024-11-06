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

    def load_config(self):
        """Load the configuration from config.json once at the start."""
        with open('config.json') as config_file:
            config = json.load(config_file)
        return config

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
        response = requests.get(f"{self.BASE_URL}/users", headers=headers)

        if response.status_code == 200:
            data = response.json().get("data", {})
            self.username = data.get("firstName", "") + data.get("lastName", "")
        else:
            self.log("Failed to retrieve user data.", Fore.RED)

    def streakLogin(self):
        """Fetch user information Streak Login."""
        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.BASE_URL}/users/streak-login", headers=headers)

        if response.status_code == 200:
            data = response.json().get("data", {})
            self.log(f"Streak: {data.get("streak", 0)}")
            self.log(f"pointBonus: {data.get("pointBonus", "N/A")}")
            self.log(f"prevPointBonus: {data.get("prevPointBonus", 0)}")
            self.log(f"nextPointBonus: {data.get("nextPointBonus", "N/A")}")
        else:
            self.log("Failed to retrieve Login data.", Fore.RED)

    def point(self):
        """Fetch user information Point user."""
        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.BASE_URL}/point-logs", headers=headers)

        if response.status_code == 200:
            data = response.json().get("data", {})
            self.log(f"Point: {data.get("point", 0)}")
            self.log(f"referralPoint: {data.get("referralPoint", 0)}")
        else:
            self.log("Failed to retrieve Point data.", Fore.RED)

    def spinPoint(self):
        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{self.BASE_URL}/user-spin-logs", headers=headers)
        data = response.json().get("data", {})
        number_of_spins = data.get("numberSpin", 0)
        self.log(f"Spin: {number_of_spins}")

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
                self.log("Login successful, token saved.", Fore.GREEN)
                self.user()
                self.log(f"Username: {self.username}", Fore.CYAN)
                self.spinPoint()
                self.point()
                self.streakLogin()
            else:
                self.log("Incomplete token in API response.", Fore.RED)
        else:
            self.log(f"Query Expired", Fore.RED)

    def start_farming(self):
        """Initiate farming request if token is present."""
        if not self.token:
            self.log("No token available. Please log in first.", Fore.RED)
            return None
        
        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}
        requests.put(f"{self.BASE_URL}/user-earn-hour", headers=headers)
        response = requests.get(f"{self.BASE_URL}/user-earn-hour", headers=headers)

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
            response = requests.get(f"{self.BASE_URL}/user-spin-logs", headers=headers)
            data = response.json().get("data", {})
            number_of_spins = data.get("numberSpin", 0)
            
            if number_of_spins == 0:
                self.log("No spin points remaining.", Fore.RED)
                return False
            
            response = requests.put(f"{self.BASE_URL}/user-spin-logs", headers=headers)

            if response.status_code == 200:
                data = response.json().get("data", {})
                points = data.get("point", 0)
                xp = data.get("xp", 0)
                usdt = data.get("usdt", 0)
                response = requests.get(f"{self.BASE_URL}/user-spin-logs", headers=headers)
                updated_data = response.json().get("data", {})
                updated_spins = updated_data.get("numberSpin", 0)
                self.log(f"Spin {spin_count} successful! Points: {points}, XP: {xp}, USDT: {usdt}, Spins left: {updated_spins}", Fore.GREEN)
                spin_count += 1
            else:
                message = data.get("message", "Unknown error")
                self.log(f"Spin failed at spin {spin_count}, message: {message}", Fore.RED)
                break

            time.sleep(5)

    def task(self):
        """Claim tasks from both basic-tasks and partner-tasks categories."""
        if not self.token:
            self.log("No token available. Please log in first.", Fore.RED)
            return None

        headers = {**self.headers, "Authorization": f"Bearer {self.token}"}
        task_ids = []  # To track claimed task IDs

        # Task Tipe 1: Basic Task
        # Mengambil task ID dengan GET
        self.log(f"{Fore.GREEN}Category: Task")
        response = requests.get(f"{self.BASE_URL}/tasks", headers=headers)
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
                    
                    do_task_response = requests.post(f"{self.BASE_URL}/tasks/do-task/{task_id}", headers=headers)

                    if do_task_response.status_code == 200 or do_task_response.status_code == 201:
                        self.log(f"Task '{task_name}' successfully claimed.", Fore.GREEN)
                    else:
                        self.log(f"Failed to complete task '{task_name}', status code: {do_task_response.status_code}", Fore.RED)
                else:
                    self.log(f"Task '{task_name}' is either completed or cannot be claimed.", Fore.YELLOW)
                
                time.sleep(5)

        # Task Tipe 2: Basic Task
        # Mengambil basic task ID dengan GET
        self.log(f"{Fore.GREEN}Category: Basic Task")
        response = requests.get(f"{self.BASE_URL}/tasks/basic-tasks", headers=headers)
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
                    
                    do_task_response = requests.post(f"{self.BASE_URL}/tasks/basic-tasks/{task_id}", headers=headers)

                    if do_task_response.status_code == 200 or do_task_response.status_code == 201:
                        self.log(f"Basic Task '{task_name}' successfully claimed.", Fore.GREEN)
                    else:
                        self.log(f"Failed to complete basic task '{task_name}', status code: {do_task_response.status_code}", Fore.RED)
                else:
                    self.log(f"Basic Task '{task_name}' is either completed or cannot be claimed.", Fore.YELLOW)

                time.sleep(5)

        # Task Tipe 3: Partner Task
        # Mengambil partner task ID dengan GET
        self.log(f"{Fore.GREEN}Category: Partner Task")
        response = requests.get(f"{self.BASE_URL}/tasks/partner-tasks", headers=headers)
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
                    
                    do_task_response = requests.post(f"{self.BASE_URL}/tasks/partner-tasks/{task_id}", headers=headers)

                    if do_task_response.status_code == 200 or do_task_response.status_code == 201:
                        self.log(f"Partner Task '{task_name}' successfully claimed.", Fore.GREEN)
                    else:
                        self.log(f"Failed to complete partner task '{task_name}', status code: {do_task_response.status_code}", Fore.RED)
                else:
                    self.log(f"Partner Task '{task_name}' is either completed or cannot be claimed.", Fore.YELLOW)

                time.sleep(5)

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
            "keyword": ""
        }

        response = requests.get(f"{self.BASE_URL}/campaigns?page=1&limit=10&keyword=", headers=headers, json=payload)
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
        user_quest_response = requests.get(user_quest_url, headers=headers)

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

            put_response = requests.put(put_url, headers=headers, json=put_payload)
            
            if put_response.status_code == 200:
                try:
                    quest_data = put_response.json().get("data", {})
                    metadata = quest_data.get("metadata", {})
                    
                    quest_title = metadata.get("name", "Unknown Title")  
                    self.log(f"Completed quest: {quest_title}", Fore.GREEN)
                    
                except ValueError:
                    self.log("Failed to parse response JSON.", Fore.RED)
            else:
                try:
                    quest_data = put_response.json().get("data", {})
                    metadata = quest_data.get("metadata", {})
                    
                    quest_title = metadata.get("name", "Unknown Title")
                    self.log(f"Failed to complete quest: {quest_title}", Fore.RED)
                    
                except ValueError:
                    self.log("Failed to parse response JSON.", Fore.RED)

            time.sleep(5)
        return quest_ids  

    def run(self):
        """Main loop to log in and process each query for up to 6 hours."""
        index = 0
        config = self.load_config()

        while True:
            self.log(f"Login To User {index+1}/{len(self.query_list)}")
            self.login(index)
            if config["auto_farming"]:
                self.log("Farming: On", Fore.GREEN)
                self.start_farming()
            else:
                self.log(f"Farming: {Fore.RED}Off", Fore.GREEN)

            if config["auto_spin"]:
                self.log("Spin: On", Fore.GREEN)
                self.spin()
            else:
                self.log(f"Spin: {Fore.RED}Off", Fore.GREEN)

            if config["auto_task"]:
                self.log("Tasks: On", Fore.GREEN)
                self.task()
            else:
                self.log(f"Tasks: {Fore.RED}Off", Fore.GREEN)

            if config["auto_campaign"]:
                self.log("Campaign: On", Fore.GREEN)
                self.campain()
            else:
                self.log(f"Campaign: {Fore.RED}Off", Fore.GREEN)

            index += 1 
            if index >= len(self.query_list):
                index = 0  
                self.log(f"Restarting In {config["delay_iteration"]} Second")
                time.sleep(config["delay_iteration"])

            self.log(f"Moving to the next account in {config["delay_change_account"]} Second", Fore.CYAN)
            time.sleep(config["delay_change_account"])

            self.log("---------------------------------------")

if __name__ == "__main__":
    auth = Auth()
    auth.run()
