import json
from datetime import datetime
from flask_bcrypt import Bcrypt
from filelock import FileLock

AUTH_LOCK = "./auth/auth.lock"      #Location of the 'auth.lock' file for filelock library
TIMEOUT_AFTER = 5        #Number of minutes after which the IP is timed out.
TIMEOUT_FOR = 10         #Number of minutes for which the IP would be timed out.
TIMEOUT_ATTEMPTS = 5     #Number of attempts after which the IP is timed out.

def write_to_json(data, path):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)

def timeout_helper(user_ip: str, failed_login_attempts: dict[str:list[str]], timed_out_ips: dict[str, str]) -> None:
    """
    This function adds the IP into failed_login_attempts.json file if login credentials are incorrect and also times out the IP for 'TIMEOUT_FOR'
    minutes if the IP do 'TIMEOUT_ATTEMPTS' number of login failed attempts within 'TIMEOUT_AFTER' minutes.
    """
    if user_ip not in failed_login_attempts:      #If IP is not in failed_login_attempts.json, then add the IP to the json file.
            failed_login_attempts[user_ip] = [datetime.now().isoformat()]
            write_to_json(failed_login_attempts, "./auth/failed_login_attempts.json")
    else:       #If IP already in failed_login_attempts.json, then check if eligible for timeout.
        first_failed_login_attempt_time = datetime.fromisoformat(failed_login_attempts[user_ip][0])
        first_failed_login_attempt_delta = datetime.now() - first_failed_login_attempt_time
        first_failed_login_attempt_minutes = first_failed_login_attempt_delta.total_seconds() / 60
        failed_login_attempts[user_ip].append(datetime.now().isoformat())
        write_to_json(failed_login_attempts, "./auth/failed_login_attempts.json")

        if first_failed_login_attempt_minutes <= TIMEOUT_AFTER and len(failed_login_attempts[user_ip]) >= TIMEOUT_ATTEMPTS:     #Checking IP for timeout condition.
            timed_out_ips[user_ip] = datetime.now().isoformat()
            write_to_json(timed_out_ips, "./auth/timed_out_ips.json")
            del failed_login_attempts[user_ip]
            write_to_json(failed_login_attempts, "./auth/failed_login_attempts.json")


def authenticate_user(User, request, bcrypt:Bcrypt) -> tuple[bool, str]:
    """
    This function authenticates the credentials for login and times out the IP after too many failed login attempts.
    """
    with FileLock(AUTH_LOCK):       #File lock for the case where 2 requests tried to modify the files at the same time.
        with open("./auth/failed_login_attempts.json", "r") as f:
            failed_login_attempts = json.load(f)

        with open("./auth/timed_out_ips.json", "r") as f:
            timed_out_ips = json.load(f)

        user_ip = request.remote_addr
        
        if user_ip in timed_out_ips:        #Checking if the IP is timed out.
            if ((datetime.now() - datetime.fromisoformat(timed_out_ips[user_ip])).total_seconds() / 60) <= TIMEOUT_FOR:
                return False, "LOGIN TIMEOUT! Too many failed attempts. Try again later."
            else:
                del  timed_out_ips[user_ip]
                write_to_json(timed_out_ips, "./auth/timed_out_ips.json")

        elif user_ip in failed_login_attempts and ((datetime.now() - datetime.fromisoformat(failed_login_attempts[user_ip][-1])).total_seconds() / 60) >= TIMEOUT_AFTER:     #To delete the IP's entries form failed_login_attempt.json if it's been more than 5 minutes since the last failed attempt.
            del failed_login_attempts[user_ip]
            write_to_json(failed_login_attempts, "./auth/failed_login_attempts.json")

        #Getting the credentials filled by user
        data = request.form
        username = data.get("username")
        password = data.get("password")
        matched_user = User.query.filter(User.username == username).first()     #Checking if username exists in users database or not.

        if matched_user is None:        #User does not exists in users database.
            timeout_helper(user_ip, failed_login_attempts, timed_out_ips)
            return False, "Invalid username or password"

        else:                           #User exists in users database, then checking for password.
            if bcrypt.check_password_hash(matched_user.password, password):
                failed_login_attempts.pop(user_ip, None)
                write_to_json(failed_login_attempts, "./auth/failed_login_attempts.json")
                return True, matched_user
            else:
                timeout_helper(user_ip, failed_login_attempts, timed_out_ips)
                return False, "Invalid username or password"